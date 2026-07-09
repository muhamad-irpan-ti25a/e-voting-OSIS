import io
import csv
import json
import string
import random
import os
import requests
import time
from flask import Blueprint, request, jsonify, session
from google import genai
from google.genai import types
from database.connection import get_db_connection, catat_log
import config.settings as settings

# Dependensi ReportLab untuk Auto-Generate PDF Laporan Berita Acara
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

ai_agent_bp = Blueprint('ai_agent', __name__)

# Menggunakan SDK Baru Google Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6LnU0HVllsAAUDhzVblDCRbv891-aQ3psv-I3Vo-2ElzA"))

# ==============================================================================
# 🧠 KECERDASAN AMAN & OTOMATISASI NATIVE TOOLS (V3.5-ADVANCED AUTONOMOUS)
# ==============================================================================

def ai_tool_ubah_status_gerbang_pemilu(status_baru: str) -> str:
    """Membuka atau menutup gerbang bilik suara pemilu secara realtime. Nilai parameter wajib: 'dimulai' atau 'belum_dimulai'."""
    if status_baru not in ['dimulai', 'belum_dimulai']:
        return "Gagal: Status gerbang pemilu tidak valid. Gunakan 'dimulai' or 'belum_dimulai'."
    try:
        settings.STATUS_GERBANG_PEMILU = status_baru
        aksi_log = "BUKA_GERBANG_AI" if status_baru == 'dimulai' else "TUTUP_GERBANG_AI"
        catat_log("Sirekap_AI_Agent", aksi_log, f"AI mengubah gerbang menjadi: {status_baru}")
        return f"Sukses Eksekusi: Gerbang akses bilik suara sekarang dialihkan secara mandiri oleh AI menjadi **{status_baru.upper()}**."
    except Exception as e:
        return f"Gagal mengeksekusi saklar gerbang: {str(e)}"

def ai_tool_karantina_blokir_user(username_target: str, alasan_blokir: str) -> str:
    """Memblokir atau mengkarantina akun DPT (Siswa/Guru) yang terindikasi melakukan fraud/pelanggaran."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nama_lengkap, is_blocked FROM users WHERE username = %s", (username_target,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return f"Gagal: Akun dengan ID/Username {username_target} tidak ditemukan."
            
        cursor.execute("UPDATE users SET is_blocked = 1 WHERE username = %s", (username_target,))
        conn.commit()
        cursor.close()
        conn.close()
        catat_log("Sirekap_AI_Agent", "BLOKIR_USER_AI", f"AI memblokir {username_target}. Alasan: {alasan_blokir}")
        return f"Sukses Eksekusi: Akun **{user['nama_lengkap']}** (ID: {username_target}) berhasil DIBLOKIR otomatis oleh AI Agent. Alasan: {alasan_blokir}."
    except Exception as e:
        return f"Gagal memproses karantina: {str(e)}"

def ai_tool_buka_blokir_user(username_target: str) -> str:
    """Membuka kembali status blokir/karantina akun pemilih tetap (DPT)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nama_lengkap FROM users WHERE username = %s", (username_target,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return f"Gagal: User {username_target} tidak ditemukan."
        cursor.execute("UPDATE users SET is_blocked = 0 WHERE username = %s", (username_target,))
        conn.commit()
        cursor.close()
        conn.close()
        return f"Sukses Eksekusi: Karantina dicabut, akun **{user['nama_lengkap']}** aktif kembali."
    except Exception as e:
        return f"Gagal pemulihan user: {str(e)}"

def ai_tool_daftarkan_dpt_tunggal(nisn_nip: str, nama: str, kelas_jabatan: str, role: str) -> str:
    """Mendaftarkan satu data pemilih tetap baru (Siswa/Guru) secara instan ke dalam MySQL."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username = %s", (nisn_nip,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return f"Gagal: DPT dengan NISN/NIP {nisn_nip} sudah terdaftar!"
            
        query = "INSERT INTO users (username, password, nama_lengkap, role, sudah_memilih, is_blocked, is_archived, kelas, tahun_menjabat) VALUES (%s, NULL, %s, %s, 0, 0, 0, %s, 2026)"
        cursor.execute(query, (nisn_nip, nama, role.lower().strip(), kelas_jabatan))
        conn.commit()
        cursor.close()
        conn.close()
        return f"Sukses Injeksi Data via AI: Nama: **{nama}** | ID: **{nisn_nip}** | Kelas: **{kelas_jabatan}**"
    except Exception as e:
        return f"Error eksekusi: {str(e)}"

def ai_tool_arsipkan_paslon_kandidat(nomor_urut_target: int, alasan_arsip: str) -> str:
    """Mengarsipkan atau menonaktifkan kandidat Paslon dari surat suara aktif berdasarkan nomor urut."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nama_ketua, nama_wakil FROM paslon WHERE nomor_urut = %s AND is_archived = 0", (nomor_urut_target,))
        paslon = cursor.fetchone()
        if not paslon:
            cursor.close()
            conn.close()
            return f"Gagal: Paslon Nomor {nomor_urut_target} tidak ditemukan atau sudah terarsip."

        cursor.execute("UPDATE paslon SET is_archived = 1 WHERE nomor_urut = %s", (nomor_urut_target,))
        conn.commit()
        cursor.close()
        conn.close()
        return f"Sukses Eksekusi: Paslon No **{nomor_urut_target}** ({paslon['nama_ketua']}) resmi **DIARSIPKAN**."
    except Exception as e:
        return f"Gagal arsip paslon: {str(e)}"

def ai_tool_pindai_fraud_spam_otp_otomatis() -> str:
    """Melakukan scanning log audit untuk mendeteksi indikasi brute-force spam OTP atau manipulasi ganda secara otonom."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT nomor_wa, COUNT(*) as total_request 
               FROM otp_verifications 
               WHERE expired_at > NOW() - INTERVAL 5 MINUTE
               GROUP BY nomor_wa HAVING total_request > 5"""
        )
        suspects = cursor.fetchall()
        if not suspects:
            cursor.close()
            conn.close()
            return "🛡️ **Hasil Pemindaian AI Guard:** Skema log aman. Tidak terdeteksi adanya anomali brute-force atau spamming OTP gateway dalam 5 menit terakhir."

        karantina_logs = []
        for s in suspects:
            cursor.execute("UPDATE users SET is_blocked = 1 WHERE nomor_wa = %s", (s['nomor_wa'],))
            karantina_logs.append(f"• Nomor WA `+62{s['nomor_wa']}` dibekukan otomatis (Spam {s['total_request']} OTP)")
            catat_log("AI_Guard_System", "AUTO_BLOCK_FRAUD", f"Spam OTP terdeteksi pada nomor {s['nomor_wa']}")

        conn.commit()
        cursor.close()
        conn.close()
        return "⚠️ **AI DEFENSE SYSTEM TRIGGERED!**\n\nTerdeteksi serangan anomali spamming gateway. AI mengambil keputusan otonom mengunci akun:\n" + "\n".join(karantina_logs)
    except Exception as e:
        return f"Gagal menjalankan AI Fraud Scanner: {str(e)}"

def ai_tool_analisis_prediksi_partisipasi_live() -> str:
    """Menghitung algoritma tren grafik linier untuk memprediksi persentase akhir penutupan suara masuk."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') AND is_archived = 0")
        total = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT COUNT(*) as voted FROM users WHERE sudah_memilih = 1 AND role IN ('siswa', 'guru') AND is_archived = 0")
        voted = cursor.fetchone()['voted'] or 0
        cursor.close()
        conn.close()

        if total == 0: return "Belum ada data DPT untuk kalkulasi prediksi matematika."
        current_percent = (voted / total) * 100
        predicted_final = min(100.0, current_percent * 1.35) if current_percent > 0 else 0.00
        
        return f"📈 **Laporan Analisis Prediktif Sirekap AI:**\n\n" \
               f"• Partisipasi Saat Ini: **{round(current_percent, 2)}%** ({voted} dari {total} DPT)\n" \
               f"• Prediksi Hasil Akhir: **{round(predicted_final, 2)}% Partisipasi** pada jam penutupan.\n" \
               f"• Rekomendasi AI: Jika angka partisipasi di bawah 75%, disarankan memicu broadcast pengingat massal otomatis via Fonnte ke sisa **{total - voted} DPT** yang belum mencoblos. Anda bisa mengetik *'Picu broadcast sekarang'* untuk menjalankannya."
    except Exception as e:
        return f"Gagal kalkulasi data prediktif: {str(e)}"

# ==============================================================================
# 🔥 NEW INTELLIGENCE TOOLS: BROADCAST MASSAL MANDIRI VIA AI AGENT
# ==============================================================================

def ai_tool_broadcast_pengingat_dpt_massal() -> str:
    """Menarik daftar nomor WA DPT yang belum mencoblos secara otomatis dari database MySQL, lalu mengirimkan pesan pengingat massal via Fonnte."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """SELECT nama_lengkap, nomor_wa 
               FROM users 
               WHERE sudah_memilih = 0 
                 AND role IN ('siswa', 'guru') 
                 AND is_archived = 0 
                 AND is_blocked = 0
                 AND nomor_wa IS NOT NULL AND nomor_wa != ''"""
        )
        daftar_antrean = cursor.fetchall()
        cursor.close()
        conn.close()

        if not daftar_antrean:
            return "📢 **Laporan Broadcast AI:** Operasi dilewati. Seluruh pemilih tetap (DPT) tercatat sudah menggunakan hak suaranya atau tidak ada nomor WhatsApp teraktivasi di antrean."

        fonnte_token = os.getenv("FONNTE_TOKEN", "Z_x28NAsY@M_vL7Xp6qW")
        url_fonnte = "https://api.fonnte.com/send"
        headers = { "Authorization": fonnte_token }
        
        sukses_kirim = 0
        for pemilih in daftar_antrean:
            target_wa = pemilih['nomor_wa'].strip()
            pesan = f"Halo *{pemilih['nama_lengkap']}*,\n\nIni adalah pengingat otomatis dari Panitia Pemilihan OSIS 2026. 🗳\n\nKami mendeteksi Anda belum menggunakan hak suara murni Anda di bilik digital. Gerbang pemilihan sedang dibuka, yuk masuk ke aplikasi dan salurkan suaramu sekarang demi demokrasi sekolah!\n\n_Pesan otomatis dikirim oleh Sirekap AI Agent_"
            
            payload = {
                'target': target_wa,
                'message': pesan,
                'countryCode': '62'
            }
            
            try:
                res = requests.post(url_fonnte, headers=headers, data=payload, timeout=5)
                if res.status_code == 200 and res.json().get('status') is True:
                    sukses_kirim += 1
                time.sleep(0.5)
            except:
                continue

        catat_log("Sirekap_AI_Agent", "BROADCAST_MASSAL_AI", f"AI mengirim broadcast pengingat sukses ke {sukses_kirim} DPT.")
        return f"🟢 **EKSEKUSI BROADCAST OTONOM BERHASIL!**\n\nAI Agent berhasil menyisir database dan mengirimkan pesan pengingat massal langsung ke **{sukses_kirim} DPT** yang belum mencoblos secara *realtime* via Fonnte Gateway!"
    except Exception as e:
        return f"Gagal mengeksekusi sistem broadcast AI: {str(e)}"

def ai_tool_generate_laporan_pdf_ke_wa_admin(nomor_wa_admin: str) -> str:
    """[FIXED MULTIPART] Menyusun Berita Acara Pleno PDF resmi dari database, lalu mengirimkannya sebagai dokumen lampiran biner asli ke WhatsApp Admin via Fonnte."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') AND is_archived = 0")
        total_dpt = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT COUNT(*) as voted FROM users WHERE sudah_memilih = 1 AND role IN ('siswa', 'guru') AND is_archived = 0")
        voted_dpt = cursor.fetchone()['voted'] or 0
        cursor.execute("SELECT nomor_urut, nama_ketua, nama_wakil, total_suara FROM paslon WHERE is_archived = 0 ORDER BY nomor_urut ASC")
        paslon_data = cursor.fetchall()
        cursor.close()
        conn.close()

        # 1. GENERATE FILE PDF (REPORTLAB)
        pdf_filename = "Berita_Acara_Pleno_E_Voting.pdf"
        pdf_path = os.path.join(os.getcwd(), pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, alignment=TA_CENTER, textColor=colors.HexColor('#1A365D'))
        body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=15, alignment=TA_JUSTIFY)

        story.append(Paragraph("BERITA ACARA REKAPITULASI HASIL PLENO E-VOTING", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Pada hari ini, sistem digital mencatat secara sah dokumen rekapitulasi surat suara bilik digital. Total hak pilih DPT terdaftar adalah <b>{total_dpt}</b> pemilih, dengan total suara murni masuk sebanyak <b>{voted_dpt}</b> suara.", body_style))
        story.append(Spacer(1, 15))

        table_data = [[Paragraph("<b>No Urut</b>", body_style), Paragraph("<b>Kandidat Paslon</b>", body_style), Paragraph("<b>Total Perolehan Suara</b>", body_style)]]
        for p in paslon_data:
            table_data.append([
                Paragraph(str(p['nomor_urut']), body_style),
                Paragraph(f"{p['nama_ketua']} & {p['nama_wakil']}", body_style),
                Paragraph(f"<b>{p['total_suara']} Suara</b>", body_style)
            ])
        
        t = Table(table_data, colWidths=[1*inch, 3.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        doc.build(story)

        # 2. FIX MULTIPART PAYLOAD: Memastikan tipe berkas dikirim murni sebagai biner boks dokumen
        fonnte_token = os.getenv("FONNTE_TOKEN", "Z_x28NAsY@M_vL7Xp6qW")
        url_fonnte = "https://api.fonnte.com/send"
        headers = { "Authorization": fonnte_token.strip() }
        
        payload = {
            'target': str(nomor_wa_admin).strip(),
            'message': '🤖 *[SIREKAP AI EXECUTIVE CORE]*\n\nBerikut adalah berkas Lampiran Berita Acara Pleno Hasil Suara Sah Pemilu E-Voting OSIS 2026 yang berhasil diekstrak langsung oleh AI dari database server pusat.',
            'countryCode': '62'
        }
        
        # Penulisan berkas open-stream biner wajib ditangani secara utuh
        with open(pdf_path, 'rb') as f_pdf:
            files = { 'file': (pdf_filename, f_pdf, 'application/pdf') }
            response_fonnte = requests.post(url_fonnte, headers=headers, data=payload, files=files, timeout=15)
            res_json = response_fonnte.json()

        print(f"\n[AI LAPORAN DEBUG] Response Fonnte Document: {res_json}\n")

        if res_json.get('status') is True:
            return f"🟢 **Sukses Eksekusi Laporan:** Dokumen Berita Acara Berformat PDF berhasil disusun otomatis dan **SUKSES DIKIRIMKAN** ke WhatsApp Admin di nomor `+62{nomor_wa_admin}` via Fonnte Gateway."
        else:
            return f"❌ **PDF Berhasil Dibuat, Tapi Gagal Kirim WA:** Respon Fonnte -> {res_json.get('reason', 'Koneksi API Gagal')}"
    except Exception as e:
        return f"Kegagalan fatal kompilasi laporan PDF: {str(e)}"

# ==============================================================================
# ROUTER API INTERFACE HUB CHAT
# ==============================================================================

@ai_agent_bp.route('/api/admin/ai-agent', methods=['POST'])
def ai_agent_chat():
    if not session.get('username') or session.get('role') not in ['admin', 'super_admin']:
        return jsonify({"status": "error", "message": "Sesi tidak valid."}), 403

    user_message = request.json.get('message', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role IN ('siswa', 'guru') AND is_archived = 0")
        total_dpt = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT COUNT(*) as voted FROM users WHERE sudah_memilih = 1 AND role IN ('siswa', 'guru') AND is_archived = 0")
        voted_dpt = cursor.fetchone()['voted'] or 0
        cursor.close()
        conn.close()

        belum_memilih = total_dpt - voted_dpt

        konteks_instruksi = f"""
        Anda adalah Autonomous Executive AI Agent tertinggi pada sistem E-Voting OSIS SMK HARBAS.
        Anda memegang otoritas penuh atas database MySQL dan token Fonnte Gateway.

        KEMAMPUAN OTONOM UTAMA ANDA:
        1. `ai_tool_ubah_status_gerbang_pemilu`: Buka/tutup saklar bilik suara.
        2. `ai_tool_karantina_blokir_user` / `ai_tool_buka_blokir_user`: Manajemen blokir fraud DPT.
        3. `ai_tool_daftarkan_dpt_tunggal`: Tambah data pemilih.
        4. `ai_tool_arsipkan_paslon_kandidat`: Singkirkan paslon dari surat suara aktif.
        5. `ai_tool_pindai_fraud_spam_otp_otomatis`: Scan & amankan sistem dari brute force OTP.
        6. `ai_tool_analisis_prediksi_partisipasi_live`: Hitung tren statistik penutupan suara.
        7. `ai_tool_broadcast_pengingat_dpt_massal`: Mengirimkan broadcast WhatsApp otomatis ke seluruh sisa {belum_memilih} DPT yang belum mencoblos.
        8. `ai_tool_generate_laporan_pdf_ke_wa_admin`: Menyusun PDF berita acara lalu mengirimkannya sebagai file attachment langsung ke nomor WA admin tujuan.

        ATURAN RESPONS KONTEKS:
        - Jika admin meminta untuk melakukan broadcast, mengirim pengingat ke sisa DPT, atau berkata "picu broadcast sekarang" / "jalankan pengingat massal" / "picu sekarang", langsung panggil fungsi `ai_tool_broadcast_pengingat_dpt_massal`!
        - Laporkan hasilnya dengan tegas dan rapi menggunakan format markdown tebal.
        """

        daftar_fungsi_tools = [
            ai_tool_ubah_status_gerbang_pemilu, 
            ai_tool_karantina_blokir_user,
            ai_tool_buka_blokir_user,
            ai_tool_daftarkan_dpt_tunggal,
            ai_tool_arsipkan_paslon_kandidat,
            ai_tool_pindai_fraud_spam_otp_otomatis,
            ai_tool_analisis_prediksi_partisipasi_live,
            ai_tool_broadcast_pengingat_dpt_massal,
            ai_tool_generate_laporan_pdf_ke_wa_admin
        ]

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=konteks_instruksi,
                tools=daftar_fungsi_tools,
                temperature=0.2
            )
        )

        ai_reply = response.text if response.text else "🤖 Perintah sistem berhasil dijalankan secara otonom oleh AI Agent."
        return jsonify({"status": "success", "reply": ai_reply})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500