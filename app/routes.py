from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """
    Rute untuk halaman utama (homepage).
    Kini terdaftar di blueprint 'main_bp'.
    """
    # Data sederhana yang akan kita kirim ke template
    judul_halaman = "Selamat Datang"
    deskripsi = "Ini adalah aplikasi pembayaran listrik pascabayar."
    
    # Merender file 'index.html' dan mengirimkan data ke dalamnya
    return render_template('index.html', title=judul_halaman, description=deskripsi)

# Anda bisa menambahkan rute lain untuk blueprint ini di bawah
# @main_bp.route('/profil')
# def profile():
#     return "Ini halaman profil"