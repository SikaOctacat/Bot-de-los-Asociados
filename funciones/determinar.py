from funciones import *

async def niveles(message):

    if message.author.bot and message.author != bot.user:
        return

    nombre = message.author.name
    criterio = {"discriminador_discord":nombre}
    
    # Esto agrega al usuario si este no existe
    usuarios_info.update_one(criterio,
                            {"$setOnInsert": crearUsuario(message.author.name)},
                            upsert=True
                            )
    
    usuarios_info.update_one(criterio,
                            {"$inc":{"estadisticas.xp":len(message.content)}})
    
    usuarios_info.update_one(criterio,
                            {"$inc":{"estadisticas.mensajes":1}})
    
    usuario = usuarios_info.find_one(criterio)

    nivel = usuario["estadisticas"]["nivel"]
    xp = usuario["estadisticas"]["xp"]

    if nombre != usuario["nombre"]:
        nombre = usuario["nombre"]
    

    subioDeNivel = False
    while xp >= nivelesXP[nivel]:
        nivel += 1
        subioDeNivel = True


    usuarios_info.update_one(criterio,
                            {"$set":{"estadisticas.nivel":nivel}}
                            )

    if nivel != 0:
        xpAvanzado = xp - nivelesXP[nivel-1]
        xpDiferencia = nivelesXP[nivel] - nivelesXP[nivel-1]
    else:
        xpDiferencia = 100
        xpAvanzado = xp

    porcentaje = round(100*(xpAvanzado/xpDiferencia))

    usuarios_info.update_one(criterio,
                            {"$set":{"estadisticas.porcentaje":porcentaje}}
                            )


    #Aca se envia el mensaje avisando la subida del nivel en todas partes
    if subioDeNivel:
        for canalNombre in ["senderoNivel","escaladaNivel","asociadosNivel"]:
            canal = bot.fetch_channel(canales[canalNombre]["ID"])
            
            if canal.archived:
                await canal.edit(archived=False)

            embed = discord.Embed(
                title= f"¡Felicidades {nombre}!",
                description=f"¡Haz subido al nivel {nivel}!",
                color=0x35F01A
            )

            await responderMensaje(canal,embed=embed,noResponder=True)

