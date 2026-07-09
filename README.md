# 🗳️ E-Voting OSIS 2026 - Digital Authentication & Voting Portal

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask Framework](https://img.shields.io/badge/Framework-Flask_3.x-green.svg?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%2FMariaDB-orange.svg?style=for-the-badge&logo=mysql)](https://www.mysql.com/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC.svg?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge)](LICENSE)
[![Security Status](https://img.shields.io/badge/Security-Anti--Fraud%20%26%20OTP-emerald.svg?style=for-the-badge)](https://github.com/muhamad-irpan-ti25a/E-VOTING-OSIS)

**E-Voting OSIS 2026** adalah platform pemungutan suara digital terintegrasi berbasis web yang dirancang khusus untuk mewujudkan Pemilihan Ketua & Wakil Ketua OSIS yang transparan, akuntabel, cepat, dan aman. 

Sistem ini mengusung antarmuka **Cyber Pro Modern** yang responsif, dilengkapi otentikasi aman berbasis **WhatsApp OTP (via Fonnte API)**, integrasi **AI Agent (Google Gemini API)** sebagai asisten navigasi cerdas pemilih, serta proteksi data suara pemilih tingkat tinggi (*One-Vote Policy & Anti-Fraud Logic*).

---

## 📑 Daftar Isi
- [Fitur Utama](#-fitur-utama)
- [Arsitektur & Teknologi](#-arsitektur--teknologi)
- [Struktur Proyek](#-struktur-proyek)
- [Prasyarat Sistem](#-prasyarat-sistem)
- [Panduan Instalasi Lengkap (Terminal)](#-panduan-instalasi-lengkap-terminal)
- [Konfigurasi Database & File `.env`](#-konfigurasi-database--file-env)
- [Cara Menjalankan Aplikasi](#-cara-menjalankan-aplikasi)
- [Detail Alur Sistem & Fitur Login](#-detail-alur-sistem--fitur-login)
- [Pemecahan Masalah (Troubleshooting)](#-pemecahan-masalah-troubleshooting)
- [Kontribusi & Lisensi](#-kontribusi--lisensi)

---

## ✨ Fitur Utama

### 1. 🛡️ Keamanan & Otentikasi Ganda (Dual-Login Mechanism)
- **Automatic Role Detection**: Form login secara otomatis mendeteksi karakter input pengguna.
  - Jika pengguna memasukkan angka (Nomor WA), sistem mengarahkannya sebagai **Pemilih (DPT)**.
  - Jika pengguna memasukkan teks huruf, field password otomatis muncul untuk akses **Administrator / Super Admin**.
- **WhatsApp OTP Engine (Fonnte API)**: Kode OTP 6-digit dikirim secara otomatis ke nomor WhatsApp pemilih yang terdaftar di database DPT.
- **Real-time Countdown Timer**: Sesi token OTP dibatasi selama 120 detik (2 menit) untuk mencegah kebocoran/penyalahgunaan kode.
- **One-Vote Guarantee**: Pemilih yang telah mengeksekusi hak pilih tidak akan dapat meminta OTP atau masuk ke bilik suara kembali.

### 2. 🎨 Antarmuka Cyber Pro UI/UX
- **Modern Dark & Glassmorphism Design**: Tampilan visual futuristik menggunakan Tailwind CSS, Bootstrap Icons, dan SweetAlert2 kustom berukuran proporsional dan responsif.
- **Anti-Shift & Anti-Squeeze Viewport**: CSS yang terkunci rapi mencegah pergeseran halaman (*scroll lock*) maupun efek gepeng saat form difokuskan atau saat popup notifikasi muncul.

### 3. 🤖 AI Voting Assistant (Google Gemini AI)
- Asisten virtual cerdas yang terintegrasi di dalam aplikasi untuk membantu pemilih mendapatkan informasi mengenai tata cara pencoblosan, visi-misi kandidat, dan peraturan pemilu OSIS secara interaktif.

### 4. 📊 Dashboard Kendali Administrator
- Manajemen Data Pemilih Tetap (DPT) & Import/Export Data.
- Manajemen Pasangan Calon (Kandidat) Ketua & Wakil Ketua OSIS.
- Monitoring Rekapitulasi Suara Real-time (Quick Count) dengan visualisasi grafik interaktif.
- Audit Trail & Log Keamanan Percobaan Login.

---

## 🛠️ Arsitektur & Teknologi

| Komponen | Teknologi | Keterangan |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Bahasa pemrograman server utama |
| **Framework** | Flask 3.x | Web framework berbasis Python dengan pola *Blueprint* |
| **Database** | MySQL / MariaDB | Penyimpanan data DPT, Paslon, User, dan Suara |
| **Frontend** | HTML5, JavaScript (ES6+) | Struktur dan interaktivitas client-side |
| **CSS Library** | Tailwind CSS v3 | Utility-first CSS framework untuk tampilan Cyber UI |
| **Alert/Popup** | SweetAlert2 | Custom modal/notifikasi OTP interaktif |
| **WA Gateway** | Fonnte API | Rest API gateway pengiriman pesan OTP WhatsApp |
| **AI Integration** | Google Gemini API (`google-genai`) | Agent AI pembantu pemilih |
| **WSGI Server** | Werkzeug / Gunicorn | Web server gateway interface |

---

## 📂 Struktur Proyek

```text
E-VOTING-OSIS/
│
├── config/                     # Pengaturan Global & Settings
│   ├── __init__.py
│   └── settings.py             # Konfigurasi environment & session
│
├── database/                   # Modul Driver & Koneksi Database
│   ├── __init__.py
│   └── connection.py           # Setup connection pool MySQL / MariaDB
│
├── flask_session/              # Caching session server-side
├── middlewares/                # Guard & Security Handlers
│   ├── __init__.py
│   └── auth_guard.py           # Proteksi middleware hak akses role & token
│
├── migrations/                 # File migrasi & skema database
├── node_modules/               # Dependensi Node.js / Tailwind CLI
│
├── routes/                     # Controller Blueprint API Flask
│   ├── __init__.py
│   ├── ai_agent.py             # Route asisten cerdas Gemini AI
│   ├── auth.py                 # Route login admin & request OTP WhatsApp
│   ├── dpt.py                  # Route manajemen Data Pemilih Tetap
│   ├── paslon.py               # Route pengelolaan data pasangan calon
│   └── spinner.py              # Route fitur undian / acak nomor paslon
│
├── static/                     # Aset Statis Client-Side
│   ├── css/
│   │   ├── input.css           # Tailwind CSS source file
│   │   └── style.css           # Compiled CSS utama
│   ├── js/
│   │   ├── auth.js             # Script interaktivitas login
│   │   ├── dashboard.js        # Script logika dashboard & grafik realtime
│   │   └── vote.js             # Script logika bilik pencoblosan & popup OTP
│   ├── folderrrr/              # Asset pendukung tambahan
│   └── uploads/                # File upload (foto kandidat/paslon)
│
├── templates/                  # Template HTML (Jinja2 Render Engine)
│   ├── admin/                  # Dashboard Tingkat Operator
│   │   ├── daftar_paslon.html
│   │   ├── dashboard.html
│   │   ├── data_pemilih.html
│   │   └── quick_count.html
│   │
│   ├── auth/                   # Halaman Autentikasi
│   │   ├── forgot.html         # Form pemulihan password operator
│   │   ├── login.html          # Gerbang Autentikasi Utama (Cyber Pro UI)
│   │   ├── register.html       # pendaftaran akun operator baru
│   │   └── reset_password.html # Form reset password
│   │
│   ├── super_admin/            # Panel Kontrol Utama Super Admin
│   │   ├── dashboard.html
│   │   ├── data_pemilih.html
│   │   ├── log_aktivitas.html  # Pelacakan audit trail keamanan
│   │   ├── manajemen_admin.html# Kelola akun operator bawah
│   │   ├── manajemen_paslon.html
│   │   ├── proyektor_view.html # Tampilan layar besar live count pleno
│   │   ├── quick_count.html
│   │   ├── rekap_spin.html     # Rekapitulasi hasil undian
│   │   └── spin_paslon.html    # Fitur spinner acak nomor urut paslon
│   │
│   └── user/                   # Halaman Sisi Pemilih (Siswa)
│       ├── terimakasih.html    # Konfirmasi sukses mencoblos
│       └── voting.html         # Bilik pencoblosan suara digital
│
├── .env                        # Variabel lingkungan rahasia (Ignored)
├── app.py                      # Application Entry Point (Main Server Flask)
├── generate_hash.py            # Utility hashing password administrator
├── Berita_Acara_Pleno_E_Voting.pdf # Dokumen PDF legalitas hasil pemilu
├── package.json & package-lock.json # Dependensi Node.js / Tailwind CSS
├── requirements.txt            # Daftar pustaka modul Python
└── npx & Untitled-1.txt        # Utility scripts & berkas pendukung
