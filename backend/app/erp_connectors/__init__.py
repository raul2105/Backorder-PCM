"""
Factory para manejar diferentes conectores ERP
"""

import yaml
import os
from .syteline_connector import SytelineConnector
from .mongus_connector import MongusConnector
from .intranet_connector import IntranetConnector

def load_config():
    """Cargar configuración de ERPs"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['erp_systems']


class ERPConnectorFactory:
    """Factory para crear conectores ERP según configuración"""
    
    @staticmethod
    def get_connector(erp_name):
        """
        Obtener conector específico
        
        Args:
            erp_name: Nombre del ERP ('syteline', 'mongus', 'intranet')
        
        Returns:
            Instancia del conector correspondiente
        """
        config = load_config()
        
        connectors = {
            'syteline': SytelineConnector,
            'mongus': MongusConnector,
            'intranet': IntranetConnector
        }
        
        if erp_name not in connectors:
            raise ValueError(f"Conector ERP '{erp_name}' no soportado")
        
        erp_config = config.get(erp_name)
        
        if not erp_config:
            raise ValueError(f"Configuración para '{erp_name}' no encontrada")
        
        connector_class = connectors[erp_name]
        return connector_class(erp_config)
    
    @staticmethod
    def get_all_active_connectors():
        """Obtener todos los conectores activos"""
        config = load_config()
        active_connectors = []
        
        for erp_name, erp_config in config.items():
            if erp_config.get('enabled', False):
                try:
                    connector = ERPConnectorFactory.get_connector(erp_name)
                    active_connectors.append({
                        'name': erp_name,
                        'connector': connector
                    })
                except Exception as e:
                    print(f"Error cargando conector {erp_name}: {str(e)}")
        
        return active_connectors
