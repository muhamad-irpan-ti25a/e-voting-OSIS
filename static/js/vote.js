// ==============================================================================
// LOGIKA UTAMA BILIK SUARA INTERAKTIF (static/js/vote.js) - PERFECT SYMMETRY
// ==============================================================================
document.addEventListener('DOMContentLoaded', loadKandidatPaslon);

let daftarPaslon = [];

async function loadKandidatPaslon() {
    const gridContainer = document.getElementById('paslon_grid_container');
    if (!gridContainer) return;

    gridContainer.innerHTML = `
        <div class="col-span-full text-center py-16">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent mb-4"></div>
            <p class="text-gray-400 font-bold text-xl">Membuka Jalur Enkripsi Kotak Suara...</p>
        </div>`;

    try {
        const response = await fetch('/api/user/paslon-aktif');
        const result = await response.json();

        if (result.status === "success" && result.data) {
            daftarPaslon = result.data;
            renderBilikSuara(daftarPaslon);
        } else {
            gridContainer.innerHTML = `<div class="col-span-full text-center text-red-400 font-black p-12 text-xl">Gagal mengambil data surat suara: ${result.message}</div>`;
        }
    } catch (error) {
        console.error("Error loading paslon:", error);
        gridContainer.innerHTML = `<div class="col-span-full text-center text-red-400 font-black p-12 text-xl">Koneksi database terputus. Periksa jaringan Anda.</div>`;
    }
}

function renderBilikSuara(listPaslon) {
    const gridContainer = document.getElementById('paslon_grid_container');
    if (!gridContainer) return;
    
    if (listPaslon.length === 0) {
        gridContainer.innerHTML = `<div class="col-span-full text-center text-slate-500 font-black p-12 text-2xl">Belum ada Surat Suara Resmi dari KPUM.</div>`;
        return;
    }

    gridContainer.innerHTML = listPaslon.map(p => {
        let fotoUrl = '/static/uploads/default.png';
        if (p.foto) {
            fotoUrl = p.foto.includes('static/') ? `/${p.foto}` : `/static/uploads/${p.foto}`;
        }

        const namaKetuaAman = p.nama_ketua.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

        // Memecah baris teks misi menjadi list berangka besar
        let listMisiHtml = '';
        const barisMisi = p.misi ? p.misi.split('\n') : [];
        let indexMisi = 1;

        barisMisi.forEach(misi => {
            if (misi.trim() !== '') {
                listMisiHtml += `
                    <div class="flex items-start gap-6">
                        <span class="text-2xl font-black text-indigo-400 min-w-[28px]">${indexMisi}</span>
                        <p class="text-xl lg:text-2xl font-extrabold text-white leading-snug tracking-wide">${misi.trim()}</p>
                    </div>
                `;
                indexMisi++;
            }
        });

        if (listMisiHtml === '') {
            listMisiHtml = `<p class="text-lg text-gray-500 italic">Belum ada rincian misi kerja.</p>`;
        }

        return `
            <div class="paslon-row-wrapper" style="width: 100%; margin-bottom: 48px;">
                <div class="spotify-wrapper">
                    
                    <div class="about-artist-box shadow-2xl" style="background-image: linear-gradient(rgba(0,0,0,0) 15%, rgba(18,18,18,0.98) 70%), url('${fotoUrl}');">
                        <div class="text-base font-black tracking-widest text-gray-400 uppercase">About the paslon</div>
                        
                        <div class="space-y-8 w-full" style="margin-top: auto; padding-top: 40px;">
                            <div style="display: flex; justify-content: space-between; align-items: end; gap: 24px; flex-wrap: wrap;">
                                <div>
                                    <h2 style="font-size: 48px; font-weight: 900; color: #fff; margin: 0; tracking-tight: -0.05em; line-height: 1;">PASLON ${p.nomor_urut}</h2>
                                    <p style="font-size: 13px; color: #818cf8; font-weight: 800; tracking-widest: 0.1em; margin: 12px 0 0 0; text-transform: uppercase;"><i class="bi bi-shield-check"></i> Surat Suara Terverifikasi</p>
                                </div>
                                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px; flex-shrink: 0;">
                                    <span style="font-size: 11px; color: #34d399; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;"><i class="bi bi-cursor-fill"></i> Klik Di Sini</span>
                                    <button onclick="eksekusiPilihanSuara(${p.id}, ${p.nomor_urut}, '${namaKetuaAman}')" class="spotify-pill-btn shadow-2xl">Coblos Paslon</button>
                                </div>
                            </div>
                            
                            <div style="padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; gap: 12px; width: 100%;">
                                <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.4); padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.03); gap: 12px;">
                                    <span style="color: #94a3b8; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; width: 90px; flex-shrink: 0;">Calon Ketua</span>
                                    <span style="color: #ffffff; font-weight: 900; font-size: 16px; flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${p.nama_ketua}</span>
                                    <span style="font-size: 12px; font-family: monospace; font-weight: 700; color: #818cf8; background: rgba(99,102,241,0.1); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(99,102,241,0.2); flex-shrink: 0;">${p.kelas_ketua || '-'}</span>
                                </div>
                                <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.4); padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.03); gap: 12px;">
                                    <span style="color: #94a3b8; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; width: 90px; flex-shrink: 0;">Calon Wakil</span>
                                    <span style="color: #cbd5e1; font-weight: 900; font-size: 16px; flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${p.nama_wakil}</span>
                                    <span style="font-size: 12px; font-family: monospace; font-weight: 700; color: #a78bfa; background: rgba(167,139,250,0.1); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(167,139,250,0.2); flex-shrink: 0;">${p.kelas_wakil || '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 24px; justify-content: space-between; width: 100%;">
                        
                        <div class="spotify-panel-dark" style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <span style="font-size: 12px; font-weight: 900; color: #818cf8; letter-spacing: 0.1em; text-transform: uppercase; display: flex; align-items: center; gap: 6px;">
                                    <i class="bi bi-eye-fill"></i> Visi Utama
                                </span>
                                <span style="font-size: 11px; font-weight: 700; color: #475569;">Show all</span>
                            </div>
                            
                            <div style="margin: auto 0; padding: 12px 0;">
                                <p style="font-size: 20px; font-weight: 900; color: #ffffff; line-height: 1.5; font-style: italic; margin: 0;">
                                    "${p.visi || 'Belum mengunggah visi strategis.'}"
                                </p>
                            </div>
                            
                            <div style="font-size: 10px; color: #475569; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 16px;">Formulir Pokok Kebijakan Visi</div>
                        </div>

                        <div class="spotify-panel-dark" style="height: 300px; display: flex; flex-direction: column; justify-content: space-between;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <span style="font-size: 12px; font-weight: 900; color: #a78bfa; letter-spacing: 0.1em; text-transform: uppercase; display: flex; align-items: center; gap: 6px;">
                                    <i class="bi bi-list-check"></i> Misi Kerja & Program Utama
                                </span>
                                <span style="font-size: 11px; font-weight: 700; color: #475569;">Open queue</span>
                            </div>
                            
                            <div class="overflow-y-auto clean-scroll" style="flex-grow: 1; padding-right: 8px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; max-height: 200px;">
                                ${listMisiHtml}
                            </div>
                        </div>

                    </div>

                </div>
            </div>
        `;
    }).join('');
}

async function eksekusiPilihanSuara(paslonId, nomorUrut, namaKetua) {
    Swal.fire({
        title: 'Konfirmasi Suara Sah?',
        text: `Anda memilih Paslon No. ${nomorUrut} (${namaKetua}). Setelah dikirim, hak pilih Anda selesai dan sistem akan mengunci serta memblokir akun Anda demi mencegah double-voting!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#10b981',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Ya, Coblos Sekarang!',
        cancelButtonText: 'Batal'
    }).then(async (result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'Menyimpan Suara...',
                text: 'Membekukan token autentikasi akun Anda secara otomatis...',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            try {
                const response = await fetch('/api/vote', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ paslon_id: paslonId })
                });
                const resData = await response.json();
                Swal.close();

                if (response.ok && resData.status === "success") {
                    // ======================================================================
                    // FIX LOCK ENGINE TIMER: Menahan popup sukses selama 3 detik murni
                    // ======================================================================
                    Swal.fire({
                        icon: 'success',
                        title: 'Suara Sah Berhasil Masuk!',
                        text: 'Pilihan Anda sukses dienkripsi penuh ke kotak suara pusat server sekolah.',
                        confirmButtonColor: '#1ed760',
                        confirmButtonText: 'Selesai',
                        allowOutsideClick: false,
                        timer: 3000,
                        timerProgressBar: true,
                        willClose: () => {
                            // Dipindah murni hanya setelah siklus popup ditutup total
                            window.location.href = '/user/terimakasih';
                        }
                    }).then((clickResult) => {
                        if (clickResult.isConfirmed) {
                            window.location.href = '/user/terimakasih';
                        }
                    });
                } else {
                    Swal.fire('Proses Ditolak', resData.message || 'Sesi tidak sah.', 'error');
                }
            } catch (error) {
                Swal.close();
                console.error("Voting error:", error);
                Swal.fire('Gangguan Jaringan', 'Gagal menghubungi server pengaman suara.', 'error');
            }
        }
    });
}