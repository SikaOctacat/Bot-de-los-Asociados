from funciones import *
from funciones.traductor import traducir
from funciones.coneccion import conectar
from funciones.mensajes import *
from funciones.consulta import *

# Quizas me hubiera sido mas utilo haber conocido esta funcion antes, no importa
#El arroba lo que hace es algo asi como agregarle una funcion ya existente al principo de otra, en en este caso on_ready... Bastante curioso
@bot.event
async def on_ready():
    print(f"Buenas gente, aca estamos como {bot.user} sirviendo a la causa!")

#Supongo que cuando el bot recibe un mensaje, ejecuta esta funcion
#Ahora que lo veo mejor, message se supone que va ser un objeto entero con mucha info, no solo un string, lo cual tiene sentido
@bot.event
async def on_message(message):

    #Esto evita que bot no se cofunda consigo mismo, me suele pasar cuando me volteo y me miro al espejo
    if (message.webhook_id in lista_webhooks) or (bot.user == message.author):
        return

    #Esta cosa lo que hace es crear la tarea de la traduccion, ya que podria ser interrumpida por otros elementos
    for conexion in conexiones.keys():
        for canal in conexiones[conexion]:
            if message.channel.id == canales[canal]["ID"]:
                traducciones_activas[message.id] = asyncio.create_task(conectar(message,conexiones[conexion]))
                
                try:
                    await traducciones_activas[message.id]
                except asyncio.CancelledError:
                    print(f"¿Porque tanto apuro? La traduccion de {message.id} fue cancelada...")
                except Exception as e:
                    print("La tarea fallo con exito (O algo así)")
                    print(e)
                finally:
                    traducciones_activas.pop(message.id,None)

                break

    #Aca reacciona el bot si lo mencionan, o le responden directamente, reutilzando el codigo del comando
    mencionado = bot.user in message.mentions
    respondido = (message.reference and message.reference.resolved) and message.reference.resolved == bot.user

    if mencionado or respondido:
        ctx = await bot.get_context(message)
        
        await consultar(ctx,message.content)

    
    #Esto hace que el bot escuche la funcion, eh, supongo que lo que hace es hacerlo esperar hasta que todo se cumpla
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    
    await editarMensajeEspejo(before,after)
    

@bot.event
async def on_message_delete(message):

    await borrarMensajeEspejo(message)

@bot.event
async def on_raw_reaction_add(payload):

    await reaccionarMensajeEspejo(payload)

@bot.event
async def on_raw_reaction_remove(payload):

    await reaccionarMensajeEspejo(payload,borrar=True)

@bot.command(name="pregunta")
async def on_comand(ctx,*,consulta):

    if not consulta:
        return

    await consultar(ctx,consulta)

#Esto hace que Render no piense que mi bot se tomo vacaciones y lo siga obligando a trabajar por el resto de la eternidad!!!
app = Flask('')

@app.route('/')
def home():
    return "Sigo aca, no hace falta que me lo recuerdes..."

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(llave_Discord)