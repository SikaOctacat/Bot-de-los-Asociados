from funciones import *

async def rankingEstrellas(ctx):
    cursor = topEstrellas.find().sort([("estrellas",-1)]).limit(10)

    ranking = list(cursor)

    if not ranking:
        ctx.send("Todavia no hay nadie en el ranking ⭐")
        return

    anchoIzquierda = max([len(str(x["usuario"])) for x in ranking])

    if anchoIzquierda < len("Usuario"):
        anchoIzquierda = len("Usuario") 

    anchoCentro = len(str(len(ranking)))

    if anchoCentro < len("Top"):
        anchoCentro = len("Top") 


    resultado = "**`"+"Usuario".rjust(anchoIzquierda)+"|"+"Top".center(anchoCentro)+"|"+"⭐`**\n"
    for i,usuario in enumerate(ranking,1):

        nombre = str(usuario["usuario"]).replace(" ","").rjust(anchoIzquierda)
        i = str(i).center(anchoCentro)
        
        puntuacion = str(usuario["estrellas"])

        if len(puntuacion) == 1:
            puntuacion += " " 

        resultado += f"**`{nombre}|{i}|{puntuacion}`**\n"

    embed = discord.Embed(
        title="Top de estrellas 🏆",
        description=resultado,
        color=0xFFFF00
    )

    await ctx.send(embed=embed)

