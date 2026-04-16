from funciones import *

async def resumir(texto):

    respuesta = False
    try:
        resumen = await co.chat(message=f"Comprime este texto en un parrafo resumido, manten el tiempo verbal y la persona, no me respondas a mi, solo comprime:\n\n {texto}")
        respuesta = resumen.text
    except Exception as e:
        print(e)

    return respuesta