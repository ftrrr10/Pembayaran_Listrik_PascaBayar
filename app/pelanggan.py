from flask import Blueprint, render_template, abort, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from .models import Tagihan, Pelanggan, Users, Roles, PendaftaranPending, Penggunaan, Tarif
from .forms import FormPendaftaran, RegistrasiPelangganForm, EditProfilForm, GantiPasswordForm
import datetime
from . import db
import secrets
import json
from sqlalchemy import func, extract

# Membuat blueprint baru untuk area pelanggan
pelanggan_bp = Blueprint('pelanggan', __name__, url_prefix='/pelanggan')

# "Penjaga" untuk memastikan hanya pelanggan yang bisa akses
def pelanggan_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.nama_role != 'pelanggan':
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@pelanggan_bp.route('/dashboard')
@login_required
@pelanggan_required
def dashboard():
    """
    Halaman utama untuk pelanggan dengan statistik dan grafik dinamis.
    """
    pelanggan = current_user.pelanggan
    if not pelanggan:
        return "Akun Anda belum terhubung dengan data pelanggan. Hubungi administrator."

    # Ambil tagihan terakhir
    tagihan_terakhir = Tagihan.query.join(Penggunaan).filter(
        Penggunaan.pelanggan_id == pelanggan.id
    ).order_by(Penggunaan.tahun.desc(), Penggunaan.bulan.desc()).first()

    # Ambil 6 penggunaan terakhir untuk menghitung rata-rata
    penggunaan_6_bulan = Penggunaan.query.filter_by(pelanggan_id=pelanggan.id).order_by(
        Penggunaan.tahun.desc(), Penggunaan.bulan.desc()
    ).limit(6).all()
    
    total_pemakaian = 0
    if penggunaan_6_bulan:
        for p in penggunaan_6_bulan:
            total_pemakaian += (p.meter_akhir - p.meter_awal)
        rata_rata_penggunaan = total_pemakaian / len(penggunaan_6_bulan)
    else:
        rata_rata_penggunaan = 0

    # Logika untuk data grafik (12 bulan terakhir)
    chart_labels = []
    chart_values = []
    sekarang = datetime.datetime.now()

    for i in range(11, -1, -1):
        target_month = sekarang.month - i
        target_year = sekarang.year
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        nama_bulan_id = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        chart_labels.append(f"{nama_bulan_id[target_month]} {target_year}")

        penggunaan_bulan_ini = Penggunaan.query.filter_by(
            pelanggan_id=pelanggan.id,
            bulan=target_month,
            tahun=target_year
        ).first()

        if penggunaan_bulan_ini:
            pemakaian = penggunaan_bulan_ini.meter_akhir - penggunaan_bulan_ini.meter_awal
            chart_values.append(pemakaian)
        else:
            chart_values.append(0)

    return render_template('pelanggan/dashboard.html',
                           tagihan_terakhir=tagihan_terakhir,
                           rata_rata_penggunaan=rata_rata_penggunaan,
                           chart_labels=json.dumps(chart_labels),
                           chart_values=json.dumps(chart_values))


@pelanggan_bp.route('/tagihan/<int:tagihan_id>')
@login_required
@pelanggan_required
def tagihan_detail(tagihan_id):
    """
    Menampilkan rincian lengkap dari satu tagihan spesifik.
    """
    tagihan = Tagihan.query.get_or_404(tagihan_id)

    # Keamanan: Pastikan pelanggan hanya bisa melihat tagihannya sendiri
    if tagihan.penggunaan.pelanggan.user_id != current_user.id:
        abort(403)

    return render_template('pelanggan/tagihan_detail.html', tagihan=tagihan)

@pelanggan_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = FormPendaftaran()
    if form.validate_on_submit():
        if PendaftaranPending.query.filter_by(nomor_meter=form.nomor_meter.data).first():
            flash('Nomor meter ini sudah pernah diajukan sebelumnya.', 'danger')
            return redirect(url_for('pelanggan.register'))

        # 2. Hasilkan token unik
        token_unik = secrets.token_hex(16)

        pendaftaran_baru = PendaftaranPending(
            nama_lengkap=form.nama_lengkap.data,
            alamat=form.alamat.data,
            email=form.email.data,
            no_telepon=form.no_telepon.data,
            nomor_meter=form.nomor_meter.data,
            tanggal_daftar=datetime.date.today(),
            token=token_unik # <-- 3. Simpan token
        )
        db.session.add(pendaftaran_baru)
        db.session.commit()

        # 4. Arahkan ke halaman sukses dengan membawa token
        return redirect(url_for('pelanggan.register_sukses', token=token_unik))

    return render_template('pelanggan/register.html', title='Pendaftaran Pelanggan', form=form)

# --- RUTE BARU UNTUK HALAMAN SUKSES ---
@pelanggan_bp.route('/register/sukses/<token>')
def register_sukses(token):
    return render_template('pelanggan/register_sukses.html', title='Pendaftaran Berhasil', token=token)

# --- RUTE BARU UNTUK HALAMAN CEK STATUS ---
@pelanggan_bp.route('/cek-status', methods=['GET', 'POST'])
def cek_status():
    pendaftaran = None
    if request.method == 'POST':
        token = request.form.get('token')
        if token:
            pendaftaran = PendaftaranPending.query.filter_by(token=token).first()
            if not pendaftaran:
                flash('Nomor referensi tidak ditemukan.', 'danger')
        else:
            flash('Silakan masukkan nomor referensi Anda.', 'danger')
    return render_template('pelanggan/cek_status.html', title='Cek Status Pendaftaran', pendaftaran=pendaftaran)

@pelanggan_bp.route('/riwayat-tagihan')
@login_required
@pelanggan_required
def riwayat_tagihan():
    """
    Menampilkan daftar lengkap riwayat tagihan pelanggan dengan paginasi.
    """
    pelanggan = current_user.pelanggan
    page = request.args.get('page', 1, type=int)

    # Query untuk mengambil semua tagihan milik pelanggan ini
    tagihan_query = Tagihan.query.join(Penggunaan).filter(
        Penggunaan.pelanggan_id == pelanggan.id
    ).order_by(Penggunaan.tahun.desc(), Penggunaan.bulan.desc())

    # Lakukan paginasi: 10 item per halaman
    pagination = tagihan_query.paginate(page=page, per_page=10, error_out=False)
    daftar_tagihan = pagination.items

    return render_template('pelanggan/riwayat_tagihan.html',
                           title='Riwayat Tagihan',
                           daftar_tagihan=daftar_tagihan,
                           pagination=pagination)

@pelanggan_bp.route('/profil', methods=['GET', 'POST'])
@login_required
@pelanggan_required
def profil():
    """
    Halaman untuk mengedit profil dan mengganti password.
    """
    profil_form = EditProfilForm(obj=current_user)
    password_form = GantiPasswordForm()

    # Logika untuk form edit profil
    if profil_form.submit_profil.data and profil_form.validate():
        current_user.nama_lengkap = profil_form.nama_lengkap.data
        # Update juga nama di data pelanggan jika ada
        if current_user.pelanggan:
            current_user.pelanggan.nama_lengkap = profil_form.nama_lengkap.data
            current_user.pelanggan.email = profil_form.email.data
            current_user.pelanggan.no_telepon = profil_form.no_telepon.data
        db.session.commit()
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(url_for('pelanggan.profil'))

    # Logika untuk form ganti password
    if password_form.submit_password.data and password_form.validate():
        if not current_user.check_password(password_form.password_lama.data):
            flash('Password lama salah.', 'danger')
        else:
            current_user.set_password(password_form.password_baru.data)
            db.session.commit()
            flash('Password berhasil diganti!', 'success')
            return redirect(url_for('pelanggan.profil'))

    return render_template('pelanggan/profil.html', 
                           title='Profil Saya',
                           profil_form=profil_form,
                           password_form=password_form)


@pelanggan_bp.route('/informasi-tarif')
@login_required
@pelanggan_required
def informasi_tarif():
    """
    Menampilkan daftar tarif listrik yang berlaku.
    """
    daftar_tarif = Tarif.query.order_by(Tarif.daya).all()
    return render_template('pelanggan/informasi_tarif.html',
                           title='Informasi Tarif',
                           daftar_tarif=daftar_tarif)

@pelanggan_bp.route('/bantuan')
@login_required
@pelanggan_required
def bantuan():
    """
    Menampilkan halaman bantuan dan dukungan.
    """
    return render_template('pelanggan/bantuan.html', title='Bantuan & Dukungan')
