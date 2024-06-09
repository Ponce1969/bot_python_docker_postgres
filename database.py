import psycopg2  # pip install psycopg2
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker



load_dotenv()
db_uri = os.getenv("DB_URI")

Base = declarative_base()

class Chiste(Base):
    __tablename__ = 'chistes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    contenido = Column(String, nullable=False)



def db_connect():
    try:
        connection = psycopg2.connect(db_uri)
        return connection
    except psycopg2.Error as e:
        print(f"Failed to connect to the database. Error: {e}")
        return None
    
    
# Función para crear la tabla de chistes usando SQLAlchemy y cargar los chistes iniciales
def create_and_load_chistes_table(chistes_list):
    try:
        engine = create_engine(db_uri)
        Base.metadata.create_all(engine)
        print("Tabla 'chistes' creada correctamente.")

        # Cargar chistes en la tabla
        Session = sessionmaker(bind=engine)
        session = Session()
        for contenido in chistes_list:
            # Verificar si el chiste ya existe
            existe_chiste = session.query(Chiste).filter_by(contenido=contenido).first()
            # Si el chiste no existe, agregarlo
            if not existe_chiste:
                nuevo_chiste = Chiste(contenido=contenido)
                session.add(nuevo_chiste)
        session.commit()
        print("Chistes cargados correctamente.")
    except Exception as e:
        print(f"Error al crear la tabla 'chistes' o cargar los chistes: {e}")
    finally:
        session.close()



chistes_list = [
        "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
        "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
        "¿Cómo se dice pañuelo en japonés? Saka-moko.",
        " ¿Qué es una mujer objeto? Una instancia de una mujer con clase.",
        "¿Por qué los programadores odian la naturaleza? Porque tiene muchos bugs.",
        "¿Cómo se llama un boomerang que no vuelve? Palo.",
        "¿Qué le dice un jardinero a otro jardinero? ¡Qué planta!",
        "¿Qué le menciona una IP a otra? — ¿Qué tramas?.",
        "¿Qué es un terapeuta? – 1024 Gigapeutas.",
        "¿Qué le dice un bit al otro? Nos vemos en el bus.",
        "¿Cuántos programadores hacen falta para cambiar una bombilla? – Ninguno, porque es un problema hardware.",
        "Se abre el telón, aparece un informático y dice: ¡qué habéis tocado que no se cierra el telón!",
        "¿Pero qué haces tirando esos portátiles al río? – ! pero mira como beben los PC,s en el rió!.",
        " Error 0094782: No se detecta ningún teclado pulse una tecla para continuar.",
        "Están 1023 gigabytes en una fiesta, llegan 1048576 más y dicen: ¿Nos hacemos un peta?.",
        "¿Qué le dice un .GIF a un .JPEG? -Anímate viejo.",
        "Los verdaderos programadores programan en binario.",
        "No te despedirán del trabajo, si nunca comentas tu código y además eres el único que sabe cómo funciona.",
        "Dos programadores comentando una noticia del menéame: fallece una persona mientras estudiaba en la biblioteca – Que estaba estudiando? – El API de Windows.",
        "Sólo hay 10 tipos de personas en este bendito mundo, las que entienden binario y las que no.",
        "¿Cuál es la diferencia entre batman y Bill Gates? Que cuando batman luchó contra el pingüino ganó.",
        "Dos programadores java charlando: «la excepción confirma la regla» «pues si hay una excepción, la capturamos».",
        " Para qué quiere un pastor un compilador? pues para tener «OBEJOTAS».",
        "La barriga de un programador es directamente proporcional a la cantidad de información que maneja.",
        " Dios es real, a no ser que lo declares como integer.",
        "Dos programadores dialogando sobre sus relaciones con su pareja: Yo tengo un vínculo muy fuerte con mi mujer. Entonces, tienes un hipervínculo?.",
        "¿Me puede decir la contraseña de wifi de su bar, por favor?, Tómate un agua por lo menos !! , Todo junto?",
        "Mi mujer me dijo que necesitaba más espacio. ¿Y qué hiciste? La regalé un disco duro de 2Tb.",
        "Hola, llamo porque no me funciona el módem de internet. ¿Qué luces tiene encendidas? La del pasillo y la del salón. Vale, ahora mismo le envío a un informático.",
        "¿Cuál es el animal más antiguo? La cebra, porque está en blanco y negro.",
        "Google es como un cuñado: no te deja acabar la frase y ya te está dando sugerencias.",
        "Me pone que mi contraseña es incorrecta, pero no dejo de escribir 'incorrecta' y no me deja entrar.",
        "He introducido lo que he comido hoy en mi nueva aplicación de fitness y acaba de enviar una ambulancia a mi casa.",
        "Cuál es el mejor lugar para esconder un cadáver? En la segunda pagina de Google.",
        "Feliz aniversario de 3 semanas a las 26 pestañas del navegador que tengo abiertas",
        "¿Qué le dice un jardinero a otro? Nos vemos cuando podamos.",
        "La mayor exportación de Australia son los boomerangs. También son la mayor importación.",
        "Intenté organizar un torneo profesional de escondite, pero fue un completo fracaso. Los buenos jugadores son difíciles de encontrar.",
        "El otro día vendí mi aspiradora. Lo único que hacía era acumular polvo.",
        "Tengo un amigo otaku que estaba triste, así que lo animé. ",
        "Van dos fantasmas y se cae el del médium.",
        " Oye, ¿sabes cómo se llaman los habitantes de Nueva York? — Hombre, pues todos no.",
        "Perdone, ¿dónde está la sección de libros sobre el sentido del gusto?— Lo siento, sobre gustos no hay nada escrito.",                                      
        # Añade más chistes según sea necesario
]
    





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