from funciones import *
from random import shuffle

mensajesSubidaNivel = [
[
    "Ya eres nivel **{}**, ¡Aunque tu historia apenas comienza, estoy seguro de que podrás ser de los mejores si te lo propones!",

    "Aunque no parecerá mucho, porcentualmente ¡Llegar al nivel **{}** es realmente significativo!",

    "Aquí, posándote sobre el nivel **{}**, el mundo se te abre ante infinitas posibilidades, ¡Sigue así!",

    "Solo se llega nivel **{}** una vez ¿No? ¡Así que pasalo bien!",

    "Aunque apenas eres nivel **{}**, cuando seas grande, no te olvides nunca de tus origenes"
],
[
    "Una vez oí que la gente de nivel **{}** era medio quisquillosa, me pregunto si serás la excepción...",

    "Míralo nomás, ahí avanzando por el nivel **{}**, se le nota la constancia",

    "Ah, has subido a nivel **{}**, perdón, casi no me doy cuenta. Por la molestia te doy de regalo una galleta :cookie:",

    "Como cuando estas re chill pero de la nada te llega una notificación avisandote de que ya eres nivel **{}**",

    "When haces tu momos en el canal de niveles: ¡El futuro es hoy oiste viejo! jejeje But terminas subiendo a nivel **{}**: ¡OHH mi lente de contacto! fjdbigihfdbgifbd"
],
[
    "¡AH!, qué susto, me tomaste desprevenido :eyes: ¿Uh? ¿Ya eres nivel **{}**? Sí, sí, qué bonito, sigue caminando, ¡Tú no viste nada!",

    "Mi parte favorita de llegar al nivel **{}** es que me recuerda a un 13 de octubre de 2016 a las 10:23 de la noche cuando Laura la cortesana me cambió por un... Ah, disculpa, casi me proyecto :projector: :projector: :projector: :projector:",

    "El nivel **{}**, el nivel más piola de todos",

    "Dicen que no puedes reducir a las personas a estadísticas, pero si tuviera que elegir, diria que eres nivel **{}**",

    "Si lees esto, y eres nivel **{}** y hueles a limon"
],
[
    "Amigo, ya basta, con ser nivel **{}** ya es suficiente, ve a tocar pasto",

    "¿Quieres subir nivel en la vida? Consigue un empleo, ese **{}** en tu nivel no te dará para tragar",

    "Ahí tenemos a homo nivelus, quien ahora festeja llegar al nivel **{}** sin razón lógica, sin duda, un enigma indecifrable",

    "Si lees esto, no solo significa que llegaste a nivel **{}**, significa que no estas muy lejos de ser el top 1 si no lo eres ya",

    "Laura, si lees esto, por favor regresa, te extraño, de que te sirve ser nivel **{}** si ya no estas conmigo... AHHHHHHHHH chat equivocado"

]
]

excepciones = {}

diccionarioSubidaNivel = {}
divisiones = len(mensajesSubidaNivel)
fraccion = 100//divisiones

async def niveles(message: discord.Message):
    global mensajesSubidaNivel

    #Esto genera el diccionario con valores aleatorios para despues
    for x in range(1,divisiones+1):
        direccion = int((x/divisiones)*100)
        diccionarioSubidaNivel[direccion] = mensajesSubidaNivel[x-1].copy()

        shuffle(diccionarioSubidaNivel[direccion])

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
    
    if nivel >= len(nivelesXP):
        return

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


    #Aca estan los posibles mensajes
    
    #Aca se envia el mensaje avisando la subida del nivel en todas partes
    if subioDeNivel:
        #Aca se busca el top 1, despues calcula en porcentajee 
        filtro = {"discriminador_discord": {"$nin":["Bot de los Asociados","Bot de Testeo"]}}
        
        top1 = usuarios_info.find_one(filtro,sort=[("estadisticas.xp", -1)])["estadisticas"]["nivel"]

        mensajeNum = (nivel/top1)*100
        for rango in diccionarioSubidaNivel.keys():

            #Como el nivel nunca puede ser 0, no hay problema con la cota inferior XD
            if mensajeNum > rango-fraccion and mensajeNum <= rango:
                #Esto toma el elemento aleatorio y lo borra de la lista
                mensaje = diccionarioSubidaNivel[rango].pop(0).format(nivel)

                #Si la lista se vacio, la reemplaza por otra
                if diccionarioSubidaNivel[rango] == []:
                
                    diccionarioSubidaNivel[rango] = mensajesSubidaNivel[(rango//fraccion)-1].copy()

                    shuffle(diccionarioSubidaNivel[rango])

        #Esta lista sirve para identificar bien cada canal y server
        for IDS in [["senderoNivel","Sendero"],["escaladaNivel","Escalada"],["asociadosNivel","Asociacion"]]:

            #Obtiene el objeto canal necesario
            canalNombre = IDS[0]
            try:
                canal = await bot.fetch_channel(canales[canalNombre]["ID"])
            except:
                continue

            #Aca identifica si esta en el server correcto para enviarlo
            serverID = servidores[IDS[1]]
            contenido = ""

            if message.guild.id == serverID:
                contenido = f"<@{message.author.id}>"


            embed = discord.Embed(
                title= f"¡Felicidades {nombre}!",
                description=mensaje,
                color=message.author.color
            )
            embed.set_thumbnail(url=message.author.avatar.url)

            await responderMensaje(canal,contenido,embed=embed,noResponder=True)

