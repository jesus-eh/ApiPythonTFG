import hashlib
from app.database import get_connection


def login_user(nif, password):
    try:
        conn = get_connection()

        print(f"Datos recibidos: NIF={nif}, Password={password}")
        print("-------------------------------")

        if not nif or not password:
            return {"error": "NIF y contraseña son obligatorios"}

        cur = conn.cursor()
        cur.execute("SELECT pass FROM authentication WHERE nif = %s", (nif,))
        user = cur.fetchone()
        cur.close()
        
        if not user:
            return {"error": "Usuario no encontrado"}

        hashed_pass = user[0].strip()

        # Calcular el hash MD5 de la contraseña recibida
        password_md5 = hashlib.md5(password.encode()).hexdigest()
        
        conn.close()

        if password_md5 == hashed_pass:
            return { 
                "success": True,
                "Mensaje": "Contraseña correcta"
                }
        else:
            return {
                "success": False,
                "Error": "Usuario no encontrado"
                }     
        
    except Exception as e:
        conn.close()
        print(f"Error en el login: {str(e)}")
        return {"error": str(e)}
