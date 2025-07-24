from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from .forms import LoginForm
from .models import Users

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Jika pengguna sudah login, arahkan ke halaman utama
    if current_user.is_authenticated:
        if current_user.role.nama_role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role.nama_role == 'petugas':
            return redirect(url_for('petugas.dashboard')) 
        elif current_user.role.nama_role == 'pelanggan':
            return redirect(url_for('pelanggan.dashboard'))
        else:
            # Fallback jika ada role lain
            return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        # Jika user tidak ada atau password salah
        if user is None or not user.check_password(form.password.data):
            flash('Username atau password salah')
            return redirect(url_for('auth.login'))
        
        # Jika berhasil, loginkan pengguna
        login_user(user, remember=form.remember_me.data)
        if user.role.nama_role == 'admin':
            flash('Login sebagai Admin berhasil!')
            return redirect(url_for('admin.dashboard'))
        elif user.role.nama_role == 'petugas':
            flash('Login sebagai Petugas berhasil!')
            return redirect(url_for('petugas.dashboard')) 
        elif user.role.nama_role == 'pelanggan':
            flash(f'Selamat datang, {user.nama_lengkap}!')
            return redirect(url_for('pelanggan.dashboard'))
        else:
            return redirect(url_for('main.index'))
            
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('admin.dashboard'))
