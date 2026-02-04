"""
Modelos de Base de Datos para Sistema de Backorder
"""

from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Order(db.Model):
    """Modelo de Órdenes"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name = db.Column(db.String(200))
    
    # Fechas
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    promised_date = db.Column(db.DateTime, nullable=True)
    requested_date = db.Column(db.DateTime)
    
    # Estado
    status = db.Column(db.String(50), default='pending')  # pending, in_production, ready, shipped, delivered
    priority = db.Column(db.Integer, default=3)  # 1=urgent, 2=high, 3=normal, 4=low
    
    # Tracking por Departamento (Flujo empresarial)
    planning_status = db.Column(db.String(50))  # pending, approved, rejected
    warehouse_status = db.Column(db.String(50))  # pending, material_available, material_missing
    purchasing_status = db.Column(db.String(50))  # pending, ordered, received
    production_status = db.Column(db.String(50))  # pending, in_process, completed
    logistics_status = db.Column(db.String(50))  # pending, ready_to_ship, shipped
    customer_service_notes = db.Column(db.Text)  # Notas de atención a clientes
    
    # Backorder
    is_backorder = db.Column(db.Boolean, default=False)
    backorder_reason = db.Column(db.Text)
    
    # Financial & CRM
    total_amount = db.Column(db.Float, default=0.0)
    sales_rep = db.Column(db.String(100))

    # ERP
    erp_source = db.Column(db.String(50))  # syteline, mongus, intranet
    erp_id = db.Column(db.String(100))
    last_sync = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')
    production_logs = db.relationship('ProductionLog', backref='order', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'promised_date': self.promised_date.isoformat() if self.promised_date else None,
            'status': self.status,
            'priority': self.priority,
            'is_backorder': self.is_backorder,
            'backorder_reason': self.backorder_reason,
            'total_amount': self.total_amount,
            'sales_rep': self.sales_rep,
            # Tracking por Departamento
            'planning_status': self.planning_status,
            'warehouse_status': self.warehouse_status,
            'purchasing_status': self.purchasing_status,
            'production_status': self.production_status,
            'logistics_status': self.logistics_status,
            'customer_service_notes': self.customer_service_notes
        }


class OrderItem(db.Model):
    """Items de Órdenes (Productos/Etiquetas)"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Producto
    item_code = db.Column(db.String(100), nullable=False, index=True)
    item_description = db.Column(db.Text)
    quantity_ordered = db.Column(db.Float, nullable=False)
    quantity_produced = db.Column(db.Float, default=0)
    quantity_shipped = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20))  # metros, unidades, etc.
    work_order = db.Column(db.String(50)) # OT
    
    # Especificaciones de etiqueta
    specifications = db.Column(JSON)  # ancho, largo, material, color, etc.
    
    # Estado
    status = db.Column(db.String(50), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(db.Model):
    """Modelo de Clientes"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    priority_level = db.Column(db.Integer, default=3)  # Prioridad del cliente
    
    # Contacto
    contact_person = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    
    # ERP
    erp_source = db.Column(db.String(50))
    erp_id = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    orders = db.relationship('Order', backref='customer', lazy='dynamic')


class Material(db.Model):
    """Inventario de Materiales"""
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # papel, adhesivo, tinta, etc.
    
    # Inventario
    quantity_available = db.Column(db.Float, default=0)
    quantity_reserved = db.Column(db.Float, default=0)
    quantity_on_order = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20))
    
    # Umbrales
    minimum_stock = db.Column(db.Float, default=0)
    reorder_point = db.Column(db.Float)
    
    # Proveedor
    supplier_name = db.Column(db.String(200))
    lead_time_days = db.Column(db.Integer)  # Tiempo de entrega
    
    # ERP
    erp_source = db.Column(db.String(50))
    erp_id = db.Column(db.String(100))
    last_sync = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductionLog(db.Model):
    """Log de Producción"""
    __tablename__ = 'production_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Producción
    production_date = db.Column(db.DateTime, default=datetime.utcnow)
    machine_id = db.Column(db.String(50))
    operator = db.Column(db.String(100))
    
    quantity_produced = db.Column(db.Float)
    quantity_rejected = db.Column(db.Float, default=0)
    
    # Status
    status = db.Column(db.String(50))  # started, in_progress, completed, paused
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    """Usuarios del Sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    
    # Roles
    role = db.Column(db.String(50), default='planning')  # admin, planning, warehouse, purchasing, production, logistics
    
    # Estado
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)


class AuditLog(db.Model):
    """Registro de auditoría de cambios realizados por usuarios"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., update_user, change_setting
    entity = db.Column(db.String(100))  # e.g., user, setting, order
    entity_id = db.Column(db.String(100))
    details = db.Column(JSON)  # cambios específicos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SystemSetting(db.Model):
    """Configuraciones del sistema (clave/valor)"""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(200), unique=True, nullable=False)
    value = db.Column(JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
