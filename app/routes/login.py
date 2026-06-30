from flask import Blueprint
from app.database import get_connection
from flask import request
from flask import Flask, jsonify
import hashlib


# Se crea el blueprint con nombre 'public', módulo actual y prefijo URL opcional
login_bp = Blueprint('login', __name__, url_prefix='/login')   

@login_bp.route('/index')
def login():
    try:
        data = request.get_json()
        nif = data.get("nif")
        password = data.get("password")
        conn = get_connection()


        print(f"Datos recibidos: NIF={nif}, Password={password}")
        print("-------------------------------")

        if not nif or not password:
            return jsonify({"error": "NIF y contraseña son obligatorios"}), 400

        cur = conn.cursor()
        cur.execute("SELECT pass FROM authentication WHERE nif = %s", (nif,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        hashed_pass = user[0].strip()

        # Calcular el hash MD5 de la contraseña recibida
        password_md5 = hashlib.md5(password.encode()).hexdigest()

        print(f"Contraseña recibida MD5: {password_md5}")
        print(f"Contraseña en BBDD     : {hashed_pass}")

        if password_md5 == hashed_pass.strip():
            print(f"Login exitoso para NIF: {nif}")
            return jsonify({"mensaje": "Login correcto", "NIF": nif})
        else:
            print("Contraseña incorrecta")
            return jsonify({"error": "Contraseña incorrecta"}), 401

    except Exception as e:
        conn.rollback()
        print(f"Error en el login: {str(e)}")
        return jsonify({"error": str(e)}), 500