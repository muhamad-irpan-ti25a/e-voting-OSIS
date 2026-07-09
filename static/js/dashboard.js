let liveChart = null;

// Menginisialisasi Grafik Batang
function initLiveChart(labels, voteData) {
    const canvas = document.getElementById('liveVoteChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    liveChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: voteData,
                backgroundColor: 'rgba(79, 70, 229, 0.6)',
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

// Sinkronisasi data real-time dashboard statistik (Polling 3 detik)
async function syncDashboard() {
    if(!document.getElementById('liveVoteChart')) return;
    try {
        const response = await fetch('/api/superadmin/dashboard-stats');
        const result = await response.json();
        if (response.ok && result.status === "success") {
            const { summary, paslon_votes } = result.data;
            
            document.getElementById('stat_total_pemilih').innerText = summary.total_pemilih;
            document.getElementById('stat_siswa').innerText = summary.total_siswa;
            document.getElementById('stat_guru').innerText = summary.total_guru;
            document.getElementById('stat_sudah_memilih').innerText = summary.sudah_memilih;
            document.getElementById('stat_belum_memilih').innerText = summary.belum_memilih;
            document.getElementById('stat_partisipasi_persen').innerText = summary.partisipasi_persen + '%';

            const labels = paslon_votes.map(p => `Paslon ${p.nomor_urut}`);
            const votes = paslon_votes.map(p => p.total_suara);

            if (!liveChart) initLiveChart(labels, votes);
            else {
                liveChart.data.labels = labels;
                liveChart.data.datasets[0].data = votes;
                liveChart.update();
            }

            let htmlList = '';
            paslon_votes.forEach(p => {
                htmlList += `
                    <div class="flex justify-between items-center p-3 bg-slate-800/40 border border-slate-800 rounded-xl">
                        <div>
                            <span class="text-xs text-indigo-400 font-bold">No. ${p.nomor_urut}</span>
                            <h4 class="text-sm font-semibold text-white">${p.nama_ketua}</h4>
                        </div>
                        <span class="text-lg font-bold text-white">${p.total_suara} <span class="text-xs text-slate-500 font-normal">Suara</span></span>
                    </div>`;
            });
            document.getElementById('paslon_cards_container').innerHTML = htmlList;
        }
    } catch (err) { console.error(err); }
}

if(document.getElementById('liveVoteChart')) {
    syncDashboard();
    setInterval(syncDashboard, 3000);
}

// Manajemen CRUD Data Admin (Super Admin View)
async function loadDataAdmin() {
    const table = document.getElementById('admin_table_body');
    if(!table) return;
    const res = await fetch('/api/superadmin/admin');
    const result = await res.json();
    if(res.ok) {
        let html = '';
        result.data.forEach(admin => {
            html += `
                <tr class="hover:bg-slate-800/30">
                    <td class="px-6 py-4 font-semibold text-white">${admin.nama_lengkap}</td>
                    <td class="px-6 py-4 text-slate-400">${admin.username}</td>
                    <td class="px-6 py-4 text-center">
                        <button onclick="hapusAdmin(${admin.id})" class="text-red-400 bg-red-500/10 p-2 rounded-lg hover:bg-red-500 hover:text-white transition-all"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>`;
        });
        table.innerHTML = html || '<tr><td colspan="3" class="text-center py-6 text-slate-500">Belum ada staf admin.</td></tr>';
    }
}
if(document.getElementById('admin_table_body')) loadDataAdmin();

async function hapusAdmin(id) {
    const conf = await Swal.fire({ title: 'Hapus Akses?', text: "Akun admin panitia akan dihapus permanen.", icon: 'warning', showCancelButton: true });
    if(conf.isConfirmed) {
        const res = await fetch(`/api/superadmin/admin/${id}`, { method: 'DELETE' });
        if(res.ok) { Swal.fire('Terhapus', 'Akses admin dicabut.', 'success'); loadDataAdmin(); }
    }
}

// Manajemen CRUD Data Pemilih (Admin View)
async function loadDPTList() {
    const table = document.getElementById('dpt_table_body');
    if(!table) return;
    const res = await fetch('/api/admin/pemilih');
    const result = await res.json();
    if(res.ok) {
        document.getElementById('dpt_badge_counter').innerText = `${result.data.length} Terdaftar`;
        let html = '';
        result.data.forEach(p => {
            const statusAkun = p.nomor_wa ? '<span class="text-emerald-400">✓ Aktif</span>' : '<span class="text-slate-500">Belum Aktivasi</span>';
            const statusVoted = p.sudah_memilih === 1 ? '<span class="bg-red-500/10 text-red-400 px-2 py-0.5 rounded text-xs border border-red-500/10">Sudah Memilih</span>' : '<span class="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-xs border border-emerald-500/10">Belum Memilih</span>';
            const actionBypass = p.sudah_memilih === 1 ? `<button onclick="bypassResetUser(${p.id})" class="text-xs bg-amber-600/20 hover:bg-amber-600 text-amber-400 hover:text-white px-2.5 py-1 rounded-lg transition-all"><i class="bi bi-arrow-counterclockwise"></i> Buka Blokir</button>` : `<span class="text-xs text-slate-600">Tidak ada aksi</span>`;
            
            html += `
                <tr class="hover:bg-slate-800/20">
                    <td class="px-6 py-4 font-mono">${p.username}</td>
                    <td class="px-6 py-4 font-semibold text-white">${p.nama_lengkap}</td>
                    <td class="px-6 py-4 uppercase text-xs text-indigo-300">${p.role}</td>
                    <td class="px-6 py-4 text-xs">${statusAkun}</td>
                    <td class="px-6 py-4">${statusVoted}</td>
                    <td class="px-6 py-4 text-center">${actionBypass}</td>
                </tr>`;
        });
        table.innerHTML = html;
    }
}
if(document.getElementById('dpt_table_body')) loadDPTList();

async function bypassResetUser(id) {
    const confirmation = await Swal.fire({ title: 'Buka Hak Suara?', text: 'Status akun akan dikembalikan menjadi belum memilih karena kendala teknis di TPS.', icon: 'info', showCancelButton: true });
    if(confirmation.isConfirmed) {
        const res = await fetch(`/api/admin/pemilih/reset-status/${id}`, { method: 'POST' });
        if(res.ok) { Swal.fire('Sukses', 'Status memilih berhasil direset.', 'success'); loadDPTList(); }
    }
}

// Logika Logout Global Panitia
async function handleLogout() {
    const res = await fetch('/api/logout', { method: 'POST' });
    if(res.ok) window.location.href = '/auth/login';
}