from flask import Flask, jsonify
import psycopg2
from dotenv import load_dotenv
from flask import request
import hashlib
import qrcode
import io
import base64
from datetime import datetime
import stripe
import os



#load_dotenv()  # Carga las variables del archivo .env
app = Flask(__name__)

# Conexión a tu base de datos Supabase
conn = psycopg2.connect(
    user="postgres.lvorolekxlsnogetekwy",
    password="Marta@023",
    host="aws-0-us-east-2.pooler.supabase.com",
    port="6543",
    dbname="postgres"
)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        nif = data.get("nif")
        password = data.get("password")

        print(f"Datos recibidos: NIF={nif}, Password={password}")
        print("-------------------------------")

        if not nif or not password:
            return jsonify({"error": "NIF y contraseña son obligatorios"}), 400

        cur = conn.cursor()
        cur.execute("SELECT pass FROM authentication WHERE nif = %s", (nif,))
        user = cur.fetchone()
        cur.close()

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



# Endpoint para obtener los datos del hermano
@app.route('/hermano/<nif>', methods=['GET'])
def get_hermano(nif):
    try:
        print("Nif del usuario: ",nif)
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

# Endpoint para obtener los datos de los puesto del hermano
@app.route('/puestos/<nif>', methods=['GET'])
def get_puestos_por_nif(nif):
    cursor = conn.cursor()

    query = """
    SELECT p.anio_salida, p.clase_seccion, p.procesa_como, p.tramo, p.posicion, p.a_pagar
    FROM procesion p
    INNER JOIN hermanos h ON p.hermano_id = h.id
    WHERE h.nif = %s
    """
    cursor.execute(query, (nif,))
    rows = cursor.fetchall()

    puestos = [
        {
            "anio_salida": r[0],
            "clase_seccion": r[1],
            "procesa_como": r[2],
            "tramo": r[3],
            "posicion": r[4],
            "a_pagar": float(r[5])
        }
        for r in rows
    ]

    return jsonify(puestos)

# Endpoint para mostrat los recibos de un hermano por su nif
@app.route('/recibos/<nif>', methods=['GET'])
def get_recibos_por_nif(nif):
    
    cursor = conn.cursor()

    query = """
    SELECT r.fecha_expedicion, r.tipo, r.importe, r.forma_pago, r.estado, r.a_pagar, r.detalle
    FROM recibos r
    INNER JOIN hermanos h ON r.hermano_id = h.id
    WHERE h.nif = %s
    """
    cursor.execute(query, (nif,))
    rows = cursor.fetchall()

    recibos = [
        {
            "fecha_expedicion": r[0].isoformat() if r[0] else None,
            "tipo": r[1],
            "importe": float(r[2]),
            "forma_pago": r[3],
            "estado": r[4],
            "a_pagar": r[5],
            "detalle": r[6]
        }
        for r in rows
    ]

    return jsonify(recibos)

# Endpoint para obtener los eventos de la base de datos
@app.route('/eventos', methods=['GET'])
def get_eventos():
    try:
        cursor = conn.cursor()
        query = """
        SELECT id, nombre, descripcion, fecha, ubicacion
        FROM eventos
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        eventos = [
            {
                "id": row[0],
                "nombre": row[1],
                "descripcion": row[2],
                "fecha": row[3].isoformat() if row[3] else None,
                "ubicacion": row[4]
            }
            for row in rows
        ]

        return jsonify(eventos), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    

# Endpoint para mostrar las asistencias de un hermano a un evento 
@app.route('/asistencias_hermano/<nif>', methods=['GET'])
def get_asistencias_de_hermano(nif):
    try:
        cursor = conn.cursor()
        query = """
            SELECT ea.id, ea.evento_id, ea.hermano_id, ea.fecha_registro, ea.qr_code,
                   e.nombre, e.fecha
            FROM evento_asistencia ea
            JOIN hermanos h ON ea.hermano_id = h.id
            JOIN eventos e ON ea.evento_id = e.id
            WHERE h.nif = %s
        """
        cursor.execute(query, (nif,))
        rows = cursor.fetchall()
        cursor.close()

        asistencias = [
            {
                "id": row[0],
                "evento_id": row[1],
                "hermano_id": row[2],
                "fecha_registro": row[3].isoformat() if row[3] else None,
                "qr_code": row[4],
                "evento_nombre": row[5],
                "evento_fecha": row[6].isoformat() if row[6] else None
            }
            for row in rows
        ]

        return jsonify(asistencias), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/registrar_asistencia', methods=['POST'])
def registrar_asistencia():
    data = request.json
    evento_id = data.get("evento_id")
    nif = data.get("nif")

    cursor = conn.cursor()

    # Obtener ID del hermano por su NIF
    cursor.execute("SELECT id FROM hermanos WHERE nif = %s", (nif,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        return jsonify({"error": "Hermano no encontrado"}), 404

    hermano_id = result[0]

    # Verificar si ya está registrado en ese evento
    cursor.execute("""
        SELECT 1 FROM evento_asistencia 
        WHERE evento_id = %s AND hermano_id = %s
    """, (evento_id, hermano_id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Asistencia ya registrada para este evento"}), 409

    # Verificar si hay plazas disponibles
    cursor.execute("""
        SELECT plazas_disponibles FROM eventos WHERE id = %s
    """, (evento_id,))
    evento = cursor.fetchone()
    if not evento:
        cursor.close()
        return jsonify({"error": "Evento no encontrado"}), 404

    plazas_disponibles = evento[0]
    if plazas_disponibles <= 0:
        cursor.close()
        return jsonify({"error": "No hay plazas disponibles"}), 400

    # Generar contenido para el QR
    qr_text = f"{evento_id}_{hermano_id}_{datetime.utcnow().isoformat()}"

    # Crear imagen QR
    qr = qrcode.make(qr_text)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Guardar la asistencia
    cursor.execute("""
        INSERT INTO evento_asistencia (evento_id, hermano_id, fecha_registro, qr_code)
        VALUES (%s, %s, NOW(), %s)
    """, (evento_id, hermano_id, qr_text))

    # Actualizar plazas disponibles
    cursor.execute("""
        UPDATE eventos SET plazas_disponibles = plazas_disponibles - 1 WHERE id = %s
    """, (evento_id,))

    conn.commit()
    cursor.close()

    return jsonify({
        "mensaje": "Asistencia registrada correctamente",
        "qr_code_text": qr_text,
        "qr_image_b64": qr_image_b64
    }), 201



# Endpoint que recupera las imagenes de la BBDD
@app.route("/imagenes", methods=["GET"])
def obtener_todas_las_imagenes():
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, imagen_base64 FROM imagenes")
    filas = cursor.fetchall()

    imagenes = []
    for fila in filas:
        id, nombre, imagen_blob = fila
        if isinstance(imagen_blob, str):
            imagen_base64 = imagen_blob
        else:
            imagen_base64 = base64.b64encode(imagen_blob).decode("utf-8")

        imagenes.append({
            "id": id,
            "nombre": nombre,
            "imagen_base64": imagen_base64
        })

    cursor.close()
    return jsonify(imagenes)

# Endpoint para recoger los productos de la tienda 
@app.route("/productos", methods=["GET"])
def obtener_productos():
    cursor = conn.cursor()
    # Solo selecciona productos con stock > 0
    cursor.execute("""
        SELECT id, nombre_producto, descripcion, precio, stock 
        FROM tienda 
        WHERE stock > 0
    """)
    productos = cursor.fetchall()
    
    resultado = [
        {
            "id": fila[0],
            "nombre_producto": fila[1],
            "description": fila[2],
            "precio": float(fila[3]),
            "stock": fila[4]
        }
        for fila in productos
    ]

    cursor.close()
    return jsonify(resultado)


# Endpoint para insertar los pedidos
@app.route("/pedidos", methods=["POST"])
def guardar_pedido():
    try:
        data = request.get_json()
        print("Datos recibidos en /pedidos:", data)

        nif = data.get("nif")
        localizador = data.get("localizador")
        direccion_envio = data.get("direccion_envio")
        ciudad_envio = data.get("ciudad_envio")
        cp_envio = data.get("cp_envio")
        estado = data.get("estado", "PENDIENTE")
        total = data.get("total")
        fecha_pedido = datetime.now()

        if total is None:
            return jsonify({"error": "Debe indicarse el total"}), 400

        if not nif and not localizador:
            return jsonify({"error": "Debe enviarse nif o localizador"}), 400

        cursor = conn.cursor()

        #Caso ENVÍO: usuario registrado con nif
        if nif:
            cursorId = conn.cursor()
            cursorId.execute("SELECT id FROM hermanos WHERE nif = %s", (nif,))
            row = cursorId.fetchone()
            cursorId.close()

            if row is None:
                return jsonify({"error": f"No se encontró un usuario con NIF {nif}"}), 404

            hermano_id = row[0]

            cursor.execute("""
                INSERT INTO pedidos (hermano_id, fecha_pedido, direccion_envio, ciudad_envio, cp_envio, estado, total)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (hermano_id, fecha_pedido, direccion_envio, ciudad_envio, cp_envio, estado, total))

        else:
            #Caso RECOGIDA: sin nif, solo localizador
            cursor.execute("""
                INSERT INTO pedidos (fecha_pedido, direccion_envio, ciudad_envio, cp_envio, estado, total, localizador)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (fecha_pedido, direccion_envio, ciudad_envio, cp_envio, estado, total, localizador))

        pedido_id = cursor.fetchone()[0]
        conn.commit()
        conn.commit()

        tarjeta_data = data.get("tarjeta")
        print("Datos de tarjeta recibidos:", tarjeta_data)

        if tarjeta_data:
            numero_completo = tarjeta_data.get("numero")
            ultimos_4 = numero_completo[-4:] if numero_completo else None
            titular = tarjeta_data.get("titular")
            expiracion = tarjeta_data.get("expiracion")

            print(f"Número completo: {numero_completo}")
            print(f"Últimos 4: {ultimos_4}")
            print(f"Titular: {titular}")
            print(f"Expiración: {expiracion}")

            if numero_completo and titular and expiracion:
                cursor.execute("""
                    INSERT INTO tarjetas (pedido_id, numero_tarjeta, titular, expiracion)
                    VALUES (%s, %s, %s, %s)
                """, (pedido_id, ultimos_4, titular, expiracion))
                conn.commit()
                print("Tarjeta insertada correctamente")
            else:
                print("Faltan datos necesarios para insertar tarjeta")
        else:
            print("No se recibió el campo 'tarjeta'")


        print("id pedido:", pedido_id)
        return jsonify({"pedido_id": pedido_id, "localizador": localizador}), 201

    except Exception as e:
        print("Error en /pedidos:", str(e))
        conn.rollback()
        return jsonify({"error": str(e)}), 500


# Endopoint para insertar los detalles del pedido
@app.route("/pedido_detalle", methods=["POST"])
def guardar_pedido_detalle():
    try:
        data = request.get_json()
        print("Datos recibidos en /pedido_detalle:", data)

        pedido_id = data.get("pedido_id")
        producto_id = data.get("producto_id")
        cantidad = data.get("cantidad")
        precio_unitario = data.get("precio_unitario")

        if not all([pedido_id, producto_id, cantidad, precio_unitario]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        cursor = conn.cursor()

        # Verificar stock antes de insertar
        cursor.execute("SELECT stock FROM tienda WHERE id = %s", (producto_id,))
        stock_actual = cursor.fetchone()
        if not stock_actual:
            cursor.close()
            return jsonify({"error": "Producto no encontrado"}), 404

        if stock_actual[0] < cantidad:
            cursor.close()
            return jsonify({"error": "Stock insuficiente"}), 400

        # Insertar detalle del pedido
        cursor.execute("""
            INSERT INTO pedido_detalle (pedido_id, producto_id, cantidad, precio_unitario)
            VALUES (%s, %s, %s, %s)
        """, (pedido_id, producto_id, cantidad, precio_unitario))

        # Actualizar stock en tienda
        cursor.execute("""
            UPDATE tienda
            SET stock = stock - %s
            WHERE id = %s
        """, (cantidad, producto_id))

        conn.commit()
        cursor.close()

        return "", 204

    except Exception as e:
        print("Error en /pedido_detalle:", str(e))
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/historial/<nif>", methods=["GET"])
def obtener_historial(nif):
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.fecha_pedido, p.estado, p.total,
                   p.direccion_envio, p.ciudad_envio, p.cp_envio,
                   t.numero_tarjeta, t.titular, t.expiracion
            FROM pedidos p
            LEFT JOIN hermanos h ON p.hermano_id = h.id
            LEFT JOIN tarjetas t ON t.pedido_id = p.id
            WHERE h.nif = %s
            ORDER BY p.fecha_pedido DESC
        """, (nif,))

        rows = cursor.fetchall()
        cursor.close()

        pedidos = []
        for row in rows:
            pedidos.append({
                "id": row[0],
                "fecha_pedido": row[1].strftime('%Y-%m-%d %H:%M'),
                "estado": row[2],
                "total": row[3],
                "tipo": "Recogida" if not row[4] and not row[5] else "Envío",
                "direccion": row[4],
                "ciudad": row[5],
                "cp": row[6],
                "tarjeta": {
                    "numero": row[7],
                    "titular": row[8],
                    "expiracion": row[9]
                } if row[7] else None
            })

        return jsonify(pedidos), 200

    except Exception as e:
        print("Error en /historial:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/subir_imagen', methods=['POST'])
def subir_imagen():
    data = request.get_json()
    nombre = data.get("nombre")
    imagen_base64 = data.get("imagen_base64")

    if not nombre or not imagen_base64:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO imagenes (nombre, imagen_base64) VALUES (%s, %s)",
            (nombre, imagen_base64)
        )
        conn.commit()
        cur.close()
        return '', 204
    except Exception as e:
        conn.rollback()
        print("Error al subir imagen:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/pedidos/pendientes", methods=["GET"])
def pedidos_pendientes():
    try:
        cur = conn.cursor()

        # LEFT JOIN con hermanos
        cur.execute("""
            SELECT 
                p.id,
                p.hermano_id,
                h.nombre AS hermano_nombre,
                h.nif AS hermano_nif,
                p.localizador,
                p.fecha_pedido,
                p.direccion_envio,
                p.ciudad_envio,
                p.cp_envio,
                p.estado,
                p.total
            FROM pedidos p
            LEFT JOIN hermanos h ON p.hermano_id = h.id
            WHERE LOWER(p.estado) = 'pendiente'
            ORDER BY p.fecha_pedido DESC
        """)

        rows = cur.fetchall()
        cur.close()

        pedidos = []
        for row in rows:
            (
                id, hermano_id, hermano_nombre, hermano_nif,
                localizador, fecha_pedido, direccion, ciudad, cp,
                estado, total
            ) = row

            # Determinar nombre
            if hermano_id:
                nombre = f"{hermano_nombre} ({hermano_nif})"
            else:
                nombre = localizador

            # Determinar tipo
            tipo = "recogida" if not direccion and not ciudad and not cp else "envio"

            pedidos.append({
                "id": id,
                "nombre": nombre,
                "fecha_pedido": fecha_pedido.strftime("%Y-%m-%d %H:%M:%S"),
                "direccion_envio": direccion,
                "ciudad_envio": ciudad,
                "cp_envio": cp,
                "estado": estado,
                "total": total,
                "tipo": tipo
            })
            print(f"Pedido ID {id} → direccion: {direccion}, ciudad: {ciudad}, cp: {cp}, tipo: {tipo}")

        return jsonify(pedidos), 200

    except Exception as e:
        print("Error en pedidos pendientes:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/pedidos/<int:pedido_id>/estado", methods=["PUT"])
def actualizar_estado_pedido(pedido_id):
    try:
        data = request.json
        nuevo_estado = data.get("estado")

        cur = conn.cursor()
        cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, pedido_id))
        conn.commit()
        cur.close()

        return jsonify({"message": "Estado actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
from flask import request, jsonify
import urllib.parse

@app.route("/evento/verificar_qr", methods=["POST"])
def verificar_qr():
    data = request.get_json()
    if not data or "qr_code" not in data:
        return jsonify({"error": "Falta el campo qr_code"}), 400

    qr_code = data["qr_code"]
    print(f"🔍 Recibido QR: {qr_code}")  # Para debug

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT e.id, e.evento_id, e.hermano_id, e.fecha_registro, e.qr_code,
                   ev.nombre, ev.fecha
            FROM evento_asistencia e
            JOIN eventos ev ON e.evento_id = ev.id
            WHERE e.qr_code = %s
        """, (qr_code,))  # ← Usa "=" para coincidencia exacta

        row = cur.fetchone()
        cur.close()

        if row:
            resultado = {
                "id": row[0],
                "evento_id": row[1],
                "hermano_id": row[2],
                "fecha_registro": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "qr_code": row[4],
                "evento_nombre": row[5],
                "evento_fecha": row[6].strftime("%Y-%m-%d") if row[6] else None
            }
            return jsonify(resultado), 200
        else:
            return jsonify(None), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para el registro de hermanos
@app.route("/hermanos", methods=["POST"])
def insertar_hermano():
    try:
        data = request.get_json()
        print("📨 Datos recibidos para nuevo hermano:", data)

        # Campos requeridos
        required_fields = [
            "nombre", "apellidos", "fecha_nacimiento", "nif",
            "domicilio", "localidad", "codigo_postal", "provincia",
            "telefono", "movil", "email", "forma_pago",
            "cuenta_bancaria", "periodicidad"
        ]

        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        cur = conn.cursor()

        # Obtener el último número de hermano y número real
        cur.execute("SELECT MAX(numero_hermano), MAX(numero_real) FROM hermanos")
        last_nums = cur.fetchone()
        nuevo_numero_hermano = (last_nums[0] or 0) + 1
        nuevo_numero_real = (last_nums[1] or 0) + 1

        # Fecha de alta actual
        from datetime import datetime
        fecha_alta = datetime.now().strftime("%Y-%m-%d")

        cur.execute("""
            INSERT INTO hermanos (
                numero_hermano, numero_real, nombre, apellidos,
                fecha_alta, fecha_nacimiento, nif, domicilio,
                localidad, codigo_postal, provincia, telefono,
                movil, email, forma_pago, cuenta_bancaria, periodicidad
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            nuevo_numero_hermano,
            nuevo_numero_real,
            data["nombre"],
            data["apellidos"],
            fecha_alta,
            data["fecha_nacimiento"],
            data["nif"],
            data["domicilio"],
            data["localidad"],
            data["codigo_postal"],
            data["provincia"],
            data["telefono"],
            data["movil"],
            data["email"],
            data["forma_pago"],
            data["cuenta_bancaria"],
            data["periodicidad"]
        ))

        conn.commit()
        cur.close()

        return "", 204

    except Exception as e:
        print("❌ Error al insertar hermano:", str(e))
        conn.rollback()
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run()