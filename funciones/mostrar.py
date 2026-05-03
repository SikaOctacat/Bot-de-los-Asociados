from funciones import *

paginaActual = 0
botones = []

for texto in ["Anterior","Siguiente"]:
    boton = discord.ui.Button(
        label= texto,
        style= discord.ButtonStyle.primary,
        custom_id= texto.lower()
    )
    botones.append(boton)

async def rankingEstrellas(ctx=False):
    global paginaActual,botones
    ventana = 5
    cursor = usuarios_info.find().sort([("estrellas",-1)])

    ranking = list(cursor)

    if not ranking and ctx:
        ctx.send("Todavia no hay nadie en el ranking ⭐")
        return
    
    nombres = [str(x["discriminador_discord"]).replace(" ","") for x in ranking]
    estrellas = [str(x["estrellas"]) for x in ranking]

    tope = ventana+paginaActual*ventana
    if tope > len(nombres):
        tope = len(nombres)

    rango = range(paginaActual*ventana,tope)

    anchoIzquierda = max([len(x) for x in nombres[rango.start:tope]])

    if anchoIzquierda < len("Usuario"):
        anchoIzquierda = len("Usuario") 

    anchoCentro = len(str(len(ranking)))

    if anchoCentro < len("Top"):
        anchoCentro = len("Top") 


    resultado = "**`"+"Usuario".rjust(anchoIzquierda)+"|"+"Top".center(anchoCentro)+"|"+"⭐`**\n"
    for i in rango:

        usuario = nombres[i].rjust(anchoIzquierda)
        top = str(i+1).center(anchoCentro)

        puntuacion = estrellas[i]
        if len(puntuacion) == 1:
            puntuacion += " "

        resultado += f"**`{usuario}|{top}|{puntuacion}`**\n"

    embed = discord.Embed(
        title="Top de estrellas 🏆",
        description=resultado,
        color=0xFFFF00
    )

    embed.set_footer(text="Solo se suma si los mensajes poseen archivos o links")

    if not ctx:
        return embed

    async def cambiarPagina(interaction):
            global paginaActual,botones

            match interaction.data["custom_id"]:
                case "siguiente": paginaActual += 1
                case "anterior": paginaActual -= 1
            
            view = discord.ui.View()
            for boton in botones:
                if boton.label == "Anterior" and paginaActual < 1:
                    continue

                if boton.label == "Siguiente" and (paginaActual+1)*ventana > len(nombres):
                    continue

                boton.callback = cambiarPagina

                view.add_item(boton)

            embed =  await rankingEstrellas()
            await interaction.response.edit_message(embed=embed,view=view)

    view = discord.ui.View()

    boton = botones[1]
    boton.callback = cambiarPagina

    view.add_item(boton)
    
    await ctx.send(embed=embed,view=view)

async def usuarioInfo(interaction,objetivo=None):

    ctx = False
    if objetivo:
        if isinstance(objetivo,str):
            nombre = objetivo
            color = 0xFFA500
            foto = ""
            ctx = True
        else:
            nombre = objetivo.name
            color = objetivo.color
            foto = objetivo.avatar.url
    else:
        nombre= interaction.user.name
        color = interaction.user.color
        foto = interaction.user.avatar.url

    cursor = usuarios_info.find({"discriminador_discord":nombre})

    usuario = list(cursor)

    if usuario == []:
        if ctx:
            interaction.send("No estas registrado en la base datos todavia")
        else:
            interaction.followup.send("No estas registrado en la base datos todavia")
        return
    else:
        usuario = usuario[0]

    alias = list(usuario["aliases"])
    if alias == []:
        alias = "Sin alias conocidos"
    else:
        alias = ", ".join(alias)
    
    titulo = ", ".join(list(usuario["titulos"]))

    redes = "\n"
    for elemento in usuario["redes"].items():
        redes += f"* **{elemento[0]}**: _{elemento[1]}_\n"

    resultado = f'**Primera aparición:** _{usuario["primera_aparicion"]}_\n**Aliases:** _{alias}_\n**Frase:** _{usuario["frase"].replace("'",'"')}_\n**Titulos:** _{titulo}_\n\n{usuario["descripcion"]} \n\n⭐:{usuario["estrellas"]} \n\n**Redes:** {redes}'

    try:
        resultado += f'\n***El usuario sugirió:***\n "{usuario["sugerencia"]}"'
    except:
        pass

    embed = discord.Embed(
        title= usuario["nombre"],
        description=resultado,
        color=color
    )

    if foto != "":
        embed.set_thumbnail(url=foto)

    embed.set_footer(text="Esta información es publica y es elegida por la administración.")

    if ctx:
        await interaction.send(embed=embed)
    else:
        await interaction.followup.send(embed=embed)
