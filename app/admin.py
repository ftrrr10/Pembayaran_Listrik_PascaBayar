from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from wtforms.validators import DataRequired, Length
from .models import Tarif, Pelanggan, Users, Roles
from .forms import TarifForm, PelangganForm, UserForm
from . import db

# Inisialisasi Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- RUTE DASHBOARD ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html', title='Dashboard Admin')

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
        tarif_baru = Tarif(daya=form.daya.data, tarif_per_kwh=form.tarif_per_kwh.data)
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
    semua_pelanggan = Pelanggan.query.all()
    return render_template('admin/pelanggan_list.html', title='Manajemen Pelanggan', daftar_pelanggan=semua_pelanggan)

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
    role_petugas = Roles.query.filter_by(nama_role='petugas').first_or_404()
    daftar_petugas = Users.query.filter_by(role_id=role_petugas.id).all()
    return render_template('admin/petugas_list.html', title='Manajemen Petugas', daftar_petugas=daftar_petugas)

@admin_bp.route('/petugas/tambah', methods=['GET', 'POST'])
@login_required
def tambah_petugas():
    form = PetugasForm()
    # Password wajib saat menambah
    form.password.validators = [DataRequired(), Length(min=6)]
    if form.validate_on_submit():
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
        petugas.username = form.username.data
        petugas.nama_lengkap = form.nama_lengkap.data
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

