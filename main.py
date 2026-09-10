from funciones import *
from funciones.traductor import traducir
from funciones.coneccion import conectar
from funciones.mensajes import *
from funciones.resumen import *
from funciones.consulta import *
from funciones.guardar import *
from funciones.mostrar import *
from funciones.determinar import *
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
        
    await niveles(message)

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
    mencionado = f"<@{bot.user.id}>" in message.content or f"<@!{bot.user.id}>" in message.content
    respondido = (message.reference and message.reference.resolved) and (message.reference.resolved.author == bot.user and marca in message.reference.resolved.content)

    if respondido or mencionado:

        ctx = await bot.get_context(message)
        
        await responder(ctx,message.content)

    
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

    await gestionarReacciones(payload,suma=1)



@bot.event
async def on_raw_reaction_remove(payload):

    await reaccionarMensajeEspejo(payload,borrar=True)
    await gestionarReacciones(payload,suma=-1)


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

@bot.command(name="servers")
async def on_comand(ctx):
    servidores = "Lista de sevidores\n"
    for guild in bot.guilds:
        servidores += f"\nNombre: {guild.name}\nID: {guild.id}\n"
    await ctx.reply(servidores)

@bot.command(name="ban")
async def on_comand(ctx, usuario: discord.Member,*,razon: str="No se dio una razon"):

    if not(ctx.author.id == 612445390314274826):
        return

    await usuario.ban(reason=razon)
    await ctx.send(f"El usuario **{usuario.name}** ha sido baneado.\n\nRazon: *{razon}*")

@bot.command(name="banGlobal")
async def ban_global(ctx, usuario: discord.User,*,razon: str="No se dio una razon"):

    if not(ctx.author.id == 612445390314274826):
        return

    servidoresLista = ""
    for guild in bot.guilds:
        try:
            await guild.ban(usuario,reason=razon)
            servidoresLista += f"{guild.name}, "

        except (discord.Forbidden, discord.HTTPException):
            continue
        
    await ctx.send(f"El usuario **{usuario.name}** ha sido baneado de los servidores {servidoresLista}\n\nRazon: *{razon}*")

# Manejo de error específico si la ID o mención no se encuentra
@ban_global.error
async def ban_global_error(ctx, error):
    if isinstance(error, commands.UserNotFound):
        await ctx.send("No se encontró ningún usuario con esa ID o mención.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Debes proporcionar una mención o una ID válida.")


@bot.command(name="pregunta")
async def on_comand(ctx,*,pregunta):

    if not pregunta:
        return

    await preguntar(ctx,pregunta)

@tree.command(name="pregunta",description="Preguntale algo al bot")
async def pregunta(interaction: discord.Interaction,texto:str):
    await interaction.response.defer()

    if not texto:
        return
    
    ctx = await bot.get_context(interaction)

    await preguntar(ctx,texto)

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

@bot.command(name="actualizarNiveles")
async def on_comand(ctx):
    if ctx.author.id != 612445390314274826:
        return

    usuarios = list(usuarios_info.find())

    for usuario in usuarios:

        nombre = usuario["discriminador_discord"]
        criterio = {"discriminador_discord":nombre}


        xp = usuario["estadisticas"]["xp"]
        nivel = 0
        for _ in nivelesXP:
            if nivelesXP[nivel] > xp:
                break
            nivel += 1

        
        if nivel == 0:
            xpAnterior = 0
        else:
            xpAnterior = nivelesXP[nivel-1]
        
        porcentaje = round( 100*((xp-xpAnterior)/(nivelesXP[nivel]-xpAnterior)))

        usuarios_info.update_one(criterio,
                                {"$set":{"estadisticas.nivel":nivel,
                                        "estadisticas.porcentaje":porcentaje
                                        }}
                                )
    await ctx.reply("Niveles actualizados con exito!")

@tree.command(name="top",description="Muestra el top de usuarios con mas estrellas del servidor")
@app_commands.choices(categoria=[
    app_commands.Choice(name="Estrellas",value="estrellas"),
    app_commands.Choice(name="Corazones",value="corazones"),
    app_commands.Choice(name="Niveles",value="xp"),
    app_commands.Choice(name="Descontextualizaciones",value="descontextualizaciones")
])
async def on_comand(interaction: discord.Interaction,categoria: app_commands.Choice[str]):
    await interaction.response.defer()

    await ranking(interaction.followup,categoria.value)

@bot.command(name="usuario_info")
async def on_command(ctx,consulta=None):
    if consulta == None:
        return

    await usuarioInfo(ctx,consulta)

@tree.command(name="usuario_info",description="Observa información en la base de datos de ti mismo o de otro usuario")
async def on_command(interaction:discord.Interaction, usuario: typing.Optional[discord.Member]=None):
    await interaction.response.defer()

    await usuarioInfo(interaction,usuario)

@tree.command(name="sugerir_info",description="Sugiere información para modificar o agregar a tu ficha de usuario")
async def on_command(interaction:discord.Interaction,texto:str):
    await interaction.response.defer()

    resultado = usuarios_info.update_one(
        {"discriminador_discord": interaction.user.name},
        {"$set": {"sugerencia":texto}},
        upsert=False
    )

    if resultado.matched_count > 0:
        await interaction.followup.send("Sugerencia subida con exito")
    else:
        await interaction.followup.send("No estas en la base de datos todavia")

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