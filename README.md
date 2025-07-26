# Pembayaran Listrik Pascabayar

Aplikasi web berbasis Flask untuk mengelola pembayaran listrik secara pascabayar. Proyek ini menyediakan antarmuka untuk admin, petugas, dan pelanggan.

## Fitur

- Autentikasi pengguna dengan peran **admin**, **petugas**, dan **pelanggan**
- Manajemen tarif listrik, pelanggan, dan petugas
- Pencatatan meter dan pembuatan tagihan
- Riwayat tagihan serta statistik penggunaan
- Registrasi pelanggan dan verifikasi pendaftaran

## Instalasi

1. Pastikan Python 3 terpasang.
2. Buat _virtual environment_ dan aktifkan.
3. Install dependensi:

   ```bash
   pip install -r requirements.txt
    ```
4. Siapkan database MySQL dan sesuaikan SQLALCHEMY_DATABASE_URI pada config.py jika diperlukan.

Jalankan aplikasi:
```bash
python run.py
```

Aplikasi akan berjalan pada http://localhost:5000 secara default.

## Struktur Proyek

app/ – kode sumber aplikasi Flask (blueprint, model, form, template)

config.py – konfigurasi aplikasi

run.py – berkas utama untuk menjalankan server

## Lisensi

Proyek ini bersifat open source dan dapat digunakan sesuai kebutuhan