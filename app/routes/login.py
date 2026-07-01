from flask import Blueprint
from app.services.auth_services import login_user
from flask import request
from flask import jsonify


# Se crea el blueprint con nombre 'public', módulo actual y prefijo URL opcional
login_bp = Blueprint('login', __name__, url_prefix='/login')   

@login_bp.route('/login')
def login():
    try:
        data = request.get_json()
        nif = data.get("nif")
        password = data.get("password")

        respuesta = login_user(nif, password)
        
        if respuesta.get("success"):
            return jsonify ({"mensaje": "Login correcto", "NIF": nif}), 200
        else:
            return jsonify ({"Error": respuesta.get("Error")}), 401

    except Exception as e:
        print(f"Error en el login: {str(e)}")
        return jsonify({"error": str(e)}), 500