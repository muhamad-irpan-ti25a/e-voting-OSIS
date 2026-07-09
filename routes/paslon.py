import os
import json
from datetime import datetime
# TAMBAHKAN render_template di baris bawah ini:
from flask import Blueprint, request, jsonify, session, current_app, render_template
from werkzeug.utils import secure_filename
from database.connection import get_db_connection, catat_log
from middlewares.auth_guard import admin_required, super_admin_required
import config.settings as settings

paslon_bp = Blueprint('paslon', __name__)

@paslon_bp.route('/api/vote', methods=['POST'])
def proses_voting():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Sesi Anda telah habis. Silakan login kembali!"}), 401

    if session['role'] not in ['siswa', 'guru']:
        return jsonify({"status": "error", "message": "Role struktural Anda tidak memiliki hak suara bilik!"}), 403

    data = request.get_json()
    paslon_id = data.get('paslon_id')

    if not paslon_id:
        return jsonify({"status": "error", "message": "Anda belum memilih paslon kandidat!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        tahun_sekarang = datetime.now().year
        cursor.execute("SELECT status_pemilu FROM pemilu_snapshots WHERE tahun_pemilu = %s", (tahun_sekarang,))
        snapshot_status = cursor.fetchone()
        
        if snapshot_status and snapshot_status['status_pemilu'] == 'terkunci':
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error", 
                "message": "Akses ditolak! Pemilihan untuk periode tahun ini telah resmi ditutup dan dikunci oleh panitia."
            }), 403

        cursor.execute("SELECT sudah_memilih, nama_lengkap, role FROM users WHERE id = %s", (session['user_id'],))
        user_status = cursor.fetchone()

        if user_status['sudah_memilih'] == 1:
            cursor.close()
            conn.close()
            session.clear()
            return jsonify({"status": "error", "message": "Kecurangan terdeteksi! Anda tercatat sudah memilih sebelumnya!"}), 403

        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()
        
        cursor.execute("UPDATE users SET sudah_memilih = 1, waktu_memilih = NOW() WHERE id = %s", (session['user_id'],))
        cursor.execute("UPDATE paslon SET total_suara = total_suara + 1 WHERE id = %s", (paslon_id,))
        conn.commit()
        
        catat_log(session['username'], 'VOTE_SUBMIT', f"{user_status['nama_lengkap']} (DPT) berhasil memasukkan hak suaranya.")
        return jsonify({"status": "success", "message": "Suara Anda berhasil disimpan! Terima kasih telah berpartisipasi."})

    except Exception as e:
        if 'conn' in locals() and conn.in_transaction:
            conn.rollback()
        return jsonify({"status": "error", "message": f"Gagal mengirimkan suara: {str(e)}"}), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

@paslon_bp.route('/api/user/paslon-aktif', methods=['GET'])
def get_paslon_user():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Sesi tidak sah!"}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nomor_urut, nama_ketua, nama_wakil, 
                   kelas_ketua, kelas_wakil, foto, visi, misi, 
                   is_archived, tahun_pemilu 
            FROM paslon 
            WHERE is_archived = 0 
            ORDER BY nomor_urut ASC
        """)
        paslon_list = cursor.fetchall()
        return jsonify({"status": "success", "data": paslon_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/api/superadmin/paslon', methods=['POST'])
@super_admin_required
def tambah_paslon_full():
    nomor_urut = request.form.get('nomor_urut')
    tahun_pemilu = request.form.get('tahun_pemilu', datetime.now().year)
    nama_ketua = request.form.get('nama_ketua')
    nama_wakil = request.form.get('nama_wakil')
    kelas_ketua = request.form.get('kelas_ketua')
    kelas_wakil = request.form.get('kelas_wakil')
    visi = request.form.get('visi')
    misi = request.form.get('misi')
    foto = request.files.get('foto')

    if not nomor_urut or not nama_ketua or not nama_wakil:
        return jsonify({"status": "error", "message": "Nomor urut, nama ketua, dan nama wakil wajib dilengkapi!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM paslon WHERE nomor_urut = %s AND tahun_pemilu = %s", (nomor_urut, tahun_pemilu))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": f"Nomor Urut {nomor_urut} sudah terdaftar untuk Pemilu Tahun {tahun_pemilu}!"}), 400

        filename = 'default.png'
        if foto and foto.filename != '':
            UPLOAD_FOLDER = 'static/uploads/'
            if not os.path.exists(UPLOAD_FOLDER): 
                os.makedirs(UPLOAD_FOLDER)
            filename = secure_filename(f"paslon_{tahun_pemilu}_{nomor_urut}_{foto.filename}")
            foto.save(os.path.join(UPLOAD_FOLDER, filename))

        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()

        cursor.execute("""
            INSERT INTO paslon (nomor_urut, nama_ketua, nama_wakil, kelas_ketua, kelas_wakil, visi, misi, foto, tahun_pemilu, is_archived)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
        """, (nomor_urut, nama_ketua, nama_wakil, kelas_ketua, kelas_wakil, visi, misi, filename, tahun_pemilu))
        
        conn.commit()
        catat_log(session.get('username', 'SUPER_ADMIN'), 'ADD_PASLON', f"Mendaftarkan Paslon No. {nomor_urut} Tahun {tahun_pemilu}: {nama_ketua} & {nama_wakil}")
        return jsonify({"status": "success", "message": f"Kandidat Paslon Nomor {nomor_urut} untuk Pemilu {tahun_pemilu} berhasil didaftarkan!"})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Gagal menyimpan data ke database: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/api/superadmin/paslon/update/<int:paslon_id>', methods=['POST'])
@super_admin_required
def update_paslon_data(paslon_id):
    nomor_urut = request.form.get('nomor_urut')
    tahun_pemilu = request.form.get('tahun_pemilu')
    nama_ketua = request.form.get('nama_ketua')
    nama_wakil = request.form.get('nama_wakil')
    kelas_ketua = request.form.get('kelas_ketua')
    kelas_wakil = request.form.get('kelas_wakil')
    visi = request.form.get('visi')
    misi = request.form.get('misi')
    foto = request.files.get('foto')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM paslon WHERE nomor_urut = %s AND tahun_pemilu = %s AND id != %s", (nomor_urut, tahun_pemilu, paslon_id))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": f"Gagal mengubah! Nomor Urut {nomor_urut} sudah dipakai paslon lain di tahun {tahun_pemilu}."}), 400

        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()

        if foto and foto.filename != '':
            UPLOAD_FOLDER = 'static/uploads/'
            if not os.path.exists(UPLOAD_FOLDER): 
                os.makedirs(UPLOAD_FOLDER)
            filename = secure_filename(f"paslon_{tahun_pemilu}_{nomor_urut}_{foto.filename}")
            foto.save(os.path.join(UPLOAD_FOLDER, filename))
            
            cursor.execute("""
                UPDATE paslon SET nomor_urut=%s, tahun_pemilu=%s, nama_ketua=%s, nama_wakil=%s, 
                kelas_ketua=%s, kelas_wakil=%s, visi=%s, misi=%s, foto=%s WHERE id=%s
            """, (nomor_urut, tahun_pemilu, nama_ketua, nama_wakil, kelas_ketua, kelas_wakil, visi, misi, filename, paslon_id))
        else:
            cursor.execute("""
                UPDATE paslon SET nomor_urut=%s, tahun_pemilu=%s, nama_ketua=%s, nama_wakil=%s, 
                kelas_ketua=%s, kelas_wakil=%s, visi=%s, misi=%s WHERE id=%s
            """, (nomor_urut, tahun_pemilu, nama_ketua, nama_wakil, kelas_ketua, kelas_wakil, visi, misi, paslon_id))
        
        conn.commit()
        catat_log(session.get('username'), 'EDIT_PASLON', f"Memperbarui data Paslon Nomor Urut {nomor_urut} Periode {tahun_pemilu}")
        return jsonify({"status": "success", "message": "Data berkas paslon berhasil diperbarui secara aman!"})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Gagal memperbarui database: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/api/superadmin/paslon/toggle-archive/<int:paslon_id>', methods=['POST'])
@super_admin_required
def toggle_archive_paslon_data(paslon_id):
    data = request.get_json() or {}
    is_archived = data.get('is_archived', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nomor_urut FROM paslon WHERE id = %s", (paslon_id,))
        paslon = cursor.fetchone()
        no_paslon = paslon['nomor_urut'] if paslon else paslon_id
        
        status_teks = "Mengaktifkan Kembali" if int(is_archived) == 0 else "Mengarsipkan"
        
        cursor.execute("UPDATE paslon SET is_archived = %s WHERE id = %s", (is_archived, paslon_id))
        conn.commit()
        catat_log(session.get('username'), 'ARCHIVE_PASLON', f"{status_teks} untuk Paslon Nomor Urut {no_paslon}")
        return jsonify({"status": "success", "message": "Status kearsipan paslon berhasil diperbarui."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/api/superadmin/paslon/delete/<int:paslon_id>', methods=['DELETE'])
@super_admin_required
def hapus_paslon_data(paslon_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nomor_urut FROM paslon WHERE id = %s", (paslon_id,))
        paslon = cursor.fetchone()
        no_paslon = paslon['nomor_urut'] if paslon else paslon_id
        
        cursor.execute("DELETE FROM paslon WHERE id = %s", (paslon_id,))
        conn.commit()
        catat_log(session.get('username'), 'DELETE_PASLON', f"Menghapus permanen Paslon Nomor Urut {no_paslon}")
        return jsonify({"status": "success", "message": "Kandidat Paslon berhasil dihapus permanen."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/api/admin/paslon/update/<int:id>', methods=['POST'])
@admin_required
def admin_koreksi_paslon(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        nama_ketua = request.form.get('nama_ketua', '').strip()
        kelas_ketua = request.form.get('kelas_ketua', '').strip()
        nama_wakil = request.form.get('nama_wakil', '').strip()
        kelas_wakil = request.form.get('kelas_wakil', '').strip()
        visi = request.form.get('visi', '').strip()
        misi = request.form.get('misi', '').strip()

        if not nama_ketua or not nama_wakil:
            return jsonify({"status": "error", "message": "Nama Ketua dan Wakil tidak boleh kosong!"}), 400

        cursor.execute("SELECT nomor_urut FROM paslon WHERE id = %s", (id,))
        paslon_exist = cursor.fetchone()
        if not paslon_exist:
            return jsonify({"status": "error", "message": "Data kandidat paslon tidak ditemukan!"}), 404

        nomor_urut = paslon_exist['nomor_urut']

        query_update = """
            UPDATE paslon 
            SET nama_ketua = %s, kelas_ketua = %s, 
                nama_wakil = %s, kelas_wakil = %s, 
                visi = %s, misi = %s
            WHERE id = %s
        """
        cursor.execute(query_update, (nama_ketua, kelas_ketua, nama_wakil, kelas_wakil, visi, misi, id))
        conn.commit()

        operator_aktif = session.get('username', 'PANITIA_TPS')
        pesan_log = f"Panitia melakukan koreksi identitas Paslon No. {nomor_urut} (Ketua: {nama_ketua}, Wakil: {nama_wakil})."
        catat_log(operator_aktif, 'KOREKSI_PASLON', pesan_log)

        return jsonify({
            "status": "success", 
            "message": f"Koreksi identitas Paslon {nomor_urut} berhasil disimpan dan dicatat dalam log audit."
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Kesalahan internal database: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/api/superadmin/kunci-pemilu/<int:tahun>', methods=['POST'])
@admin_required
def kunci_pemilu(tahun):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nomor_urut, total_suara FROM paslon WHERE tahun_pemilu = %s", (tahun,))
        paslon_live = cursor.fetchall()
        
        peta_suara = {str(p['nomor_urut']): p['total_suara'] for p in paslon_live}
        rincian_json_str = json.dumps(peta_suara)

        cursor.execute("SELECT role, COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') GROUP BY role")
        roles_count = cursor.fetchall()
        total_siswa = sum(r['total'] for r in roles_count if r['role'] == 'siswa')
        total_guru = sum(r['total'] for r in roles_count if r['role'] == 'guru')
        total_dpt = total_siswa + total_guru

        cursor.execute("SELECT sudah_memilih, COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') GROUP BY sudah_memilih")
        voted_count = cursor.fetchall()
        suara_masuk = sum(v['total'] for v in voted_count if v['sudah_memilih'] == 1)
        belum_memilih = sum(v['total'] for v in voted_count if v['sudah_memilih'] == 0)
        partisipasi_percent = round((suara_masuk / (total_dpt if total_dpt > 0 else 1)) * 100, 2)

        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()

        cursor.execute("""
            INSERT INTO pemilu_snapshots 
            (tahun_pemilu, total_dpt, total_siswa, total_guru, suara_masuk, belum_memilih, partisipasi_percent, rincian_suara_paslon, status_pemilu, waktu_dikunci)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'terkunci', NOW())
            ON DUPLICATE KEY UPDATE 
            total_dpt=%s, total_siswa=%s, total_guru=%s, suara_masuk=%s, belum_memilih=%s, partisipasi_percent=%s, rincian_suara_paslon=%s, status_pemilu='terkunci'
        """, (tahun, total_dpt, total_siswa, total_guru, suara_masuk, belum_memilih, partisipasi_percent, rincian_json_str,
              total_dpt, total_siswa, total_guru, suara_masuk, belum_memilih, partisipasi_percent, rincian_json_str))
        
        cursor.execute("""
            UPDATE users 
            SET is_archived = 1 
            WHERE sudah_memilih = 1
        """)
        
        aktor_aktif = session.get('username', 'SuperAdmin') 
        cursor.execute("INSERT INTO audit_logs (aktor, tipe_aksi, deskripsi) VALUES (%s, %s, %s)", 
                       (aktor_aktif, "KUNCI_PEMILU", f"Berhasil mengunci data Pemilu Tahun {tahun} ke snapshot. Layar live tetap menampilkan hasil akhir."))
        
        conn.commit()
        return jsonify({"status": "success", "message": f"Statistik Pemilu Tahun {tahun} berhasil diamankan ke snapshot arsip!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@paslon_bp.route('/admin/daftar-paslon')
@admin_required
def page_admin_daftar_paslon():
    return render_template('admin/daftar_paslon.html', role=session.get('role'))