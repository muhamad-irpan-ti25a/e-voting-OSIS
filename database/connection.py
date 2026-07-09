import os
import mysql.connector
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Instansiasi untuk sistem tracking Flask-Migrate
db = SQLAlchemy()
migrate = Migrate()

def get_db_connection():
    """Fungsi koneksi raw query bawaan kodemu (dipertahankan 100%)"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),         
        password=os.getenv("DB_PASSWORD", ""),         
        database=os.getenv("DB_NAME", "evoting_osis")
    )

def catat_log(aktor, tipe_aksi, deskripsi):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO audit_logs (aktor, tipe_aksi, deskripsi) VALUES (%s, %s, %s)"
        cursor.execute(query, (aktor, tipe_aksi, deskripsi))
        conn.commit()
    except Exception as e:
        print(f"!!! GAGAL MENCATAT LOG: {e} !!!")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()