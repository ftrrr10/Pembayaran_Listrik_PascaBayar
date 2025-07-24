from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from functools import wraps

# Membuat blueprint baru untuk area pelanggan
pelanggan_bp = Blueprint('pelanggan', __name__, url_prefix='/pelanggan')

# Membuat "penjaga" untuk memastikan hanya pelanggan yang bisa akses
def pelanggan_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.nama_role != 'pelanggan':
            abort(403) # Error: Akses Dilarang
        return f(*args, **kwargs)
    return decorated_function

@pelanggan_bp.route('/dashboard')
@login_required
@pelanggan_required
def dashboard():
    """
    Halaman utama untuk pelanggan. Menampilkan riwayat tagihan mereka.
    """
    # Ambil profil pelanggan yang tertaut dengan user yang sedang login
    pelanggan = current_user.pelanggan

    if not pelanggan:
        # Kasus jika akun pelanggan belum ditautkan oleh admin
        return "Akun Anda belum terhubung dengan data pelanggan. Hubungi administrator."

    # Ambil semua tagihan milik pelanggan ini, urutkan dari yang terbaru
    semua_tagihan = sorted(
        [penggunaan.tagihan for penggunaan in pelanggan.penggunaan if penggunaan.tagihan],
        key=lambda t: (t.penggunaan.tahun, t.penggunaan.bulan),
        reverse=True
    )

    return render_template('pelanggan/dashboard.html', daftar_tagihan=semua_tagihan)
