import io
import csv
import os
import openpyxl
from datetime import datetime
from flask import Blueprint, request, jsonify, session, app
from database.connection import get_db_connection, catat_log
from middlewares.auth_guard import admin_required, super_admin_required
from config.settings import normalisasi_nomor_wa

dpt_bp = Blueprint('dpt', __name__)

@dpt_bp.route('/api/admin/pemilih', methods=['GET', 'POST'])
@admin_required
def manajemen_pemilih():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT id, username, nama_lengkap, role, nomor_wa, 
                       sudah_memilih, waktu_memilih, is_archived, kelas 
                FROM users 
                WHERE role IN ('siswa', 'guru') 
                ORDER BY role DESC, username ASC
            """)
            list_pemilih = cursor.fetchall()
            return jsonify({"status": "success", "data": list_pemilih if list_pemilih else []})
            
        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Payload JSON tidak ditemukan!"}), 400
                
            username = data.get('username')
            nama_lengkap = data.get('nama_lengkap')
            role = data.get('role')
            kelas = data.get('kelas', '')
            nomor_wa_input = data.get('nomor_wa', '').strip()

            if not username or not nama_lengkap or not nomor_wa_input or role not in ['siswa', 'guru']:
                return jsonify({"status": "error", "message": "Data tidak lengkap! Nama, NISN/NIP, Nomor WA, dan Kategori wajib diisi."}), 400
                
            nomor_wa_bersih = normalisasi_nomor_wa(nomor_wa_input)
                
            cursor.execute(
                """INSERT INTO users (username, password, nama_lengkap, role, kelas, nomor_wa, sudah_memilih, is_blocked, is_archived, is_alumni) 
                   VALUES (%s, NULL, %s, %s, %s, %s, 0, 0, 0, 0)""", 
                (username, nama_lengkap, role, kelas, nomor_wa_bersih)
            )
            conn.commit()
            catat_log(session.get('username'), 'ADD_DPT', f"Menambahkan DPT baru: {nama_lengkap} ({username}) WA: {nomor_wa_bersih}.")
            return jsonify({"status": "success", "message": f"Data {role} berhasil didaftarkan dan langsung aktif!"})

    except mysql.connector.Error as err:
        if conn and request.method == 'POST': conn.rollback()
        if err.errno == 1062:
            return jsonify({"status": "error", "message": "NISN/NIP sudah terdaftar di sistem!"}), 400
        return jsonify({"status": "error", "message": f"Database error: {str(err)}"}), 500
    except Exception as e:
        if conn and request.method == 'POST': conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

@dpt_bp.route('/api/admin/pemilih/<int:user_id>', methods=['PUT', 'DELETE'])
@admin_required
def manajemen_pemilih_spesifik(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'PUT':
            data = request.get_json()
            username_baru = data.get('username')
            nama_baru = data.get('nama_lengkap')
            role_baru = data.get('role')
            kelas_baru = data.get('kelas', '')
            nomor_wa_baru = data.get('nomor_wa', '').strip()
            
            if not username_baru or not nama_baru or not nomor_wa_baru or role_baru not in ['siswa', 'guru']:
                return jsonify({"status": "error", "message": "Data tidak boleh kosong! Nama, NISN/NIP, and Nomor WA wajib diisi."}), 400
                
            cursor.execute("SELECT username, nama_lengkap, role, kelas, nomor_wa FROM users WHERE id = %s", (user_id,))
            sebelum = cursor.fetchone()
            
            if not sebelum:
                return jsonify({"status": "error", "message": "Data tidak ditemukan."}), 404
                
            nomor_wa_bersih = normalisasi_nomor_wa(nomor_wa_baru)
                
            cursor.execute(
                """UPDATE users 
                   SET username = %s, nama_lengkap = %s, role = %s, kelas = %s, nomor_wa = %s 
                   WHERE id = %s""",
                (username_baru, nama_baru, role_baru, kelas_baru, nomor_wa_bersih, user_id)
            )
            conn.commit()
            
            perubahan = []
            if sebelum['nama_lengkap'] != nama_baru: perubahan.append(f"Nama: '{sebelum['nama_lengkap']}' → '{nama_baru}'")
            if sebelum['username'] != username_baru: perubahan.append(f"Username: '{sebelum['username']}' → '{username_baru}'")
            if sebelum['role'] != role_baru: perubahan.append(f"Kategori: '{sebelum['role']}' → '{role_baru}'")
            if sebelum['kelas'] != kelas_baru: perubahan.append(f"Kelas: '{sebelum['kelas']}' → '{kelas_baru}'")
            if sebelum['nomor_wa'] != nomor_wa_bersih: perubahan.append(f"WA: '{sebelum['nomor_wa']}' → '{nomor_wa_bersih}'")
            
            detail_perubahan = ", ".join(perubahan) if perubahan else "Tidak ada perubahan nilai data."
            catat_log(session.get('username'), 'EDIT_DPT', f"Mengubah profil DPT ID: {user_id}. Perubahan [ {detail_perubahan} ]")
            return jsonify({"status": "success", "message": "Profil pemilih dan Nomor WhatsApp berhasil diperbarui."})

        elif request.method == 'DELETE':
            if session.get('role') != 'super_admin':
                return jsonify({"status": "error", "message": "Akses Ditolak! Hanya Super Admin yang diizinkan menghapus data pemilih secara permanen."}), 403

            cursor.execute("SELECT username, nama_lengkap, role, kelas FROM users WHERE id = %s", (user_id,))
            pemilih = cursor.fetchone()
            
            if pemilih:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                catat_log(session.get('username'), 'DEL_DPT', f"Menghapus permanen DPT {pemilih['role'].upper()}: {pemilih['nama_lengkap']} ({pemilih['username']}).")
                return jsonify({"status": "success", "message": "Data pemilih berhasil dihapus oleh Super Admin."})
            
            return jsonify({"status": "error", "message": "Pemilih tidak ditemukan."}), 404

    except Exception as e:
        if 'conn' in locals(): conn.rollback()
        return jsonify({"status": "error", "message": f"Error Database: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@dpt_bp.route('/api/admin/pemilih/import', methods=['POST'])
@admin_required
def api_admin_import_excel_file():
    data = request.get_json()
    if not data or 'pemilih' not in data:
        return jsonify({"status": "error", "message": "Format data payload tidak valid!"}), 400
        
    list_pemilih = data.get('pemilih')
    conn = get_db_connection()
    cursor = conn.cursor()
    sukses_count, gagal_count = 0, 0
    log_messages = []
    
    try:
        conn.start_transaction()
        for p in list_pemilih:
            username = str(p.get('username', '')).strip()
            nama_lengkap = str(p.get('nama_lengkap', '')).strip()
            role = str(p.get('role', '')).lower().strip()
            kelas = str(p.get('kelas', '')).strip()
            nomor_wa = str(p.get('nomor_wa', '')).strip()
            
            if username.endswith('.0'): username = username[:-2]
                
            if username and nama_lengkap and nomor_wa and role in ['siswa', 'guru']:
                try:
                    wa_bersih = normalisasi_nomor_wa(nomor_wa)
                    
                    cursor.execute(
                        """INSERT INTO users (username, password, nama_lengkap, role, kelas, nomor_wa, sudah_memilih, is_blocked, is_archived, is_alumni) 
                           VALUES (%s, NULL, %s, %s, %s, %s, 0, 0, 0, 0)
                           ON DUPLICATE KEY UPDATE nama_lengkap=%s, kelas=%s, nomor_wa=%s""", 
                        (username, nama_lengkap, role, kelas, wa_bersih, nama_lengkap, kelas, wa_bersih)
                    )
                    sukses_count += 1
                except Exception as ex: 
                    gagal_count += 1
                    log_messages.append(f"Error NISN {username}: {str(ex)}")
            else:
                gagal_count += 1
        
        conn.commit()
        catat_log(session.get('username', 'PANITIA_DPT'), 'IMPORT_FILE', f"Impor massal sukses: {sukses_count} baris data, Gagal: {gagal_count}.")
        return jsonify({
            "status": "success", 
            "message": f"Impor selesai. {sukses_count} data baru diproses masuk.",
            "logs": log_messages if log_messages else ["Semua data sukses diimpor."]
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@dpt_bp.route('/api/admin/import-pemilih', methods=['POST'])
@admin_required
def api_admin_import_excel_file_v2():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file berkas yang terdeteksi!"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Nama file kosong!"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.xlsx', '.xls', '.csv']:
        return jsonify({"status": "error", "message": "Format file tidak didukung! Wajib .xlsx, .xls, atau .csv"}), 400

    list_pemilih = []
    log_messages = []

    try:
        if ext == '.csv':
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            sample = stream.read(2048)
            stream.seek(0)
            delimiter = ';' if ';' in sample else ','
            reader = csv.DictReader(stream, delimiter=delimiter)
            for row in reader:
                clean_row = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k}
                username = clean_row.get('username') or clean_row.get('nisn') or clean_row.get('nip') or clean_row.get('id', '')
                nama_lengkap = clean_row.get('nama_lengkap') or clean_row.get('nama', '')
                role = clean_row.get('role') or clean_row.get('kategori', 'siswa')
                kelas = clean_row.get('kelas') or clean_row.get('rombel', '')
                nomor_wa = clean_row.get('nomor_wa') or clean_row.get('no_whatsapp') or clean_row.get('wa', '')
                
                if username and nama_lengkap and nomor_wa:
                    list_pemilih.append({
                        'username': username, 'nama_lengkap': nama_lengkap,
                        'role': 'guru' if 'guru' in role.lower() else 'siswa', 'kelas': kelas,
                        'nomor_wa': nomor_wa
                    })
        else:
            wb = openpyxl.load_workbook(file.stream, data_only=True)
            sheet = wb.active
            header = [str(cell.value).strip().lower() for cell in sheet[1] if cell.value]
            
            idx_user = next((i for i, h in enumerate(header) if h in ['username', 'nisn', 'nip', 'id']), None)
            idx_nama = next((i for i, h in enumerate(header) if h in ['nama_lengkap', 'nama']), None)
            idx_role = next((i for i, h in enumerate(header) if h in ['role', 'kategori']), None)
            idx_kelas = next((i for i, h in enumerate(header) if h in ['kelas', 'rombel', 'ruang']), None)
            idx_wa = next((i for i, h in enumerate(header) if h in ['nomor_wa', 'no_whatsapp', 'wa']), None)

            if idx_user is None or idx_nama is None or idx_wa is None:
                return jsonify({"status": "error", "message": "Kolom 'username', 'nama_lengkap', dan 'nomor_wa' wajib ada di header baris pertama file Excel!"}), 400

            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or idx_user >= len(row) or idx_nama >= len(row) or idx_wa >= len(row): continue
                username = str(row[idx_user]).strip() if row[idx_user] is not None else ''
                nama_lengkap = str(row[idx_nama]).strip() if row[idx_nama] is not None else ''
                nomor_wa = str(row[idx_wa]).strip() if row[idx_wa] is not None else ''
                
                if username.endswith('.0'): username = username[:-2]
                if nomor_wa.endswith('.0'): nomor_wa = nomor_wa[:-2]
                
                if not username or not nama_lengkap or not nomor_wa: continue
                
                role_raw = str(row[idx_role]).strip().lower() if idx_role is not None and idx_role < len(row) and row[idx_role] else 'siswa'
                kelas = str(row[idx_kelas]).strip() if idx_kelas is not None and idx_kelas < len(row) and row[idx_kelas] else ''
                
                list_pemilih.append({
                    'username': username, 'nama_lengkap': nama_lengkap,
                    'role': 'guru' if 'guru' in role_raw else 'siswa', 'kelas': kelas,
                    'nomor_wa': nomor_wa
                })

        if not list_pemilih:
            return jsonify({"status": "error", "message": "Tidak ada baris data valid (Pastikan NISN, Nama, dan No WA terisi)!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        sukses_count = 0
        gagal_count = 0
        
        try:
            conn.start_transaction()
            for p in list_pemilih:
                try:
                    wa_bersih = normalisasi_nomor_wa(p['nomor_wa'])
                    
                    cursor.execute(
                        """INSERT INTO users (username, password, nama_lengkap, role, kelas, nomor_wa, sudah_memilih, is_blocked, is_archived, is_alumni) 
                           VALUES (%s, NULL, %s, %s, %s, %s, 0, 0, 0, 0)
                           ON DUPLICATE KEY UPDATE nama_lengkap=%s, kelas=%s, nomor_wa=%s""", 
                        (p['username'], p['nama_lengkap'], p['role'], p['kelas'], wa_bersih, p['nama_lengkap'], p['kelas'], wa_bersih)
                    )
                    sukses_count += 1
                except Exception as e:
                    gagal_count += 1
                    log_messages.append(f"Error pada {p['username']}: {str(e)}")
            
            conn.commit()
            catat_log(session.get('username', 'PANITIA_DPT'), 'IMPORT_FILE', f"Impor massal selesai. {sukses_count} berhasil dimasukkan/diperbarui.")
            
            return jsonify({
                "status": "success", 
                "total_rows": len(list_pemilih),
                "sukses_count": sukses_count,
                "fail_count": gagal_count,
                "logs": log_messages if log_messages else ["Semua data berhasil diimpor dengan skema nomor WA aktif murni."]
            })
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({"status": "error", "message": f"Kegagalan sistem: {str(e)}"}), 500

@dpt_bp.route('/api/admin/pemilih/toggle-archive/<int:user_id>', methods=['POST'])
@admin_required
def toggle_archive_pemilih(user_id):
    is_archived = request.get_json().get('is_archived', 0)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username, nama_lengkap FROM users WHERE id = %s", (user_id,))
        pemilih = cursor.fetchone()
        
        if not pemilih:
            return jsonify({"status": "error", "message": "Data pemilih tidak ditemukan"}), 404

        cursor.execute("UPDATE users SET is_archived = %s WHERE id = %s", (is_archived, user_id))
        conn.commit()
        
        status_text = "Mengarsipkan" if int(is_archived) == 1 else "Memulihkan"
        deskripsi_log = f"{status_text} status struktural DPT Pemilih: {pemilih['nama_lengkap']} (NISN: {pemilih['username']})"
        
        catat_log(session.get('username'), 'ARCHIVE_DPT', deskripsi_log)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@dpt_bp.route('/api/admin/pemilih/reset-status/<int:user_id>', methods=['POST'])
@admin_required
def reset_status_memilih_tunggal(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username, nama_lengkap FROM users WHERE id = %s", (user_id,))
        pemilih = cursor.fetchone()
        
        if pemilih:
            cursor.execute("UPDATE users SET sudah_memilih = 0, waktu_memilih = NULL WHERE id = %s", (user_id,))
            conn.commit()
            catat_log(session.get('username'), 'RESET_VOTE', f"Menggunakan hak pilih pemilih: {pemilih['nama_lengkap']} ({pemilih['username']}).")
            return jsonify({"status": "success", "message": "Status hak pilih user berhasil dikembalikan."})
        return jsonify({"status": "error", "message": "Data pemilih tidak ditemukan."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@dpt_bp.route('/api/admin/pemilih/ekspor', methods=['GET'])
@admin_required
def ekspor_pemilih_csv():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT username as NISN_NIP, nama_lengkap as Nama_Pemilih, 
                   role as Kategori, kelas as Kelas, nomor_wa as No_WhatsApp,
                   sudah_memilih as Status_Vote, waktu_memilih as Waktu_Hadir
            FROM users 
            WHERE role IN ('siswa', 'guru') AND (is_archived = 0 OR is_archived IS NULL)
            ORDER BY waktu_memilih DESC, username ASC
        """)
        rows = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['NISN/NIP', 'Nama Pemilih', 'Kategori', 'Kelas', 'No WhatsApp', 'Status Vote (1=Sudah, 0=Belum)', 'Waktu Hadir Bilik Suara'])
        
        for r in rows:
            waktu_str = r['Waktu_Hadir'].strftime('%Y-%m-%d %H:%M:%S') if r['Waktu_Hadir'] else '-'
            writer.writerow([
                r['NISN_NIP'],
                r['Nama_Pemilih'],
                r['Kategori'].upper(),
                r['Kelas'] if r['Kelas'] else '-',
                f"+62{r['No_WhatsApp']}" if r['No_WhatsApp'] else '-',
                r['Status_Vote'],
                waktu_str
            ])
            
        catat_log(session.get('username'), 'EXPORT_DATA', "Operator TPS melakukan ekspor data kehadiran DPT untuk dokumen bukti fisik pemilu.")
        
        from flask import current_app
        response = current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename=BUKTI_HADIR_DPT_OSIS_{datetime.now().year}.csv"}
        )
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@dpt_bp.route('/api/admin/pemilih', methods=['GET'])
def api_get_pemilih():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users") 
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500