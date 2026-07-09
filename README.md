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
├── config/                     # Konfigurasi aplikasi & driver koneksi
│   ├── __init__.py
│   └── database.py             # Setup & manajemen pool koneksi MySQL/MariaDB
│
├── routes/                     # Router / Endpoint API Flask (Modular Blueprints)
│   ├── __init__.py
│   ├── admin.py                # Endpoint kelola kandidat, DPT, & rekap suara
│   ├── ai_agent.py             # Endpoint terintegrasi Gemini AI Agent
│   ├── auth.py                 # Endpoint request OTP, verifikasi, & login admin
│   └── voting.py               # Endpoint bilik suara & proses pencoblosan
│
├── static/                     # Aset Statis Frontend
│   ├── css/
│   │   └── style.css           # Custom CSS styling & Tailwind directives
│   ├── js/
│   │   ├── admin.js            # Script logika interaksi dashboard admin
│   │   └── voting.js           # Script logika interaksi bilik pencoblosan
│   └── img/                    # Asset gambar, logo OSIS, & foto kandidat
│       ├── candidates/
│       └── logo.png
│
├── templates/                  # Template HTML (Jinja2 Render Engine)
│   ├── admin/
│   │   ├── dashboard.html      # Panel kendali Super Admin / Operator
│   │   └── candidates.html     # Manajemen data paslon kandidat
│   ├── auth/
│   │   ├── login.html          # Gerbang Autentikasi Utama (Cyber Pro UI)
│   │   └── forgot.html         # Halaman bypass pemulihan operator
│   ├── user/
│   │   ├── bilik_suara.html    # Halaman pencoblosan suara pemilih
│   │   └── success.html        # Halaman konfirmasi suara berhasil masuk
│   └── components/             # Komponen HTML modular yang re-usable
│       ├── navbar.html
│       └── footer.html
│
├── utils/                      # Helper & Fungsi Utilitas Tambahan
│   ├── __init__.py
│   ├── fonnte_helper.py        # Klien HTTP Request pengiriman WA OTP via Fonnte API
│   ├── security.py             # Hashing password, sanitasi input, & token generator
│   └── decorators.py           # Decorator Flask proteksi role/sesi login
│
├── database/                   # File Skema Database
│   └── schema.sql              # DDL Script (Tabel DPT, Paslon, Votes, & Admin)
│
├── .env                        # Variabel lingkungan lokal (Rahasia / Ignored)
├── .env.example                # Template contoh acuan variabel lingkungan
├── .gitignore                  # Berkas pengabaian Git
├── app.py                      # Application Entry Point (Server Flask Utama)
├── README.md                   # Dokumentasi resmi proyek
└── requirements.txt            # Daftar dependensi modul Python
