from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Pelanggan, Penggunaan, Tagihan
from .forms import FormPencatatanMeter
import datetime
from . import db

# Membuat blueprint baru untuk area petugas
petugas_bp = Blueprint('petugas', __name__, url_prefix='/petugas')

# Custom decorator untuk memastikan hanya petugas yang bisa akses
from functools import wraps
from flask import abort

def petugas_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.nama_role != 'petugas':
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@petugas_bp.route('/dashboard')
@login_required
@petugas_required
def dashboard():
    """
    Halaman utama untuk petugas. Menampilkan daftar semua pelanggan.
    """
    daftar_pelanggan = Pelanggan.query.order_by(Pelanggan.nama_pelanggan).all()
    return render_template('petugas/dashboard.html', daftar_pelanggan=daftar_pelanggan)

@petugas_bp.route('/catat-meter/<int:pelanggan_id>', methods=['GET', 'POST'])
@login_required
@petugas_required
def catat_meter(pelanggan_id):
    pelanggan = Pelanggan.query.get_or_404(pelanggan_id)
    form = FormPencatatanMeter()

    # Tentukan bulan dan tahun saat ini
    sekarang = datetime.datetime.now()
    bulan_ini = sekarang.month
    tahun_ini = sekarang.year

    # Cek apakah sudah ada catatan untuk bulan ini
    catatan_bulan_ini = Penggunaan.query.filter_by(
        pelanggan_id=pelanggan.id, 
        bulan=bulan_ini, 
        tahun=tahun_ini
    ).first()
    if catatan_bulan_ini:
        flash('Pencatatan untuk pelanggan ini di bulan ini sudah dilakukan.', 'info')
        return redirect(url_for('petugas.dashboard'))

    # Cari meteran akhir dari bulan sebelumnya untuk dijadikan meteran awal bulan ini
    bulan_lalu = bulan_ini - 1
    tahun_lalu = tahun_ini
    if bulan_lalu == 0:
        bulan_lalu = 12
        tahun_lalu -= 1
    
    catatan_bulan_lalu = Penggunaan.query.filter_by(
        pelanggan_id=pelanggan.id,
        bulan=bulan_lalu,
        tahun=tahun_lalu
    ).first()

    meter_awal_bulan_ini = 0
    if catatan_bulan_lalu:
        meter_awal_bulan_ini = catatan_bulan_lalu.meter_akhir

    if form.validate_on_submit():
        meter_akhir = form.meter_akhir.data
        if meter_akhir < meter_awal_bulan_ini:
            flash('Meteran akhir tidak boleh lebih kecil dari meteran awal bulan ini!', 'danger')
            return render_template('petugas/catat_meter.html', title='Catat Meter', form=form, pelanggan=pelanggan, meter_awal=meter_awal_bulan_ini)

        # --- Proses Perhitungan ---
        # 1. Simpan data penggunaan
        penggunaan_baru = Penggunaan(
            pelanggan_id=pelanggan.id,
            bulan=bulan_ini,
            tahun=tahun_ini,
            meter_awal=meter_awal_bulan_ini,
            meter_akhir=meter_akhir
        )
        db.session.add(penggunaan_baru)
        
        # 2. Hitung dan buat tagihan
        jumlah_meter = meter_akhir - meter_awal_bulan_ini
        total_bayar = jumlah_meter * pelanggan.tarif.tarif_per_kwh
        
        tagihan_baru = Tagihan(
            penggunaan=penggunaan_baru, # Relasi langsung
            jumlah_meter=jumlah_meter,
            total_bayar=total_bayar,
            tanggal_tagihan=sekarang.date()
        )
        db.session.add(tagihan_baru)
        
        # 3. Commit semua ke database
        db.session.commit()
        
        flash(f'Tagihan untuk {pelanggan.nama_pelanggan} berhasil dibuat!', 'success')
        return redirect(url_for('petugas.dashboard'))

    return render_template('petugas/catat_meter.html', title='Catat Meter', form=form, pelanggan=pelanggan, meter_awal=meter_awal_bulan_ini)

