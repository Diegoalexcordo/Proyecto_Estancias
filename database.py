import sqlite3
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_db_path():
    return os.path.join(os.getenv("LOCALAPPDATA"), "RegistroDolores", "base_datos.db")

DB_PATH = get_db_path()

def conectar():
    return sqlite3.connect(DB_PATH)

def crear_base_datos():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            fecha_insercion TEXT,
            fecha_documento TEXT,
            genero TEXT,
            tipo_trabajo TEXT DEFAULT 'Valoracion'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            ruta TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)
    conn.commit()
    conn.close()

def insertar_cliente(nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo))
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cliente_id

def actualizar_cliente(cliente_id, nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clientes
        SET nombre=?, apellido=?, fecha_insercion=?, fecha_documento=?, genero=?, tipo_trabajo=?
        WHERE id=?
    """, (nombre, apellido, fecha_insercion, fecha_documento, genero, tipo_trabajo, cliente_id))
    conn.commit()
    conn.close()

def insertar_archivo(cliente_id, ruta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO archivos (cliente_id, ruta) VALUES (?, ?)", (cliente_id, ruta))
    conn.commit()
    conn.close()

def borrar_cliente(cliente_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM archivos WHERE cliente_id=?", (cliente_id,))
    cursor.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    conn.commit()
    conn.close()

def borrar_archivo_por_ruta(ruta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM archivos WHERE ruta = ?", (ruta,))
    conn.commit()
    conn.close()

def obtener_clientes_con_archivos(tipo="Todos"):
    conn = conectar()
    cursor = conn.cursor()
    consulta = """
        SELECT c.id, c.nombre, c.apellido, c.fecha_insercion, c.fecha_documento, c.genero, c.tipo_trabajo, a.ruta
        FROM clientes c
        LEFT JOIN archivos a ON c.id = a.cliente_id
    """
    if tipo != "Todos":
        consulta += " WHERE c.tipo_trabajo = ?"
        cursor.execute(consulta, (tipo,))
    else:
        cursor.execute(consulta)
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def buscar_clientes(nombre="", apellido="", fecha_insercion="", fecha_documento="", tipo="Todos"):
    conn = conectar()
    cursor = conn.cursor()
    consulta = """
        SELECT c.id, c.nombre, c.apellido, c.fecha_insercion, c.fecha_documento, c.genero, c.tipo_trabajo, a.ruta
        FROM clientes c
        LEFT JOIN archivos a ON c.id = a.cliente_id
        WHERE c.nombre LIKE ? AND c.apellido LIKE ?
    """
    params = [f"%{nombre}%", f"%{apellido}%"]

    if fecha_insercion and fecha_insercion != "2000-01-01":
        consulta += " AND c.fecha_insercion = ?"
        params.append(fecha_insercion)

    if fecha_documento and fecha_documento != "2000-01-01":
        consulta += " AND c.fecha_documento = ?"
        params.append(fecha_documento)

    if tipo != "Todos":
        consulta += " AND c.tipo_trabajo = ?"
        params.append(tipo)

    cursor.execute(consulta, params)
    resultados = cursor.fetchall()
    conn.close()
    return resultados
