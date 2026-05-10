from funciones import *

async def niveles(message):

    criterio = {"discriminador_discord":message.author.name}
    
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

    
    while xp >= nivelesXP[nivel]:
        nivel += 1
    else:
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