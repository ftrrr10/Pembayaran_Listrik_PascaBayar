from app import create_app

# Membuat aplikasi menggunakan factory
app = create_app()

if __name__ == '__main__':
    # Menjalankan aplikasi dalam mode debug
    app.run(debug=True)
