
from app import create_app, db
from app.models import Order, OrderItem, Customer, AuditLog
from datetime import datetime, timedelta

def create_demo_data():
    app = create_app()
    with app.app_context():
        print("Creating Demo Data...")
        
        # Ensure demo customer
        cust = Customer.query.filter_by(customer_code='DEMO-001').first()
        if not cust:
            cust = Customer(customer_code='DEMO-001', name='CLIENTE DE EJEMPLO S.A.', erp_source='demo', erp_id='DEMO-001')
            db.session.add(cust)
            db.session.flush()
        
        # List of demo order numbers to clean up first
        demo_order_numbers = ["DEMO-PLAN-001", "DEMO-ALM-002", "DEMO-PROD-003", "DEMO-LOG-004"]
        
        # Delete existing demo orders to avoid specific constraint errors and ensure fresh state
        existing_orders = Order.query.filter(Order.order_number.in_(demo_order_numbers)).all()
        for ord in existing_orders:
            # Delete items first
            OrderItem.query.filter_by(order_id=ord.id).delete()
            db.session.delete(ord)
        
        db.session.commit()
        print(f"Cleaned up {len(existing_orders)} existing DEMO orders.")

        # Fixed past date to ensure they appear at the TOP of the list (Sorted by Priority ASC, Date ASC)
        # Using a date in the past ensures they are "overdue" and thus first in the list.
        # Backend sorts by promised_date ASC. Oldest dates first.
        base_date = datetime(2023, 1, 1) # Very old date

        # 1. Orden para Planeación (Recién llegada)
        o1 = Order(
            order_number="DEMO-PLAN-001",
            customer_id=cust.id,
            customer_name=cust.name + " (Planeación)",
            order_date=datetime.utcnow(),
            promised_date=base_date, # 2023
            status='pending',
            priority=1, # High priority
            is_backorder=True,
            backorder_reason="Recién ingresada para planeación",
            sales_rep="Juan Pérez",
            total_amount=1500.00,
            # Departments
            planning_status='pending',
            warehouse_status='pending',
            purchasing_status='pending',
            production_status='pending',
            logistics_status='pending'
        )
        db.session.add(o1)
        
        i1 = OrderItem(order=o1, item_code="SKU-1001", item_description="Etiqueta Premium 4x4", quantity_ordered=1000, unit="PZA", 
                      specifications={"MP": "Papel Couche", "Ancho": "100mm", "Avance": "100mm"}, work_order="OT-5001")
        db.session.add(i1)

        # 2. Orden para Almacén (Ya planeada, falta material)
        o2 = Order(
            order_number="DEMO-ALM-002",
            customer_id=cust.id,
            customer_name=cust.name + " (Almacén)",
            order_date=datetime.utcnow() - timedelta(days=1),
            promised_date=base_date + timedelta(days=1),
            status='pending',
            priority=1, # Changed to 1 to show on top
            is_backorder=True,
            backorder_reason="En espera de material",
            sales_rep="María González",
            total_amount=2300.50,
            # Departments
            planning_status='approved',
            warehouse_status='material_missing',
            purchasing_status='ordered',
            production_status='pending',
            logistics_status='pending'
        )
        db.session.add(o2)
        
        i2 = OrderItem(order=o2, item_code="SKU-2005", item_description="Etiqueta Térmica Directa", quantity_ordered=5000, unit="ROLLO", 
                      specifications={"MP": "Térmico Directo", "Ancho": "40mm", "Largo": "25mm"}, work_order="OT-5002")
        db.session.add(i2)
        
        # 3. Orden en Producción
        o3 = Order(
            order_number="DEMO-PROD-003",
            customer_id=cust.id,
            customer_name=cust.name + " (Producción)",
            order_date=datetime.utcnow() - timedelta(days=2),
            promised_date=base_date + timedelta(days=2),
            status='in_production',
            priority=1,
            is_backorder=True,
            backorder_reason="En máquina",
            sales_rep="Juan Pérez",
            total_amount=5000.00,
            # Departments
            planning_status='approved',
            warehouse_status='material_available',
            purchasing_status='received',
            production_status='in_process',
            logistics_status='pending'
        )
        db.session.add(o3)
        
        i3 = OrderItem(order=o3, item_code="SKU-3010", item_description="BOPP Transparente", quantity_ordered=20000, unit="ETIQ", 
                       quantity_produced=5000,
                      specifications={"MP": "BOPP", "Ancho": "50mm"}, work_order="OT-5003")
        db.session.add(i3)
        
        # 4. Orden Lista para Logística
        o4 = Order(
            order_number="DEMO-LOG-004",
            customer_id=cust.id,
            customer_name=cust.name + " (Logística)",
            order_date=datetime.utcnow() - timedelta(days=5),
            promised_date=base_date + timedelta(days=3),
            status='ready',
            priority=1, # Changed to 1 to show on top
            is_backorder=True,
            backorder_reason="Listo para embarque",
            sales_rep="Ana López",
            total_amount=890.00,
            # Departments
            planning_status='approved',
            warehouse_status='material_available',
            purchasing_status='received',
            production_status='completed',
            logistics_status='ready_to_ship'
        )
        db.session.add(o4)
        
        i4 = OrderItem(order=o4, item_code="SKU-4020", item_description="Etiqueta Logística", quantity_ordered=2000, unit="PZA", 
                      specifications={"MP": "Papel Mate", "Ancho": "4x6"}, work_order="OT-5004")
        db.session.add(i4)
        
        db.session.commit()
        print("Successfully recreated 4 DEMO orders with HIGH PRIORITY and PAST DATES (to appear first).")

if __name__ == "__main__":
    create_demo_data()
