import json
import random
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, redirect
from database.connection import get_db_connection, catat_log
from middlewares.auth_guard import admin_required, super_admin_required
import config.settings as settings

spinner_bp = Blueprint('spinner', __name__)

@spinner_bp.route('/api/superadmin/paslon/save-spin', methods=['POST'])
@super_admin_required
def api_save_spin_result():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Payload tidak valid!"}), 400
        
    paslon_id = data.get('paslon_id')
    nomor_urut = data.get('nomor_urut')
    saksi_saksi = data.get('saksi') 
    tahun_pemilu = datetime.now().year

    if not paslon_id or not nomor_urut or not saksi_saksi:
        return jsonify({"status": "error", "message": "Data id paslon, nomor urut, dan saksi wajib diisi!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()

        cursor.execute("SELECT nama_ketua, nama_wakil FROM paslon WHERE id = %s", (paslon_id,))
        paslon = cursor.fetchone()
        
        if not paslon:
            return jsonify({"status": "error", "message": "Kandidat paslon tidak ditemukan!"}), 404

        cursor.execute("SELECT id FROM paslon WHERE nomor_urut = %s AND tahun_pemilu = %s AND id != %s", (nomor_urut, tahun_pemilu, paslon_id))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": f"Nomor Urut {nomor_urut} sudah terpakai oleh paslon lain!"}), 400

        cursor.execute("UPDATE paslon SET nomor_urut = %s WHERE id = %s", (nomor_urut, paslon_id))

        data_rekap = {
            "tahun": tahun_pemilu,
            "saksi": saksi_saksi,
            "nama_ketua": paslon['nama_ketua'],
            "nama_wakil": paslon['nama_wakil'],
            "nomor_urut": nomor_urut
        }
        json_rekap_str = json.dumps(data_rekap)

        query_log = "INSERT INTO audit_logs (waktu_kejadian, aktor, tipe_aksi, deskripsi) VALUES (NOW(), %s, %s, %s)"
        cursor.execute(query_log, (session.get('username'), 'SPIN_NOMOR_URUT', json_rekap_str))

        conn.commit()
        print(f"LOG SPIN BERHASIL: SPIN_NOMOR_URUT oleh {session.get('username')}")
        return jsonify({"status": "success", "message": f"Nomor urut {nomor_urut} untuk {paslon['nama_ketua']} berhasil dikunci di database & log audit!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Gagal mengunci data spin: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/paslon/rekap-spin', methods=['GET'])
@super_admin_required
def api_get_rekap_spin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, waktu_kejadian, tahun_pemilu, nama_ketua, nama_wakil, nomor_urut_didapat, saksi_saksi, operator_aktor 
            FROM rekap_spin_paslon 
            ORDER BY waktu_kejadian DESC
        """)
        rows = cursor.fetchall()
        
        rekap_list = []
        hari_list = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]

        for r in rows:
            waktu = r['waktu_kejadian']
            hari_nama = hari_list[int(waktu.strftime('%w'))]
            tanggal_str = waktu.strftime('%d-%m-%Y')
            jam_str = waktu.strftime('%H:%M:%S')

            rekap_list.append({
                "id": r['id'],
                "hari": hari_nama,
                "tanggal": tanggal_str,
                "jam": jam_str,
                "tahun": r['tahun_pemilu'],
                "tahun_pemilu": r['tahun_pemilu'],
                "nama_ketua": r['nama_ketua'],
                "nama_wakil": r['nama_wakil'],
                "nomor_urut": r['nomor_urut_didapat'],
                "nomor_urut_didapat": r['nomor_urut_didapat'],
                "saksi": r['saksi_saksi'],
                "saksi_saksi": r['saksi_saksi'],
                "operator": r['operator_aktor'],
                "operator_aktor": r['operator_aktor']
            })
            
        return jsonify({"status": "success", "data": rekap_list})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal memuat dari database: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/paslon/save-spin-massal', methods=['POST'])
@super_admin_required
def api_save_spin_massal_result():
    data = request.get_json()
    if not data or 'hasil_pleno' not in data or 'saksi' not in data:
        return jsonify({"status": "error", "message": "Payload berkas pleno tidak valid!"}), 400
        
    list_hasil = data.get('hasil_pleno') 
    saksi_saksi = data.get('saksi').strip()
    tahun_otomatis = datetime.now().year

    if not list_hasil or not saksi_saksi:
        return jsonify({"status": "error", "message": "Daftar hasil kocokan roda dan nama saksi wajib dilengkapi!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()

        query_insert = """
            INSERT INTO rekap_spin_paslon 
            (tahun_pemilu, nama_ketua, nama_wakil, nomor_urut_didapat, saksi_saksi, operator_aktor) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        for p in list_hasil:
            nama_k = str(p.get('nama_ketua')).strip()
            nama_w = str(p.get('nama_wakil')).strip()
            no_urut = int(p.get('nomor_urut'))

            if not nama_k or not nama_w or not no_urut:
                conn.rollback()
                return jsonify({"status": "error", "message": "Ada data nama kandidat atau nomor urut kosong yang terdeteksi!"}), 400

                cursor.execute(query_insert, (
                    tahun_otomatis,
                    nama_k,
                    nama_w,
                    no_urut,
                    saksi_saksi,
                    session.get('username', 'SUPER_ADMIN')
                ))

        query_audit = "INSERT INTO audit_logs (aktor, tipe_aksi, deskripsi) VALUES (%s, %s, %s)"
        deskripsi_audit = f"Super Admin mengunci hasil pleno penarikan nomor urut {len(list_hasil)} Paslon Tahun {tahun_otomatis}. Saksi: {saksi_saksi}"
        cursor.execute(query_audit, (session.get('username'), 'SPIN_NOMOR_URUT', deskripsi_audit))

        conn.commit()
        print(f"PLENO BERHASIL: {len(list_hasil)} Paslon dikunci otomatis ke database tahun {tahun_otomatis}.")
        return jsonify({"status": "success", "message": f"Berhasil mengunci {len(list_hasil)} berkas berita acara paslon ke database tahun {tahun_otomatis}!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Gagal mengamankan data transaksi pleno: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/superadmin/spin-paslon')
def page_superadmin_spin_paslon():
    if session.get('role') != 'super_admin': 
        return redirect('/auth/login')
    return render_template('super_admin/spin_paslon.html')

@spinner_bp.route('/superadmin/rekap-spin')
def page_superadmin_rekap_spin():
    if session.get('role') != 'super_admin': 
        return redirect('/auth/login')
    return render_template('super_admin/rekap_spin.html')

@spinner_bp.route('/api/superadmin/reset-system', methods=['POST'])
@super_admin_required
def api_reset_sistem_total():
    data = request.get_json()
    konfirmasi = data.get('konfirmasi')
    
    if konfirmasi != "RESET TOTAL SISTEM VOTE OSIS":
        return jsonify({"status": "error", "message": "Kalimat konfirmasi salah!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if conn.in_transaction: conn.rollback()
        conn.start_transaction()
        
        cursor.execute("UPDATE users SET sudah_memilih = 0, waktu_memilih = NULL, is_archived = 0")
        cursor.execute("UPDATE paslon SET total_suara = 0 WHERE tahun_pemilu = 2026")
        cursor.execute("TRUNCATE TABLE otp_verifications")
        conn.commit()
        
        catat_log(session.get('username'), 'HARD_RESET_SYSTEM', "Melakukan reset total sistem. Kotak suara live kosong kembali ke 0%.")
        return jsonify({"status": "success", "message": "Sistem berhasil dikosongkan kembali ke 0%!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/pemilih/luluskan-massal', methods=['POST'])
@super_admin_required
def luluskan_pemilih_massal():
    data = request.get_json() or {}
    kelas_target = data.get('kelas') 
    tahun_lulusan = datetime.now().year
    
    if not kelas_target:
        return jsonify({"status": "error", "message": "Pilih tingkatan kelas yang ingin diluluskan!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if conn.in_transaction: 
            conn.rollback()
        conn.start_transaction()
        
        if kelas_target == "XII":
            query = """
                UPDATE users 
                SET is_alumni = 1, is_archived = 1, tahun_lulus = %s 
                WHERE (kelas LIKE '%%XII%%' OR kelas LIKE '%%xii%%' OR kelas LIKE '12%%') 
                  AND role = 'siswa' 
                  AND (is_alumni = 0 OR is_alumni IS NULL)
            """
            cursor.execute(query, (tahun_lulusan,))
        else:
            query = """
                UPDATE users 
                SET is_alumni = 1, is_archived = 1, tahun_lulus = %s 
                WHERE kelas = %s 
                  AND role = 'siswa' 
                  AND (is_alumni = 0 OR is_alumni IS NULL)
            """
            cursor.execute(query, (tahun_lulusan, kelas_target))
            
        jumlah_lulus = cursor.rowcount
        conn.commit()
        
        catat_log(session.get('username'), 'GRADUATE_MASSAL', f"Meluluskan massal {jumlah_lulus} siswa kelas {kelas_target} ke folder Alumni angkatan {tahun_lulusan}.")
        
        if jumlah_lulus == 0:
            return jsonify({
                "status": "error",
                "message": f"Sistem tidak menemukan siswa aktif di kelas '{kelas_target}'. Periksa kembali penulisan nama kelas di tabel DPT Anda!"
            }), 404
            
        return jsonify({
            "status": "success", 
            "message": f"Berhasil memindahkan {jumlah_lulus} siswa kelas {kelas_target} ke Direktori Alumni Abadi."
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/dashboard-stats', methods=['GET'])
@admin_required 
def get_dashboard_stats():
    tahun_req = request.args.get('tahun') 
    mode_req = request.args.get('mode', 'live')
    tahun_sekarang = datetime.now().year
    
    try:
        tahun_kueri = int(tahun_req) if (tahun_req and tahun_req != 'ALL') else tahun_sekarang
    except ValueError:
        tahun_kueri = tahun_sekarang
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nomor_urut, nama_ketua, nama_wakil, 
                   kelas_ketua, kelas_wakil, total_suara, foto, 
                   visi, misi, is_archived, tahun_pemilu
            FROM paslon 
            WHERE tahun_pemilu = %s
            ORDER BY nomor_urut ASC
        """, (tahun_kueri,))
        paslon_stats = cursor.fetchall()

        summary = {}
        
        if mode_req == 'archive' or tahun_kueri != tahun_sekarang:
            cursor.execute("SELECT * FROM pemilu_snapshots WHERE tahun_pemilu = %s", (tahun_kueri,))
            snapshot = cursor.fetchone()
            
            if snapshot:
                summary = {
                    "total_pemilih": snapshot['total_dpt'],
                    "total_siswa": snapshot['total_siswa'],
                    "total_guru": snapshot['total_guru'],
                    "sudah_memilih": snapshot['suara_masuk'],
                    "belum_memilih": snapshot['belum_memilih'],
                    "partisipasi_percent": float(snapshot['partisipasi_percent'])
                }
                
                if snapshot.get('rincian_suara_paslon'):
                    try:
                        peta_suara_arsip = json.loads(snapshot['rincian_suara_paslon'])
                        for paslon in paslon_stats:
                            no_urut_str = str(paslon['nomor_urut'])
                            if no_urut_str in peta_suara_arsip:
                                paslon['total_suara'] = int(peta_suara_arsip[no_urut_str])
                    except:
                        pass
            else:
                summary = {
                    "total_pemilih": 0, "total_siswa": 0, "total_guru": 0,
                    "sudah_memilih": 0, "belum_memilih": 0, "partisipasi_percent": 0.00
                }
        else:
            cursor.execute("SELECT role, COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') GROUP BY role")
            roles_count = cursor.fetchall()
            total_siswa = sum(r['total'] for r in roles_count if r['role'] == 'siswa')
            total_guru = sum(r['total'] for r in roles_count if r['role'] == 'guru')
            
            cursor.execute("SELECT sudah_memilih, COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') GROUP BY sudah_memilih")
            voted_count = cursor.fetchall()
            sudah_memilih = sum(v['total'] for v in voted_count if v['sudah_memilih'] == 1)
            belum_memilih = sum(v['total'] for v in voted_count if v['sudah_memilih'] == 0)
            
            total_aktif = total_siswa + total_guru
            summary = {
                "total_pemilih": total_aktif,
                "total_siswa": total_siswa,
                "total_guru": total_guru,
                "sudah_memilih": sudah_memilih,
                "belum_memilih": belum_memilih,
                "partisipasi_percent": round((sudah_memilih / (total_aktif if total_aktif > 0 else 1)) * 100, 2)
            }
        
        cursor.execute("SELECT DISTINCT tahun_pemilu FROM pemilu_snapshots")
        tahun_snapshots = [row['tahun_pemilu'] for row in cursor.fetchall()]

        semua_tahun = list(set([int(p['tahun_pemilu']) for p in paslon_stats] + [int(th) for th in tahun_snapshots] + [tahun_sekarang]))
        semua_tahun.sort(reverse=True)

        return jsonify({
            "status": "success",
            "data": {
                "summary": summary,
                "paslon_votes": paslon_stats,
                "daftar_tahun": semua_tahun,
                "status_pemilu_sekarang": settings.STATUS_GERBANG_PEMILU  
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/toggle-pemilu', methods=['POST'])
@admin_required
def toggle_status_pemilu():
    data = request.get_json() or {}
    status_baru = data.get('status')

    if status_baru not in ['belum_dimulai', 'dimulai']:
        return jsonify({"status": "error", "message": "Status tidak valid!"}), 400

    settings.STATUS_GERBANG_PEMILU = status_baru
    teks_log = "MEMBUKA Bilik Suara" if status_baru == "dimulai" else "MENUTUP Bilik Suara"
    catat_log(session.get('username', 'SuperAdmin'), 'TOGGLE_GERBANG', f"Panitia telah {teks_log} secara real-time.")

    return jsonify({
        "status": "success", 
        "message": f"Akses bilik suara berhasil diubah menjadi: {status_baru.upper()}"
    })

@spinner_bp.route('/api/superadmin/pemilih', methods=['GET'])
@super_admin_required
def get_pemilih_superadmin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, username, nama_lengkap, role, kelas, nomor_wa, 
                   sudah_memilih, waktu_memilih, is_blocked, is_archived, is_alumni 
            FROM users
            ORDER BY role DESC, username ASC
        """) 
        data = cursor.fetchall()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/pemilih/aktifkan-kembali/<int:user_id>', methods=['POST'])
@super_admin_required
def aktifkan_kembali_pemilih(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()

        cursor.execute("SELECT username, nama_lengkap FROM users WHERE id = %s", (user_id,))
        pemilih = cursor.fetchone()
        
        if not pemilih:
            return jsonify({"status": "error", "message": "Data akun pemilih tidak ditemukan."}), 404

        cursor.execute("UPDATE users SET sudah_memilih = 0, waktu_memilih = NULL WHERE id = %s", (user_id,))
        conn.commit()
        
        if 'user_id' in session and session['user_id'] == user_id:
            session.clear()

        catat_log(session.get('username'), 'RESET_VOTE', f"Super Admin mengaktifkan kembali hak pilih akun: {pemilih['nama_lengkap']} ({pemilih['username']}).")
        return jsonify({"status": "success", "message": f"Akun {pemilih['nama_lengkap']} berhasil diaktifkan kembali secara murni!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/pemilih/reset-status-massal', methods=['POST'])
@super_admin_required
def reset_status_massal():
    data = request.get_json() or {}
    if data.get('konfirmasi') != "RESET_SUARA_TAHUNAN":
        return jsonify({"status": "error", "message": "Kode konfirmasi salah!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET sudah_memilih = 0, waktu_memilih = NULL WHERE is_archived = 0 OR is_archived IS NULL")
        conn.commit()
        return jsonify({"status": "success", "message": "Seluruh status hak pilih telah di-reset untuk pemilu tahun depan!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/pemilih/unarchive-all', methods=['POST'])
@super_admin_required
def pulihkan_semua_arsip():
    data = request.get_json() or {}
    konfirmasi = data.get('konfirmasi')
    tahun_filter = data.get('tahun')
    kelas_filter = data.get('kelas')
    
    if konfirmasi != "PULIKA_SEMUA_ARSIP" and konfirmasi != "PULIHKAN_SEMUA_ARSIP":
        return jsonify({"status": "error", "message": "Kode konfirmasi pemulihan massal tidak sah!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()
        
        query = """
            UPDATE users 
            SET is_archived = 0, tahun_menjabat = NULL 
            WHERE is_archived = 1 AND (is_alumni = 0 OR is_alumni IS NULL)
        """
        params = []
        log_detail = "seluruh DPT terarsip temporer"
        
        if tahun_filter and tahun_filter != 'ALL':
            query += " AND tahun_menjabat = %s"
            params.append(tahun_filter)
            log_detail = f"DPT arsip tahun {tahun_filter}"
            
        if kelas_filter and kelas_filter != 'ALL':
            query += " AND kelas = %s"
            params.append(kelas_filter)
            log_detail += f" folder kelas {kelas_filter}"
            
        cursor.execute(query, tuple(params))
        jumlah_terdampak = cursor.rowcount
        conn.commit()
        
        catat_log(session.get('username'), 'UNARCHIVE_ALL_DPT', f"Super Admin memulihkan massal {log_detail} ({jumlah_terdampak} akun) menjadi DPT Aktif. Data alumni diabaikan.")
        return jsonify({"status": "success", "message": f"Berhasil memulihkan {jumlah_terdampak} akun ke DPT Aktif."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/pemilih/delete-all', methods=['DELETE'])
@super_admin_required
def hapus_semua_pemilih():
    konfirmasi = request.args.get('confirm')
    if konfirmasi != "HAPUS_SEMUA_DPT":
        return jsonify({"status": "error", "message": "Kode konfirmasi tidak valid!"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE role IN ('siswa', 'guru')")
        conn.commit()
        catat_log(session.get('username'), 'DEL_DPT', "Super Admin menghapus seluruh data pemilih (DPT) secara massal.")
        return jsonify({"status": "success", "message": "Seluruh data pemilih telah dihapus permanen."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/admin', methods=['GET', 'POST'])
@super_admin_required
def manajemen_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'GET':
            query = "SELECT id, username, nama_panitia, nomor_wa, is_blocked, is_archived, foto, tahun_menjabat FROM kpo_panitia"
            cursor.execute(query)
            list_admin = cursor.fetchall()
            return jsonify({"status": "success", "data": list_admin if list_admin else []})
            
        elif request.method == 'POST':
            username = request.form.get('username') 
            nama_panitia = request.form.get('nama_panitia') 
            nomor_wa = request.form.get('nomor_wa') 
            tahun_menjabat = request.form.get('tahun_menjabat', datetime.now().year)
            password_panel = request.form.get('password') 
            foto = request.files.get('foto')
            
            if not username or not password_panel or not nama_panitia or not nomor_wa:
                return jsonify({"status": "error", "message": "Semua field input panitia wajib diisi!"}), 400

            filename = None
            if foto and foto.filename != '':
                UPLOAD_FOLDER = 'static/uploads/admin/'
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                filename = secure_filename(f"kpo_{username}_{foto.filename}")
                foto.save(os.path.join(UPLOAD_FOLDER, filename))
            else:
                filename = 'default.png'
                
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(password_panel, method='pbkdf2:sha256')
            
            if conn.in_transaction:
                conn.rollback()
            conn.start_transaction()
            
            try:
                cursor.execute(
                    "INSERT INTO kpo_panitia (username, password, nama_panitia, nomor_wa, foto, is_blocked, is_archived, tahun_menjabat) VALUES (%s, %s, %s, %s, %s, 0, 0, %s)",
                    (username, hashed_password, nama_panitia, nomor_wa, filename, tahun_menjabat)
                )
                conn.commit()
                catat_log(session.get('username', 'SUPER_ADMIN'), 'ADD_ADMIN', f"Membuat akun operasional TPS baru: {nama_panitia} ({username}).")
                return jsonify({"status": "success", "message": f"Berhasil mendaftarkan Panitia TPS {nama_panitia}!"})
            
            except mysql.connector.Error as db_err:
                conn.rollback()
                if db_err.errno == 1062: 
                    return jsonify({"status": "error", "message": f"Username '{username}' sudah digunakan oleh panitia lain!"}), 400
                raise db_err 

    except Exception as e:
        if 'conn' in locals() and conn.in_transaction:
            conn.rollback()
        return jsonify({"status": "error", "message": f"Kegagalan internal server kontrol: {str(e)}"}), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

@spinner_bp.route('/api/superadmin/admin/update/<int:panitia_id>', methods=['POST'])
@super_admin_required
def update_admin(panitia_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Payload data tidak valid atau kosong!"}), 400

    nama_panitia = data.get('nama_panitia')
    nomor_wa = data.get('nomor_wa')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username, nama_panitia FROM kpo_panitia WHERE id = %s", (panitia_id,))
        panitia = cursor.fetchone()
        if not panitia:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Data kepanitiaan tidak ditemukan."}), 404
            
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()
        
        if password and password.strip() != "":
            from werkzeug.security import generate_password_hash
            hashed = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute("UPDATE kpo_panitia SET nama_panitia=%s, nomor_wa=%s, password=%s WHERE id=%s", (nama_panitia, nomor_wa, hashed, panitia_id))
        else:
            cursor.execute("UPDATE kpo_panitia SET nama_panitia=%s, nomor_wa=%s WHERE id=%s", (nama_panitia, nomor_wa, panitia_id))
            
        conn.commit()
        catat_log(session.get('username'), 'EDIT_ADMIN', f"Menyelaraskan data operasional Panitia KPO: {panitia['username']}.")
        return jsonify({"status": "success", "message": "Profil akun panitia berhasil diperbarui."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Gagal memproses perubahan: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/admin/toggle-block/<int:panitia_id>', methods=['POST'])
@super_admin_required
def toggle_block_admin(panitia_id):
    is_blocked = request.get_json().get('is_blocked')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE kpo_panitia SET is_blocked = %s WHERE id = %s", (is_blocked, panitia_id))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/admin/toggle-archive/<int:panitia_id>', methods=['POST'])
@super_admin_required
def toggle_archive_admin(panitia_id):
    is_archived = request.get_json().get('is_archived')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nama_panitia, username FROM kpo_panitia WHERE id = %s", (panitia_id,))
        panitia = cursor.fetchone()
        cursor.execute("UPDATE kpo_panitia SET is_archived = %s WHERE id = %s", (is_archived, panitia_id))
        conn.commit()
        if panitia:
            status_text = "Mendemisionerkan" if int(is_archived) == 1 else "Memulihkan ke Aktif"
            catat_log(session.get('username'), 'ARCHIVE_ADMIN', f"{status_text} Panitia KPO: {panitia['nama_panitia']}.")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/admin/<int:panitia_id>', methods=['DELETE'])
@super_admin_required
def hapus_admin(panitia_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT username, nama_panitia FROM kpo_panitia WHERE id = %s"
        cursor.execute(query, (panitia_id,))
        admin = cursor.fetchone()
        
        if admin:
            cursor.execute("DELETE FROM kpo_panitia WHERE id = %s", (panitia_id,))
            conn.commit()
            catat_log(session.get('username'), 'DEL_ADMIN', f"Menghapus permanen akun panitia TPS: {admin['nama_panitia']} ({admin['username']}).")
            return jsonify({"status": "success", "message": "Akun operator TPS berhasil dihapus permanen."})
        return jsonify({"status": "error", "message": "Data tidak ditemukan."}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/pemilih/archive-all', methods=['POST'])
@super_admin_required
def arsipkan_semua_pemilih():
    data = request.get_json() or {}
    konfirmasi = data.get('konfirmasi')
    
    if konfirmasi != "ARSIPKAN_SEMUA_DPT":
        return jsonify({"status": "error", "message": "Kode konfirmasi arsip massal tidak valid!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    tahun_sekarang = datetime.now().year
    
    try:
        if conn.in_transaction:
            conn.rollback()
        conn.start_transaction()
        
        query = "UPDATE users SET is_archived = 1, tahun_menjabat = %s WHERE role IN ('siswa', 'guru') AND (is_archived = 0 OR is_archived IS NULL)"
        cursor.execute(query, (tahun_sekarang,))
        
        jumlah_terdampak = cursor.rowcount
        conn.commit()
        
        catat_log(session.get('username'), 'ARCHIVE_ALL_DPT', f"Super Admin mengarsipkan seluruh DPT Aktif massal ({jumlah_terdampak} akun) ke arsip tahun {tahun_sekarang}.")
        return jsonify({"status": "success", "message": f"Berhasil mengarsipkan {jumlah_terdampak} data pemilih secara massal ke tahun {tahun_sekarang}!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/logs', methods=['GET', 'DELETE'])
@super_admin_required
def manajemen_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            cursor.execute("SELECT DATE_FORMAT(waktu_kejadian, '%d/%m/%Y %H:%i') as waktu, aktor, tipe_aksi, deskripsi FROM audit_logs ORDER BY id DESC")
            logs = cursor.fetchall()
            return jsonify({"status": "success", "data": logs if logs else []})
        elif request.method == 'DELETE':
            cursor.execute("TRUNCATE TABLE audit_logs")
            conn.commit()
            catat_log(session.get('username'), 'CLEAR_LOGS', "Membersihkan seluruh riwayat audit log.")
            return jsonify({"status": "success", "message": "Riwayat Audit Log Berhasil dikosongkan secara total."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@spinner_bp.route('/api/superadmin/admin/send-reset-wa', methods=['POST'])
@super_admin_required
def api_send_reset_wa():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Payload request tidak valid!"}), 400

    nomor_wa = data.get('nomor_wa')
    nama_lengkap = data.get('nama_lengkap')
    username = data.get('username')
    
    if not nomor_wa or nomor_wa == "null" or nomor_wa.strip() == "":
        return jsonify({"status": "error", "message": "Nomor WhatsApp tujuan tidak ditemukan atau kosong."}), 400

    clean_number = ''.join(filter(str.isdigit, str(nomor_wa)))
    if clean_number.startswith('0'):
        clean_number = '62' + clean_number[1:]
    elif clean_number.startswith('8'):
        clean_number = '62' + clean_number

    origin_url = request.url_root.rstrip('/')
    pesan = (
        f"Halo Panitia *{nama_lengkap}* ({username}),\n\n"
        f"Berikut tautan konvalidasi Reset Password panel Operator TPS Anda:\n\n"
        f"🔗 {origin_url}/auth/reset-password?user={username}"
    )

    try:
        from config.settings import kirim_wa_otp
        response_fonnte = kirim_wa_otp(clean_number, pesan)
        if response_fonnte and response_fonnte.get('status') is True:
            catat_log(session.get('username'), 'SEND_CREDENTIALS', f"Mengirimkan link akses panel operator ke {nama_lengkap} ({username}) via Fonnte.")
            return jsonify({"status": "success", "message": f"Kredensial link berhasil diantrekan oleh Fonnte Gateway ke nomor +{clean_number}."})
        else:
            detail_error = response_fonnte.get('reason', 'Fonnte menolak permintaan atau token salah.') if response_fonnte else 'Koneksi Fonnte putus.'
            return jsonify({"status": "error", "message": f"Fonnte Engine gagal memproses: {detail_error}"}), 502
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal mengirim data ke gateway: {str(e)}"}), 500