"""
Servicio de Priorización de Backorders
Calcula prioridades automáticas basadas en reglas configurables
"""

from app import db
from app.models import Order, Material
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BackorderPriorityService:
    """Servicio para calcular y actualizar prioridades de backorders"""
    
    @staticmethod
    def calculate_priority(order):
        """
        Calcular prioridad de una orden basada en múltiples factores
        
        Returns:
            int: Prioridad calculada (1=urgente, 2=alta, 3=normal, 4=baja)
        """
        score = 0
        
        # Factor 1: Fecha prometida (40% del peso)
        days_until_due = (order.promised_date - datetime.utcnow()).days
        if days_until_due < 0:
            score += 40  # Ya vencida
        elif days_until_due <= 2:
            score += 35  # Muy urgente
        elif days_until_due <= 7:
            score += 25  # Urgente
        elif days_until_due <= 14:
            score += 15  # Moderado
        else:
            score += 5   # Normal
        
        # Factor 2: Prioridad del cliente (30% del peso)
        if order.customer:
            customer_priority = order.customer.priority_level
            if customer_priority == 1:
                score += 30
            elif customer_priority == 2:
                score += 20
            elif customer_priority == 3:
                score += 10
            else:
                score += 5
        
        # Factor 3: Disponibilidad de materiales (30% del peso)
        material_availability = BackorderPriorityService._check_material_availability(order)
        score += material_availability * 30
        
        # Convertir score a prioridad (1-4)
        if score >= 70:
            return 1  # Urgente
        elif score >= 50:
            return 2  # Alta
        elif score >= 30:
            return 3  # Normal
        else:
            return 4  # Baja
    
    @staticmethod
    def _check_material_availability(order):
        """
        Verificar disponibilidad de materiales para una orden
        
        Returns:
            float: Score de 0 a 1 (1 = todos los materiales disponibles)
        """
        # Simplificado - se puede expandir para verificar materiales específicos
        # Por ahora retorna un score basado en el inventario general
        
        low_stock_count = Material.query.filter(
            Material.quantity_available <= Material.minimum_stock
        ).count()
        
        total_materials = Material.query.count()
        
        if total_materials == 0:
            return 0.5
        
        availability_ratio = 1 - (low_stock_count / total_materials)
        return availability_ratio
    
    @staticmethod
    def update_all_backorder_priorities():
        """Actualizar prioridades de todos los backorders activos"""
        backorders = Order.query.filter_by(is_backorder=True).all()
        
        updated_count = 0
        
        for order in backorders:
            try:
                new_priority = BackorderPriorityService.calculate_priority(order)
                
                if order.priority != new_priority:
                    order.priority = new_priority
                    order.updated_at = datetime.utcnow()
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error calculando prioridad para orden {order.id}: {str(e)}")
        
        db.session.commit()
        
        logger.info(f"Actualización de prioridades completada: {updated_count} órdenes actualizadas")
        
        return updated_count
    
    @staticmethod
    def identify_new_backorders():
        """Identificar órdenes que deben marcarse como backorder"""
        # Órdenes pendientes con fecha prometida pasada o materiales faltantes
        today = datetime.utcnow()
        
        potential_backorders = Order.query.filter(
            Order.is_backorder == False,
            Order.status.in_(['pending', 'in_production']),
            Order.promised_date < today
        ).all()
        
        new_backorders = 0
        
        for order in potential_backorders:
            order.is_backorder = True
            order.backorder_reason = "Fecha prometida excedida"
            order.priority = BackorderPriorityService.calculate_priority(order)
            new_backorders += 1
        
        db.session.commit()
        
        logger.info(f"Identificados {new_backorders} nuevos backorders")
        
        return new_backorders
