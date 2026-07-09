from werkzeug.security import generate_password_hash

# Membuat hash baru untuk kata sandi: admin123
password_baru = "fathan2626"
hash_hasil = generate_password_hash(password_baru, method='pbkdf2:sha256')

print("=== SALIN KODE HASH DI BAWAH INI ===")
print(hash_hasil)
print("====================================")

