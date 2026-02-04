"""
Conector para MONGUS ERP
Implementa conexión vía API REST con retry y circuit breaker
"""

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from datetime import datetime
import logging
import time
from .base_connector import BaseERPConnector
from .resilience import with_retry, StructuredLogger

logger = logging.getLogger(__name__)


class MongusConnector(BaseERPConnector):
    """Conector para MONGUS ERP vía API"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key', '')
        self.session = None
        
    def connect(self):
        """Establecer sesión con API de MONGUS"""
        try:
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
            logger.info("Sesión establecida con MONGUS API")
            return True
        except Exception as e:
            logger.error(f"Error estableciendo sesión con MONGUS: {str(e)}")
            raise
    
    def disconnect(self):
        """Cerrar sesión"""
        if self.session:
            self.session.close()
            self.session = None
            logger.info("Sesión cerrada con MONGUS")
    
    def test_connection(self):
        """Verificar conexión con API"""
        try:
            self.connect()
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.default_timeout
            )
            self.disconnect()
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Test de conexión falló: {str(e)}")
            return False
    
    @with_retry(
        max_attempts=3,
        backoff_base=2.0,
        exceptions=(Timeout, ConnectionError, RequestException)
    )
    def _make_request(self, endpoint, method='GET', params=None, data=None):
        """
        Helper para hacer requests a la API con retry y logging estructurado.
        """
        if not self.session:
            self.connect()
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.default_timeout
                )
            elif method == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    timeout=self.default_timeout
                )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log estructurado
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint=endpoint,
                method=method,
                status=response.status_code,
                duration_ms=duration_ms
            )
            
            response.raise_for_status()
            return response.json()
            
        except RequestException as e:
            duration_ms = (time.time() - start_time) * 1000
            status = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            
            # Log estructurado de error
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint=endpoint,
                method=method,
                status=status or 0,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            logger.error(f"Error en request a MONGUS {endpoint}: {str(e)}")
            raise  # Re-raise para que retry pueda manejarlo
    
    def fetch_orders(self, start_date=None, end_date=None):
        """Obtener órdenes desde MONGUS API"""
        params = {}
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # Endpoint adaptable según API real de MONGUS
        data = self._make_request('/orders', params=params)
        
        if data and 'orders' in data:
            logger.info(f"Se obtuvieron {len(data['orders'])} órdenes de MONGUS")
            return data['orders']
        
        return []
    
    def fetch_materials(self):
        """Obtener inventario de materiales"""
        data = self._make_request('/inventory/materials')
        
        if data and 'materials' in data:
            logger.info(f"Se obtuvieron {len(data['materials'])} materiales de MONGUS")
            return data['materials']
        
        return []
    
    def fetch_customers(self):
        """Obtener clientes"""
        data = self._make_request('/customers')
        
        if data and 'customers' in data:
            logger.info(f"Se obtuvieron {len(data['customers'])} clientes de MONGUS")
            return data['customers']
        
        return []
    
    def fetch_production_data(self, order_id=None):
        """Obtener datos de producción"""
        endpoint = '/production'
        params = {}
        
        if order_id:
            params['order_id'] = order_id
        
        data = self._make_request(endpoint, params=params)
        
        if data and 'production' in data:
            return data['production']
        
        return []
