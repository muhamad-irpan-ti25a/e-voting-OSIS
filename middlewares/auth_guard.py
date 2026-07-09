from functools import wraps
from flask import jsonify, session

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'super_admin':
            return jsonify({"status": "error", "message": "Akses ditolak! Anda bukan Super Admin."}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'super_admin']:
            return jsonify({"status": "error", "message": "Akses ditolak! Anda tidak memiliki hak akses Admin."}), 403
        return f(*args, **kwargs)
    return decorated_function