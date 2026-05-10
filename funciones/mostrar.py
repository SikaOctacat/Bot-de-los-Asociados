from funciones import *

paginaActual = 0
botones = []
seleccion = "estrellas"

for texto in ["Anterior","Siguiente"]:
    boton = discord.ui.Button(
        label= texto,
        style= discord.ButtonStyle.primary,
        custom_id= texto.lower()
    )
    botones.append(boton)

async def ranking(ctx=False,select="estrellas"):
    global paginaActual,botones,seleccion

    if select != seleccion:
        seleccion = select
    ventana = 10

    selectInfo = {
        "estrellas": {"emoji":"⭐","color":0xFFFF00,"pie":"Solo se suma si los mensajes poseen archivos o links"},
        "corazones": {"emoji":"❤️","color":0xFF0000},
        "nivel": {"emoji":"🔝","color":0xC800FF},
        "descontextualizaciones": {"emoji":"📸","color":0xCCCCCC}
        
    }

    cursor = usuarios_info.find().sort([(f"estadisticas.{select}",-1)])

    listaTop = list(cursor)

    if not listaTop and ctx:
        ctx.send(f"Todavia no hay nadie en el ranking {selectInfo[select]["emoji"]}")
        return
    
    nombres = [str(x["discriminador_discord"]).replace(" ","") for x in listaTop]
    valores = [str(x["estadisticas"][select]) for x in listaTop]

    tope = ventana+paginaActual*ventana
    if tope > len(nombres):
        tope = len(nombres)

    rango = range(paginaActual*ventana,tope)

    anchoIzquierda = max([len(x) for x in nombres[rango.start:tope]])

    if anchoIzquierda < len("Usuario"):
        anchoIzquierda = len("Usuario") 

    anchoCentro = len(str(len(listaTop)))

    if anchoCentro < len("Top"):
        anchoCentro = len("Top") 


    resultado = "**`"+"Usuario".rjust(anchoIzquierda)+"|"+"Top".center(anchoCentro)+"|"+f"{selectInfo[select]["emoji"]}`**\n"
    for i in rango:

        usuario = nombres[i].rjust(anchoIzquierda)
        top = str(i+1).center(anchoCentro)

        puntuacion = valores[i]
        if len(puntuacion) == 1:
            puntuacion += " "

        resultado += f"**`{usuario}|{top}|{puntuacion}`**\n"

    embed = discord.Embed(
        title=f"Top de {select} 🏆",
        description=resultado,
        color=selectInfo[select]["color"]
    )

    if "pie" in selectInfo[select]:
        embed.set_footer(text=selectInfo[select]["pie"])

    if not ctx:
        return embed

    async def cambiarPagina(interaction):
            global paginaActual,botones,seleccion

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

            embed =  await ranking(select=seleccion)
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

    nivel = 0
    xp = 0
    estadisticas = "\n"
    for elemento in usuario["estadisticas"].items():
        if elemento[0] == "porcentaje":
            estadisticas += f"* **{elemento[0]}**: _{elemento[1]}%_\n"
            if nivel > 0: resta = nivelesXP[nivel-1] 
            else: resta = 0

            estadisticas += f"{xp-resta}/{nivelesXP[nivel]-resta}xp ({nivelesXP[nivel]-xp}xp restante para subir de nivel)\n"
            estadisticas +=f"{crearCargador(elemento[1])}\n"
        else:
            estadisticas += f"* **{elemento[0]}**: _{elemento[1]}_\n"
            match elemento[0]:
                case "xp":
                    xp = elemento[1]
                case "nivel":
                    nivel = elemento[1]

    redes = "\n"
    for elemento in usuario["redes"].items():
        redes += f"* **{elemento[0]}**: _{elemento[1]}_\n"
    
    

    resultado = f'**Primera aparición:** _{usuario["primera_aparicion"]}_\n**Aliases:** _{alias}_\n**Frase:** _{usuario["frase"].replace("'",'"')}_\n**Titulos:** _{titulo}_\n\n{usuario["descripcion"]} \n\n **Estadisticas:** {estadisticas} \n**Redes:** {redes}'

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
