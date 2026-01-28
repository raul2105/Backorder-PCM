"""
Servicio de Sincronización con ERPs
Maneja la sincronización automática de datos desde los diferentes ERPs
"""

from app import db, celery
from app.models import Order, OrderItem, Customer, Material
from app.erp_connectors import ERPConnectorFactory
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SyncService:
    """Servicio para sincronizar datos con ERPs"""
    
    @staticmethod
    def sync_orders_from_erp(erp_name):
        """Sincronizar órdenes desde un ERP específico"""
        try:
            connector = ERPConnectorFactory.get_connector(erp_name)
            
            if not connector.enabled:
                logger.info(f"{erp_name} está deshabilitado")
                return {'success': False, 'message': 'Conector deshabilitado'}
            
            # Obtener órdenes del ERP
            erp_orders = connector.fetch_orders()
            
            synced_count = 0
            updated_count = 0
            
            for erp_order in erp_orders:
                # Buscar si la orden ya existe
                order = Order.query.filter_by(
                    erp_source=erp_name,
                    erp_id=erp_order.get('order_number')
                ).first()
                
                if order:
                    # Actualizar orden existente
                    order.status = SyncService._map_status(erp_order.get('status'))
                    order.last_sync = datetime.utcnow()
                    updated_count += 1
                else:
                    # Crear nueva orden
                    customer = SyncService._get_or_create_customer(
                        erp_order.get('customer_id'),
                        erp_order.get('customer_name'),
                        erp_name
                    )
                    
                    order = Order(
                        order_number=erp_order.get('order_number'),
                        customer_id=customer.id,
                        customer_name=erp_order.get('customer_name'),
                        order_date=erp_order.get('order_date'),
                        promised_date=erp_order.get('promised_date'),
                        requested_date=erp_order.get('requested_date'),
                        status=SyncService._map_status(erp_order.get('status')),
                        erp_source=erp_name,
                        erp_id=erp_order.get('order_number'),
                        last_sync=datetime.utcnow()
                    )
                    
                    db.session.add(order)
                    synced_count += 1
                
                # Crear/actualizar items
                if 'items' in erp_order:
                    for item_data in erp_order['items']:
                        SyncService._sync_order_item(order, item_data)
            
            db.session.commit()
            
            logger.info(f"Sincronización completada: {synced_count} nuevas, {updated_count} actualizadas")
            
            return {
                'success': True,
                'new_orders': synced_count,
                'updated_orders': updated_count
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando órdenes desde {erp_name}: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def sync_materials_from_erp(erp_name):
        """Sincronizar materiales desde un ERP"""
        try:
            connector = ERPConnectorFactory.get_connector(erp_name)
            
            erp_materials = connector.fetch_materials()
            
            synced_count = 0
            updated_count = 0
            
            for erp_material in erp_materials:
                material = Material.query.filter_by(
                    erp_source=erp_name,
                    erp_id=erp_material.get('material_code')
                ).first()
                
                if material:
                    # Actualizar inventario
                    material.quantity_available = erp_material.get('quantity_available', 0)
                    material.quantity_reserved = erp_material.get('quantity_reserved', 0)
                    material.quantity_on_order = erp_material.get('quantity_on_order', 0)
                    material.last_sync = datetime.utcnow()
                    updated_count += 1
                else:
                    # Crear nuevo material
                    material = Material(
                        material_code=erp_material.get('material_code'),
                        description=erp_material.get('description'),
                        category=erp_material.get('category'),
                        quantity_available=erp_material.get('quantity_available', 0),
                        quantity_reserved=erp_material.get('quantity_reserved', 0),
                        quantity_on_order=erp_material.get('quantity_on_order', 0),
                        unit=erp_material.get('unit'),
                        minimum_stock=erp_material.get('minimum_stock', 0),
                        supplier_name=erp_material.get('supplier_name'),
                        lead_time_days=erp_material.get('lead_time_days'),
                        erp_source=erp_name,
                        erp_id=erp_material.get('material_code'),
                        last_sync=datetime.utcnow()
                    )
                    db.session.add(material)
                    synced_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'new_materials': synced_count,
                'updated_materials': updated_count
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando materiales: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _get_or_create_customer(customer_code, customer_name, erp_source):
        """Obtener o crear cliente"""
        customer = Customer.query.filter_by(
            customer_code=customer_code
        ).first()
        
        if not customer:
            customer = Customer(
                customer_code=customer_code,
                name=customer_name,
                erp_source=erp_source,
                erp_id=customer_code
            )
            db.session.add(customer)
            db.session.flush()
        
        return customer
    
    @staticmethod
    def _sync_order_item(order, item_data):
        """Sincronizar item de orden"""
        item = OrderItem.query.filter_by(
            order_id=order.id,
            item_code=item_data.get('item_code')
        ).first()
        
        if not item:
            item = OrderItem(
                order_id=order.id,
                item_code=item_data.get('item_code'),
                item_description=item_data.get('item_description'),
                quantity_ordered=item_data.get('quantity_ordered'),
                quantity_produced=item_data.get('quantity_produced', 0),
                quantity_shipped=item_data.get('quantity_shipped', 0),
                unit=item_data.get('unit')
            )
            db.session.add(item)
        else:
            item.quantity_produced = item_data.get('quantity_produced', 0)
            item.quantity_shipped = item_data.get('quantity_shipped', 0)
    
    @staticmethod
    def _map_status(erp_status):
        """Mapear estados del ERP a estados internos"""
        status_mapping = {
            'O': 'pending',
            'P': 'in_production',
            'R': 'ready',
            'S': 'shipped',
            'D': 'delivered',
            'Open': 'pending',
            'In Progress': 'in_production',
            'Released': 'in_production',
            'Complete': 'ready'
        }
        
        return status_mapping.get(erp_status, 'pending')


# Tareas Celery para sincronización automática
@celery.task
def sync_all_erps():
    """Tarea para sincronizar todos los ERPs activos"""
    active_connectors = ERPConnectorFactory.get_all_active_connectors()
    
    results = []
    for connector_info in active_connectors:
        erp_name = connector_info['name']
        
        # Sincronizar órdenes
        order_result = SyncService.sync_orders_from_erp(erp_name)
        
        # Sincronizar materiales
        material_result = SyncService.sync_materials_from_erp(erp_name)
        
        results.append({
            'erp': erp_name,
            'orders': order_result,
            'materials': material_result
        })
    
    return results
