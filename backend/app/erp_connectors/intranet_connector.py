"""
Conector para Intranet Interna
Implementa conexión con API REST de intranet corporativa con retry y circuit breaker
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.exceptions import RequestException, Timeout, ConnectionError
from datetime import datetime
import logging
import time
from .base_connector import BaseERPConnector
from .resilience import with_retry, StructuredLogger

logger = logging.getLogger(__name__)


class IntranetConnector(BaseERPConnector):
    """Conector para Intranet Interna vía API"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_url = config.get('base_url', '')
        self.auth_type = config.get('auth_type', 'none')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.session = None
        
    def connect(self):
        """Establecer sesión con API de Intranet"""
        try:
            self.session = requests.Session()
            
            # Configurar autenticación según tipo
            if self.auth_type == 'basic':
                self.session.auth = HTTPBasicAuth(self.username, self.password)
            elif self.auth_type == 'digest':
                self.session.auth = HTTPDigestAuth(self.username, self.password)
            elif self.auth_type == 'bearer':
                # Para bearer token, obtener token primero
                token = self._get_bearer_token()
                if token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {token}'
                    })
            
            self.session.headers.update({
                'Content-Type': 'application/json'
            })
            
            logger.info("Sesión establecida con Intranet API")
            return True
            
        except Exception as e:
            logger.error(f"Error estableciendo sesión con Intranet: {str(e)}")
            raise
    
    def _get_bearer_token(self):
        """Obtener token de autenticación Bearer con timeout"""
        try:
            # Adaptar según endpoint real de autenticación
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    'username': self.username,
                    'password': self.password
                },
                timeout=self.default_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('token') or data.get('access_token')
            
        except Exception as e:
            logger.error(f"Error obteniendo token: {str(e)}")
        
        return None
    
    def disconnect(self):
        """Cerrar sesión"""
        if self.session:
            self.session.close()
            self.session = None
            logger.info("Sesión cerrada con Intranet")
    
    def test_connection(self):
        """Verificar conexión"""
        try:
            self.connect()
            response = self.session.get(
                f"{self.base_url}/api/status",
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
        Helper para hacer requests con retry y logging estructurado.
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
                    verify=False,  # verify=False para cert internos
                    timeout=self.default_timeout
                )
            elif method == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    verify=False,
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
            
            logger.error(f"Error en request a Intranet {endpoint}: {str(e)}")
            raise  # Re-raise para que retry pueda manejarlo
    
    def fetch_orders(self, start_date=None, end_date=None):
        """Obtener órdenes desde Intranet"""
        params = {
            'status': 'active'
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        # Adaptar endpoint según API real
        data = self._make_request('/api/orders', params=params)
        
        if data:
            orders = data if isinstance(data, list) else data.get('data', [])
            logger.info(f"Se obtuvieron {len(orders)} órdenes de Intranet")
            return orders
        
        return []
    
    def fetch_materials(self):
        """Obtener inventario"""
        data = self._make_request('/api/inventory')
        
        if data:
            materials = data if isinstance(data, list) else data.get('data', [])
            logger.info(f"Se obtuvieron {len(materials)} materiales de Intranet")
            return materials
        
        return []
    
    def fetch_customers(self):
        """Obtener clientes"""
        data = self._make_request('/api/customers')
        
        if data:
            customers = data if isinstance(data, list) else data.get('data', [])
            logger.info(f"Se obtuvieron {len(customers)} clientes de Intranet")
            return customers
        
        return []
    
    def fetch_production_data(self, order_id=None):
        """Obtener datos de producción"""
        endpoint = '/api/production'
        params = {}
        
        if order_id:
            params['order_id'] = order_id
        
        data = self._make_request(endpoint, params=params)
        
        if data:
            production = data if isinstance(data, list) else data.get('data', [])
            return production
        
        return []
