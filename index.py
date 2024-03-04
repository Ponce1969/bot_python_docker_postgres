# aqui se desarrolla la logica para el bot de discord.
# se importan las librerias necesarias
import discord
from dotenv import load_dotenv
from discord.ext import tasks
import os
from discord.ext import commands
import database
import datetime
from googleapiclient.discovery import build
import pytz
import asyncio
import psycopg2
from database import db_connect


# Carga las variables de entorno desde el archivo .env
db_uri = os.getenv('DB_URI')
token = os.getenv('DISCORD_TOKEN')
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

youtube_api = build('youtube', 'v3', developerKey=youtube_api_key)

intents = discord.Intents.default()
intents.message_content = True
# comando de prefijo ' > '
bot = commands.Bot(command_prefix='>', description="Esto es un bot de ayuda", intents=intents, case_insensitive=True)


# Crear la conexión a la base de datos antes de iniciar el bot
try:
    connection = db_connect() # asegurarse de que la función db_connect() esté definida en database.py
    if connection is None:
        print("No se pudo conectar a la base de datos")
    else:
        print("Conexión a la base de datos establecida correctamente")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")



# Evento on_ready combinado
@bot.event
async def on_ready():
    try:
        await bot.change_presence(activity=discord.Streaming(name="Tutorial de Mouredev", url="https://www.twitch.tv/mouredev/videos"))
        print("Bot iniciado correctamente")
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")
    
    
# Comando register
@bot.command(help="registrate en la database")
async def register(ctx):
    try:
        global connection
        cursor = None  # Inicializa cursor aquí
        flag = database.verify_id(connection, str(ctx.author.id))
        if flag:
            await ctx.send("Usted se encuentra registrado en la base de datos")
        else:
            cursor = connection.cursor()  # Mueve la inicialización aquí
            database.register(connection, ctx)
            await ctx.send("Te has registrado correctamente en la base de datos")
    except psycopg2.Error as e:
        await ctx.send(f"Error de psycopg2: {e}")
    except Exception as e:
          print(f"Ocurrió un error: {e}")
          print(f"Type of exception: {type(e)}")
          print(f"Exception details: {e.args}")
          await ctx.send(f"Ocurrió un error: {e}")
    finally:
        if cursor is not None:
            cursor.close()  # Cierra el cursor en el bloque finally




 # Decorador para la función ping
@bot.command()
async def ping(ctx):
    await ctx.send('pong')      
    
    
# Decorador para la función ayuda
@bot.command()
async def ayuda(ctx):
    """
    Muestra información sobre los comandos disponibles del bot.

    Uso:
    >ayuda

    Descripción:
    Este comando proporciona información detallada sobre los comandos disponibles del bot.
    """

    ayuda_msg = """
    Hola! Soy tu bot de Discord. Aquí están las cosas que puedo hacer:

    1. **Buscar canciones de YouTube**: Usa `>youtube <nombre de la canción>` para buscar una canción en YouTube.
    2. **Operaciones matemáticas**: Puedo sumar, restar, multiplicar y dividir;
        - Para sumar: `>operacion sum <número 1> <número 2>`
        - Para restar: `>operacion resta <número 1> <número 2>`
        - Para multiplicar: `>operacion mult <número 1> <número 2>`
        - Para dividir: `>operacion div <número 1> <número 2>`
        - Para obtener el resto: `>operacion resto <número 1> <número 2>`
    3. **Saludar**: Usa `>saludo` y te devolveré un saludo!
    4. **Info**: Usa `>info` y te devolveré información y hora del servidor.
    5. **Registrarse**: Usa `>register` y te registraré en la base de datos.
    Si tienes alguna otra pregunta, no dudes en preguntar!
    """
    await ctx.send(ayuda_msg)
    
    
 # Decorador para la función saludo   
@bot.command()
async def saludo(ctx, nombre: str = None):
    if nombre:
        await ctx.send(f"Hola,  {nombre}!! \n Bienvenido al Servidor de Gonzalo Ponce.")
    else:
        await ctx.send("Hola! Por favor, dime tu nombre para saludarte correctamente, asi \n >saludo y tu nombre")
        


# Decorador para la función operacion_matematica
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
                await ctx.send("Error: No se puede dividir por cero.")
                return
        elif operador == 'resto':
            resultado = numero_uno % numero_dos
        else:
            await ctx.send("Error: Operador no válido.")
            return
        await ctx.send(resultado)
    except Exception as e:
        await ctx.send(f"Error en la operación: {e}")


# Ejemplo de uso: >operacion sum 5 3
# Resultado: 8
    
# Decorador para la función info de zona horaria.
@bot.command()
async def info(ctx):
    try:
        # Obten la hora actual en la zona horaria de Uruguay
        uruguay_time = datetime.datetime.now(pytz.timezone('America/Montevideo')) # Cambia a tu zona horaria'

        if ctx.guild is None:
            title = "Mensaje Directo"
        else:
            title = ctx.guild.name

        # Crea el embed con el título y la hora de Uruguay
        embed = discord.Embed(title=title, 
            description="Aprendiendo Python y sus librerias",
            timestamp=uruguay_time, color=discord.Color.blue())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error en la función info: {e}")
 
 
 # Decorador para la función youtube                        
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
            options = []
            for i, item in enumerate(response['items']):
                if item['id']['kind'] == "youtube#video":
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    options.append(f"{i + 1}: {title}")

            if not options:
                await ctx.send('No se encontraron videos para tu búsqueda.')
                return

            options_message = "\n".join(options)
            await ctx.send("Elije un video:\n" + options_message)

            def check(m):
                return m.author == ctx.author and m.content.isdigit() and 0 < int(m.content) <= len(options)

            try:
                choice = await bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send('No se recibió respuesta, cancelando operación.')
                return

            selected = int(choice.content) - 1
            video_id = response['items'][selected]['id']['videoId']
            await ctx.send('https://www.youtube.com/watch?v=' + video_id)
        else:
            await ctx.send('No se encontraron videos para tu búsqueda.')
    except Exception as e:
        await ctx.send(f"Ha ocurrido un error al buscar videos: {str(e)}")
        

"""  
# Decorador para la función clear_old_messages
# lograr permisos para borrar mensajes y luego descomentar el codigo
@tasks.loop(hours=24)  # Ejecuta esta función cada 24 horas
async def clear_old_messages():
    for guild in bot.guilds:  # Para cada servidor en el que el bot está presente
        for channel in guild.text_channels:  # Para cada canal de texto en el servidor
            limit_time = datetime.datetime.now() - datetime.timedelta(days=30)  # Los mensajes deben ser más antiguos que esto para ser borrados
            await channel.purge(limit=25, before=limit_time)  # Borra los mensajes antiguos

@bot.event
async def on_ready():
    clear_old_messages.start()  # Inicia la tarea cuando el bot está listo


"""
        
        
     
bot.run(token)        