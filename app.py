import os
from flask import Flask, render_template, session, redirect, flash, request
from flask_session import Session
from dotenv import load_dotenv

# Muat Konfigurasi Variabel Lingkungan
load_dotenv()

# Impor global koneksi & instansiasi DB dari folder database
from database.connection import db, migrate, get_db_connection
import config.settings as settings

# Impor Blueprint Komponen
from routes.auth import auth_bp
from routes.dpt import dpt_bp
from routes.paslon import paslon_bp
from routes.spinner import spinner_bp
from routes.ai_agent import ai_agent_bp

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'SuperSecureRandomKeyOSIS2026!@#')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Konfigurasi Jalur URI untuk Flask-Migrate mendeteksi MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME', 'evoting_osis')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi DB & Migrate ke App Flask
db.init_app(app)
migrate.init_app(app, db)

Session(app)

# Registrasi Semua Router Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(dpt_bp)
app.register_blueprint(paslon_bp)
app.register_blueprint(spinner_bp)
app.register_blueprint(ai_agent_bp)

# ==============================================================================
# RUTE REKAYASA NAVIGASI INTERFACE UTAMA (RENDER TEMPLATES)
# ==============================================================================
@app.route('/')
@app.route('/auth/login')
def page_login():
    if 'user_id' in session and 'role' in session:
        if session['role'] == 'super_admin': 
            return redirect('/superadmin/dashboard')
        elif session['role'] == 'admin': 
            return redirect('/admin/dashboard')
        elif session['role'] in ['siswa', 'guru']: 
            if settings.STATUS_GERBANG_PEMILU == 'dimulai':
                return redirect('/user/voting')
                
    return render_template('auth/login.html')

@app.route('/auth/register')
def page_register():
    return render_template('auth/register.html')

@app.route('/auth/forgot')
def page_forgot():
    return render_template('auth/forgot.html')

@app.route('/auth/reset-password')
def page_reset_password():
    username = request.args.get('user')
    if not username:
        return redirect('/auth/login')
    return render_template('auth/reset_password.html', username=username)

@app.route('/superadmin/dashboard')
def page_superadmin_dashboard():
    if session.get('role') != 'super_admin': return redirect('/auth/login')
    return render_template('super_admin/dashboard.html')

@app.route('/superadmin/data-pemilih')
def data_pemilih():
    if session.get('role') != 'super_admin': return redirect('/auth/login')
    return render_template('super_admin/data_pemilih.html', role=session.get('role'))

@app.route('/superadmin/quick-count')
def page_superadmin_quick_count():
    if session.get('role') != 'super_admin': return redirect('/auth/login')
    return render_template('super_admin/quick_count.html')

@app.route('/superadmin/manajemen-admin')
def page_superadmin_manage_admin():
    if session.get('role') != 'super_admin': return redirect('/auth/login')
    return render_template('super_admin/manajemen_admin.html')

@app.route('/superadmin/manajemen-paslon')
def page_superadmin_manage_paslon():
    if session.get('role') != 'super_admin': return redirect('/auth/login')
    return render_template('super_admin/manajemen_paslon.html')

@app.route('/admin/dashboard')
def page_admin_dashboard():
    if session.get('role') not in ['admin', 'super_admin']: return redirect('/auth/login')
    return render_template('admin/dashboard.html')

@app.route('/user/voting')
def page_user_voting():
    if 'user_id' not in session: 
        return redirect('/auth/login')
        
    if session.get('role') == 'admin': 
        return redirect('/admin/dashboard')
    elif session.get('role') == 'super_admin': 
        return redirect('/superadmin/dashboard')
        
    if session.get('role') not in ['siswa', 'guru']: 
        return redirect('/auth/login')
        
    if settings.STATUS_GERBANG_PEMILU != 'dimulai':
        flash('belum_dibuka', 'status_gerbang')
        return redirect('/auth/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        from datetime import datetime
        tahun_sekarang = datetime.now().year
        cursor.execute("SELECT status_pemilu FROM pemilu_snapshots WHERE tahun_pemilu = %s", (tahun_sekarang,))
        snapshot_status = cursor.fetchone()
        
        if snapshot_status and snapshot_status['status_pemilu'] == 'terkunci':
            return redirect('/auth/login')
            
        cursor.execute("SELECT sudah_memilih FROM users WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        if user_data and (user_data['sudah_memilih'] == 1 or user_data['sudah_memilih'] == '1'):
            return redirect('/user/terimakasih')
            
        return render_template('user/voting.html')
    except:
        return redirect('/auth/login')
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

@app.route('/user/terimakasih')
def page_user_terimakasih():
    response = render_template('user/terimakasih.html')
    session.clear() 
    return response

@app.route('/admin/data-pemilih')
def page_admin_data_pemilih():
    if session.get('role') not in ['admin', 'super_admin']: return redirect('/auth/login')
    return render_template('admin/data_pemilih.html')

@app.route('/superadmin/log-aktivitas')
def page_superadmin_log_aktivitas():
    if session.get('role') != 'super_admin': return redirect('/auth/login')
    return render_template('super_admin/log_aktivitas.html')

@app.route('/admin/quick-count')
def page_admin_quick_count():
    if session.get('role') not in ['admin', 'super_admin']: return redirect('/auth/login')
    return render_template('admin/quick_count.html')

@app.route('/superadmin/proyektor')
def page_superadmin_proyektor():
    if session.get('role') not in ['admin', 'super_admin']: return redirect('/auth/login')
    return render_template('super_admin/proyektor_view.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)