import asyncio
import concurrent.futures
import datetime
import io
import logging
import os
import pathlib
import random as rd
import time
import textwrap

import discord
import psycopg2
import requests
from discord import Embed
from discord.ext.commands import Bot
from dotenv import load_dotenv
from googleapiclient.discovery import build
from PIL import Image
from pytz import timezone
from translate import Translator

import google.generativeai as geneai
from IPython.display import Markdown, display

from database import (create_chat_table, save_chat, create_interventions_table,
                      increment_interventions, get_interventions,
                      get_all_interventions, db_connect, verify_id, register,
                      create_and_load_chistes_table, chistes_list)




# Cargar variables de entorno
load_dotenv()
db_uri = os.getenv('DB_URI')
token = os.getenv('DISCORD_TOKEN')
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
GOOGLE_API_KEY= os.getenv('GOOGLE_API_KEY')
max_history = int(os.getenv('MAX_HISTORY'))

# Inicializar API de YouTube
youtube_api = build('youtube', 'v3', developerKey=youtube_api_key)

# Configurar el registro de eventos
logging.basicConfig(level=logging.INFO)

# Configurar intents y bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Asegúrate de que el bot puede ver los cambios de estado de voz
intents.members = True  # Permite al bot ver los miembros
bot = Bot(command_prefix='>', description="Bot de ayuda", intents=intents, case_insensitive=True)


# ID del servidor de Discord
CHANNEL_ID = 1172339507035639831

# constante para el comando history
MAX_HISTORY = 15


# Conexión a la base de datos
try:
    connection = db_connect()
    if connection:
        print("Conexión a la base de datos establecida correctamente")
        create_chat_table(connection)  # Crear la tabla después de establecer la conexión
    else:
        print("No se pudo conectar a la base de datos")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")

# Evento de inicio del bot
@bot.event
async def on_ready():
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="el blog de Pythonesa"))
        print("Bot iniciado correctamente")
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")

#registrarse en la base de datos
@bot.command(help="Regístrate en la base de datos")
async def register(ctx):
    conn = db_connect()
    try:
        flag = verify_id(conn, str(ctx.author.id))
        if flag:
            await ctx.send("Usted se encuentra registrado en la base de datos")
        else:
            register(conn, ctx.author.id)
            await ctx.send("**Te has registrado correctamente en la base de datos**")
    except psycopg2.Error as e:
        await ctx.send(f"Error de psycopg2: {e}")
    except Exception as e:
        await ctx.send(f"Ocurrió un error: {e}")
    finally:
        conn.close()

# comando ping
@bot.command()
async def ping(ctx):
    response = await ctx.send('pong')
    await asyncio.sleep(8)
    await response.delete()

# comando ayuda , muestra los comandos disponibles
@bot.command()
async def ayuda(ctx):
    ayuda_msg = """
Hola! Soy tu bot de Discord. Aquí están las cosas que puedo hacer:

**1.  Buscar  en YouTube**: Usa `>youtube <nombre de la canción>`.

**2.  Operaciones**: Usa `>operacion <sum|resta|mult|div|resto> <número 1> <número 2>`.

**3.  Saludar**: Usa `>saludo` y te devolveré un saludo!

**4.  Info**: Usa `>info` y te devolveré información y hora del servidor, mas la temperatura del procesador.

**5.  Registrarse**: Usa `>register` y te registraré en la base de datos.

**6.  Traducir**: Usa `>translate <mensaje>` y te devolveré el mensaje traducido al español.

**7.  Abrazo**: Usa `>abrazo` y te enviaré un mensaje de ánimo.

**8.  Invitar**: Usa `>invitar_alcohol <@usuario>` y enviaré una invitación para tomar algo.

**9.  Gemini**: Usa `>gemini <mensaje>` y te responderé con un mensaje generado por IA.

**10. Historial**: Usa `>historial` y te mostraré el historial de conversaciones.

**11. Gracias**: Usa `>gracias <@usuario>` y otorgaré una moneda de oro al usuario más activo.

**12. Ranking**: Usa `>ranking` y te mostraré el ranking de los usuarios más activos.

**13. Chiste**: Usa `>chistes` y te contaré un chiste.

**14. Adivina**: Usa `>adivina` y jugarás al juego de adivinar la palabra.

**15. Al salir del canal de voz**: Te enviaré un mensaje  en el canal de texto.

"""
    response = await ctx.send(ayuda_msg)
    await asyncio.sleep(50)
    await response.delete()


# comando saludo y dar la bienvenida
@bot.command()
async def saludo(ctx, nombre: str = None):
    if nombre:
        response = await ctx.send(f"Hola, {nombre}!! \n Bienvenido al Servidor de Gonzalo Ponce.")
    else:
        response =  await ctx.send("Hola! Por favor, dime tu nombre para saludarte correctamente, asi \n >saludo y tu nombre")
    await asyncio.sleep(15)
    await response.delete()


# comando de operaciones matemáticas
@bot.command()
async def operacion(ctx, operador: str, numero_uno: int, numero_dos: int):
    try:
        if operador == 'sum':
            resultado = numero_uno + numero_dos
        elif operador == 'resta':
            resultado = numero_uno - numero_dos
        elif operador == 'mult':
            resultado = numero_uno * numero_dos
        elif operador == 'div':
            if numero_dos != 0:
                resultado = numero_uno // numero_dos
            else:
                response = await ctx.send("Error: No se puede dividir por cero.")
                await asyncio.sleep(10)
                await response.delete()
                return
        elif operador == 'resto':
            resultado = numero_uno % numero_dos
        else:
            response = await ctx.send("Error: Operador no válido.")
            await asyncio.sleep(11)
            await response.delete()
            return
        await ctx.send(resultado)
    except Exception as e:
        response =  await ctx.send(f"Error en la operación: {e}")
        await asyncio.sleep(10)
        await response.delete()


# comando de información, muestra la hora del servidor y la temperatura del procesador
@bot.command()
async def info(ctx):
    try:
        # Obtener la hora actual en Uruguay
        uruguay_time = datetime.datetime.now(timezone('America/Montevideo'))
        
        # Leer la temperatura del procesador
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp_file:
            cpu_temp = int(temp_file.read()) / 1000  # Convertir de miligrados a grados
        
        # Crear el título del mensaje
        title = "Mensaje Directo" if ctx.guild is None else ctx.guild.name
        
        # Crear la descripción incluyendo la temperatura del procesador
        description = f"Aprendiendo Python y sus librerías\nTemperatura del CPU: {cpu_temp}°C"
        
        # Crear el embed con la información
        embed = discord.Embed(
            title=title,
            description=description,
            timestamp=uruguay_time,
            color=discord.Color.blue()
        )
        
        # Enviar el embed y eliminarlo después de 30 segundos
        response = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await response.delete()
        
    except Exception as e:
        # Manejar excepciones enviando un mensaje de error y eliminándolo después de 10 segundos
        response = await ctx.send(f"Error en la función info: {e}")
        await asyncio.sleep(30)
        await response.delete()



# comando de búsqueda de videos en YouTube
@bot.command()
async def youtube(ctx, *, search):
    try:
        if not search:
            await ctx.send("Debes proporcionar un término de búsqueda. Ejemplo: >youtube tango")
            return

        request = youtube_api.search().list(
            part="snippet",
            maxResults=5,
            q=search,
            type="video"
        )
        response = request.execute()

        if response['items']:
            options = [f"{i + 1}: {item['snippet']['title']}" for i, item in enumerate(response['items']) if item['id']['kind'] == "youtube#video"]

            if not options:
                await ctx.send('No se encontraron videos para tu búsqueda.')
                return

            await ctx.send("Elije un video:\n" + "\n".join(options))
            
            
            def check(m):
                return m.author == ctx.author and m.content.isdigit() and 0 < int(m.content) <= len(options)

            try:
                choice = await bot.wait_for('message', check=check, timeout=30.0)
                selected = int(choice.content) - 1
                video_id = response['items'][selected]['id']['videoId']
                await ctx.send('https://www.youtube.com/watch?v=' + video_id)
                
                
                
            except asyncio.TimeoutError:
                await ctx.send('No se recibió respuesta, cancelando operación.')
                
            
        else:
            await ctx.send('No se encontraron videos para tu búsqueda.')
            
                  
    except Exception as e:
        await ctx.send(f"Ha ocurrido un error al buscar videos: {e}")
    
        

# comando de traducción de mensajes
@bot.command()
async def translate(ctx, *, message):
    try:
        translator = Translator(to_lang="es", from_lang="en")
        translated = translator.translate(message)
        response = await ctx.send(f"Mensaje original (inglés): {message}\nMensaje traducido (español): {translated}")
        await asyncio.sleep(30)
        await response.delete()
        
    except ValueError:
        response = await ctx.send("Error: El mensaje es demasiado largo para ser traducido.")
        await asyncio.sleep(10)
        await response.delete()
        
    except Exception as e:
        response = await ctx.send(f"Error al traducir el mensaje: {e}")
        await asyncio.sleep(10)
        await response.delete()


# comando de ánimo, envía un mensaje de ánimo
async def seleccionar_y_enviar_frase(ctx, destinatario=None):
    frases_motivadoras = [
        "¡Ánimo! Todo saldrá bien.",
        "¡No te rindas! Eres más fuerte de lo que crees.",
        "¡Tú puedes! Eres capaz de superar cualquier obstáculo.",
        "¡Eres increíble! No dejes que nada te detenga.",
        "¡Eres valiente! Afronta tus miedos y sigue adelante.",
        "¡Eres un guerrero! No hay nada que no puedas lograr.",
        "¡Eres un campeón! No dejes que nada te detenga.",
        "¡Eres muy importante para este grupo, ánimo!",
        "¡Un tropiezo no es caída, sigue adelante!",
        "¡Cuando todo parezca en tu contra, recuerda que el avión despega contra el viento!",
        "¡No hay que ir para atrás ni para darse impulso!",
        "¡Si vas a mirar atrás, que sea para ver lo lejos que has llegado!",
        "¡No importa lo lento que vayas, siempre y cuando no te detengas!",
        "¡Saber lo que hay que hacer elimina el miedo!",
        "¡No te preocupes por los fracasos, preocúpate por las oportunidades que pierdes cuando ni siquiera lo intentas!",
        "¡No te rindas, el principio es siempre lo más difícil!",
        "¡El que tiene fe en sí mismo no necesita que los demás crean en él!",
    ]
    mensaje = f"¡Hola {destinatario}!\n{rd.choice(frases_motivadoras)}" if destinatario else f"¡Hola!\n{rd.choice(frases_motivadoras)}"
    response = await ctx.send(mensaje)
    await asyncio.sleep(40)
    await response.delete()

def destinatario_en_base_de_datos(destinatario):
    try:
        conn = db_connect()
        if conn:
            return verify_id(conn, destinatario)
        else:
            return False
    except Exception as e:
        print(f"Error al verificar el destinatario: {e}")
        return False

# comando de abrazo, envía un mensaje de ánimo
@bot.command()
async def abrazo(ctx, destinatario=None):
    if destinatario and not destinatario_en_base_de_datos(destinatario):
        destinatario = None
    await seleccionar_y_enviar_frase(ctx, destinatario)


# comando de invitar a tomar algo
@bot.command()
async def invitar_alcohol(ctx, invitado: discord.Member):
    invitar = ctx.author # Quien invita
    elegir_bebida = [
        f"{invitar.name} invita a {invitado.name} a tomar un vaso del mejor whisky escocés.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de cerveza artesanal.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de vino tinto.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de ron.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de tequila.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de vodka.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de pisco.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de ginebra.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de mojito.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de bourbon.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de coñac.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de absenta.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de pisco sour.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de chilcano de maracuyá.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de amaretto.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Baileys.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Campari.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Chartreuse.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Cointreau.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de curacao.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Grand Marnier.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Kahlua.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Aperol Spritz.",
        f"{invitar.name} invita a {invitado.name} a tomar un vaso de Bellini.",
    ]
    mensaje = rd.choice(elegir_bebida)
    response = await ctx.send(mensaje)
    await asyncio.sleep(40)
    await response.delete()


@bot.command()
async def listar_emojis(ctx):
    # Verificar si el bot tiene permisos para enviar mensajes y añadir reacciones
    if not ctx.channel.permissions_for(ctx.guild.me).send_messages or \
       not ctx.channel.permissions_for(ctx.guild.me).add_reactions:
        mensaje = await ctx.send("No tengo los permisos necesarios para ejecutar este comando.")
        await asyncio.sleep(40)  # Esperar 40 segundos
        await mensaje.delete()  # Borrar el mensaje
        return

    # Obtener la lista de emojis del servidor
    emojis = ctx.guild.emojis

    print(f"Encontrados {len(emojis)} emojis en el servidor.")  # Impresión de depuración

    # Verificar si hay emojis para listar
    if not emojis:
        mensaje = await ctx.send("No hay emojis personalizados en este servidor.")
        await asyncio.sleep(40)  # Esperar 40 segundos
        await mensaje.delete()  # Borrar el mensaje
        return

    # Inicializar el mensaje con el título
    mensaje = "Emojis del servidor:\n"
    mensajes = []
    mensajes_enviados = []  # Lista para almacenar los objetos de mensaje enviados

    # Construir los mensajes asegurándose de que no superen el límite de caracteres
    for emoji in emojis:
        if len(mensaje) + len(str(emoji)) + 1 > 2000:
            mensajes.append(mensaje)
            mensaje = "Emojis del servidor:\n"  # Reiniciar el mensaje con el título para cada nuevo mensaje
        mensaje += str(emoji) + "\n"

    # Añadir el último mensaje si no está vacío
    if mensaje:
        mensajes.append(mensaje)

    # Enviar cada mensaje y almacenar el objeto de mensaje en mensajes_enviados
    for msg in mensajes:
        mensaje_enviado = await ctx.send(msg)
        mensajes_enviados.append(mensaje_enviado)

    # Esperar 40 segundos antes de borrar los mensajes
    await asyncio.sleep(40)
    for mensaje in mensajes_enviados:
        try:
            await mensaje.delete()
        except Exception as e:
            print(f"Error al borrar el mensaje: {e}")




# configurar el modelo generativo IA
text_generation_config = {
     "temperature": 0.9, 
     "top_p": 1,
     "top_k": 1,
     "max_output_tokens": 500,
}
image_generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 500,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},  
]
text_model = geneai.GenerativeModel(model_name="gemini-pro" , generation_config=text_generation_config, safety_settings=safety_settings)
image_model = geneai.GenerativeModel(model_name="gemini-pro-vision" , generation_config=image_generation_config, safety_settings=safety_settings)    

chat = text_model.start_chat(history=[])


#funcion para hablar con API de generacion de texto
@bot.command()
async def gemini(ctx, string: str):
    user_message = ctx.message.content
    respuesta_ia = chat.send_message(user_message)
    
    # Divide el texto en segmentos de 2000 caracteres o menos y los envía uno por uno
    segmentos = [respuesta_ia.text[i:i+2000] for i in range(0, len(respuesta_ia.text), 2000)]
    for segmento in segmentos:
        await ctx.send(segmento)
    
    # Guardar en la base de datos
    save_chat(connection, str(ctx.author.id), user_message, respuesta_ia.text)
    

# Comando para mostrar el historial de conversaciones
@bot.command()
async def historial(ctx):
    try:
        conn = db_connect()
        if conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM gemini_chats WHERE discordID = '{ctx.author.id}' ORDER BY id DESC LIMIT {MAX_HISTORY} OFFSET 0")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    await ctx.send(f"{row[2]}: {row[3]}")
            else:
                await ctx.send("No se encontraron conversaciones en el historial.")
        else:
            await ctx.send("No se pudo conectar a la base de datos.")
    except psycopg2.Error as e:
        await ctx.send(f"Error de psycopg2: {e}")
    except Exception as e:
        await ctx.send(f"Ocurrió un error: {e}")
    finally:
        conn.close()


#Conectar a la base de datos y crear tabla de intervenciones si no existe
conn = db_connect()
try:
    create_interventions_table(conn)
finally:
    conn.close()

# Constante para la ruta de la imagen de moneda de oro
RUTA_IMAGEN_MONEDA_ORO = "images\moneda_oro.png"


# Comando para otorgar monedas de oro al usuario que más ayude en el servidor
@bot.command()
async def gracias(ctx, usuario: discord.Member):
    # conectar a la base de datos
    conn = db_connect()
    try:
        # Incrementar las intervenciones del usuario en la base de datos
        increment_interventions(conn, str(usuario.id))

        # Obtener el número de intervenciones del usuario de la base de datos
        intervenciones = get_interventions(conn, str(usuario.id))

        # verificar si el usuario tiene más de 10 intervenciones
        if intervenciones >= 10:
            # resetear el conteo en la base de datos
            increment_interventions(conn, str(usuario.id), reset=True)
            await ctx.send(f"El usuario {usuario.name} ha sido muy activo en el servidor y ha sido premiado con una moneda de oro.")

            # Enviar la imagen de la moneda de oro como un archivo adjunto
            with open(RUTA_IMAGEN_MONEDA_ORO, 'rb') as archivo_imagen:
                await ctx.send(f"{usuario.mention}", file=discord.File(archivo_imagen, 'moneda_oro.png'))
    finally:
        conn.close()

# Comando para mostrar el ranking de los usuarios que mas ayudan en el servidor
@bot.command()
async def ranking(ctx):
    # conectar a la base de datos
    conn = db_connect()
    try:
        intervenciones = get_all_interventions(conn)
        if intervenciones:
            mensaje = "Ranking de usuarios más activos en el servidor:\n"
            for i, (usuario_id, cantidad) in enumerate(intervenciones):
                usuario = ctx.guild.get_member(int(usuario_id))
                if usuario:  # Verificar que el usuario todavía está en el servidor
                    mensaje += f"{i+1}. {usuario.name}: {cantidad} intervenciones\n"
            await ctx.send(mensaje)
        else:
            await ctx.send("No hay intervenciones registradas en el servidor.")
    finally:
        conn.close()
        
 
# Cargar la tabla de chistes al inicio
create_and_load_chistes_table(chistes_list) 
 
 
# Comando para contar un chiste
@bot.command(name='chistes')
async def chistes(ctx):
    conn = db_connect()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT contenido FROM chistes ORDER BY RANDOM() LIMIT 1")
        chiste = cursor.fetchone()
        await ctx.send(chiste[0] if chiste else "No hay chistes disponibles en este momento.")
        cursor.close()
        conn.close()
        
        



# Juego de adivinar la palabra
def generar_mensaje(palabra_descubierta, vidas, letras_usadas):
    return (f"**Palabra secreta:** {' '.join(palabra_descubierta)}\n"
            f"**Vidas restantes:** {vidas}\n"
            f"**Letras usadas:** {' '.join(sorted(letras_usadas))}")

@bot.command()
async def adivina(ctx):
    palabras = ["python", "ordenador", "libreria", "programacion", "discord", "bot", "juego", "videojuego", "tecnologia", "inteligencia", "django"]
    palabra_secreta = rd.choice(palabras)
    vidas = 6
    palabra_descubierta = ['_'] * len(palabra_secreta)
    letras_usadas = set()

    await ctx.send(f"**Bienvenido al juego de adivinar la palabra!**\n\n" + generar_mensaje(palabra_descubierta, vidas, letras_usadas) + "\n**Escribe una letra para adivinar la palabra.**")

    while vidas > 0:
        def check(m):
            return m.author == ctx.author and m.content.isalpha()

        try:
            respuesta = await bot.wait_for('message', check=check, timeout=30.0)
            contenido = respuesta.content.lower()
            if len(contenido) == 1:  # adivinando una letra
                letra = contenido
                if letra in letras_usadas:
                    await ctx.send(f"Ya has usado la letra {letra}. Inténtalo de nuevo.")
                    continue
                letras_usadas.add(letra)
                if letra in palabra_secreta:
                    for i, c in enumerate(palabra_secreta):
                        if c == letra:
                            palabra_descubierta[i] = letra
                    await ctx.send(f"La letra {letra} está en la palabra.\n\n" + generar_mensaje(palabra_descubierta, vidas, letras_usadas))
                    if '_' not in palabra_descubierta:
                        await ctx.send(f"**Felicidades! Has adivinado la palabra.**\n\n**Palabra secreta:** {palabra_secreta}")
                        break
                else:
                    vidas -= 1
                    await ctx.send(f"La letra {letra} no está en la palabra. Inténtalo de nuevo.\n\n" + generar_mensaje(palabra_descubierta, vidas, letras_usadas))
            else:  # adivinando la palabra completa
                if palabra_descubierta.count('_') <= len(palabra_secreta) / 2:  # si se ha adivinado al menos la mitad de las letras
                    if contenido == palabra_secreta:
                        await ctx.send(f"**Felicidades! Has adivinado la palabra.**\n\n**Palabra secreta:** {palabra_secreta}")
                        break
                    else:
                        vidas -= 1
                        await ctx.send(f"La palabra {contenido} no es correcta. Inténtalo de nuevo.\n\n" + generar_mensaje(palabra_descubierta, vidas, letras_usadas))
                else:
                    await ctx.send("Aún no puedes adivinar la palabra completa. Sigue adivinando letras.")
        except asyncio.TimeoutError:
            await ctx.send("Se acabó el tiempo. Inténtalo de nuevo.")
            break
    else:
        await ctx.send(f"**Perdiste! La palabra secreta era: {palabra_secreta}**")
        


# Evento que se activa cuando un miembro cambia su estado de voz
@bot.event
async def on_voice_state_update(member, before, after):
    # Verifica si el miembro se desconectó de un canal de voz
    if before.channel is not None and after.channel is None:
        # Obtén el canal de texto donde deseas enviar el mensaje
        channel = discord.utils.get(member.guild.text_channels, name='chat_general')
        if channel:
            # Crea un Embed con un título, descripción y color (el color es un valor hexadecimal)
            embed = discord.Embed(
                title="**Saliste del canal de voz!!**",
                description=f"Gracias por tu ayuda, en el canal de voz de Gonzalo Ponce, {member.name}",
                color=0x00ff00  # Verde
            )
            # Envía el Embed al canal
            response = await channel.send(embed=embed)
            await asyncio.sleep(80)
            await response.delete()



    
        
        



# Iniciar el bot    
bot.run(token)
        