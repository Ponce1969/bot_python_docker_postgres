import psycopg2  # pip install psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_uri = os.getenv("DB_URI")

def db_connect():
    try:
        connection = psycopg2.connect(db_uri)
        return connection
    except psycopg2.Error as e:
        print(f"Failed to connect to the database. Error: {e}")
        return None

def user_exists(conn, discord_ID):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE discordID = %s", (discord_ID,))
        existing_user = cursor.fetchone()
        return existing_user is not None
    except psycopg2.Error as e:
        print(f"Error during user verification: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()

def register(conn, ctx):
    cursor = None
    try:
        if user_exists(conn, str(ctx.author.id)):
            print("Usuario ya registrado en la base de datos.")
        else:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (discordID, userName) VALUES (%s, %s)", (str(ctx.author.id), str(ctx.author)))
            conn.commit()
            print("Usuario registrado correctamente.")
    except psycopg2.Error as e:
        print(f"Error during registration: {e}")
    finally:
        if cursor is not None:
            cursor.close()

def verify_id(conn, discord_ID):
    return user_exists(conn, discord_ID)


# crear tabla para chat de gemini ia
def create_chat_table(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gemini_chats (
                id SERIAL PRIMARY KEY,
                discordID VARCHAR(255),
                user_message TEXT,
                gemini_response TEXT
            )
        """)
        conn.commit()
        print("Tabla de chats de Gemini creada correctamente.")
    except psycopg2.Error as e:
        print(f"Error al crear la tabla de chats de Gemini: {e}")
    finally:
        if cursor is not None:
            cursor.close()
            
            
            
# codigo para insertar mensajes de usuario y respuestas de gemini en la tabla
def save_chat(conn, discord_ID, user_message, gemini_response):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO gemini_chats (discordID, user_message, gemini_response)
            VALUES (%s, %s, %s)
        """, (discord_ID, user_message, gemini_response))
        conn.commit()
        print("Chat guardado correctamente.")
    except psycopg2.Error as e:
        print(f"Error al guardar el chat: {e}")
    finally:
        if cursor is not None:
            cursor.close()
            


# codigo para almacenar intervenciones de usuario ayuda en el chat, para las monedas
def create_interventions_table(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interventions (
                id SERIAL PRIMARY KEY,
                discordID VARCHAR(255),
                interventions INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        print("Tabla de intervenciones de usuario creada correctamente.")
    except psycopg2.Error as e:
        print(f"Error al crear la tabla de intervenciones de usuario: {e}")
    finally:
        if cursor is not None:
            cursor.close()
            
# incrementar el contador de intervenciones de usuario
def increment_interventions(conn, discord_ID):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_interventions (discordID, interventions)
            VALUES (%s, 1)
            ON CONFLICT (discordID) DO UPDATE SET interventions = user_interventions.interventions + 1
        """, (discord_ID,))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al incrementar las intervenciones: {e}")
    finally:
        if cursor is not None:
            cursor.close()

# obtener el numero de intervenciones de usuario
def get_interventions(conn, discord_ID):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT interventions FROM user_interventions WHERE discordID = %s", (discord_ID,))
        interventions = cursor.fetchone()
        return interventions[0] if interventions else 0
    except psycopg2.Error as e:
        print(f"Error al obtener las intervenciones: {e}")
        return 0
    finally:
        if cursor is not None:
            cursor.close()
            
# obtener todas las intervenciones de todos los usuarios
def get_all_interventions(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT discordID, interventions FROM user_interventions ORDER BY interventions DESC")
        return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"Error al obtener todas las intervenciones: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()