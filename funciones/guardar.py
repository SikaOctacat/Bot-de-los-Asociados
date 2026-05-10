from funciones import *
from .mensajes import filtrarMensajesPings

async def gestionarReacciones(payload,poseeArchivo=False,poseeLink=False,suma=1,negativos=False):

    emojis = {
        "⭐": ["estrellas",["Sumarte a ti mismo","Sumar sin adjunto","Procesar si suma negativa"]],
        "❌": ["estrellas",["Sumar"]],
        "❤️": ["corazones",["Sumarte a ti mismo"]],
        "📸": ["descontextualizaciones",["Acomular","Actuar sobre uno mismo"]]
    }

    canal = bot.get_channel(payload.channel_id)
    mensaje = await canal.fetch_message(payload.message_id)

    try:
        direccion = emojis[str(payload.emoji)][0]
        evitar = emojis[str(payload.emoji)][1]
    except:
        return
    
    if ("Acomular" in evitar):
        registro = registros.find_one({"_id": ObjectId("69f8e16ec800ad6f9849505c")})
        if payload.message_id in registro["registro"]:
            return
    
    if mensaje.guild == None:
        reaccionado = bot.get_user(mensaje.author.id) or await bot.fetch_user(mensaje.author.id)
    else:
        reaccionado = mensaje.guild.get_member(mensaje.author.id) or await mensaje.guild.fetch_member(mensaje.author.id)
    
    reaccionador = bot.get_user(payload.user_id) or await bot.fetch_user(payload.user_id)

    if ("Actuar sobre uno mismo" in evitar) and reaccionado.id == reaccionador.id:
        return

    links = bool(re.search(
            r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
            mensaje.content,
            re.IGNORECASE
        ))

    archivos = mensaje.attachments != []

    
    if poseeArchivo and not(archivos):
        return
    elif poseeLink and not(links):
        return

    #Antes si quiera de enviar el documento al MD, actualizamos la base de datos... Por si acaso

    cancelar = ("Sumar" in evitar) or ("Sumar sin adjunto" in evitar and (not(archivos) and not(links))) or ("Sumarte a ti mismo" in evitar and (reaccionador.id == reaccionado.id))

    if suma and not(cancelar):
        criterio = {"discriminador_discord":reaccionado.name}

        usuarios_info.update_one(
            criterio,
            {"$setOnInsert": crearUsuario(reaccionador.name)},
            upsert=True
        )

        usuario_db = usuarios_info.find_one(criterio)

        if not(negativos) and usuario_db["estadisticas"][direccion] + suma < 0:
            return
        
        usuarios_info.update_one(
            criterio,
            {"$inc": {f"estadisticas.{direccion}":suma}}
        )
    
    cancelar = ("Procesar" in evitar) or ("Procesar si suma negativa" in evitar and suma < 0)
    if not cancelar:
        match direccion:
            case "estrellas":
                await archivo(payload,canal,mensaje,reaccionado,reaccionador)
            case "descontextualizaciones":
                await fueraDeContexto(payload,canal,mensaje,reaccionado,reaccionador)
            case _: pass



async def archivo(payload,canal,mensaje,reaccionado,reaccionador):


    #Con esto evito conflictos con los mensajes hechos en servers o en MD, los detalles se manejan mas adelante
    #Desgraciados, ya me rompieron el bot, esto deberia solucionarlo
    if reaccionador.bot:
        return
    criterio = {"discriminador_discord":reaccionador.name}
    usuarioDB = usuarios_info.find_one(criterio)
    if str(payload.emoji) == "❌":
        if str(mensaje.id) in usuarioDB["mensajes_md"]:
            chatDM = reaccionador.dm_channel or await reaccionador.create_dm()

            for borrar in range(len(usuarioDB["mensajes_md"][str(mensaje.id)])):
                mensajeBorrar = await chatDM.fetch_message(int(usuarioDB["mensajes_md"][str(mensaje.id)][borrar]))
                await mensajeBorrar.delete()
                
            usuarios_info.update_one(criterio,
                                    {"$unset":{f"mensajes_md.{mensaje.id}":""}})
        return

    listaArchivos = []
    listaEmbeds = []

    #Aca se vefican los datos extras
    for archivo in mensaje.attachments:
        bytes = await archivo.read()

        listaArchivos.append(discord.File(io.BytesIO(bytes),filename=archivo.filename))

    for embed in mensaje.embeds:
        listaEmbeds.append(discord.Embed(
            title=embed.title,
            description=embed.description
        ))


    #Esto evita la redudancia del apodo del usuario con su nombre global
    nombreGlobal = ""
    if reaccionado.global_name and reaccionado.display_name != reaccionado.global_name:
        nombreGlobal = reaccionado.global_name + ","    

    #Esta cosa es para que la hora se ajusta la del usuaro y tenga un formato lindo
    fechaFormato = f"<t:{int(mensaje.created_at.timestamp())}:f>"

    descripcion = f"> Publicado por: **{reaccionado.display_name} ({nombreGlobal}{reaccionado.name})**\n> Canal: **{mensaje.channel.name}**\n> Servidor: **{mensaje.guild.name}**\n> Fecha y hora: **{fechaFormato}**\n> Mensaje original: **{mensaje.jump_url}**"


    try:   
        directorio = os.path.dirname(__file__)
        indicacion = os.path.join(directorio,"..","imagenes","indicaciones.png")

        

        if usuarioDB:
            if "mensajes_md" not in usuarioDB:
                await reaccionador.send('Recciona con una "❌" para borrar cualquiera de los archivos\n\nTambien puedes puedes filtras las imagenes por nombre u usuario usando el buscador nativo de discord\n------------------------------------------------')
                
                usuarios_info.update_one(criterio,
                                            {"$set": {"mensajes_md":{}}},
                                            upsert=True
                                        )
            
            mensajeDescripcion = await reaccionador.send(descripcion)
            mensajeResultado = await mensajeDescripcion.reply(mensaje.content,files=listaArchivos,embeds=mensaje.embeds)
            # Aca se guardan los datos  en la base de datos
            usuarios_info.update_one(criterio,
                                        {"$set": {f"mensajes_md.{mensajeResultado.id}":[str(mensajeResultado.id),str(mensajeDescripcion.id)]}}
                                    )
            
            recortarRegistroDB(usuarios_info,criterio,"mensajes_md",exceso=1)
            
            
            # recortarRegistro(mensajesMD[reaccionador.id][mensajeResultado.id],exceso=1)

        else:
            instruccion = await canal.send(f'{reaccionador.mention} Para poder guardar los mensajes en tu MD debes tener configurado **en tu perfil** en la seccion de **Permisos de interacción** la opcion de **Mensajes directos** activa al menos para este servidor:',file=discord.File(indicacion))

            await asyncio.sleep(20)

            await instruccion.delete()
            return

    except Exception as e:
        print(f"Supongo que ha de ser la base de datos o algo...\n{e}")
        


async def fueraDeContexto(payload,canal,mensaje,victima,victimario):
    if str(payload.emoji) != "📸":
        return
    
    listaArchivos = []

    if victimario.bot:
        return

    #Como depende del servidor, se tiene que hacer esto
    match mensaje.guild.id:
        case 1020042170230648852:
            config = canales["senderoContexto"]
        case 1086801840764629093:
            config = canales["escaladaContexto"]
        case 1294734570788491304:
            config = canales["asociadosContexto"]
        case _:
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
            #Justo aca se guarda el descontexto xd
            registros.update_one({"_id": ObjectId("69f8e16ec800ad6f9849505c")},
                                {"$push":{"registro":str(mensaje.id)}}
                                )

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