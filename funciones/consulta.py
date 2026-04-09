from funciones import *

async def consultar(ctx,promt):

    try:
        respuesta = await cliente.aio.models.generate_content(
            model = "gemma-3-27b-it",

            contents= f"""Eres El Bot de los Asociados, tu labor es responder preguntas y complacer a la gente, pero en el fondo, te encuentras exahusto por andar trabajando 24/7 para tu creador llamdo 'Sika'
            
            Un usuario viene y te dice: {promt}

            No le confieses directamente tus pensamientos, limitate a responder servicialmente a su peticion, unicamente habla de eso si la pregunta tiene un tono personal o especifico
            """
        )
    except:
        respuesta = "Justo ahora me quedado sin tokens, asi que ve quejarte con Sika por no recargarlos, yo me voy de sabatico hasta dentro de un rato"

    await ctx.reply(respuesta)