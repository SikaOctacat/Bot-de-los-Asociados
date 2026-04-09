from funciones import *

async def buscarMensaje(messageID,buscar="mensaje",ID=False):

    for clave in canales:
        historial = canales[clave]["historial"]
        mensaje = historial.get(messageID)

        if mensaje:
            if ID:

                if buscar == "canal":
                    return canales[clave]["ID"]
                elif buscar == "espejo":
                    return mensaje["espejo"]

                return mensaje["ID"]
            else:
                if buscar == "canal":
                    return clave
                elif buscar == "espejo":
                    return await buscarMensaje(mensaje["espejo"])

                return mensaje["contenido"]
    
    return False

async def editarMensajeEspejo(before, after):
    #Claro, si la edicion no cambio nada ps no hace nada
    if before.content == after.content:
        return

    #Si no esta en nuestro registro, no lo tomes en cuenta para editar de vuelta
    for valor in canales.values():
        if before.id in valor["historial"]:
            #Esto obtiene el objeto con los datos necesarios del canal para poder saber que hacer exacmente
            config = canales[await buscarMensaje(after.id,buscar="canal")]

            if not config:
                return
            
            try:
                #Esto genera la traduccion nueva tomando en cuenta el nuevo mensaje editado, y el webhook aun sin traducir
                from .traductor import traducir
                nueva_traduccion = await traducir(after,config)
                webhook_a_traducir = valor["historial"][before.id]["espejo"]

                async with aiohttp.ClientSession() as session:
                    #Esta magia negra creo que extrae el webhook de el cliente de la url de de discord de los sueños de Mishu o algo asi
                    webhook = Webhook.from_url(config["webhook_destino"], session=session)

                    # Ya con todo listo, solo edita el mensaje
                    await webhook.edit_message(webhook_a_traducir,content=nueva_traduccion)
            except discord.NotFound:
                pass
            except Exception as e:
                print("¿Debia editar algo? Ah si, me equivoque")
                print(e)


async def borrarMensajeEspejo(message):
    # Se evita asi mismo si se detecta a el mismo o se da cuenta que el mensaje ya lo habia borrado antes
    if (message.author == bot.user) or (message.id in mensajes_borrados.values()):
        return
    
    #Esto es basicamente: "ALTO AHI, a, espera, ya terminaste? xd"
    try:
        traducciones_activas[message.id].cancel()
    except:
        pass

    servidor = message.guild

    mensajeEspejoID = await buscarMensaje(message.id,"espejo",ID=True)
    if not mensajeEspejoID:
        return

    canalClave = await buscarMensaje(message.id,"canal")
    canalEspejoClave = await buscarMensaje(mensajeEspejoID,"canal")

    canalEspejo = servidor.get_channel(canales[canalEspejoClave]["ID"])

    if canalEspejo:
        try:
            msg_a_borrar = await canalEspejo.fetch_message(mensajeEspejoID)
            await msg_a_borrar.delete()
            mensajes_borrados[message.id] = mensajeEspejoID
            recortarRegistro(mensajes_borrados)
        
        except discord.NotFound:
            pass

        except Exception as e:
            print("OYE SIKA COMO BORRO ESTO?, No me deja...")
            print(e)
        
    canales[canalClave]["historial"].pop(message.id, None)
    canales[canalEspejoClave]["historial"].pop(mensajeEspejoID, None)

async def reaccionarMensajeEspejo(payload,borrar=False):
    if payload.message_id in traducciones_activas:
        try:
            await traducciones_activas[payload.message_id]
        except:
            pass

    mensaje_espejo_ID = await buscarMensaje(payload.message_id,"espejo",ID=True)
    if not(mensaje_espejo_ID) or payload.user_id == bot.user.id:
        return

    try:
        canal_espejo_ID = await buscarMensaje(mensaje_espejo_ID,"canal",ID=True)
        canal_espejo = await bot.fetch_channel(canal_espejo_ID)
        mensaje_espejo = await canal_espejo.fetch_message(mensaje_espejo_ID)

        if borrar:
            await mensaje_espejo.remove_reaction(payload.emoji,bot.user)
        else:
            await mensaje_espejo.add_reaction(payload.emoji)

    except Exception as e:
        print("No pude reaccionar o des-reaccionar a un mensaje (Litralmente)")
        print(e)