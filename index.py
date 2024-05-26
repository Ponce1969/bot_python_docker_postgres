import os
import datetime
import random as rd
import asyncio
import discord
from discord.ext.commands import Bot
from dotenv import load_dotenv
from googleapiclient.discovery import build
import pytz
from translate import Translator
from database import db_connect, verify_id, register
import psycopg2


# Cargar variables de entorno
load_dotenv()
db_uri = os.getenv('DB_URI')
token = os.getenv('DISCORD_TOKEN')
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

# Inicializar API de YouTube
youtube_api = build('youtube', 'v3', developerKey=youtube_api_key)

# Configurar intents y bot
intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix='>', description="Bot de ayuda", intents=intents, case_insensitive=True)

# Conexión a la base de datos
try:
    connection = db_connect()
    if connection:
        print("Conexión a la base de datos establecida correctamente")
    else:
        print("No se pudo conectar a la base de datos")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")

# Evento de inicio del bot
@bot.event
async def on_ready():
    try:
        await bot.change_presence(activity=discord.Streaming(name="Tutorial de Mouredev", url="https://www.twitch.tv/mouredev/videos"))
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
            await ctx.send("Te has registrado correctamente en la base de datos")
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
    1. **Buscar canciones de YouTube**: Usa `>youtube <nombre de la canción>` para buscar una canción en YouTube.
    2. **Operaciones matemáticas**: Usa `>operacion <sum|resta|mult|div|resto> <número 1> <número 2>`.
    3. **Saludar**: Usa `>saludo` y te devolveré un saludo!
    4. **Info**: Usa `>info` y te devolveré información y hora del servidor.
    5. **Registrarse**: Usa `>register` y te registraré en la base de datos.
    6. **Traducir**: Usa `>translate <mensaje>` y te devolveré el mensaje traducido al español.
    7. **Abrazo**: Usa `>abrazo` y te enviaré un mensaje de ánimo.
    8. **Invitar**: Usa `>invitar_alcohol <@usuario>` y enviaré una invitación para tomar algo.
    """
    response = await ctx.send(ayuda_msg)
    await asyncio.sleep(30)
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
        
# comando de información, muestra la hora del servidor
@bot.command()
async def info(ctx):
    try:
        uruguay_time = datetime.datetime.now(pytz.timezone('America/Montevideo'))
        title = "Mensaje Directo" if ctx.guild is None else ctx.guild.name
        embed = discord.Embed(
            title=title,
            description="Aprendiendo Python y sus librerías",
            timestamp=uruguay_time,
            color=discord.Color.blue()
        )
        response = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await response.delete()
        
    except Exception as e:
        response = await ctx.send(f"Error en la función info: {e}")
        await asyncio.sleep(10)
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
    await ctx.send(mensaje)



# Iniciar el bot    
bot.run(token)
       