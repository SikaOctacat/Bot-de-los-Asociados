from funciones import *
from .mensajes import filtrarMensajesPings

async def archivo(payload):

    listaArchivos = []

    canal = bot.get_channel(payload.channel_id)
    mensaje = await canal.fetch_message(payload.message_id)
    usuario = bot.get_user(payload.user_id) or await bot.fetch_user(payload.user_id)

    if usuario.bot:
        return
    
    if str(payload.emoji) == "❌":
        if (usuario.id in mensajesMD) and (mensaje.id in mensajesMD[usuario.id]):
            for borrar in range(len(mensajesMD[usuario.id][mensaje.id])):
                await mensajesMD[usuario.id][mensaje.id][borrar].delete()
            del mensajesMD[usuario.id][mensaje.id]
        return
    elif str(payload.emoji) != "⭐":
        return


    for archivo in mensaje.attachments:
        bytes = await archivo.read()

        listaArchivos.append(discord.File(io.BytesIO(bytes),filename=archivo.filename))

    #Esta cosa es para que la hora se ajusta la del usuaro y tenga un formato lindo
    fechaFormato = f"<t:{int(mensaje.created_at.timestamp())}:f>"

    descripcion = f"> Servidor: **{mensaje.guild.name}**\n> Canal: **{mensaje.channel.name}**\n> Fecha y hora: **{fechaFormato}**\n> Publicado por: **{mensaje.author.display_name} ({mensaje.author.name})**\n> Mensaje original: **{mensaje.jump_url}**"


    try:   
        directorio = os.path.dirname(__file__)
        indicacion = os.path.join(directorio,"..","imagenes","indicaciones.png")

        if usuario.id not in usuariosConMD:
            await usuario.send('Recciona con una "❌" para borrar cualquiera de los archivos\n\nTambien puedes puedes filtras las imagenes por nombre u usuario usando el buscador nativo de discord\n------------------------------------------------')
            usuariosConMD.append(usuario.id)

        mensajeDescripcion = await usuario.send(descripcion)
        mensajeResultado = await mensajeDescripcion.reply(mensaje.content,files=listaArchivos)

        if not (usuario.id in mensajesMD):
            mensajesMD[usuario.id] = {}

        
        mensajesMD[usuario.id][mensajeResultado.id] = [mensajeResultado,mensajeDescripcion]
        recortarRegistro(mensajesMD[usuario.id][mensajeResultado.id],exceso=1)

    except:
        instruccion = await canal.send(f'{usuario.mention} Para poder guardar los mensajes en tu MD debes tener configurado **en tu perfil** en la seccion de **Permisos de interacción** la opcion de **Mensajes directos** activa al menos para este servidor:',file=discord.File(indicacion))

        await asyncio.sleep(20)

        await instruccion.delete()


async def fueraDeContexto(payload):
    if str(payload.emoji) != "📸":
        return
    
    listaArchivos = []

    canal = bot.get_channel(payload.channel_id)
    mensaje = await canal.fetch_message(payload.message_id)
    victima = mensaje.author
    victimario = bot.get_user(payload.user_id) or await bot.fetch_user(payload.user_id)

    if victimario.bot:
        return

    #Como depende del servidor, se tiene que hacer esto
    match mensaje.guild.id:
        case 1020042170230648852:
            config = canales["senderoContexto"]
        case 1086801840764629093:
            config = canales["escaladaContexto"]
        case _:
            return
        
    if mensaje.id in config["historial"]:
        return

    

    for archivo in mensaje.attachments:
        bytes = await archivo.read()
        listaArchivos.append(discord.File(io.BytesIO(bytes),filename=archivo.filename))

    async with aiohttp.ClientSession() as session:
        try:
            webhook = Webhook.from_url(config["webhook"],session=session)

            mensajeFiltrado = await filtrarMensajesPings(mensaje.guild,mensaje.content)
            resultado = await webhook.send(
                content=mensajeFiltrado,
                username=victima.display_name,
                avatar_url= victima.display_avatar.url,
                files=listaArchivos,
                wait=True
            )
            config["historial"].append(mensaje.id)

            #Dado que los webhooks no se les puede hacer reply directamente, se debe hacer esta maroma
            canalDestino = bot.get_channel(config["ID"])
            referencia = discord.MessageReference(
                message_id= resultado.id,
                channel_id= canalDestino.id,
                guild_id= mensaje.guild.id
            )

            #Esta cosa es para que la hora se ajusta la del usuaro y tenga un formato lindo
            fechaFormato = f"<t:{int(mensaje.created_at.timestamp())}:f>"
            await canalDestino.send(f"Tomado por: {victimario.mention}\nFecha y hora original: {fechaFormato}",reference=referencia)

        except Exception as e:
            print("Uy, yo si queria descontextualizarlo...")
            print(e)