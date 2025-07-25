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