# 🗳️ E-Voting OSIS - Platform Pemungutan Suara Digital Modern

![Version](https://img.shields.io/badge/version-2.5.0-indigo.svg?style=for-the-badge)
![Framework](https://img.shields.io/badge/Framework-Flask_3.x-green.svg?style=for-the-badge&logo=flask)
![Database](https://img.shields.io/badge/Database-MySQL%2FMariaDB-orange.svg?style=for-the-badge&logo=mysql)
![Security](https://img.shields.io/badge/Security-Auth__Guard%20Active-emerald.svg?style=for-the-badge)
![Node Engine](https://img.shields.io/badge/Node-v18%2B-blue.svg?style=for-the-badge&logo=node.js)

**E-Voting OSIS** adalah sistem manajemen pemilu digital berbasis web yang dirancang menggunakan Python Flask untuk memfasilitasi pemilihan Ketua dan Wakil Ketua OSIS secara aman, transparan, dan real-time. 

Sistem ini mengadopsi konsep keamanan tingkat lanjut dengan arsitektur **Middleware Auth Guard**, otentikasi WhatsApp OTP, dan pemisahan hak akses berjenjang yang memisahkan fitur antara **User (Pemilih)**, **Admin**, dan **Super Admin**.

---

## 📂 Struktur Proyek Terbuka (Repository Tree)

Berikut adalah pemetaan berkas dan struktur folder resmi sesuai arsitektur proyek:

```text
E-VOTING-OSIS/
│
├── config/                     # Pengaturan Global Aplikasi
│   ├── settings.py             # Konfigurasi app, session, dan global environment
│   └── __init__.py
│
├── database/                   # Modul Basis Data (MySQL / MariaDB)
│   ├── connection.py           # Driver koneksi database pool
│   └── __init__.py
│
├── middlewares/                # Filter & Interseptor Keamanan Sesi
│   ├── auth_guard.py           # Validasi token, hak akses role, dan proteksi rute
│   └── __init__.py
│
├── routes/                     # Controller / Modul Blueprint API Flask
│   ├── ai_agent.py             # Handler asisten cerdas berbasis Google Gemini AI
│   ├── auth.py                 # Handler otentikasi login admin & request OTP Fonnte
│   ├── dpt.py                  # Handler manajemen Data Pemilih Tetap
│   ├── paslon.py               # Handler pengelolaan data pasangan calon
│   ├── spinner.py              # Handler fitur undian/acak nomor urut paslon
│   └── __init__.py
│
├── flask_session/              # Penyimpanan session server-side (server caching)
├── migrations/                 # File tracking perubahan skema database
├── node_modules/               # Dependensi package JavaScript/Tailwind CLI
│
├── static/                     # Asset Statis Utama Frontend
│   ├── css/
│   │   ├── input.css           # Tailwind source file
│   │   └── style.css           # File compile CSS utama halaman
│   ├── js/
│   │   ├── auth.js             # Logika interaktivitas login & deteksi DPT/Admin
│   │   ├── dashboard.js        # Logika visualisasi grafik realtime & tabel data
│   │   └── vote.js             # Logika interaksi bilik pencoblosan & SweetAlert2
│   ├── folderrrr/              # Dokumentasi asset tambahan
│   └── uploads/                # Penyimpanan gambar paslon / kandidat yang diunggah
│
├── templates/                  # Render Engine View (Jinja2)
│   ├── admin/                  # Dashboard Tingkat Operator/Admin
│   │   ├── daftar_paslon.html
│   │   ├── dashboard.html
│   │   ├── data_pemilih.html
│   │   └── quick_count.html
│   │
│   ├── auth/                   # Sistem Gerbang Otentikasi
│   │   ├── forgot.html         # Lupa password admin
│   │   ├── login.html          # Gerbang utama login DPT & Admin (Bebas Gepeng)
│   │   ├── register.html       # Pembuatan akun operator baru
│   │   └── reset_password.html # Pengaturan ulang kredensial password
│   │
│   ├── super_admin/            # Panel Kontrol Tertinggi (Hak Akses Penuh)
│   │   ├── dashboard.html      # Overview utama status server global
│   │   ├── data_pemilih.html   # Manajemen database DPT seluruh siswa
│   │   ├── log_aktivitas.html  # Audit trail pelacakan aksi mencurigakan
│   │   ├── manajemen_admin.html# Kelola akun admin level operator bawah
│   │   ├── manajemen_paslon.html
│   │   ├── proyektor_view.html # Tampilan layar besar real-time untuk pleno
│   │   ├── quick_count.html    # Grafik live perhitungan suara sah
│   │   ├── rekap_spin.html     # Hasil undian spinner
│   │   └── spin_paslon.html    # Modul acak nomor urut kandidat
│   │
│   └── user/                   # Tampilan Sisi Pemilih (Siswa)
│       ├── voting.html         # Bilik suara digital tempat mencoblos kandidat
│       └── terimakasih.html    # Landing page sukses mencoblos (Status: Voted)
│
├── .env                        # Variabel rahasia lokal (Private / Ignored)
├── app.py                      # Berkas Utama untuk Menyalakan Server Flask
├── generate_hash.py            # Utility script pembuatan enkripsi password admin
├── Berita_Acara_Pleno_E_Voting.pdf # Output dokumen legalitas hasil pemilu
├── package.json & package-lock.json # Dependensi Node.js / Tailwind CSS
├── requirements.txt            # Daftar dependensi library Python
└── npx & Untitled-1.txt        # File utilitas & skrip eksekusi lokal
