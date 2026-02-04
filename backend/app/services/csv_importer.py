import pandas as pd
from datetime import datetime
from app import db
from app.models import Order, OrderItem, Customer, AuditLog
from werkzeug.utils import secure_filename
import logging
import os

logger = logging.getLogger(__name__)


class CSVImporterValidator:
    """Validador de seguridad para archivos CSV"""
    
    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 10000
    
    @staticmethod
    def validate_file(file):
        """
        Validar archivo antes de procesar
        
        Args:
            file: FileStorage object from Flask request
            
        Raises:
            ValueError: Si el archivo no es válido
        """
        if not file:
            raise ValueError("No se proporcionó archivo")
        
        # Check filename
        filename = secure_filename(file.filename)
        if not filename:
            raise ValueError("Nombre de archivo inválido")
        
        # Check extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in CSVImporterValidator.ALLOWED_EXTENSIONS:
            raise ValueError(f"Solo se permiten archivos {CSVImporterValidator.ALLOWED_EXTENSIONS}")
        
        return True
    
    @staticmethod
    def validate_row_count(df):
        """Validar número de filas en DataFrame"""
        if len(df) > CSVImporterValidator.MAX_ROWS:
            raise ValueError(f"Archivo contiene {len(df)} filas, máximo permitido: {CSVImporterValidator.MAX_ROWS}")
        
        return True
    
    @staticmethod
    def sanitize_string(value, max_length=500):
        """Sanitizar string para prevenir inyección"""
        if value is None or pd.isna(value):
            return None
        
        # Convert to string and strip
        value = str(value).strip()
        
        # Remove null bytes and control characters
        value = value.replace('\x00', '')
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Truncate to max length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value if value else None


STATUS_MAP = {
    # Planeación / Liberaciones
    'PLANEACION': 'pending',
    'LIB NP5': 'in_production',
    'LIB NP4': 'in_production',
    'LIB FLXR': 'in_production',
    'LIB NP': 'in_production',

    # Producción / Saldos abiertos
    'SALDO POR CERRAR': 'in_production',

    # Listo para envío / por facturar
    'PT': 'ready',
    'PT LOGISTICA': 'ready',
    'SOLO FACT': 'ready',

    # Retenidos
    'RETENIDO': 'pending',

    # Cancelaciones
    'CANCELACION SIST': 'delivered',
    'CANCELACION': 'delivered',

    # Materia prima / Compras (por defecto se considera pendiente)
    'MP': 'pending',
    'MP FLEXCON': 'pending',
    'MP RICOH': 'pending',
}

PRIORITY_MAP = {
    'A': 1,
    'B': 2,
    'C': 3,
    'D': 4,
    'E': 4
}


def _parse_date(value):
    if not value or pd.isna(value):
        return None
    for fmt in ['%d/%m/%y', '%d/%m/%Y', '%d-%m-%Y', '%d-%m-%y']:
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


def _to_number(value):
    if value is None or value == '' or pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return value
    try:
        return float(str(value).replace(',', ''))
    except ValueError:
        return 0


def import_backorders_from_csv(path: str, user_id: int | None = None, test_mode: bool = False):
    """
    Importa datos de backorder desde CSV con validaciones de seguridad.
    
    Args:
        path: Ruta al archivo CSV
        user_id: ID del usuario que realiza la importación (opcional)
        test_mode: Si es True, agrega prefijo 'TEST-' a los números de orden
        
    Returns:
        Dict con estadísticas de importación
        
    Raises:
        ValueError: Si el archivo no es válido o contiene datos inválidos
    """
    # Validar que el archivo existe
    if not os.path.exists(path):
        raise ValueError(f"Archivo no encontrado: {path}")
    
    # Validar tamaño
    file_size = os.path.getsize(path)
    if file_size > CSVImporterValidator.MAX_FILE_SIZE:
        raise ValueError(f"Archivo muy grande: {file_size} bytes (máximo: {CSVImporterValidator.MAX_FILE_SIZE})")
    
    try:
        # Leer CSV con límite de filas
        df = pd.read_csv(path, encoding='latin-1', nrows=CSVImporterValidator.MAX_ROWS + 1)
    except Exception as e:
        logger.error(f"Error leyendo CSV: {e}")
        raise ValueError(f"Error leyendo archivo CSV: {str(e)}")
    
    # Validar número de filas
    CSVImporterValidator.validate_row_count(df)
    
    # Sanitizar nombres de columnas
    df.columns = [CSVImporterValidator.sanitize_string(c, max_length=100) or f'col_{i}' 
                  for i, c in enumerate(df.columns)]

    new_orders = 0
    updated_orders = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # Sanitizar y validar order number
            order_number = CSVImporterValidator.sanitize_string(row.get('No. Pedido', ''), max_length=50)
            if not order_number:
                continue
            
            # Agregar prefijo TEST- si está en modo de pruebas
            if test_mode:
                order_number = f"TEST-{order_number}"

            # Sanitizar campos
            info = CSVImporterValidator.sanitize_string(row.get('INFO', ''), max_length=100)
            if info:
                info = info.upper()
            else:
                info = ''
            
            # Normalizar claves y aplicar reglas adicionales
            status = STATUS_MAP.get(info, None)
            if status is None:
                # 'PT' como estado exacto (evitar coincidir con 'PTE')
                if info in ('PT', 'PT LOGISTICA', 'SOLO FACT'):
                    status = 'ready'
                elif info.startswith('MP'):
                    status = 'pending'
                elif info.startswith('LIB') or 'LIBERACION' in info:
                    status = 'in_production'
                elif 'CANCEL' in info:
                    status = 'delivered'
                else:
                    status = 'pending'
            
            priority_str = CSVImporterValidator.sanitize_string(row.get('ABCD', ''), max_length=10)
            priority = PRIORITY_MAP.get(priority_str.upper() if priority_str else '', 3)

            order = Order.query.filter_by(order_number=order_number).first()

            customer_code = CSVImporterValidator.sanitize_string(row.get('Cve', ''), max_length=50)
            customer_name = CSVImporterValidator.sanitize_string(row.get('Cliente', ''), max_length=200)
            
            # En modo prueba, agregar prefijo también al código de cliente
            if test_mode:
                customer_code = f"TEST-{customer_code}" if customer_code else ""
            
            customer = None
            if customer_code:
                customer = Customer.query.filter_by(customer_code=customer_code).first()
                if not customer:
                customer = Customer(customer_code=customer_code, name=customer_name, erp_source='csv', erp_id=customer_code)
                db.session.add(customer)
                db.session.flush()

        if order:
            updated_orders += 1
        else:
            order = Order(order_number=order_number)
            new_orders += 1
            db.session.add(order)

        order.total_amount = _to_number(row.get('Total')) or order.total_amount
        # Concatenar vendedor si hay info
        vend = str(row.get('Vend', '')).strip()
        vendedores = str(row.get('VENDEDORES', '')).strip()
        sales_rep = vend if vend else vendedores
        order.sales_rep = sales_rep or order.sales_rep

        # Notas adicionales
        nota = str(row.get('Nota', '')).strip()
        if nota and nota.lower() != 'nan':
             current_notes = order.customer_service_notes or ''
             if nota not in current_notes:
                 order.customer_service_notes = f"{current_notes}\n{nota}".strip()

        order.customer_id = customer.id if customer else order.customer_id
        order.customer_name = customer_name or order.customer_name
        order.order_date = _parse_date(row.get('F.Pedido')) or order.order_date
        order.promised_date = _parse_date(row.get('F. Venci. Ped')) or order.promised_date
        order.requested_date = _parse_date(row.get('F. Soli. Clie')) or order.requested_date
        order.status = status
        order.priority = priority
        order.is_backorder = True
        order.backorder_reason = info
        order.erp_source = 'csv_test' if test_mode else 'csv'
        order.erp_id = order_number
        order.last_sync = datetime.utcnow()

        # START - Tracking departamental inteligente derivado del INFO
        
        # Resetear estados por defecto si es una nueva actualización para tener una base limpia
        # (Opcional, pero ayuda a que el estado actual refleje exactamente el CSV)
        
        # 1. Planeación
        if info == 'PLANEACION' or 'PLANEACION' in info:
            order.planning_status = 'pending'
            order.production_status = 'pending'
            order.warehouse_status = 'pending'
        
        # 2. Materia Prima / Almacén
        elif info.startswith('MP'):
            order.planning_status = 'approved'
            order.warehouse_status = 'material_missing'
            order.purchasing_status = 'ordered'
            order.production_status = 'pending'
            
        # 3. Liberación / En Cola
        elif info.startswith('LIB') or 'LIBERACION' in info:
            order.planning_status = 'approved'
            order.warehouse_status = 'material_available'
            order.production_status = 'pending'
            
        # 4. En Producción / Saldos
        elif info == 'SALDO POR CERRAR' or 'SALDO' in info:
            order.planning_status = 'approved'
            order.warehouse_status = 'material_available'
            order.production_status = 'in_process'
        
        # 5. Producto Terminado / Logística
        elif info in ('PT', 'PT LOGISTICA', 'PT ALMACEN'):
             order.planning_status = 'approved'
             order.production_status = 'completed'
             order.warehouse_status = 'material_available' # Ya se usó
             order.logistics_status = 'ready_to_ship'
        
        # 6. Facturación / Enviado
        elif info in ('SOLO FACT', 'SOLO FACTURAR', 'ENVIADO'):
             order.planning_status = 'approved'
             order.production_status = 'completed'
             order.logistics_status = 'shipped'
        
        # 7. Rechazado / Retenido
        elif 'RETENIDO' in info:
            order.planning_status = 'rejected'
        
        # Default fallback para status general
        # Esto asegura que el status global (legacy) coincida con el flujo
        if order.logistics_status == 'shipped':
            order.status = 'shipped'
        elif order.logistics_status == 'ready_to_ship':
            order.status = 'ready'
        elif order.production_status == 'in_process':
            order.status = 'in_production'
        
        # END - Tracking departamental

        # Items
        sku = str(row.get('Sku item', '')).strip()
        desc = str(row.get('Descripcion', '')).strip()
        qty_ord = _to_number(row.get('C.Orded.'))
        qty_ship = _to_number(row.get('C.Surtida'))
        qty_pending = _to_number(row.get('C.XSurtir'))
        unit = str(row.get('U/M', '')).strip() or None
        work_order = str(row.get('OT', '')).strip()

        # Especificaciones
        specs = {
            'MP': str(row.get('MP', '')).strip(),
            'ANCHO': str(row.get('ANCHO', '')).strip(),
            'ML_UV': _to_number(row.get('ML UV')),
            'ML_TOTAL': _to_number(row.get('ML TOTAL')),
            'M2': _to_number(row.get('M2')),
            'F_EMB_PLAN': str(row.get('F. Emb. Plan', '')).strip(),
            'F_MODIFICADA': str(row.get('F. MODIFICADA', '')).strip(),
            'DIAS_LIB': str(row.get('Dias Lib', '')).strip(),
            'DIAS_VENCI': str(row.get('Dias Venci.', '')).strip()
        }
        # Limpiar specs vacias
        specs = {k: v for k, v in specs.items() if v and v != 'nan' and v != 0}

        if sku:
            item = OrderItem.query.filter_by(order_id=order.id, item_code=sku).first()
            if not item:
                item = OrderItem(order_id=order.id, item_code=sku)
                db.session.add(item)
            item.item_description = desc or item.item_description
            item.quantity_ordered = qty_ord if qty_ord is not None else item.quantity_ordered
            item.quantity_shipped = qty_ship if qty_ship is not None else item.quantity_shipped
            item.status = order.status
            item.unit = unit
            item.work_order = work_order
            
            # Actualizar especificaciones (merge)
            current_specs = item.specifications or {}
            current_specs.update(specs)
            item.specifications = current_specs

            # Guardar pendiente en quantity_produced como proxy si no hay campo específico
            item.quantity_produced = qty_ord - qty_pending if qty_ord else item.quantity_produced

    db.session.commit()

    if user_id:
        log = AuditLog(
            user_id=user_id,
            action='import_csv_test' if test_mode else 'import_csv',
            entity='order',
            entity_id='bulk',
            details={'file': path, 'new': new_orders, 'updated': updated_orders, 'test_mode': test_mode}
        )
        db.session.add(log)
        db.session.commit()

    return {'new_orders': new_orders, 'updated_orders': updated_orders}
