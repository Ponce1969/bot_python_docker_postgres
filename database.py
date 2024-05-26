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

