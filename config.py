import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-rahasia-yang-sulit-ditebak'
    
    # --- TAMBAHKAN BARIS INI ---
    # Format: mysql+pymysql://user:password@host/nama_database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/db_listrik_pascabayar'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False