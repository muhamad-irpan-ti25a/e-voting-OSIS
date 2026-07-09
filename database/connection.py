import os
import mysql.connector
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def get_db_connection():
    """Fungsi koneksi murni menggunakan Environment Variables"""
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "evoting_osis")
    
    config = {
        "host": db_host,
        "user": db_user,
        "password": db_password,
        "database": db_name,
        "port": db_port,
    }

    # Aktifkan SSL jika terhubung ke cloud Aiven
    if "aivencloud.com" in db_host:
        config["ssl_disabled"] = False
        config["ssl_verify_cert"] = False

    return mysql.connector.connect(**config)

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
