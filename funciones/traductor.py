from .mensajes import *
from funciones import *

async def traducir(message,config):

    #Debo admiitr que este lo copie y pegue mi amiga gimena, no por flojera (Mas o menos) sino porque sin querer hice modificaciones sin guardar correctamente el codigo origina, no quera tardar mas tiempo

    #Si en un futuro reemplazare el traductor quizas me sirva tenerlo separado
    try:
        traductor = MyMemoryTranslator(source=config["idioma_entrada"], target=config["idioma_salida"])
    except Exception as e:
        print("Se me olvido como traducir xd")
        print(e)
    
    reenvio = False
    #Esto toma en cuenta si el mensaje es un reenvio
    if message.reference and (message.reference.type == discord.MessageReferenceType.forward):
        reenvio = True 
        mensaje_original = message.message_snapshots[0].content
    else:
        mensaje_original = message.content

    for embed in message.embeds:
        if embed.title:
            mensaje_original += f"\n**{embed.title}**"
        if embed.description:
            mensaje_original += f"\n{embed.description}"

    if mensaje_original.strip() == "":
        return message.content

    #¿Como va terminar esto?
    if mensaje_original.strip() != "":
        try:
            respuesta = traductor.translate(mensaje_original)
        except:
            respuesta = GoogleTranslator(source=config["idioma_entrada"][:2], target=config["idioma_salida"][:2]).translate(mensaje_original)

        #Otra invocacion demoniaca, esta vez anula los pings
        respuesta = await filtrarMensajesPings(message.guild,respuesta)
        traduccion = respuesta

    if reenvio:
        traduccion = f"> <:reenviado:1495526768679981167> **{config["reenviado"]}**\n> " + traduccion
    
    #Si el mensasje tiene una respuesta, y si esa respuesta existe, haz algo
    if message.reference and message.reference.resolved:

        salto = ""
        ref_id = await buscarMensaje(message.reference.resolved.id,buscar="espejo",ID=True)
        if not ref_id:
            contenido_ref = traductor.translate(message.reference.resolved.content)
            autor_ref = False
        else:
            contenido_ref = await buscarMensaje(ref_id)
            autor_ref = await buscarMensaje(ref_id,buscar="autor",ID=True)
            ref_canal_id = await buscarMensaje(ref_id,buscar="canal",ID=True)
            server_id = message.guild.id

            url_mensaje = f"https://discord.com/channels/{server_id}/{ref_canal_id}/{ref_id}"
            salto = f"\n> ([{config['boton']}]({url_mensaje}))"



        # Si el mensaje ya tiene una respuesta, la elimina
        contenido_ref = re.sub(r'^>.*$', '', contenido_ref, flags=re.MULTILINE).strip()

        if contenido_ref != "":
            limite = 100
            contenido_ref = contenido_ref[:limite]
            contenido_ref = contenido_ref.split("\n")[0]

            if len(contenido_ref) == limite:
                contenido_ref += "..."

            #Esto evita que se lleno todo de pings xd
            contenido_ref = await filtrarMensajesPings(message.guild,contenido_ref)
            #Esto evita que los enlaces de desplieguen en las respuestas
            contenido_ref = re.sub(r'(https?://[^\s]+)', r'<\1>', contenido_ref)
        else:
            contenido_ref = config["archivo"]
        
        if message.reference.resolved.webhook_id and autor_ref:
            traduccion = f"> {config['respuesta']} <@{autor_ref}>: *{contenido_ref}* {salto}\n{traduccion}"
        else:
            autor_nombre = message.reference.resolved.author.display_name
            traduccion = f"> {config['respuesta']} **{autor_nombre}**: *{contenido_ref}* {salto}\n{traduccion}"

    
    return traduccion