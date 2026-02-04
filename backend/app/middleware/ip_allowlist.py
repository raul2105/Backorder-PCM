"""
Middleware de Allowlist de IPs
Validación consistente para endpoints de escritura
"""

from functools import wraps
from flask import request, jsonify, current_app
import ipaddress
import yaml
import os


def _get_client_ip() -> str:
    """
    Obtiene la IP real del cliente.
    Si TRUST_PROXY está habilitado, confía en X-Forwarded-For.
    De lo contrario usa request.remote_addr directamente.
    """
    # Leer config desde config.yaml
    config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
    trust_proxy = False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            trust_proxy = config.get('network', {}).get('trust_proxy', False)
    except Exception:
        pass
    
    if trust_proxy:
        # Usar el PRIMER valor de X-Forwarded-For (el cliente original)
        forwarded_for = request.headers.get('X-Forwarded-For', '').strip()
        if forwarded_for:
            # X-Forwarded-For puede ser: "client, proxy1, proxy2"
            return forwarded_for.split(',')[0].strip()
    
    # Por defecto, usar remote_addr
    return request.remote_addr or '127.0.0.1'


def _is_ip_allowed(ip: str) -> bool:
    """
    Valida si la IP está en la allowlist.
    Si no hay configuración, permite por defecto (whitelist vacía = acceso abierto).
    """
    from app.models import SystemSetting
    
    setting = SystemSetting.query.filter_by(key='network.allowed_ips').first()
    
    # Si no hay configuración, permitir acceso
    if not setting or not setting.value:
        return True
    
    allowed_ips = setting.value
    
    # Si la lista está vacía, permitir acceso
    if not allowed_ips or len(allowed_ips) == 0:
        return True
    
    try:
        for rule in allowed_ips:
            rule = rule.strip()
            if not rule:
                continue
            
            # Coincidencia directa
            if rule == ip:
                return True
            
            # CIDR notation (ej: 192.168.1.0/24)
            try:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(rule, strict=False):
                    return True
            except ValueError:
                # Regla inválida, continuar
                continue
    except Exception as e:
        # En caso de error de configuración, registrar y denegar acceso por seguridad
        current_app.logger.error(f"Error validando IP allowlist: {e}")
        return False
    
    return False


def require_allowed_ip(f):
    """
    Decorator para endpoints de escritura.
    Valida que la IP del cliente esté en la allowlist.
    
    Uso:
        @bp.route('/endpoint', methods=['POST'])
        @jwt_required()
        @require_allowed_ip
        def my_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = _get_client_ip()
        
        if not _is_ip_allowed(client_ip):
            current_app.logger.warning(
                f"IP bloqueada: {client_ip} intentó acceder a {request.endpoint}"
            )
            return jsonify({
                'error': 'Operación no permitida desde esta IP',
                'ip': client_ip
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
