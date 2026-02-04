"""
Conector Base para ERPs
Clase abstracta para implementar conectores específicos
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from .resilience import CircuitBreaker, StructuredLogger

logger = logging.getLogger(__name__)


class BaseERPConnector(ABC):
    """Clase base para conectores ERP"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.sync_interval = config.get('sync_interval', 300)
        self.last_sync = None
        self.source_name = self.__class__.__name__.replace('Connector', '').lower()
        
        # Circuit breaker por fuente
        self.circuit_breaker = CircuitBreaker(
            source=self.source_name,
            failure_threshold=config.get('circuit_breaker', {}).get('failure_threshold', 5),
            window_seconds=config.get('circuit_breaker', {}).get('window_seconds', 300),
            timeout_seconds=config.get('circuit_breaker', {}).get('timeout_seconds', 300)
        )
        
        # Timeouts configurables
        self.default_timeout = config.get('timeout', 30)  # 30 segundos por defecto
        
    @abstractmethod
    def connect(self):
        """Establecer conexión con el ERP"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Cerrar conexión con el ERP"""
        pass
    
    @abstractmethod
    def test_connection(self):
        """Verificar que la conexión funciona"""
        pass
    
    @abstractmethod
    def fetch_orders(self, start_date=None, end_date=None):
        """Obtener órdenes del ERP"""
        pass
    
    @abstractmethod
    def fetch_materials(self):
        """Obtener inventario de materiales"""
        pass
    
    @abstractmethod
    def fetch_customers(self):
        """Obtener lista de clientes"""
        pass
    
    @abstractmethod
    def fetch_production_data(self, order_id=None):
        """Obtener datos de producción"""
        pass
    
    def sync_all(self):
        """
        Sincronizar todos los datos con manejo de errores resiliente.
        Si el ERP falla, retorna error pero NO bloquea el sistema.
        """
        if not self.enabled:
            logger.warning(f"{self.source_name} está deshabilitado")
            return {
                'success': False,
                'error': 'Connector disabled',
                'source': self.source_name
            }
        
        # Verificar circuit breaker
        if self.circuit_breaker.is_open():
            error_msg = f"Circuit breaker abierto para {self.source_name}"
            logger.warning(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'source': self.source_name,
                'circuit_breaker': self.circuit_breaker.get_status()
            }
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Iniciando sincronización con {self.source_name}")
            
            self.connect()
            
            # Sincronizar diferentes entidades (cada una con su propio manejo de errores)
            orders = self._safe_fetch('orders', self.fetch_orders)
            materials = self._safe_fetch('materials', self.fetch_materials)
            customers = self._safe_fetch('customers', self.fetch_customers)
            
            self.last_sync = datetime.utcnow()
            duration_ms = (self.last_sync - start_time).total_seconds() * 1000
            
            self.disconnect()
            
            # Registrar éxito en circuit breaker
            self.circuit_breaker.record_success()
            
            # Log estructurado
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='sync_all',
                method='SYNC',
                status=200,
                duration_ms=duration_ms,
                extra={
                    'orders_count': len(orders) if orders else 0,
                    'materials_count': len(materials) if materials else 0,
                    'customers_count': len(customers) if customers else 0
                }
            )
            
            return {
                'success': True,
                'source': self.source_name,
                'orders': len(orders) if orders else 0,
                'materials': len(materials) if materials else 0,
                'customers': len(customers) if customers else 0,
                'timestamp': self.last_sync.isoformat(),
                'duration_ms': round(duration_ms, 2)
            }
            
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            error_msg = str(e)
            
            # Registrar falla en circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log estructurado de error
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='sync_all',
                method='SYNC',
                status=500,
                duration_ms=duration_ms,
                error=error_msg
            )
            
            logger.error(f"Error en sincronización de {self.source_name}: {error_msg}")
            
            return {
                'success': False,
                'source': self.source_name,
                'error': error_msg,
                'duration_ms': round(duration_ms, 2)
            }
    
    def _safe_fetch(self, entity_type: str, fetch_func):
        """
        Wrapper seguro para fetch functions.
        Si una entidad falla, no bloquea las demás.
        """
        try:
            return fetch_func()
        except Exception as e:
            logger.warning(f"Error fetching {entity_type} from {self.source_name}: {str(e)}")
            return []
    
    def get_circuit_breaker_status(self):
        """Obtener estado del circuit breaker"""
        return self.circuit_breaker.get_status()
