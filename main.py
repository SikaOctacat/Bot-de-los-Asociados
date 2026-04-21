from funciones import *
from funciones.traductor import traducir
from funciones.coneccion import conectar
from funciones.mensajes import *
from funciones.resumen import *
from funciones.consulta import consultar
from funciones.guardar import *
from funciones import consulta


# Quizas me hubiera sido mas utilo haber conocido esta funcion antes, no importa
#El arroba lo que hace es algo asi como agregarle una funcion ya existente al principo de otra, en en este caso on_ready... Bastante curioso
@bot.event
async def on_ready():
    print(f"Buenas gente, aca estamos como {bot.user} sirviendo a la causa!")

#Supongo que cuando el bot recibe un mensaje, ejecuta esta funcion
#Ahora que lo veo mejor, message se supone que va ser un objeto entero con mucha info, no solo un string, lo cual tiene sentido
@bot.event
async def on_message(message):
    global traduccionesIniciadas,traduccionActual
    #Esto evita que bot no se cofunda consigo mismo, me suele pasar cuando me volteo y me miro al espejo
    if message.webhook_id in lista_webhooks:
            return

    if bot.user == message.author:
        if not(message.content.endswith(marca)):
            return

    #Esta cosa lo que hace es crear la tarea de la traduccion, ya que podria ser interrumpida por otros elementos
    for conexion in conexiones.keys():
        for canal in conexiones[conexion]:
            if message.channel.id == canales[canal]["ID"]:
                traduccionesActivas[message.id] = asyncio.create_task(conectar(message,conexiones[conexion]))
                
                try:
                    await traduccionesActivas[message.id]
                except asyncio.CancelledError:
                    print(f"¿Porque tanto apuro? La traduccion de {message.id} fue cancelada...")
                except Exception as e:
                    print("La tarea fallo con exito (O algo así)")
                    print(e)
                finally:
                    traduccionesActivas.pop(message.id,None)

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

    await archivo(payload)
    await fueraDeContexto(payload)



@bot.event
async def on_raw_reaction_remove(payload):

    await reaccionarMensajeEspejo(payload,borrar=True)

@bot.command()
async def sync(ctx):
    if ctx.author.id == 612445390314274826:
        try:
            await tree.sync()
            await ctx.send("Los comandos slash han sido sincronizados, Sika")
        except Exception as e:
            await ctx.send("Los comandos no pudieron sincronizarce, Sika")
            print(e)
    else:   
        await ctx.send("Quien sos vos? LOL, conseguite una vida pibe, no tienes los permisos")


@bot.command(name="pregunta")
async def on_comand(ctx,*,consulta):

    if not consulta:
        return

    await consultar(ctx,consulta)

@tree.command(name="resume",description="Pidele al bot que resuma un texto por ti")
async def pregunta(interaction: discord.Interaction,texto:str):
    await interaction.response.defer()

    resumen = await resumir(texto)
    await responderMensaje(interaction.followup,resumen)

@bot.command(name="resume")
async def on_comand(ctx,*,consulta):

    if not consulta:
        return
    
    respuesta = await resumir(consulta)
    if respuesta:
        await responderMensaje(ctx,respuesta)
    else:
        await ctx.reply("Justo ahora no puedo resumir"+marca)

@bot.command(name="contexto")
async def on_comand(ctx):

    if ctx.author.id != 612445390314274826:
        return

    for _ in range(10):
        if consulta.contexto and consulta.contexto != "":
            await responderMensaje(ctx,consulta.contexto,limite=1990,envol="`")
            return
            
        await asyncio.sleep(0.5)
        

    await ctx.reply("No tengo contexto todavia..."+marca)



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