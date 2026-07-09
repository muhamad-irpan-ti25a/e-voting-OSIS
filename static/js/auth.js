// ==============================================================================
// A. LOGIKA FORM LOGIN (SINKRONISASI GERBANG UTAMA BARU - USER VS ADMIN)
// ==============================================================================
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Elemen input default halaman login konvensional
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');

        // ----------------------------------------------------------------------
        // JALUR 1: LOGIKA LOGIN UNTUK PANITIA (ADMIN & SUPER ADMIN)
        // ----------------------------------------------------------------------
        // Jika form diisi kombinasi username teks biasa (bukan angka murni nomor hp)
        // atau jika di halaman login kamu masih menyediakan input password terliat.
        if (passwordInput && passwordInput.value.trim() !== "") {
            const username = usernameInput.value.trim();
            const password = passwordInput.value;

            if (!username || !password) {
                return Swal.fire({ icon: 'warning', title: 'Peringatan', text: 'Username dan Password wajib diisi!', confirmButtonColor: '#4f46e5' });
            }

            Swal.fire({ title: 'Memproses Autentikasi...', text: 'Menghubungkan ke gerbang enkripsi panel kontrol', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const result = await response.json();

                if (response.ok) {
                    Swal.fire({ icon: 'success', title: 'Login Operator Berhasil!', text: result.message, timer: 1200, showConfirmButton: false }).then(() => {
                        window.location.href = result.redirect; 
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Akses Ditolak', text: result.message, confirmButtonColor: '#4f46e5' });
                }
            } catch (error) {
                console.error("Admin Login Error:", error);
                Swal.fire({ icon: 'error', title: 'Koneksi Terputus', text: 'Gagal terhubung ke server database utama.', confirmButtonColor: '#4f46e5' });
            }
            return; // Hentikan eksekusi agar tidak masuk ke jalur user
        }

        // ----------------------------------------------------------------------
        // JALUR 2: LOGIKA LOGIN UNTUK USER / PEMILIH (MURNI NOMOR HP + OTP)
        // ----------------------------------------------------------------------
        // Jika password kosong, berarti ini adalah user yang menginput nomor HP di kolom utama
        const nomorWaInput = usernameInput.value.trim();

        if (!nomorWaInput) {
            return Swal.fire({ icon: 'warning', title: 'Peringatan', text: 'Silakan masukkan Nomor WhatsApp Anda untuk meminta akses masuk!', confirmButtonColor: '#4f46e5' });
        }

        // --- LANGKAH 1: Kirim Permintaan OTP ke Backend ---
        Swal.fire({ title: 'Memproses Nomor HP...', text: 'Memeriksa DPT dan mengirimkan kode keamanan via WhatsApp Fonnte...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        try {
            const responseRequest = await fetch('/api/login/user/request-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nomor_wa: nomorWaInput })
            });
            const resultRequest = await responseRequest.json();
            Swal.close();

            if (!responseRequest.ok) {
                return Swal.fire({ icon: 'error', title: 'Gagal Masuk', text: resultRequest.message, confirmButtonColor: '#4f46e5' });
            }

            // --- LANGKAH 2: Munculkan Pop-up Input OTP Interaktif Jika OTP Berhasil Dikirim ---
            const { value: otpCode } = await Swal.fire({
                title: 'Verifikasi Keamanan Bilik Suara',
                text: 'Kode OTP telah dikirimkan ke WhatsApp Anda. Silakan masukkan 6 digit kode tersebut di bawah ini:',
                input: 'text',
                inputPlaceholder: 'Masukkan 6 Digit OTP',
                showCancelButton: true,
                confirmButtonColor: '#10b981',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Verifikasi & Masuk',
                cancelButtonText: 'Batal',
                inputValidator: (value) => {
                    if (!value) return 'Kode OTP tidak boleh kosong!';
                    if (value.length !== 6 || isNaN(value)) return 'Kode OTP harus berupa 6 digit angka murni!';
                }
            });

            // Jika user menekan tombol batal pada prompt OTP
            if (!otpCode) return;

            // --- LANGKAH 3: Kirim Kode OTP Ke Backend Untuk Validasi & Sesi ---
            Swal.fire({ title: 'Memvalidasi OTP...', text: 'Membuka jalur enkripsi bilik suara...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

            const responseVerify = await fetch('/api/login/user/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nomor_wa: nomorWaInput, otp: otpCode })
            });
            const resultVerify = await responseVerify.json();
            Swal.close();

            if (responseVerify.ok) {
                Swal.fire({ icon: 'success', title: 'Otentikasi Berhasil!', text: resultVerify.message, timer: 1200, showConfirmButton: false }).then(() => {
                    window.location.href = resultVerify.redirect; // Pengalihan otomatis ke /user/voting
                });
            } else {
                Swal.fire({ icon: 'error', title: 'Verifikasi Gagal', text: resultVerify.message, confirmButtonColor: '#4f46e5' });
            }

        } catch (error) {
            console.error("User Login Engine Error:", error);
            Swal.fire({ icon: 'error', title: 'Gangguan Sistem', text: 'Gagal terhubung ke server pengaman suara.', confirmButtonColor: '#4f46e5' });
        }
    });
}