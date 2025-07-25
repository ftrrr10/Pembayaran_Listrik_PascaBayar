from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
import datetime
from .models import Pelanggan, Penggunaan, Tarif, Tagihan
from sqlalchemy import or_
from .forms import FormPencatatanMeter
from . import db

# Membuat blueprint baru untuk area petugas
petugas_bp = Blueprint('petugas', __name__, url_prefix='/petugas')

# "Penjaga" untuk memastikan hanya petugas yang bisa akses
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
    Halaman utama untuk petugas dengan statistik.
    """
    # Logika untuk menghitung statistik
    sekarang = datetime.datetime.now()
    bulan_ini = sekarang.month
    tahun_ini = sekarang.year

    total_pelanggan = Pelanggan.query.count()
    
    pelanggan_tercatat_bulan_ini = Penggunaan.query.filter_by(
        bulan=bulan_ini, 
        tahun=tahun_ini
    ).count()

    sisa_pelanggan = total_pelanggan - pelanggan_tercatat_bulan_ini

    return render_template('petugas/dashboard.html', 
                           total_pelanggan=total_pelanggan,
                           tercatat=pelanggan_tercatat_bulan_ini,
                           sisa=sisa_pelanggan)

@petugas_bp.route('/pencatatan')
@login_required
@petugas_required
def pencatatan_meter():
    """
    Halaman utama untuk pencatatan meter dengan fitur pencarian.
    """
    # Ambil kata kunci pencarian dari URL (query parameter)
    query = request.args.get('q', '')
    
    # Query dasar untuk mengambil semua pelanggan
    pelanggan_query = Pelanggan.query

    # Jika ada kata kunci pencarian, filter datanya
    if query:
        search_term = f"%{query}%"
        pelanggan_query = pelanggan_query.filter(
            or_(
                Pelanggan.nama_pelanggan.like(search_term),
                Pelanggan.nomor_meter.like(search_term),
                Pelanggan.no_telepon.like(search_term)
            )
        )
    
    daftar_pelanggan = pelanggan_query.order_by(Pelanggan.nama_pelanggan).all()

    # Logika untuk mengecek status pencatatan bulan ini
    sekarang = datetime.datetime.now()
    bulan_ini = sekarang.month
    tahun_ini = sekarang.year
    
    # Ambil ID semua pelanggan yang sudah dicatat bulan ini
    id_tercatat = [p.pelanggan_id for p in Penggunaan.query.filter_by(bulan=bulan_ini, tahun=tahun_ini).all()]

    return render_template('petugas/pencatatan_meter.html', 
                           daftar_pelanggan=daftar_pelanggan,
                           id_tercatat=id_tercatat,
                           query=query)

@petugas_bp.route('/data-pelanggan')
@login_required
@petugas_required
def data_pelanggan():
    """
    Halaman untuk melihat daftar semua pelanggan (read-only).
    """
    query = request.args.get('q', '')
    pelanggan_query = Pelanggan.query
    if query:
        search_term = f"%{query}%"
        pelanggan_query = pelanggan_query.filter(
            or_(
                Pelanggan.nama_pelanggan.like(search_term),
                Pelanggan.nomor_meter.like(search_term),
                Pelanggan.no_telepon.like(search_term)
            )
        )
    daftar_pelanggan = pelanggan_query.order_by(Pelanggan.nama_pelanggan).all()
    return render_template('petugas/data_pelanggan.html', 
                           daftar_pelanggan=daftar_pelanggan,
                           query=query)

@petugas_bp.route('/data-penggunaan')
@login_required
@petugas_required
def data_penggunaan():
    """
    Halaman untuk melihat riwayat penggunaan per pelanggan.
    """
    query = request.args.get('q', '')
    daftar_penggunaan = []
    if query:
        # Cari pelanggan dulu
        search_term = f"%{query}%"
        pelanggan = Pelanggan.query.filter(
            or_(
                Pelanggan.nama_pelanggan.like(search_term),
                Pelanggan.nomor_meter.like(search_term)
            )
        ).first()
        
        if pelanggan:
            # Jika pelanggan ditemukan, ambil riwayat penggunaannya
            daftar_penggunaan = Penggunaan.query.filter_by(pelanggan_id=pelanggan.id).order_by(Penggunaan.tahun.desc(), Penggunaan.bulan.desc()).all()

    return render_template('petugas/data_penggunaan.html',
                           daftar_penggunaan=daftar_penggunaan,
                           query=query)

@petugas_bp.route('/lihat-tarif')
@login_required
@petugas_required
def lihat_tarif():
    """
    Halaman untuk melihat daftar tarif listrik yang berlaku.
    """
    daftar_tarif = Tarif.query.order_by(Tarif.daya).all()
    return render_template('petugas/lihat_tarif.html',
                           daftar_tarif=daftar_tarif)

@petugas_bp.route('/catat-meter/<int:pelanggan_id>', methods=['GET', 'POST'])
@login_required
@petugas_required
def catat_meter(pelanggan_id):
    pelanggan = Pelanggan.query.get_or_404(pelanggan_id)
    form = FormPencatatanMeter()

    sekarang = datetime.datetime.now()
    bulan_ini = sekarang.month
    tahun_ini = sekarang.year
    
    nama_bulan_id = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    periode_pencatatan = f"{nama_bulan_id[bulan_ini]} {tahun_ini}"

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

    # --- LOGIKA BARU YANG SUDAH DIPERBAIKI ---
    if form.validate_on_submit():
        meter_akhir = form.meter_akhir.data
        
        # 1. Lakukan pengecekan custom SEKARANG
        if meter_akhir < meter_awal_bulan_ini:
            # 2. Jika gagal, tambahkan pesan error secara manual ke dalam form
            form.meter_akhir.errors.append('Angka meteran akhir tidak boleh lebih kecil dari meteran awal.')
        else:
            # 3. Jika semua pengecekan berhasil, LANJUTKAN PROSES PENYIMPANAN
            penggunaan_baru = Penggunaan(
                pelanggan_id=pelanggan.id,
                bulan=bulan_ini,
                tahun=tahun_ini,
                meter_awal=meter_awal_bulan_ini,
                meter_akhir=meter_akhir
            )
            db.session.add(penggunaan_baru)
            
            jumlah_meter = meter_akhir - meter_awal_bulan_ini
            total_bayar = jumlah_meter * pelanggan.tarif.tarif_per_kwh
            
            tagihan_baru = Tagihan(
                penggunaan=penggunaan_baru,
                jumlah_meter=jumlah_meter,
                total_bayar=total_bayar,
                tanggal_tagihan=sekarang.date()
            )
            db.session.add(tagihan_baru)
            db.session.commit()
            
            flash(f'Tagihan untuk {pelanggan.nama_pelanggan} berhasil dibuat!', 'success')
            return redirect(url_for('petugas.pencatatan_meter'))

    # Halaman akan dirender ulang di sini jika validasi gagal (baik validasi dasar maupun custom)
    # Karena template sudah bisa menampilkan error, pesan akan muncul.
    return render_template('petugas/catat_meter.html', 
                           title='Catat Meter', 
                           form=form, 
                           pelanggan=pelanggan, 
                           meter_awal=meter_awal_bulan_ini,
                           periode=periode_pencatatan)



