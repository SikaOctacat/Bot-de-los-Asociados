from funciones import *

botones = []

for texto in ["Anterior","Siguiente"]:
    boton = discord.ui.Button(
        label= texto,
        style= discord.ButtonStyle.primary,
        custom_id= texto.lower()
    )
    botones.append(boton)

async def ranking(ctx=False,select="estrellas",paginaActual=0):
    global botones
    ventana = 10

    selectInfo = {
        "estrellas": {"emoji":"⭐","color":0xFFFF00,"pie":"Solo se suma si los mensajes poseen archivos o links"},
        "corazones": {"emoji":"❤️","color":0xFF0000},
        "nivel": {"emoji":"🔝","color":0xC800FF},
        "descontextualizaciones": {"emoji":"📸","color":0xCCCCCC}
        
    }

    filtro = {"discriminador_discord": {"$nin":["Bot de los Asociados","Bot de Testeo"]}}
    cursor = usuarios_info.find(filtro).sort(f"estadisticas.{select}",-1)

    listaTop = list(cursor)

    if not listaTop:
        if ctx:
            ctx.send(f"Todavia no hay nadie en este ranking")
        return
    


    nombres = [str(x["nombre"]).replace(" ","") for x in listaTop]

    if select == "xp":
        embed = await rankingNiveles(listaTop,nombres,paginaActual)
    else:

        valores = [str(x["estadisticas"][select]) for x in listaTop]

        tope = ventana+(paginaActual*ventana)
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

    #A esto le faltan comentarios xD
    async def cambiarPagina(interaction):
            global botones
            #Primera vez en la vida usando el nonlocal, pemite usar una variable de una funcion superior
            nonlocal paginaActual,select
            match interaction.data["custom_id"]:
                case "siguiente": paginaActual += 1
                case "anterior": paginaActual -= 1

            #El view es donde van los botones, vale
            view = discord.ui.View()
            for boton in botones:
                if boton.label == "Anterior" and paginaActual < 1:
                    continue

                try:
                    limite = len(embed)
                except:
                    limite = len(nombres)

                #Veo que el limite es limite total de nombres y no el de paginas, por eso no entendia ae
                if boton.label == "Siguiente" and (paginaActual+1)*ventana > limite:
                    continue

                boton.callback = cambiarPagina

                view.add_item(boton)

            embed =  await ranking(select=select,paginaActual=paginaActual)

            if isinstance(embed,list):
                await interaction.response.edit_message(embeds=embed,view=view)
            else:
                await interaction.response.edit_message(embed=embed,view=view)

    view = discord.ui.View()

    boton = botones[1]
    boton.callback = cambiarPagina

    view.add_item(boton)
    
    if isinstance(embed,list):
        await ctx.send(embeds=embed,view=view)
    else:
        await ctx.send(embed=embed,view=view)

async def rankingNiveles(listaTop,nombres,paginaActual):
    mensajes = [str(x["estadisticas"]["mensajes"]) for x in listaTop]
    xps = [str(x["estadisticas"]["xp"]) for x in listaTop]
    niveles = [str(x["estadisticas"]["nivel"]) for x in listaTop]
    porcentajes = [str(x["estadisticas"]["porcentaje"]) for x in listaTop]

    embeds = []
    largo = 30
    ventana = 10
    limiteInferior = paginaActual*ventana

    descripcion = ""
    nivelActual = niveles[limiteInferior]
    colorIndice = 1
    
    for usuario in range(limiteInferior,limiteInferior+ventana):
        
        if nivelActual == 0:
            nivelAnteriorXP = 0
        else:
            nivelAnteriorXP = nivelesXP[int(nivelActual)-1]

        xpAvanzado = int(xps[usuario]) - nivelAnteriorXP
        xpTotal = nivelesXP[int(nivelActual)] - nivelAnteriorXP
        xpFaltante = xpTotal - xpAvanzado

        cargador = crearCargador(int(porcentajes[usuario]),largo=largo)

        descripcion += f"## {usuario+1}. {nombres[usuario]}\n"

        descripcion += f"{xps[usuario]} xp".center(int(largo/2),"ㅤ")
        descripcion += f"{mensajes[usuario]} mensajes".center(int(largo/2),"ㅤ") + "\n"

        descripcion += f"ㅤㅤㅤ**{porcentajes[usuario]}%**ㅤㅤㅤ".center(largo,"ㅤ") + "\n"
        descripcion += f"{cargador}\n"
        descripcion += f"_{xpAvanzado}/{xpTotal}xp ({xpFaltante} restante)_\n"

        # Este codigo ctm se encarga de dividir los embeds
        if usuario+1 == len(niveles) or niveles[usuario+1] != nivelActual:
            if paginaActual > 0:
                color = 0x3e3e3e
            else:
                match colorIndice:
                    case 1: color = 0xe4eb23
                    case 2: color = 0xe0e0e0
                    case 3: color = 0xff8500
                    case _: color = 0x3e3e3e

            embeds.append(discord.Embed(
                title=f"Nivel {nivelActual}",
                description=descripcion,
                color = color
            ))
            descripcion = ""
            if usuario+1 != len(niveles):
                nivelActual = niveles[usuario+1]
            colorIndice += 1

    return embeds

async def usuarioInfo(interaction,objetivo=None,giveEmbed=False):

    ctx = False
    if objetivo:
        #Esto es dado el caso que se busque por sus discriminador  y no este en el server
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


    #Dado el caso que se introduzca un numero, intenta buscarlo por su numero
    try:
        nombre = int(nombre)
        cursor = usuarios_info.find({"num":nombre})
        usuario = list(cursor)

        nombre = usuario[0]["discriminador_discord"]
    except:
        cursor = usuarios_info.find({"discriminador_discord":nombre})
        usuario = list(cursor)

    if usuario == []:
        if ctx:
            await interaction.send("El usuario no esta registrado en la base datos todavia")
        else:
            await interaction.followup.send("El usuario no esta registrado en la base datos todavia")
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

    #Aca se procesa las estadisticas
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

    if usuario["num"] == None:
        usuario["num"] = ""

    #Obtenemos la fotos dl usuario de tener una
    embed = discord.Embed(
        title= f"#{usuario["num"]} {usuario["nombre"]}",
        description=resultado,
        color=color
    )

    #Obtenemos la fotos dl usuario de tener una
    if foto != "":
        embed.set_thumbnail(url=foto)

    embed.set_footer(text="Esta información es publica y es elegida por la administración.")

    if giveEmbed:
        return embed

    async def cambiarPagina(interaction):
            global botones
            #Primera vez en la vida usando el nonlocal, pemite usar una variable de una funcion superior
            nonlocal usuario
            match interaction.data["custom_id"]:
                case "siguiente": usuario["num"] += 1
                case "anterior": usuario["num"] -= 1
    
            #El view es donde van los botones, vale
            view = discord.ui.View()
            for boton in botones:
                if boton.label == "Anterior" and usuario["num"] < 1:
                    continue
    
                #Busca si existe un usuario mas arriba
                if boton.label == "Siguiente":
                    siguiente = list(usuarios_info.find({"num":usuario["num"]+1}))
                    if siguiente == []:
                        continue
    
                boton.callback = cambiarPagina
    
                view.add_item(boton)
    
            embed = await usuarioInfo(interaction,objetivo=str(usuario["num"]),giveEmbed=True)
    
            if isinstance(embed,list):
                await interaction.response.edit_message(embeds=embed,view=view)
            else:
                await interaction.response.edit_message(embed=embed,view=view)

    view = discord.ui.View()

    for boton in botones:
        if boton.label == "Anterior" and usuario["num"] < 1:
            continue
        elif boton.label == "Siguiente":
            siguiente = list(usuarios_info.find({"num":usuario["num"]+1}))
            if siguiente == []:
                continue

        boton.callback = cambiarPagina

        view.add_item(boton)


    if ctx:
        await interaction.send(embed=embed,view=view)
    else:
        await interaction.followup.send(embed=embed,view=view)
