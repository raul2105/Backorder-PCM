"""
Conector Base para ERPs
Clase abstracta para implementar conectores específicos
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseERPConnector(ABC):
    """Clase base para conectores ERP"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.sync_interval = config.get('sync_interval', 300)
        self.last_sync = None
        
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
        """Sincronizar todos los datos"""
        if not self.enabled:
            logger.warning(f"{self.__class__.__name__} está deshabilitado")
            return None
            
        try:
            logger.info(f"Iniciando sincronización con {self.__class__.__name__}")
            
            self.connect()
            
            # Sincronizar diferentes entidades
            orders = self.fetch_orders()
            materials = self.fetch_materials()
            customers = self.fetch_customers()
            
            self.last_sync = datetime.utcnow()
            
            self.disconnect()
            
            return {
                'success': True,
                'orders': len(orders) if orders else 0,
                'materials': len(materials) if materials else 0,
                'customers': len(customers) if customers else 0,
                'timestamp': self.last_sync
            }
            
        except Exception as e:
            logger.error(f"Error en sincronización: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
