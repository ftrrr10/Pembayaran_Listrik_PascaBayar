from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, DecimalField, TextAreaField, SelectField
from wtforms.validators import DataRequired, NumberRange, Optional, Length, EqualTo, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ingat Saya')
    submit = SubmitField('Login')

class TarifForm(FlaskForm):
    """Form untuk menambah/mengedit data tarif."""
    daya = IntegerField('Daya (VA)', 
                        validators=[DataRequired(message="Daya harus diisi."), 
                                    NumberRange(min=1, message="Daya harus angka positif.")])
    tarif_per_kwh = DecimalField('Tarif per kWh (Rp)', 
                                 validators=[DataRequired(message="Tarif harus diisi.")],
                                 places=2)
    deskripsi = TextAreaField('Deskripsi', validators=[Optional()])
    submit = SubmitField('Simpan')

class PelangganForm(FlaskForm):
    """Form untuk menambah/mengedit data pelanggan."""
    nomor_meter = StringField('Nomor Meter', validators=[DataRequired()])
    nama_pelanggan = StringField('Nama Pelanggan', validators=[DataRequired()])
    alamat = TextAreaField('Alamat', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email(message="Format email tidak valid.")])
    no_telepon = StringField('No. Telepon', validators=[Optional()])
    tarif_id = SelectField('Jenis Tarif', coerce=int, validators=[DataRequired()])
    username = StringField('Username untuk Login', validators=[Optional(), Length(min=4)])
    password = PasswordField('Password', validators=[
        Optional(), 
        EqualTo('confirm_password', message='Password harus sama.')
    ])
    confirm_password = PasswordField('Konfirmasi Password')
    
    submit = SubmitField('Simpan Data Pelanggan')

class PetugasForm(FlaskForm):
    """Form untuk menambah/mengedit data petugas."""
    username = StringField('Username', 
                           validators=[DataRequired(message="Username wajib diisi."), 
                                       Length(min=4, message="Username minimal 4 karakter.")])
    nama_lengkap = StringField('Nama Lengkap', 
                               validators=[DataRequired(message="Nama lengkap wajib diisi.")])
    
    # Password bersifat wajib saat membuat, opsional saat mengedit
    password = PasswordField('Password', 
                             validators=[Optional(), 
                                         Length(min=6, message="Password minimal 6 karakter."),
                                         EqualTo('confirm_password', message='Password harus sama.')])
    confirm_password = PasswordField('Konfirmasi Password')
    submit = SubmitField('Simpan')

class FormPencatatanMeter(FlaskForm):
    """Form untuk petugas mencatat meteran akhir pelanggan."""
    meter_akhir = IntegerField('Angka Meteran Terakhir', 
                               validators=[DataRequired(), 
                                           NumberRange(min=0, message="Angka meteran tidak boleh negatif.")])
    submit = SubmitField('Simpan & Buat Tagihan')

class RegistrasiPelangganForm(FlaskForm):
    """Form untuk pelanggan mendaftarkan akun login mereka."""
    nomor_meter = StringField('Nomor Meter Anda', 
                              validators=[DataRequired(message="Nomor meter wajib diisi.")])
    username = StringField('Username Baru', 
                           validators=[DataRequired(message="Username wajib diisi."), 
                                       Length(min=4, message="Username minimal 4 karakter.")])
    password = PasswordField('Password Baru', 
                             validators=[DataRequired(message="Password wajib diisi."), 
                                         Length(min=6, message="Password minimal 6 karakter."),
                                         EqualTo('confirm_password', message='Password harus sama.')])
    confirm_password = PasswordField('Konfirmasi Password')
    submit = SubmitField('Daftar Sekarang')

class FormPendaftaran(FlaskForm):
    """Form untuk calon pelanggan mendaftarkan diri."""
    nama_lengkap = StringField('Nama Lengkap Sesuai KTP', validators=[DataRequired()])
    alamat = TextAreaField('Alamat Lengkap Pemasangan', validators=[DataRequired()])
    email = StringField('Email (Opsional)', validators=[Optional(), Email()])
    no_telepon = StringField('No. Telepon Aktif', validators=[DataRequired()])
    nomor_meter = StringField('Nomor Meter (Jika Sudah Ada)', validators=[DataRequired()])
    submit = SubmitField('Ajukan Pendaftaran')

class EditProfilForm(FlaskForm):
    """Form untuk pelanggan mengedit data diri mereka."""
    nama_lengkap = StringField('Nama Lengkap', 
                               validators=[DataRequired(message="Nama lengkap wajib diisi.")])
    email = StringField('Email', 
                        validators=[DataRequired(message="Email wajib diisi."), 
                                    Email(message="Format email tidak valid.")])
    no_telepon = StringField('No. Telepon', 
                             validators=[DataRequired(message="No. telepon wajib diisi.")])
    submit_profil = SubmitField('Simpan Perubahan Profil')


class GantiPasswordForm(FlaskForm):
    """Form untuk pelanggan mengganti password mereka."""
    password_lama = PasswordField('Password Lama', 
                                  validators=[DataRequired(message="Password lama wajib diisi.")])
    password_baru = PasswordField('Password Baru', 
                                  validators=[DataRequired(message="Password baru wajib diisi."), 
                                              Length(min=6, message="Password minimal 6 karakter."),
                                              EqualTo('konfirmasi_password', message='Password baru harus sama.')])
    konfirmasi_password = PasswordField('Konfirmasi Password Baru')
    submit_password = SubmitField('Ganti Password')
