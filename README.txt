REYZ DOWNLOADER — PAKET DEPLOY

ISI PAKET
- index.html: tampilan HTML terbaru yang dikirim, dipertahankan apa adanya.
- app.py: backend Flask untuk mengambil URL langsung ke berkas media.
- requirements.txt: dependensi Python.
- render.yaml: konfigurasi deploy Render.
- README.txt: petunjuk dan batasan.

CARA DEPLOY SINGKAT KE RENDER
1. Ekstrak ZIP ini.
2. Upload kelima file ke repository GitHub milikmu (index.html harus di folder utama/root).
3. Di Render, buat New > Web Service dan hubungkan repository tersebut.
4. Render membaca render.yaml; jika diminta, gunakan:
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
5. Tunggu deploy selesai, lalu buka URL layanan Render di Chrome.

CATATAN PENTING
- Ini hanya mendukung URL langsung ke berkas media publik yang memang boleh kamu unduh. URL halaman biasa YouTube/TikTok/Pinterest tidak diproses.
- Mode YouTube MP3 belum mengubah video menjadi MP3. Mode itu hanya menerima URL langsung berjenis audio/* atau video/*; video tidak dikonversi ke audio.
- Login pada halaman hanya simulasi visual: username/password apa pun yang tidak kosong diterima. Jangan masukkan kata sandi akun asli.
- Backend menolak alamat IP privat/nonpublik, membatasi berkas sampai 100 MB, dan memeriksa tipe media.
- Jangan gunakan untuk mengunduh konten yang tidak kamu miliki atau tidak mendapat izin untuk mengunduh.
- Hosting gratis bisa tidur saat tidak digunakan dan mungkin perlu beberapa saat untuk aktif kembali. Ketersediaan/kuota bergantung pada kebijakan penyedia hosting.
- Jangan menyimpan rahasia, kata sandi, atau token pribadi di repository publik.
