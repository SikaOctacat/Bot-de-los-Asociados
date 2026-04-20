from funciones import *
from .traductor import traducir

tokens = True
traduccionesIniciadas = 0
traduccionActual = 1
async def conectar(message,conexion):
    global tokens,traduccionesIniciadas,traduccionActual
    traduccionesIniciadas += 1

    canal_ingles = conexion[0]
    canal_espanol = conexion[1]

    salidaClave = None
    llegadaClave = None

    #La Doctrina Dry es una cosa
    if message.channel.id == canales[canal_ingles]["ID"]:
        salidaClave = canal_ingles
        salida = canales[canal_ingles]

        llegadaClave = canal_espanol
        llegada = canales[canal_espanol]

    elif message.channel.id == canales[canal_espanol]["ID"]:
        salidaClave = canal_espanol
        salida = canales[canal_espanol]

        llegadaClave = canal_ingles
        llegada = canales[canal_ingles]
    else:
        return
    
    try:
        #Esto extrae el webhook del canal y para usarlo
        async with aiohttp.ClientSession() as session:
            

            canal_destino = bot.get_channel(llegada["ID"])
            
            #Esto crea el boton con el mensaje de escribiendo en otro canal, cuando el mensaje llegue (O falle) se borrara
            view = discord.ui.View()
            boton = discord.ui.Button(
                label = message.author.display_name+salida["escribiendo"],
                emoji="<a:cargando:1495241883910275172>",
                style= discord.ButtonStyle.gray,
                disabled=True
            )
            view.add_item(boton)

            escribiendo = await canal_destino.send(view=view)

            webhook =  Webhook.from_url(salida["webhook_destino"],session=session)

            #Es esta parte ocurre la traduccion, mientes se ejecuta y se hacen los ajustes el bot muestra una señal de escribri
            traduccion = ""
            lista_archivos = []
            try:
                traduccion = await traducir(message,salida)

                #Aca se agregan los stickers y las imagenes
                for archivo in message.attachments:
                    bytes = await archivo.read()
                    lista_archivos.append(discord.File(io.BytesIO(bytes),filename=archivo.filename))

                if message.reference and (message.reference.type == discord.MessageReferenceType.forward):
                    
                    snapshot = message.message_snapshots[0]
                    if snapshot and snapshot.attachments:
                        for adjunto in message.snapshot.attachments:
                            traduccion = f"\n{adjunto.url}"

                
                for sticker in message.stickers:
                    traduccion += f"\n{sticker.url}"

                if traduccion == "" and lista_archivos == []:
                    await escribiendo.delete()
                    return
            except Exception as e:
                traduccion = message.content
                print("Uhm, y si... Nadie se va dar cuentnadaa si no traduzco ")
                print(e)

            #Forma algo torpe, pero sencilla, de gestionar el orde de llegada de los mensajes
                
            try:
                msj_enviado = await webhook.send(
                    content=traduccion,
                    username= message.author.display_name,
                    avatar_url= message.author.display_avatar.url,
                    files=lista_archivos,
                    # allowed_mentions=discord.AllowedMentions(users=False),
                    wait=True
                )
            except Exception as e:
                print("Yo habia ponido mi webhook aqui y ya no ta...")
                print(e)

            try:
                await escribiendo.delete()
            except:
                print("EHHH, ni para esperar me dejan...")


        #Esto se encarga de actualizar el registo de mensajes
        limite_mensajes_largo = 250

        canales[salidaClave]["historial"][message.id] = {
            "autor": message.author.display_name,
            "autor_ID": message.author.id,
            "contenido": message.content[:limite_mensajes_largo],
            "espejo": msj_enviado.id
        }

        canales[llegadaClave]["historial"][msj_enviado.id] = {
            "autor": message.author.display_name,
            "autor_ID": message.author.id,
            "contenido": traduccion[:limite_mensajes_largo],
            "espejo": message.id
        }
        
        #Esto corta parte del regristo si este se hace muy largo
        for clave in [salidaClave,llegadaClave]:
            recortarRegistro(canales[clave]["historial"])
        
        tokens = True
    except Exception as e:

        if not tokens:
            print("Sika, algo salio mal el proceso de conexion, no me ignores y reparame!!!")
            print(e)

            general_ingles = bot.get_channel(canales[canal_ingles]["ID"])
            general_espanol = bot.get_channel(canales[canal_espanol]["ID"])
                
            if general_ingles:
                # Enviamos el mensaje indicando quién lo dijo originalmente
                await general_ingles.send(f"Hey guy, there is posibily that I've run out of tokens, so I wont be able to translate more for today, sorry")

            if general_espanol:
                await general_espanol.send(f"Oigan chicos, creo que me qude sin tonkens para traducir mas XD, ehm, no podre continuar por hoy, para que lo tengan claro, perdon por las molestias")

            tokens = False
    
    traduccionActual += 1