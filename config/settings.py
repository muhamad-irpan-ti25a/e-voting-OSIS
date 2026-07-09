import requests
import os

# Instans Global Penanda Pintu Pemilu
STATUS_GERBANG_PEMILU = 'belum_dimulai'
# Mengunci token Fonnte aktif milikmu agar sinkron secara menyeluruh
FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "1nqujfT3A5hT71idmaEK")

def normalisasi_nomor_wa(nomor_input):
    """Membersihkan nomor inputan user dan menyisakan angka intinya saja (tanpa 628/08)"""
    clean = ''.join(filter(str.isdigit, str(nomor_input)))
    if clean.startswith('628'):
        return clean[2:]
    elif clean.startswith('08'):
        return clean[1:]
    elif clean.startswith('8'):
        return clean
    return clean

def kirim_wa_otp(nomor_wa, pesan):
    """Fungsi pengiriman pesan teks OTP yang sudah disesuaikan dengan skema API Fonnte multipart payload"""
    url = "https://api.fonnte.com/send"
    headers = {"Authorization": FONNTE_TOKEN.strip()}
    
    # --------------------------------------------------------------------------
    # PERBAIKAN FORMULASI TARGET: 
    # Karena nomor_wa dari auth.py dikirim dalam bentuk hasil normalisasi (misal: 857xxx),
    # kita wajib memastikan nomor tersebut memiliki awalan kode negara '628xxx' agar dikenali Fonnte.
    # --------------------------------------------------------------------------
    target_wa = str(nomor_wa).strip()
    if not target_wa.startswith('62') and not target_wa.startswith('0'):
        target_wa = '62' + target_wa
    elif target_wa.startswith('0'):
        target_wa = '62' + target_wa[1:]

    data = {
        'target': target_wa,
        'message': str(pesan),
        'countryCode': '62'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        respon_json = response.json()
        
        # MONITORING LOG MANDIRI DI TERMINAL CMD FLASK
        print(f"\n================ [LOG OTP PEMILIH VIA FONNTE] ================")
        print(f"Target Kirim     : {target_wa}")
        print(f"HTTP Status Code : {response.status_code}")
        print(f"Respon Fonnte    : {respon_json}")
        print(f"==============================================================\n")
        
        if respon_json.get('status') is True:
            return True
        else:
            print(f"❌ [FONNTE REJECT] Alasan Gagal: {respon_json.get('reason')}")
            return False
            
    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Gagal menghubungi endpoint Fonnte: {str(e)}")
        return False

def buat_pesan_otp(otp):
    return (f"Halo, Pemilih! 🗳️\n\n"
            f"Anda sedang melakukan proses *Aktivasi Mandiri Bilik Suara Digital E-Voting OSIS 2026*.\n\n"
            f"Kode OTP Anda adalah: *{otp}*\n\n"
            f"Kode ini bersifat *RAHASIA* dan akan kedaluwarsa dalam 5 menit. "
            f"Jangan berikan kode ini kepada siapa pun, termasuk panitia. "
            f"Keamanan suara Anda adalah prioritas kami.")

def buat_pesan_otp_login(otp):
    return (f"Halo, Pemilih! 🗳️\n\n"
            f"Berikut adalah Kode OTP untuk masuk ke Bilik Suara Digital E-Voting OSIS 2026: *{otp}*\n\n"
            f"Kode ini bersifat *RAHASIA* dan kedaluwarsa dalam 2 menit. "
            f"Jangan berikan kode ini kepada siapa pun, termasuk panitia lapangan.")