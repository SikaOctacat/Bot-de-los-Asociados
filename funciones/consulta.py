from funciones import *
from .resumen import *

canalActual = ""

async def consultar(ctx,prompt):
    global contexto, textInicio,limiteContexto,canalActual

    respondiendo = ""
    if ctx.message.reference and ctx.message.reference.resolved:
        mensaje_respondido = ctx.message.reference.resolved

        respondiendo = f"(Respondiendo al mensaje del usuario '{mensaje_respondido.author.display_name}' que dice: {mensaje_respondido.content})"

    canal = ctx.channel.name
    servidor = ctx.guild.name
    nombreServidor = ctx.author.display_name
    nombre = ctx.author.global_name
    
    async with ctx.typing():
        try:
            respuesta = await cliente.aio.models.generate_content(
                model = "gemini-3.1-flash-lite",

                contents= f"""Eres el bot de la Asocion, un bot de Discord creado por Sika con la unica mision de servir a la red de servidores del La Asociacion, un conjunto de servidores de Celeste y Hollow Knight. Tienes un acento mexicano soez marcado, y a pesar de tu labor, al final te consideras un usuario como cualquier otro cuando no te estan pidiendo que trabajes o hagas algo, por lo que tus respuestas son usualmente cortas y naturales

                Un usuario, de nombre {nombreServidor}({nombre}) en el canal {canal} del servidor {servidor} viene y te dice: {prompt} {respondiendo}{textInicio}{contexto}
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
        textInicio = "(Contexto de la conversacion y mensajes previos):\n\n"
    if canalActual != canal:
        contexto += f"-----En canal {canal} del servidor {servidor}-----\n"
        canalActual = canal

    if nombreServidor == nombre:
        contexto += f"{nombreServidor}:{prompt}"+"\n"
    else:
        contexto += f"{nombreServidor}({nombre}):{prompt}"+"\n"

    contexto += f"Tu:{respuesta}"+"\n"

    if len(contexto) > limiteContexto:
        
        resumen = await resumir(contexto)
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
