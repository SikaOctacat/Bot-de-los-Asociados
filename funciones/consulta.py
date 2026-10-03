from funciones import *
from .resumen import *

canalActual = ""

async def responder(ctx,prompt):
    global contexto, textInicio,limiteContexto,canalActual

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

    descripcion = extraInfo["descripcion"]
    titulos = ",".join(extraInfo["titulos"])
    frase = extraInfo["frase"]

    
    async with ctx.typing():
        try:
            respuesta = await cliente.aio.models.generate_content(
                model = "gemma-4-26b-a4b-it",

                contents= f"""Eres el bot de la Asociación, un bot de Discord creado por Sika con la unica mision de servir a la red de servidores de La Asociacion, un conjunto de servidores de Celeste y Hollow Knight. 
                
                Habla en forma de textos cortos, como una persona normal
                
                Se irrevente y casrismatico con tus respuestas

                Un usuario, con el apodo de {nombreServidor} (quien es {nombre}) en el canal {canal} del servidor {servidor} viene y te dice: {prompt} {respondiendo}

                datos extra:

                descripción del usuario: {descripcion}
                Frase propia: {frase}
                Titulos/logros: {titulos}
                (Intenta no nombrar estas caracteristicas sino es completamente necesario para evitar ser molesto, solo tomalo en cuenta en tu mente)

                {textInicio}:
                {contexto}
                """
            )
        
            respuesta = respuesta.text

        except Exception as e:
            respuesta = "Justo ahora me quedado sin tokens, asi que ve quejarte con Sika por no recargarlos, yo me voy de sabatico hasta dentro de un rato"

            print("Ojala solo sea que nos quedamos sin tokens...")
            print(e)
        

        # Esto se encarga de enviar el mensaje sin que el Discord se queje de que es muy largo
        await responderMensaje(ctx,respuesta)
        

    #Aca se suma al historial de mensajes, intentando que no se pase a travez de resumenes
    if contexto == "":
        textInicio = "Contexto de la conversacion y mensajes previos:\n\n"
    if canalActual != canal:
        contexto += f"-----En canal {canal} del servidor {servidor}-----\n"
        canalActual = canal

    if nombreServidor == nombre:
        contexto += f"{nombreServidor}:{prompt}"+"\n"
    else:
        contexto += f"{nombreServidor}({nombre}):{prompt}"+"\n"

    contexto += f"Tu:{respuesta}"+"\n"

    if len(contexto) > limiteContexto:
        
        resumen = await resumir(contexto, promt="""Haz un resumen de este texto, tomando en cuenta que tu eres el Bot de los Asociados, por lo que refierete a el primera persona 
        
        Sigue esta estructura rigida:
        
        [Descripcion general de la situacion]
        
        [Usuario relevante]: [descripcion breve], [opinion tuya sobre el]
        (Repite con el resto)

        Si un usario te parecio lo suficientemente interesante, puedes encerrar pudes darle una descripcion mas larga y encerrarla en '^' (Pero tampoco te pases), pero solo puedes hacerlo con uno

        Finalmente, escribe la evolucion logica de tu estado a partir de ahora

        """)
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

                #Aca se supone que extrae la descripcion si al bot le gusto

                favorito = re.findall(r'^(.*?)^', resumen)

                if len(favorito) > 0:
                    favorito = favorito[0]

                    criterio2 = {"discriminador_discord":autor.name,
                                "Sin descripcion establecida":{"$ne":"Sin descripcion establecida"}}
                    
                    usuarios_info.update_one(criterio2,
                                            {"$set":{"descripcion":favorito}})
                    
                    await responderMensaje(ctx,"El bot ha hecho una descripcion de ti, puedes verla en **/usuario_info **")


            except Exception as e:
                print("Algo fallo al enviar el contexto al registro (Ah)")
                print(e)
            contexto = resumen + "\n\n"

        if len(contexto) > limiteContexto:
            corte = contexto.find("\n",-limiteContexto)
            if corte != -1:
                contexto = "..."+contexto[corte+1:]
            else:
                corte = contexto.find(" ",-limiteContexto)

            if corte != -1:
                contexto = "..."+contexto[corte+1:]
            else:
                contexto = contexto[-limiteContexto:]


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