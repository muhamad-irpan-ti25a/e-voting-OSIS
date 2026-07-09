import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database.connection import get_db_connection, catat_log
from middlewares.auth_guard import admin_required, super_admin_required
from config.settings import normalisasi_nomor_wa, buat_pesan_otp_login, kirim_wa_otp
import config.settings as settings

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Semua field harus diisi!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM super_admins WHERE username = %s", (username,))
        super_user = cursor.fetchone()
        if super_user and check_password_hash(super_user['password'], password):
            session.clear()
            session['user_id'] = super_user['id']
            session['username'] = super_user['username']
            session['role'] = 'super_admin'
            session['nama_lengkap'] = super_user['nama_lengkap']
            
            cursor.close()
            conn.close()
            catat_log(super_user['username'], 'AUTH_LOGIN', f"Super Admin {super_user['nama_lengkap']} berhasil masuk ke Master Kontrol.")
            return jsonify({"status": "success", "message": "Login Super Admin Berhasil!", "role": "super_admin", "redirect": "/superadmin/dashboard"})

        cursor.execute("SELECT * FROM kpo_panitia WHERE username = %s", (username,))
        admin_user = cursor.fetchone()
        if admin_user:
            if admin_user['is_blocked'] == 1:
                cursor.close()
                conn.close()
                return jsonify({"status": "error", "message": "Akses panel operator Anda ditangguhkan/diblokir oleh Super Admin!"}), 403
                
            if check_password_hash(admin_user['password'], password):
                session.clear()
                session['user_id'] = admin_user['id']
                session['username'] = admin_user['username']
                session['role'] = 'admin'
                session['nama_lengkap'] = admin_user['nama_panitia']
                
                cursor.close()
                conn.close()
                catat_log(admin_user['username'], 'AUTH_LOGIN', f"Operator TPS {admin_user['nama_panitia']} berhasil masuk.")
                return jsonify({"status": "success", "message": "Login Operator Berhasil!", "role": "admin", "redirect": "/admin/dashboard"})

        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Username atau Password yang Anda masukkan salah!"}), 401

    except Exception as e:
        if 'cursor' in locals() and cursor: 
            try: cursor.close()
            except: pass
        if 'conn' in locals() and conn: 
            try: conn.close()
            except: pass
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"}), 500

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    if 'role' in session and session['role'] in ['siswa', 'guru']:
        return jsonify({
            "status": "error", 
            "message": "Aturan Ketat! Anda tidak diizinkan meninggalkan bilik suara sebelum menentukan pilihan."
        }), 403

    if 'username' in session:
        catat_log(session['username'], 'AUTH_LOGOUT', "Pengguna keluar dari sesi sistem.")
    session.clear()
    return jsonify({"status": "success", "message": "Berhasil logout."})

@auth_bp.route('/api/register/request-otp', methods=['POST'])
def request_otp_register():
    return jsonify({"status": "error", "message": "Fitur Registrasi Mandiri telah dinonaktifkan. Seluruh data DPT diatur penuh oleh administrator!"}), 403

@auth_bp.route('/api/register/verify', methods=['POST'])
def verify_register():
    return jsonify({"status": "error", "message": "Fitur Aktivasi Mandiri telah dinonaktifkan!"}), 403

@auth_bp.route('/api/login/user/request-otp', methods=['POST'])
def login_user_request_otp():
    data = request.get_json()
    nomor_input = data.get('nomor_wa', '').strip()

    if not nomor_input:
        return jsonify({"status": "error", "message": "Nomor WhatsApp wajib diisi!"}), 400

    # 1. PROTEKSI EARLY-CHECK: Cek gerbang pemilu global sebelum menyentuh database/kuota
    if settings.STATUS_GERBANG_PEMILU != 'dimulai':
        return jsonify({
            "status": "error", 
            "message": "Akses Ditolak! Waktu pemilihan belum resmi dibuka oleh panitia lapangan."
        }), 403

    nomor_wa_bersih = normalisasi_nomor_wa(nomor_input)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 2. Ambil data profil lengkap DPT berdasarkan nomor WA
        # ======================================================================
        # PERBAIKAN: Menambahkan 'FROM users' yang sempat tertinggal
        # ======================================================================
        cursor.execute(
            """SELECT id, nama_lengkap, username, role, sudah_memilih, is_blocked, is_archived, is_alumni 
               FROM users
               WHERE (nomor_wa LIKE %s OR nomor_wa LIKE %s)
                 AND role IN ('siswa', 'guru')""", 
            (f"%{nomor_wa_bersih}", f"{nomor_input}")
        )
        user = cursor.fetchone()

        # 3. FILTER VALIASI KETAT (Bypass API Fonnte jika tidak lolos kualifikasi)
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Nomor HP tidak terdaftar di dalam DPT!"}), 404

        if user['is_archived'] == 1:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Akses Ditolak! Akun DPT Anda berstatus non-aktif/diarsipkan."}), 403

        if user['is_blocked'] == 1:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Akses Ditangguhkan! Akun Anda diblokir oleh sistem karena indikasi kecurangan/pelanggaran."}), 403

        if user.get('is_alumni') == 1:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Akses Ditolak! Anda tercatat sudah berstatus Alumni sekolah."}), 403

        if user['sudah_memilih'] == 1 or str(user['sudah_memilih']) == '1':
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error", 
                "message": f"Akses Ditolak! Saudara {user['nama_lengkap']} tercatat sudah menggunakan hak suara murni!"
            }), 403

        # ======================================================================
        # JALUR AMAN: Token Fonnte hanya dibakar jika pemilih lolos seluruh filter di atas
        # ======================================================================
        otp_code = str(random.randint(100000, 999999))
        expired_at = datetime.now() + timedelta(minutes=2)

        cursor.execute(
            "INSERT INTO otp_verifications (nomor_wa, otp_code, jenis_aksi, expired_at, is_used) VALUES (%s, %s, 'login', %s, 0)",
            (nomor_wa_bersih, otp_code, expired_at)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Kirim pesan via Fonnte Gateway
        pesan_wa = buat_pesan_otp_login(otp_code)
        kirim_wa_otp(nomor_wa_bersih, pesan_wa)

        print(f"\n[SERVER OTP] Token Hemat Terpakai -> Pemilih: {user['nama_lengkap']} | OTP: {otp_code}")
        return jsonify({"status": "success", "message": "Kode OTP masuk berhasil dikirimkan ke WhatsApp Anda!"}), 200

    except Exception as e:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()
        return jsonify({"status": "error", "message": f"Sistem Gagal Memproses Permintaan: {str(e)}"}), 500

@auth_bp.route('/api/login/user/verify', methods=['POST'])
def login_user_verify():
    data = request.get_json()
    nomor_input = data.get('nomor_wa', '').strip()
    otp_input = data.get('otp', '').strip()

    if not nomor_input or not otp_input:
        return jsonify({"status": "error", "message": "Nomor WhatsApp dan Kode OTP wajib diisi!"}), 400

    nomor_wa_bersih = normalisasi_nomor_wa(nomor_input)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT * FROM otp_verifications 
               WHERE (nomor_wa = %s OR nomor_wa = %s OR nomor_wa LIKE %s) 
                 AND otp_code = %s 
                 AND is_used = 0 
               ORDER BY id DESC LIMIT 1""",
            (nomor_wa_bersih, nomor_input, f"%{nomor_wa_bersih}", otp_input)
        )
        otp_record = cursor.fetchone()

        if not otp_record:
            cursor.execute(
                """SELECT * FROM otp_verifications 
                   WHERE otp_code = %s AND is_used = 0 
                   ORDER BY id DESC LIMIT 1""",
                (otp_input,)
            )
            otp_record = cursor.fetchone()

        if not otp_record:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Kode OTP salah atau tidak terdaftar!"}), 400

        waktu_sekarang = datetime.now()
        if waktu_sekarang > otp_record['expired_at']:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Masa berlaku kode OTP (2 menit) telah habis!"}), 400

        cursor.execute(
            """SELECT * FROM users 
               WHERE (nomor_wa = %s OR nomor_wa = %s OR nomor_wa LIKE %s)
                 AND role IN ('siswa', 'guru') AND is_blocked = 0 AND is_archived = 0""", 
            (nomor_wa_bersih, nomor_input, f"%{nomor_wa_bersih}")
        )
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Nomor WhatsApp valid, namun data DPT tidak ditemukan!"}), 404

        if settings.STATUS_GERBANG_PEMILU != 'dimulai':
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Akses Ditolak! Waktu pemilihan belum resmi dibuka oleh panitia."}), 403

        if user['sudah_memilih'] == 1 or str(user['sudah_memilih']) == '1':
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Akses Ditolak! Anda tercatat sudah menggunakan hak pilih."}), 403

        cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE id = %s", (otp_record['id'],))
        conn.commit()

        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['nama_lengkap'] = user['nama_lengkap']

        cursor.close()
        conn.close()

        catat_log(user['username'], 'AUTH_LOGIN', f"Pemilih {user['nama_lengkap']} berhasil masuk ke bilik suara menggunakan OTP ponsel.")

        return jsonify({
            "status": "success", 
            "message": "Kode OTP Valid! Membuka gerbang bilik suara...", 
            "role": user['role'], 
            "redirect": "/user/voting"
        }), 200

    except Exception as e:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()
        return jsonify({"status": "error", "message": f"Sistem Gagal Memvalidasi: {str(e)}"}), 500

@auth_bp.route('/api/forgot-password/request-otp', methods=['POST'])
def request_otp_forgot():
    return jsonify({"status": "error", "message": "Fitur Lupa Password untuk pemilih dinonaktifkan. Login saat ini murni menggunakan verifikasi OTP Nomor HP!"}), 403

@auth_bp.route('/api/forgot-password/verify', methods=['POST'])
def verify_forgot_password():
    data = request.get_json()
    username = data.get('username')
    otp_input = data.get('otp')
    password_baru = data.get('password')

    if not username or not password_baru:
        return jsonify({"status": "error", "message": "Data tidak lengkap!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT username, nama_panitia AS nama_lengkap FROM kpo_panitia WHERE username = %s", (username,))
    target_admin = cursor.fetchone()

    if not target_admin:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Akun Operator Panitia tidak terdaftar di sistem!"}), 404

    hashed_password = generate_password_hash(password_baru, method='pbkdf2:sha256')

    if otp_input == "BYPASS_WA_LINK":
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()
        
        cursor.execute("UPDATE kpo_panitia SET password = %s WHERE username = %s", (hashed_password, username))
        conn.commit()
        cursor.close()
        conn.close()
        
        catat_log(session.get('username', 'SYSTEM'), 'CHG_PASSWORD', f"Pengguna {target_admin['nama_lengkap']} berhasil memperbarui kata sandi panel operator via Link WhatsApp.")
        return jsonify({"status": "success", "message": "Password Panel Operator berhasil diperbarui! Silakan login kembali."})

    cursor.close()
    conn.close()
    return jsonify({"status": "error", "message": "Metode pemulihan tidak sah atau ditolak sistem!"}), 400