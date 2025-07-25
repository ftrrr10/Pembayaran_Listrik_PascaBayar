from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required
from wtforms.validators import DataRequired, Length
from .models import Tarif, Pelanggan, Users, Roles, Tagihan, PendaftaranPending 
from .forms import TarifForm, PelangganForm, PetugasForm
from . import db
import datetime
from sqlalchemy import func, extract, or_
import json
from calendar import month_name
import csv
import io

# Inisialisasi Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- RUTE DASHBOARD ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Halaman dashboard yang menampilkan statistik kunci dan grafik.
    """
    sekarang = datetime.datetime.now()
    bulan_ini = sekarang.month
    tahun_ini = sekarang.year

    
    total_pendapatan_query = db.session.query(func.sum(Tagihan.total_bayar)).filter(
        Tagihan.status == 'Lunas',
        extract('month', Tagihan.tanggal_bayar) == bulan_ini,
        extract('year', Tagihan.tanggal_bayar) == tahun_ini
    ).scalar()
    total_pendapatan_bulan_ini = total_pendapatan_query or 0
    tagihan_belum_lunas = Tagihan.query.filter_by(status='Belum Bayar').count()
    total_pelanggan = Pelanggan.query.count()
    petugas_role = Roles.query.filter_by(nama_role='petugas').first()
    total_petugas = Users.query.filter_by(role_id=petugas_role.id).count() if petugas_role else 0
    tagihan_terbaru_belum_lunas = Tagihan.query.filter_by(status='Belum Bayar').order_by(Tagihan.tanggal_tagihan.desc()).limit(5).all()

    # --- LOGIKA BARU UNTUK DATA GRAFIK (6 BULAN TERAKHIR) ---
    chart_data = {}
    nama_bulan_id = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

    for i in range(6):
        # Mundur bulan per bulan
        target_date = sekarang - datetime.timedelta(days=i*30)
        bulan = target_date.month
        tahun = target_date.year
        label = f"{nama_bulan_id[bulan]} {tahun}"
        
        # Inisialisasi data untuk bulan ini jika belum ada
        if label not in chart_data:
            chart_data[label] = 0

    # Query untuk mengambil total tagihan per bulan
    six_months_ago = sekarang - datetime.timedelta(days=180)
    monthly_totals = db.session.query(
        extract('year', Tagihan.tanggal_tagihan).label('tahun'),
        extract('month', Tagihan.tanggal_tagihan).label('bulan'),
        func.sum(Tagihan.total_bayar).label('total')
    ).filter(Tagihan.tanggal_tagihan >= six_months_ago).group_by('tahun', 'bulan').all()

    # Isi data dari hasil query
    for row in monthly_totals:
        label = f"{nama_bulan_id[row.bulan]} {row.tahun}"
        if label in chart_data:
            chart_data[label] = float(row.total)

    # Urutkan data dan siapkan untuk dikirim ke template
    chart_labels = json.dumps(list(reversed(chart_data.keys())))
    chart_values = json.dumps(list(reversed(chart_data.values())))
    # -----------------------------------------------------------

    return render_template('admin/dashboard.html', 
                           title='Dashboard Admin',
                           total_pendapatan_bulan_ini=total_pendapatan_bulan_ini,
                           tagihan_belum_lunas=tagihan_belum_lunas,
                           total_pelanggan=total_pelanggan,
                           total_petugas=total_petugas,
                           tagihan_terbaru=tagihan_terbaru_belum_lunas,
                           chart_labels=chart_labels, # <-- Kirim data grafik
                           chart_values=chart_values) # <-- Kirim data grafik

# --- MANAJEMEN TARIF ---
@admin_bp.route('/tarif')
@login_required
def list_tarif():
    semua_tarif = Tarif.query.all()
    return render_template('admin/tarif_list.html', title='Manajemen Tarif', daftar_tarif=semua_tarif)

@admin_bp.route('/tarif/tambah', methods=['GET', 'POST'])
@login_required
def tambah_tarif():
    form = TarifForm()
    if form.validate_on_submit():
        tarif_baru = Tarif(daya=form.daya.data, tarif_per_kwh=form.tarif_per_kwh.data, deskripsi=form.deskripsi.data)
        db.session.add(tarif_baru)
        db.session.commit()
        flash('Tarif baru berhasil ditambahkan!', 'success')
        return redirect(url_for('admin.list_tarif'))
    return render_template('admin/tarif_form.html', title='Tambah Tarif', form=form)

@admin_bp.route('/tarif/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tarif(id):
    tarif = Tarif.query.get_or_404(id)
    form = TarifForm(obj=tarif)
    if form.validate_on_submit():
        tarif.daya = form.daya.data
        tarif.tarif_per_kwh = form.tarif_per_kwh.data
        tarif.deskripsi = form.deskripsi.data
        db.session.commit()
        flash('Data tarif berhasil diperbarui!', 'success')
        return redirect(url_for('admin.list_tarif'))
    return render_template('admin/tarif_form.html', title='Edit Tarif', form=form)

@admin_bp.route('/tarif/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_tarif(id):
    tarif = Tarif.query.get_or_404(id)
    db.session.delete(tarif)
    db.session.commit()
    flash('Data tarif berhasil dihapus.', 'info')
    return redirect(url_for('admin.list_tarif'))

# --- MANAJEMEN PELANGGAN ---
@admin_bp.route('/pelanggan')
@login_required
def list_pelanggan():
    # --- LOGIKA BARU UNTUK PENCARIAN & PAGINASI ---
    
    # 1. Ambil kata kunci pencarian dan nomor halaman dari URL
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)
    
    # 2. Query dasar untuk pelanggan
    pelanggan_query = Pelanggan.query.order_by(Pelanggan.nama_pelanggan)
    
    # 3. Jika ada kata kunci pencarian, filter datanya
    if query:
        search_term = f"%{query}%"
        pelanggan_query = pelanggan_query.filter(
            or_(
                Pelanggan.nama_pelanggan.like(search_term),
                Pelanggan.nomor_meter.like(search_term),
                Pelanggan.no_telepon.like(search_term),
                Pelanggan.email.like(search_term)
            )
        )
        
    # 4. Lakukan paginasi: 10 item per halaman
    pagination = pelanggan_query.paginate(page=page, per_page=10, error_out=False)
    daftar_pelanggan = pagination.items
    
    return render_template('admin/pelanggan_list.html', 
                           title='Manajemen Pelanggan', 
                           daftar_pelanggan=daftar_pelanggan,
                           pagination=pagination,
                           query=query)

@admin_bp.route('/pelanggan/tambah', methods=['GET', 'POST'])
@login_required
def tambah_pelanggan():
    form = PelangganForm()
    form.tarif_id.choices = [(t.id, f"{t.daya} VA") for t in Tarif.query.order_by('daya').all()]
    
    # Membuat field username dan password wajib diisi saat menambah
    form.username.validators.append(DataRequired())
    form.password.validators.append(DataRequired())
    form.password.validators.append(Length(min=6))

    if form.validate_on_submit():
        existing_user = Users.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username sudah digunakan. Silakan pilih username lain.', 'danger')
            return render_template('admin/pelanggan_form.html', title='Tambah Pelanggan', form=form, pelanggan=None)

        role_pelanggan = Roles.query.filter_by(nama_role='pelanggan').first_or_404()
        user_baru = Users(
            username=form.username.data,
            nama_lengkap=form.nama_pelanggan.data,
            role_id=role_pelanggan.id
        )
        user_baru.set_password(form.password.data)
        db.session.add(user_baru)

        pelanggan_baru = Pelanggan(
            nomor_meter=form.nomor_meter.data,
            nama_pelanggan=form.nama_pelanggan.data,
            alamat=form.alamat.data,
            email=form.email.data,
            no_telepon=form.no_telepon.data,
            tarif_id=form.tarif_id.data,
            user=user_baru
        )
        db.session.add(pelanggan_baru)
        db.session.commit()
        
        flash('Pelanggan baru dan akun loginnya berhasil dibuat!', 'success')
        return redirect(url_for('admin.list_pelanggan'))
        
    return render_template('admin/pelanggan_form.html', title='Tambah Pelanggan', form=form, pelanggan=None)

@admin_bp.route('/pelanggan/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_pelanggan(id):
    pelanggan = Pelanggan.query.get_or_404(id)
    form = PelangganForm(obj=pelanggan)
    
    if pelanggan.user:
        form.username.data = pelanggan.user.username

    form.tarif_id.choices = [(t.id, f"{t.daya} VA") for t in Tarif.query.order_by('daya').all()]

    if form.validate_on_submit():
        pelanggan.nomor_meter = form.nomor_meter.data
        pelanggan.nama_pelanggan = form.nama_pelanggan.data
        pelanggan.alamat = form.alamat.data
        pelanggan.email = form.email.data
        pelanggan.no_telepon = form.no_telepon.data
        pelanggan.tarif_id = form.tarif_id.data
        
        if form.password.data:
            if pelanggan.user:
                pelanggan.user.set_password(form.password.data)
            else:
                flash('Tidak bisa mengubah password karena pelanggan ini belum punya akun login.', 'warning')

        db.session.commit()
        flash('Data pelanggan berhasil diperbarui!', 'success')
        return redirect(url_for('admin.list_pelanggan'))
        
    return render_template('admin/pelanggan_form.html', title='Edit Pelanggan', form=form, pelanggan=pelanggan)

@admin_bp.route('/pelanggan/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_pelanggan(id):
    pelanggan = Pelanggan.query.get_or_404(id)
    # Jika pelanggan punya akun user, hapus akunnya juga
    if pelanggan.user:
        db.session.delete(pelanggan.user)
    db.session.delete(pelanggan)
    db.session.commit()
    flash('Data pelanggan dan akun terkait berhasil dihapus.', 'info')
    return redirect(url_for('admin.list_pelanggan'))

# --- MANAJEMEN PETUGAS ---
@admin_bp.route('/petugas')
@login_required
def list_petugas():
    # --- LOGIKA BARU UNTUK PENCARIAN & PAGINASI ---
    
    # 1. Ambil parameter dari URL
    query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)

    # 2. Query dasar untuk mengambil semua staf (admin & petugas)
    admin_role = Roles.query.filter_by(nama_role='admin').first()
    petugas_role = Roles.query.filter_by(nama_role='petugas').first()
    
    if not admin_role or not petugas_role:
        flash('Role "admin" atau "petugas" tidak ditemukan.', 'danger')
        return redirect(url_for('admin.dashboard'))

    role_ids = [admin_role.id, petugas_role.id]
    staf_query = Users.query.filter(Users.role_id.in_(role_ids))

    # 3. Jika ada kata kunci pencarian, filter datanya
    if query:
        search_term = f"%{query}%"
        staf_query = staf_query.filter(
            or_(
                Users.username.like(search_term),
                Users.nama_lengkap.like(search_term)
            )
        )
    
    # 4. Lakukan paginasi: 10 item per halaman
    pagination = staf_query.order_by(Users.id).paginate(page=page, per_page=10, error_out=False)
    daftar_staf = pagination.items
    
    return render_template('admin/petugas_list.html', 
                           title='Manajemen Staf', 
                           daftar_petugas=daftar_staf,
                           pagination=pagination,
                           query=query)

@admin_bp.route('/petugas/tambah', methods=['GET', 'POST'])
@login_required
def tambah_petugas():
    form = PetugasForm()
    # Membuat password wajib diisi saat menambah
    form.password.validators.insert(0, DataRequired(message="Password wajib diisi."))

    if form.validate_on_submit():
        # Cek dulu apakah username sudah ada
        existing_user = Users.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username sudah digunakan. Silakan pilih username lain.', 'danger')
        else:
            role_petugas = Roles.query.filter_by(nama_role='petugas').first_or_404()
            petugas_baru = Users(
                username=form.username.data,
                nama_lengkap=form.nama_lengkap.data,
                role_id=role_petugas.id
            )
            petugas_baru.set_password(form.password.data)
            db.session.add(petugas_baru)
            db.session.commit()
            flash('Petugas baru berhasil ditambahkan!', 'success')
            return redirect(url_for('admin.list_petugas'))
            
    return render_template('admin/petugas_form.html', title='Tambah Petugas', form=form)

@admin_bp.route('/petugas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_petugas(id):
    petugas = Users.query.get_or_404(id)
    form = PetugasForm(obj=petugas)

    if form.validate_on_submit():
        # Cek jika username diubah dan sudah ada yang pakai
        if petugas.username != form.username.data and Users.query.filter_by(username=form.username.data).first():
            flash('Username sudah digunakan. Silakan pilih username lain.', 'danger')
        else:
            petugas.username = form.username.data
            petugas.nama_lengkap = form.nama_lengkap.data
            # Hanya update password jika field diisi
            if form.password.data:
                petugas.set_password(form.password.data)
            db.session.commit()
            flash('Data petugas berhasil diperbarui!', 'success')
            return redirect(url_for('admin.list_petugas'))

    return render_template('admin/petugas_form.html', title='Edit Petugas', form=form)


@admin_bp.route('/petugas/hapus/<int:id>', methods=['POST'])
@login_required
def hapus_petugas(id):
    petugas = Users.query.get_or_404(id)
    db.session.delete(petugas)
    db.session.commit()
    flash('Data petugas berhasil dihapus.', 'info')
    return redirect(url_for('admin.list_petugas'))

@admin_bp.route('/tagihan')
@login_required
def list_tagihan():
    # Mengambil semua tagihan dan mengurutkannya dari yang terbaru
    semua_tagihan = Tagihan.query.order_by(Tagihan.tanggal_tagihan.desc()).all()
    return render_template('admin/tagihan_list.html', 
                           title='Manajemen Tagihan', 
                           daftar_tagihan=semua_tagihan)

@admin_bp.route('/tagihan/bayar/<int:id>', methods=['POST'])
@login_required
def bayar_tagihan(id):
    tagihan = Tagihan.query.get_or_404(id)
    if tagihan.status == 'Belum Bayar':
        tagihan.status = 'Lunas'
        tagihan.tanggal_bayar = datetime.date.today()
        db.session.commit()
        flash(f'Tagihan #{tagihan.id} untuk pelanggan {tagihan.penggunaan.pelanggan.nama_pelanggan} telah lunas.', 'success')
    else:
        flash('Tagihan ini sudah lunas atau dibatalkan.', 'info')
    
    return redirect(url_for('admin.list_tagihan'))

# --- MANAJEMEN LAPORAN ---

@admin_bp.route('/laporan', methods=['GET'])
@login_required
def laporan():
    """
    Menampilkan halaman untuk memilih periode laporan.
    """
    return render_template('admin/laporan.html', title='Buat Laporan Tagihan')

@admin_bp.route('/laporan/unduh', methods=['POST'])
@login_required
def unduh_laporan():
    """
    Memproses permintaan unduh laporan dan menghasilkan file CSV.
    """
    try:
        tanggal_awal_str = request.form.get('tanggal_awal')
        tanggal_akhir_str = request.form.get('tanggal_akhir')

        # Konversi string tanggal ke objek date
        tanggal_awal = datetime.datetime.strptime(tanggal_awal_str, '%Y-%m-%d').date()
        tanggal_akhir = datetime.datetime.strptime(tanggal_akhir_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Format tanggal tidak valid. Silakan coba lagi.', 'danger')
        return redirect(url_for('admin.laporan'))

    # Ambil data tagihan dalam rentang tanggal yang dipilih
    daftar_tagihan = Tagihan.query.join(Penggunaan).join(Pelanggan).filter(
        Tagihan.tanggal_tagihan >= tanggal_awal,
        Tagihan.tanggal_tagihan <= tanggal_akhir
    ).order_by(Tagihan.tanggal_tagihan).all()

    if not daftar_tagihan:
        flash('Tidak ada data tagihan ditemukan untuk periode yang dipilih.', 'info')
        return redirect(url_for('admin.laporan'))

    # Proses pembuatan file CSV di memori
    output = io.StringIO()
    writer = csv.writer(output)

    # Tulis header kolom
    writer.writerow(['ID Tagihan', 'Tanggal Tagihan', 'Nama Pelanggan', 'Nomor Meter', 'Periode', 'Total Bayar (Rp)', 'Status', 'Tanggal Bayar'])

    # Tulis baris data
    for tagihan in daftar_tagihan:
        writer.writerow([
            tagihan.id,
            tagihan.tanggal_tagihan.strftime('%Y-%m-%d'),
            tagihan.penggunaan.pelanggan.nama_pelanggan,
            tagihan.penggunaan.pelanggan.nomor_meter,
            f"{tagihan.penggunaan.bulan}/{tagihan.penggunaan.tahun}",
            tagihan.total_bayar,
            tagihan.status,
            tagihan.tanggal_bayar.strftime('%Y-%m-%d') if tagihan.tanggal_bayar else ''
        ])

    output.seek(0)
    
    # Buat nama file yang dinamis
    nama_file = f"laporan_tagihan_{tanggal_awal_str}_sd_{tanggal_akhir_str}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={nama_file}"}
    )

@admin_bp.route('/verifikasi')
@login_required
def verifikasi_pendaftaran():
    daftar_pending = PendaftaranPending.query.filter_by(status='Pending').order_by(PendaftaranPending.tanggal_daftar).all()
    return render_template('admin/verifikasi_pendaftaran.html', 
                           title='Verifikasi Pendaftaran',
                           daftar_pending=daftar_pending)

@admin_bp.route('/verifikasi/setujui/<int:id>', methods=['POST'])
@login_required
def setujui_pendaftaran(id):
    pendaftaran = PendaftaranPending.query.get_or_404(id)
    
    # Buat username & password sementara
    username = pendaftaran.nama_lengkap.split()[0].lower() + pendaftaran.nomor_meter[-4:]
    password_sementara = 'wattbill123'
    
    # Cek jika username sudah ada, tambahkan angka acak
    if Users.query.filter_by(username=username).first():
        import random
        username = username + str(random.randint(10,99))

    # --- SIMPAN DETAIL LOGIN KE PENDAFTARAN PENDING ---
    pendaftaran.generated_username = username
    pendaftaran.generated_password = password_sementara
    # -------------------------------------------------
    
    # Buat user dan pelanggan baru
    role_pelanggan = Roles.query.filter_by(nama_role='pelanggan').first_or_404()
    user_baru = Users(username=username, nama_lengkap=pendaftaran.nama_lengkap, role_id=role_pelanggan.id)
    user_baru.set_password(password_sementara)
    
    tarif_default = Tarif.query.first()
    if not tarif_default:
        flash('Tidak ada data tarif di sistem. Tambahkan tarif terlebih dahulu.', 'danger')
        return redirect(url_for('admin.verifikasi_pendaftaran'))

    pelanggan_baru = Pelanggan(
        nomor_meter=pendaftaran.nomor_meter,
        nama_pelanggan=pendaftaran.nama_lengkap,
        alamat=pendaftaran.alamat,
        email=pendaftaran.email,
        no_telepon=pendaftaran.no_telepon,
        tarif_id=tarif_default.id,
        user=user_baru
    )
    
    pendaftaran.status = 'Disetujui'
    db.session.add(user_baru)
    db.session.add(pelanggan_baru)
    db.session.commit()
    
    flash(f'Pendaftaran untuk {pendaftaran.nama_lengkap} berhasil disetujui.', 'success')
    return redirect(url_for('admin.verifikasi_pendaftaran'))

@admin_bp.route('/verifikasi/tolak/<int:id>', methods=['POST'])
@login_required
def tolak_pendaftaran(id):
    pendaftaran = PendaftaranPending.query.get_or_404(id)
    pendaftaran.status = 'Ditolak'
    db.session.commit()
    flash(f'Pendaftaran untuk {pendaftaran.nama_lengkap} telah ditolak.', 'info')
    return redirect(url_for('admin.verifikasi_pendaftaran'))

