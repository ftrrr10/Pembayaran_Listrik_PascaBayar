from . import db 
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# Model untuk tabel 'roles'
class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nama_role = db.Column(db.String(50), unique=True, nullable=False)
    # Relasi ke Users
    users = db.relationship('Users', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.nama_role}>'

# Model untuk tabel 'users'
class Users(UserMixin, db.Model): # Tambahkan UserMixin
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nama_lengkap = db.Column(db.String(150))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    pelanggan = db.relationship('Pelanggan', backref='user', uselist=False, lazy=True)


    # Method untuk mengatur password (mengubah teks biasa menjadi hash)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method untuk memeriksa password (membandingkan hash)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# Model untuk tabel 'tarif'
class Tarif(db.Model):
    __tablename__ = 'tarif'
    id = db.Column(db.Integer, primary_key=True)
    daya = db.Column(db.Integer, nullable=False)
    tarif_per_kwh = db.Column(db.Numeric(10, 2), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)

    pelanggan = db.relationship('Pelanggan', backref='tarif', lazy=True)

    def __repr__(self):
        return f'<Tarif {self.daya} VA>'

# Model untuk tabel 'pelanggan'
class Pelanggan(db.Model):
    __tablename__ = 'pelanggan'
    id = db.Column(db.Integer, primary_key=True)
    nomor_meter = db.Column(db.String(100), unique=True, nullable=False)
    nama_pelanggan = db.Column(db.String(150))
    alamat = db.Column(db.Text)
    email = db.Column(db.String(120), nullable=True)
    no_telepon = db.Column(db.String(20), nullable=True)
    tarif_id = db.Column(db.Integer, db.ForeignKey('tarif.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)


    def __repr__(self):
        return f'<Pelanggan {self.nama_pelanggan}>'
    
class Penggunaan(db.Model):
    __tablename__ = 'penggunaan'
    id = db.Column(db.Integer, primary_key=True)
    pelanggan_id = db.Column(db.Integer, db.ForeignKey('pelanggan.id'), nullable=False)
    bulan = db.Column(db.Integer, nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    meter_awal = db.Column(db.Integer, nullable=False)
    meter_akhir = db.Column(db.Integer, nullable=False)
    # Relasi
    pelanggan = db.relationship('Pelanggan', backref='penggunaan')
    tagihan = db.relationship('Tagihan', backref='penggunaan', uselist=False) # Satu penggunaan punya satu tagihan

class Tagihan(db.Model):
    __tablename__ = 'tagihan'
    id = db.Column(db.Integer, primary_key=True)
    penggunaan_id = db.Column(db.Integer, db.ForeignKey('penggunaan.id'), nullable=False)
    jumlah_meter = db.Column(db.Integer, nullable=False)
    total_bayar = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Belum Bayar')
    tanggal_tagihan = db.Column(db.Date, nullable=False)
    tanggal_bayar = db.Column(db.Date)
