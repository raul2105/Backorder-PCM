"""
Conector para INFOR Syteline
Implementa conexión vía ODBC/SQL Server con retry y circuit breaker
"""

import pyodbc
from datetime import datetime, timedelta
import logging
import time
from .base_connector import BaseERPConnector
from .resilience import with_retry, StructuredLogger

logger = logging.getLogger(__name__)


class SytelineConnector(BaseERPConnector):
    """Conector para INFOR Syteline ERP"""
    
    def __init__(self, config):
        super().__init__(config)
        self.connection = None
        self.connection_config = config.get('connection', {})
        
    @with_retry(
        max_attempts=3,
        backoff_base=2.0,
        exceptions=(pyodbc.OperationalError, pyodbc.DatabaseError)
    )
    def connect(self):
        """Establecer conexión con Syteline vía ODBC con retry"""
        try:
            conn_str = (
                f"DRIVER={self.connection_config['driver']};"
                f"SERVER={self.connection_config['server']};"
                f"DATABASE={self.connection_config['database']};"
            )
            
            if self.connection_config.get('trusted_connection'):
                conn_str += "Trusted_Connection=yes;"
            else:
                conn_str += (
                    f"UID={self.connection_config['username']};"
                    f"PWD={self.connection_config['password']};"
                )
            
            # Timeout en la conexión (en segundos)
            self.connection = pyodbc.connect(
                conn_str, 
                timeout=self.default_timeout
            )
            
            # Configurar timeout para comandos (queries)
            self.connection.timeout = self.default_timeout
            
            logger.info("Conexión exitosa con Syteline")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a Syteline: {str(e)}")
            raise
    
    def disconnect(self):
        """Cerrar conexión"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Conexión cerrada con Syteline")
    
    def test_connection(self):
        """Verificar conexión"""
        try: con logging estructurado.
        Adaptar según estructura real de tablas en Syteline.
        """
        if not self.connection:
            self.connect()
        
        start_time = time.time()
        cursor = self.connection.cursor()
        
        # Query adaptable - modificar según esquema real de Syteline
        query = """
        SELECT 
            co.CoNum AS order_number,
            co.CustNum AS customer_id,
            c.Name AS customer_name,
            co.OrderDate AS order_date,
            co.DueDate AS promised_date,
            co.Stat AS status,
            co.CoLine AS line_number,
            coi.Item AS item_code,
            coi.Description AS item_description,
            coi.QtyOrderedConv AS quantity_ordered,
            coi.QtyShippedConv AS quantity_shipped,
            coi.UM AS unit
        FROM 
            co_mst co
            INNER JOIN customer_mst c ON co.CustNum = c.CustNum
            INNER JOIN coitem_mst coi ON co.CoNum = coi.CoNum
        WHERE 
            co.Stat IN ('O', 'P')  -- Open, Partially Shipped
        """
        
        if start_date:
            query += f" AND co.OrderDate >= '{start_date}'"
        if end_date:
            query += f" AND co.OrderDate <= '{end_date}'"
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log estructurado
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='fetch_orders',
                method='SQL',
                status=200,
                duration_ms=duration_ms,
                extra={'rows': len(results)}
            )
            
            logger.info(f"Se obtuvieron {len(results)} órdenes de Syteline")
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log estructurado de error
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='fetch_orders', con logging estructurado.
        Adaptar según estructura real de Syteline.
        """
        if not self.connection:
            self.connect()
        
        start_time = time.time()
        cursor = self.connection.cursor()
        
        # Query adaptable
        query = """
        SELECT 
            i.Item AS material_code,
            i.Description AS description,
            i.ProductCode AS category,
            il.QtyOnHand AS quantity_available,
            il.QtyReserved AS quantity_reserved,
            il.QtyOnOrder AS quantity_on_order,
            i.UM AS unit,
            i.MinimumQty AS minimum_stock,
            iv.Supplier AS supplier_name,
            iv.LeadTime AS lead_time_days
        FROM 
            item_mst i
            LEFT JOIN itemloc_mst il ON i.Item = il.Item
            LEFT JOIN itemvend_mst iv ON i.Item = iv.Item
        WHERE 
            i.Stat = 'A'  -- Active items
        """
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log estructurado
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='fetch_materials',
                method='SQL',
                status=200, con logging estructurado"""
        if not self.connection:
            self.connect()
        
        start_time = time.time()
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            CustNum AS customer_code,
            Name AS name,
            Contact AS contact_person,
            Email AS email,
            Phone AS phone
        FROM 
            customer_mst
        WHERE 
            Stat = 'A'  -- Active customers
        """
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log estructurado
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='fetch_customers',
                method='SQL',
                status=200,
                duration_ms=duration_ms,
                extra={'rows': len(results)}
            )
            
            logger.info(f"Se obtuvieron {len(results)} clientes de Syteline")
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log estructurado de error
            StructuredLogger.log_request(
                source=self.source_name,
                endpoint='fetch_customers',
                method='SQL',
                status=500,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            logger.error(f"Error obteniendo clientes: {str(e)}")
            raise
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            logger.info(f"Se obtuvieron {len(results)} materiales de Syteline")
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo materiales: {str(e)}")
            return []
    
    def fetch_customers(self):
        """Obtener clientes"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            CustNum AS customer_code,
            Name AS name,
            Contact AS contact_person,
            Email AS email,
            Phone AS phone
        FROM 
            customer_mst
        WHERE 
            Stat = 'A'  -- Active customers
        """
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            logger.info(f"Se obtuvieron {len(results)} clientes de Syteline")
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo clientes: {str(e)}")
            return []
    
    def fetch_production_data(self, order_id=None):
        """Obtener datos de producción"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            job.Job AS job_number,
            job.Item AS item_code,
            job.QtyReleased AS quantity_ordered,
            job.QtyComplete AS quantity_produced,
            job.Stat AS status,
            job.RelDate AS release_date
        FROM 
            job_mst job
        WHERE 
            job.Stat IN ('R', 'P')  -- Released, Partially Complete
        """
        
        if order_id:
            query += f" AND job.CoNum = '{order_id}'"
        
        try:
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de producción: {str(e)}")
            return []
