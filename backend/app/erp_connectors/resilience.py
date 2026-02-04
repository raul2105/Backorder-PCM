"""
Utilidades de Resiliencia para Conectores ERP
- Retry con backoff exponencial
- Circuit Breaker por fuente
- Logging estructurado
"""

import time
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Any, Optional
import json

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Excepción cuando el circuit breaker está abierto"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker simple por fuente ERP.
    Si falla N veces en ventana T, suspende por X minutos.
    """
    
    # Estado compartido por fuente (class-level dict)
    _breakers = {}
    
    def __init__(
        self, 
        source: str,
        failure_threshold: int = 5,
        window_seconds: int = 300,  # 5 minutos
        timeout_seconds: int = 300   # 5 minutos suspendido
    ):
        self.source = source
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.timeout_seconds = timeout_seconds
        
        # Inicializar estado si no existe
        if source not in CircuitBreaker._breakers:
            CircuitBreaker._breakers[source] = {
                'state': 'closed',  # closed, open, half-open
                'failures': [],
                'opened_at': None,
                'last_success': None
            }
    
    @property
    def state(self):
        return CircuitBreaker._breakers[self.source]
    
    def is_open(self) -> bool:
        """Verificar si el circuit breaker está abierto"""
        if self.state['state'] == 'closed':
            return False
        
        if self.state['state'] == 'open':
            # Verificar si ya pasó el timeout
            if self.state['opened_at']:
                elapsed = (datetime.utcnow() - self.state['opened_at']).total_seconds()
                if elapsed >= self.timeout_seconds:
                    # Transición a half-open para probar
                    self.state['state'] = 'half-open'
                    logger.info(f"Circuit breaker {self.source} transicionó a HALF-OPEN")
                    return False
            return True
        
        # half-open: permitir request pero con cautela
        return False
    
    def record_success(self):
        """Registrar éxito"""
        self.state['failures'] = []
        self.state['last_success'] = datetime.utcnow()
        
        if self.state['state'] != 'closed':
            self.state['state'] = 'closed'
            logger.info(f"Circuit breaker {self.source} CERRADO (éxito)")
    
    def record_failure(self):
        """Registrar falla"""
        now = datetime.utcnow()
        self.state['failures'].append(now)
        
        # Limpiar fallas fuera de la ventana
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.state['failures'] = [
            f for f in self.state['failures'] if f > cutoff
        ]
        
        # Verificar si se alcanzó el threshold
        if len(self.state['failures']) >= self.failure_threshold:
            self.state['state'] = 'open'
            self.state['opened_at'] = now
            logger.warning(
                f"Circuit breaker {self.source} ABIERTO "
                f"({len(self.state['failures'])} fallas en {self.window_seconds}s)"
            )
    
    def get_status(self) -> dict:
        """Obtener estado del circuit breaker"""
        return {
            'source': self.source,
            'state': self.state['state'],
            'failure_count': len(self.state['failures']),
            'opened_at': self.state['opened_at'].isoformat() if self.state['opened_at'] else None,
            'last_success': self.state['last_success'].isoformat() if self.state['last_success'] else None
        }


def with_retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator para retry con backoff exponencial.
    
    Args:
        max_attempts: Número máximo de intentos
        backoff_base: Base para backoff exponencial (espera = base^intento)
        exceptions: Tupla de excepciones a reintentar
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        # Calcular delay con backoff exponencial
                        delay = backoff_base ** (attempt - 1)
                        
                        logger.warning(
                            f"Intento {attempt}/{max_attempts} falló para {func.__name__}: {str(e)}. "
                            f"Reintentando en {delay}s..."
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Todos los intentos ({max_attempts}) fallaron para {func.__name__}: {str(e)}"
                        )
            
            # Si llegamos aquí, todos los intentos fallaron
            raise last_exception
        
        return wrapper
    return decorator


class StructuredLogger:
    """
    Logger estructurado para requests ERP.
    Genera logs en formato JSON con campos consistentes.
    """
    
    @staticmethod
    def log_request(
        source: str,
        endpoint: str,
        method: str = 'GET',
        status: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        extra: Optional[dict] = None
    ):
        """
        Log estructurado de un request.
        
        Args:
            source: Nombre del ERP (syteline, mongus, intranet)
            endpoint: Endpoint o query llamado
            method: Método HTTP o tipo de operación
            status: Código de status (200, 500, etc)
            duration_ms: Duración en milisegundos
            error: Mensaje de error si aplica
            extra: Campos adicionales
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': source,
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'duration_ms': round(duration_ms, 2) if duration_ms else None,
            'success': status is not None and 200 <= status < 300,
            'error': error
        }
        
        if extra:
            log_data.update(extra)
        
        # Remover campos None
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Determinar nivel de log
        if error or (status and status >= 500):
            log_level = logging.ERROR
        elif status and status >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        logger.log(log_level, json.dumps(log_data))


def measure_time(func: Callable) -> Callable:
    """
    Decorator para medir tiempo de ejecución.
    Útil para calcular duration_ms en logs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            return result, duration_ms
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            raise e
    return wrapper
