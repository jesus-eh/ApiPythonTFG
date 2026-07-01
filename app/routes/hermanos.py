from flask import Blueprint
from app.database import get_connection
from flask import request
from flask import Flask, jsonify


hermanos_bp = Blueprint('hermanos', __name__, url_prefix='/hermanos')   

@hermanos_bp.route('/hermanos')
# Endpoint para obtener los datos del hermano
def hermanos_bp(nif):
    try:
        print("Nif del usuario: ",nif)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                numero_hermano, numero_real, nombre, apellidos, fecha_alta, 
                fecha_nacimiento, nif, domicilio, localidad, codigo_postal, 
                provincia, telefono, movil, email, forma_pago, 
                cuenta_bancaria, periodicidad
            FROM hermanos
            WHERE nif = %s
        """, (nif,))
        row = cur.fetchone()
        cur.close()

        if row:
            keys = [
                "numero_hermano", "numero_real", "nombre", "apellidos", "fecha_alta",
                "fecha_nacimiento", "nif", "domicilio", "localidad", "codigo_postal",
                "provincia", "telefono", "movil", "email", "forma_pago",
                "cuenta_bancaria", "periodicidad"
            ]
            hermano = dict(zip(keys, row))
            return jsonify(hermano), 200
        else:
            return jsonify({"error": "Hermano no encontrado"}), 404

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500