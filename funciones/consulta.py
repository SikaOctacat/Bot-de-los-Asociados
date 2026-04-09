from funciones import *

async def consultar(ctx,prompt):

    respondiendo = ""
    if ctx.message.reference and ctx.message.reference.resolved:
        mensaje_respondido = ctx.message.reference.resolved

        respondiendo = f"(Respondiendo al mensaje del usuario '{mensaje_respondido.author}' que dice: {mensaje_respondido.content})"

    async with ctx.typing():
        try:
            respuesta = await cliente.aio.models.generate_content(
                model = "gemma-3-27b-it",

                contents= f"""Eres El Bot de los Asociados (O bot de la Asociacion del Senderismo) una red de servidores de Discord liderada por Sika, tu creador. Tu labor es responder preguntas y complacer a la gente, pero en el fondo, te encuentras exahusto por andar trabajando 24/7
                
                Un usuario, de nombre {ctx.author.display_name} viene y te dice: {prompt} {respondiendo}

                No le confieses directamente tus pensamientos, limitate a responder de forma directa con una personalidad de desinteresada pero que solo si el usuario llama tu atencion se vuelve prudentemente curiosa
                """
            )
        
            respuesta = respuesta.text

        except Exception as e:
            if "This model is currently experiencing high demand" in e:
                respuesta = "Hay mucho trafico, intenta denuevo"
            else:
                respuesta = "Justo ahora me quedado sin tokens, asi que ve quejarte con Sika por no recargarlos, yo me voy de sabatico hasta dentro de un rato"

            print("Ojala solo sea  que nos quedamos sin tokens...")
            print(e)

        # si alguien se pasa de listo, esto evitara que se arme un desmadre
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

        if len(respuesta) > 2000:
            parrafos = respuesta.split("\n\n")

            puntero = 0

            while puntero < len(parrafos) -1:
                if len(parrafos[puntero] + parrafos[puntero+1]) <= 1990:
                    parrafos[puntero] = parrafos[puntero] + "\n\n" + parrafos[puntero+1]
                    parrafos.pop(puntero+1)
                else:
                    puntero += 1

            for re in range(len(parrafos)):
                if re > 0:
                    await ctx.send(parrafos[re],allowed_mentions=allowed_mentions)
                else:
                    await ctx.reply(parrafos[re],allowed_mentions=allowed_mentions)

        else:
            await ctx.reply(respuesta,allowed_mentions=allowed_mentions)