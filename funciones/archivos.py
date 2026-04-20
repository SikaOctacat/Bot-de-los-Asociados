from funciones import *

async def guardarArchivo(payload):

    listaArchivos = []

    canal = bot.get_channel(payload.channel_id)
    mensaje = await canal.fetch_message(payload.message_id)
    usuario = bot.get_user(payload.user_id) or await bot.fetch_user(payload.user_id)

    if usuario.bot:
        return

    poseeLinks = bool(re.search(r'https?://\S+|www\.\S+',mensaje.content))

    if str(payload.emoji) != "⭐" or (not(mensaje.attachments) and not(poseeLinks)):
        return
    
    for archivo in mensaje.attachments:
        bytes = await archivo.read()

        listaArchivos.append(discord.File(io.BytesIO(bytes),filename=archivo.filename))

    descripcion = f"> Servidor: **{mensaje.guild.name}**\n> Publicado por: **{mensaje.author.display_name} ({mensaje.author.name})**"

    if mensaje.content != "":
        descripcion += f'\n> "*{mensaje.content}*"'

    try:   
        directorio = os.path.dirname(__file__)
        indicacion = os.path.join(directorio,"..","imagenes","indicaciones.png")

        await usuario.send(descripcion,files=listaArchivos)
    except:
        instruccion = await canal.send(f'{usuario.mention} Para poder guardar los mensajes en tu MD debes tener configurado **en tu perfil** en la seccion de **Permisos de interacción** la opcion de **Mensajes directos** activa al menos para este servidor:',file=discord.File(indicacion))

        await asyncio.sleep(20)

        await instruccion.delete()