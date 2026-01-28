"""
Punto de entrada de la aplicación Flask
"""

import os
from app import create_app, db
from app.models import User, Order, Customer, Material, OrderItem, ProductionLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Contexto para Flask shell"""
    return {
        'db': db,
        'User': User,
        'Order': Order,
        'Customer': Customer,
        'Material': Material,
        'OrderItem': OrderItem,
        'ProductionLog': ProductionLog
    }

@app.cli.command()
def init_db():
    """Inicializar la base de datos"""
    db.create_all()
    print('Base de datos inicializada')

@app.cli.command()
def create_admin():
    """Crear usuario administrador por defecto"""
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Usuario admin ya existe')
        return
    
    admin = User(
        username='admin',
        email='admin@backorder.com',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print('Usuario admin creado exitosamente')
    print('Username: admin')
    print('Password: admin123')
    print('IMPORTANTE: Cambiar la contraseña en producción')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
