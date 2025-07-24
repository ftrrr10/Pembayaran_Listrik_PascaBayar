from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from .forms import LoginForm
from .models import Users

auth_bp = Blueprint('auth', __name__)

# --- LOGIN UNTUK STAF (ADMIN & PETUGAS) ---
@auth_bp.route('/login/staf', methods=['GET', 'POST'])
def login_staf():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard')) # Arahkan ke dashboard admin jika sudah login

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        # Cek jika user ada, password benar, DAN rolenya adalah admin atau petugas
        if user and user.check_password(form.password.data) and user.role.nama_role in ['admin', 'petugas']:
            login_user(user, remember=form.remember_me.data)
            if user.role.nama_role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else: # Pasti petugas
                return redirect(url_for('petugas.dashboard'))
        else:
            flash('Username atau password staf salah.', 'danger')
            return redirect(url_for('auth.login_staf'))
            
    return render_template('auth/login_staf.html', title='Login Staf', form=form)


# --- LOGIN UNTUK PELANGGAN ---
@auth_bp.route('/login/pelanggan', methods=['GET', 'POST'])
def login_pelanggan():
    if current_user.is_authenticated:
        return redirect(url_for('pelanggan.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        # Cek jika user ada, password benar, DAN rolenya adalah pelanggan
        if user and user.check_password(form.password.data) and user.role.nama_role == 'pelanggan':
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('pelanggan.dashboard'))
        else:
            flash('Username atau password pelanggan salah.', 'danger')
            return redirect(url_for('auth.login_pelanggan'))

    return render_template('auth/login_pelanggan.html', title='Login Pelanggan', form=form)


# --- LOGOUT (Tetap sama untuk semua) ---
@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Anda telah berhasil logout.')
    return redirect(url_for('main.index')) # Arahkan ke halaman utama setelah logout
