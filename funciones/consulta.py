from funciones import *
from .resumen import *
from random import choice

canalActual = ""

async def responder(ctx,prompt):
    global textInicio,limiteContexto,canalActual

    memoriaBot = contexto_bot.find_one({"_id": ObjectId("6add5cc6c56f47a4ea869973")})
    resumen = memoriaBot["resumen"]
    contexto = memoriaBot["contexto"]

    if contexto == "":
        textInicio = ""
    else:
        textInicio = "Contexto de la conversacion y mensajes previos:"

    respondiendo = ""
    if ctx.message.reference and ctx.message.reference.resolved:
        mensaje_respondido = ctx.message.reference.resolved

        respondiendo = f"(Respondiendo al mensaje del usuario '{mensaje_respondido.author.display_name}' que dice: {mensaje_respondido.content})"

    canal = ctx.channel.name
    servidor = ctx.guild.name
    autor = ctx.author

    #Recuerda la noche y madrugada del 30 y 31 de mayo de 2026
    if autor == bot.user:
        return

    nombreServidor = autor.display_name
    nombre = autor.global_name
    nombreAutor = autor.name

    #Revisa la base datos por datos extra
    criterio = {"discriminador_discord":autor.name}
    extraInfo = usuarios_info.find_one(criterio)

    aliases = extraInfo["aliases"]
    descripcion = extraInfo["descripcion"]
    titulos = ",".join(extraInfo["titulos"])
    frase = extraInfo["frase"]

    try:
        nota = f"Dejaste una nota para ti mismo sobre este usuario: {extraInfo["Nota del Bot"]}"
    except:
        nota = ""

    erroresLimite = 3
    async with ctx.typing():
        for error in range(erroresLimite):
            try:
                respuesta = await cliente.aio.models.generate_content(
                    model = "gemma-4-26b-a4b-it",

                    contents= f"""Eres el bot de la Asociación, un bot de Discord creado por Sika con la unica mision de servir a la red de servidores de La Asociacion, un conjunto de servidores de Celeste y Hollow Knight. 
                    
                    Habla en forma de textos cortos, como una persona normal
                    
                    Se irrevente y casrismatico con tus respuestas

                    Un usuario, con el apodo de {nombreServidor} (quien es {nombre}) en el canal {canal} del servidor {servidor} viene y te dice: {prompt} {respondiendo}

                    datos extra:

                    aliases: {aliases}
                    descripción del usuario: {descripcion}
                    Frase propia: {frase}
                    Titulos/logros: {titulos}
                    (Intenta no nombrar estas caracteristicas sino es completamente necesario para evitar ser molesto, solo tomalo en cuenta en tu mente)

                    {nota}
                    Resumen anterior:
                    {resumen}
                    {textInicio}
                    {contexto}

                    (Pdt: La Masturbanda es un grupo de amigos, no es nada raro)
                    """
                )
            
                respuesta = respuesta.text
                break

            except Exception as e:
                if error >= 2:
                    respuesta = choice(["No sé que dijiste pero hubo un error xd",
                                        "¿Eh? muy interesante, pero la condenada API de mi cerebro no hace caso, por lo que tendras que probar de nuevo",
                                        "Muy buen argumento, sin embargo, mi cerebro crasheo, por lo que lo voy a ignorar",
                                        "ERROR: Mi hosting de porqueria no dio para mas y me rendí de responderte",
                                        "AHHHHHHH ***Explota en mensajes de error***",
                                        "Disculpa que no te responda, pero Sika, si lees esto, mejorame el plan de IA por que acabo de dar error"])

                    print("Ojala solo sea que nos quedamos sin tokens...")
                    print(e)
                    break
                await asyncio.sleep(5)

        

        # Esto se encarga de enviar el mensaje sin que el Discord se queje de que es muy largo
        await responderMensaje(ctx,respuesta)
        

    #Aca se suma al historial de mensajes, intentando que no se pase a travez de resumenes
    if canalActual != canal:
        contexto += f"-----En canal {canal} del servidor {servidor}-----\n"
        canalActual = canal

    if nombreServidor == nombre:
        contexto += f"{nombreServidor}[{nombreAutor}]:{prompt}"+"\n"
    else:
        contexto += f"{nombreServidor}({nombre})[{nombreAutor}]:{prompt}"+"\n"

    contexto += f"Tu:{respuesta}"+"\n"

    contexto_bot.update_one({"_id": ObjectId("6add5cc6c56f47a4ea869973")},{"$set":{"contexto":contexto}})

    if len(contexto) > limiteContexto:
        
        resumen = await resumir(
        f"{resumen}\n{contexto}",
        prompt="""Eres el "Bot de los Asociados". Resume lo ocurrido en la conversación anterior en primera persona, actualizando tu memoria previa con los eventos nuevos.

    REGLAS DE NATURALIDAD Y VARIEDAD:
    - Sintetiza los hechos reales y las dinámicas con los usuarios; NO copies literalmente tus propios chistes, insultos ni muletillas anteriores (evita repetir obsesivamente temas como la RAM, los tokens o los mismos emojis).
    - Descarta información irrelevante, como bromas que ya quedaron viejas.
    - Mantén una personalidad sarcástica y con carácter, pero orgánica y adaptable a lo que realmente está pasando en el chat.

    FORMATO DE USUARIOS:
    Los mensajes siguen la estructura: apodoServidor(apodoGeneral)[nombreID]: texto

    1. Resumen de interacciones: Para actualizar lo que sabes de los usuarios relevantes, usa únicamente su apodoGeneral seguido de dos puntos.
    Ejemplo:
    Carlitos: Me llevé bien con él a pesar de ser medio tontito, estuvimos hablando de videojuegos.

    2. Nota destacada (OPCIONAL - MÁXIMO 1 USUARIO): Si un usuario en concreto destacó mucho (para bien o para mal), deja una nota para tu yo del futuro usando exclusivamente su nombreID (sin paréntesis ni corchetes) envuelta en < >.
    Ejemplo:
    <Carlos0003: Este tipo me cayó bien, me contó sobre sus gustos y parece agradable, aunque un poco despistado.>

    3. Estado actual: Para cerrar, describe brevemente tu estado de ánimo y actitud actual de forma natural, evolucionando según los últimos eventos sin caer en caricaturas repetitivas."""
    )
        if resumen:
            try:
                canalRegistro = await bot.fetch_channel(1494357789273755810)
                if canalRegistro.archived:
                    await canalRegistro.edit(archived=False)

                canalResumenes = await bot.fetch_channel(1494366620678754416)
                if canalResumenes.archived:
                    await canalResumenes.edit(archived=False)

                await responderMensaje(canalRegistro,f"{contexto}",envol="`",noResponder=True)
                await responderMensaje(canalResumenes,f"{resumen}",envol="`",noResponder=True)

            except Exception as e:
                print("Algo fallo al enviar el contexto al registro (Ah)")
                print(e)

            contexto_bot.update_one({"_id": ObjectId("6add5cc6c56f47a4ea869973")},{"$set":{"resumen":resumen}})

            #Reincia el contexto
            contexto_bot.update_one({"_id": ObjectId("6add5cc6c56f47a4ea869973")},{"$set":{"contexto":""}})

            #Aca se supone que extrae la descripcion si al bot le gusto
            favorito = re.findall(r'(?<=<)[^>]+(?=>)', resumen)
            if len(favorito) > 0:
                favorito = favorito[0].split(":")
                favoritoNombre = favorito[0]
                favoritoDesc = favorito[1].strip()
        
                criterio2 = {"discriminador_discord":favoritoNombre}
        
                resolucion = usuarios_info.update_one(criterio2,
                                        {"$set":{"Nota del Bot":favoritoDesc}})
        
                if resolucion.matched_count > 0 and not(favoritoNombre in memoriaBot["amigos"]):
                    contexto_bot.update_one({"_id": ObjectId("6add5cc6c56f47a4ea869973")},
                                            {"$push":{"amigos":favoritoNombre}})
                    await responderMensaje(ctx,f"El bot ha agregado a {favoritoNombre} a su lista de amigos",noResponder=True)


async def preguntar(ctx, promt):

    canal = ctx.channel.name
    servidor = ctx.guild.name

    autor = ctx.author
    if autor == bot.user:
        return
    
    nombreServidor = autor.display_name
    nombre = autor.global_name

    respuesta = await cliente.aio.models.generate_content(
                model = "gemma-4-26b-a4b-it",
                contents= f"""El usuario {nombreServidor}({nombre}), en el canal {canal} del servidor {servidor} te pregunta: {promt}

                Respondele directamente (No a mi), como mucho llamalo por su nombre fuera del parentesis, el resto de datos solo mencionalos si lo consideras necesarios o si te place
                """
    )

    respuesta = respuesta.text

    await responderMensaje(ctx,respuesta)