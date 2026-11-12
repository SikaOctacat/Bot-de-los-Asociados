import discord
from discord import Webhook
from discord.ext import commands
from discord import app_commands
from deep_translator import MyMemoryTranslator,GoogleTranslator
from google import genai
import asyncio
import re
import aiohttp 
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from cohere import AsyncClient
import io
import typing
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

llave_IA = os.getenv("LLAVE_IA")
co = AsyncClient(os.getenv("LLAVE_COHERE"))
cliente = genai.Client(api_key=llave_IA)
mongoCliente = MongoClient(os.getenv("mongoUri"))
#Recuerda cambiar esto a DISCORD cuando no lo estes testeando
llave_Discord = os.getenv("LLAVE_DISCORD")

#Aca obtenemos la base de datos de mongo y la carpetas que nos interesan
baseDatos = mongoCliente["proyecto_asociacion_db"]
usuarios_info = baseDatos["usuarios_info"]
registros = baseDatos["registros"]
contexto_bot  = baseDatos["contexto_bot"]
memoriaBot = contexto_bot.find_one({"_id": ObjectId("6add5cc6c56f47a4ea869973")})


# Vale, entonces esto le dice a Discord que por favor me deje leer los mensajes de los usarios por favorcito
intents = discord.Intents.default()
intents.message_content = True
intents.typing = True

#Esto declara el objeto que sera el bot... Creo
bot = commands.Bot(command_prefix="$",intents=intents)

#Esto obtiene el objeto necesario para los slash commands
tree = bot.tree

#Estas funciones de encargar de manejar el orden de las traducciones
traduccionesActivas = {}
#Aca se guardan los mensajes que son enviados al MD
mensajesMD = {}
usuariosConMD = []

#Identificador del mensaje para que traductor lo tome  en cuenta
marca = "\u200b"

#Adjunto aqui la formula
# base = 100
# constante = 100**(1/100)
# niveles = []

# for nivel in range(0,base):
#     if len(niveles) > 0:
#         niveles.append(niveles[-1]+round(100*(constante**nivel)))
#     else:
#         niveles.append(round(100*(constante**nivel)))


#Referencia para subir de nivel
nivelesXP = [100, 205, 315, 430, 550, 676, 808, 946, 1091, 1242, 1400, 1566, 1740, 1922, 2113, 2313, 2522, 2741, 2970, 3210, 3461, 3724, 3999, 4287, 4589, 4905, 5236, 5583, 5946, 6326, 6724, 7141, 7578, 8035, 8514, 9015, 9540, 10090, 10665, 11268, 11899, 12560, 13252, 13976, 14735, 15529, 16361, 17232, 18144, 19099, 20099, 21146, 22242, 23390, 24592, 25851, 27169, 28549, 29994, 31508, 33093, 34753, 36491, 38311, 40216, 42211, 44300, 46488, 48779, 51178, 53690, 56320, 59074, 61958, 64978, 68140, 71451, 74918, 78549, 82351, 86332, 90501, 94866, 99437, 104223, 109235, 114483, 119978, 125732, 131758, 138068, 144675, 151593, 158837, 166423, 174366, 182684, 191394, 200514, 210064]

#Esto es el historial de repuestas de bot
limiteContexto = 3000

mensajes_respondiendo = {
    "en-US": ["Responding to ","Go to message","[Image or archive]"," is writing","Fowarded"],
    "es-419": ["Respondiendo a ","Ir al mensaje","[Imagen o archivo]"," esta ecribiendo","Reenviado"]
}

servidores = {
    "Sendero": 1020042170230648852,
    "Escalada": 1086801840764629093,
    "Asociacion": 1294734570788491304
}

canales = {
    #Canales de traduccion
    "escaladaIngles" : {
        "ID": 1428833199320076379,
        "idioma_entrada": "en-US",
        "idioma_salida": "es-419",
        "webhook_destino": "",
        "historial" : {}
    },

    "escaladaEspanol" : {
        "ID": 1086801841754472580,
        "idioma_entrada": "es-419",
        "idioma_salida": "en-US",
        "webhook_destino": "",
        "historial" : {}
    },

    "senderoIngles" : {
        "ID": 1490930083161182440,
        "idioma_entrada": "en-US",
        "idioma_salida": "es-419",
        "webhook_destino": "",
        "historial" : {}
    },

    "senderoEspanol" : {
        "ID": 1020042170230648854,
        "idioma_entrada": "es-419",
        "idioma_salida": "en-US",
        "webhook_destino": "",
        "historial" : {}
    },

    "pruebaIngles" : {
        "ID": 1495156399385088180,
        "idioma_entrada": "en-US",
        "idioma_salida": "es-419",
        "historial" : {}
    },

    "pruebaEspanol" : {
        "ID": 1495156490007482508,
        "idioma_entrada": "es-419",
        "idioma_salida": "en-US",
        "historial" : {}
    },

    #Canales de fuera de contexto
    "senderoContexto": {
        "ID": 1051626976227635230
    },

    "escaladaContexto": {
        "ID": 1087034941793112084
    },

    "asociadosContexto": {
        "ID": 1502753232756412426
    },
    #Canales subida de nivel
    "senderoNivel": {
        "ID": 1020455712456982559
    },

    "escaladaNivel": {
        "ID": 1294833147321520230
    },

    "asociadosNivel": {
        "ID": 1294848209134551050
    },
}
mensajes_borrados = {}
lista_webhooks = []
for clave in canales:

    if "idioma_salida" in canales[clave]:
        canal_idioma = canales[clave]["idioma_salida"]
        canales[clave]["respuesta"] = mensajes_respondiendo[canal_idioma][0]
        canales[clave]["boton"] = mensajes_respondiendo[canal_idioma][1]
        canales[clave]["archivo"] = mensajes_respondiendo[canal_idioma][2]
        canales[clave]["escribiendo"] = mensajes_respondiendo[canal_idioma][3]
        canales[clave]["reenviado"] = mensajes_respondiendo[canal_idioma][4]

        canales[clave]["webhook_destino"] = os.getenv(clave)
    else:
        canales[clave]["webhook"] = os.getenv(clave)

    for web in ["weebhook","webhook_destino"]:

        if web in canales[clave]:
            canales[clave]["webhook_ID"] = int(re.search(r"webhooks/(\d+)/", canales[clave][web]).group(1))
            lista_webhooks.append(canales[clave]["webhook_ID"])



canalesClave = list(canales.keys())
conexiones = {
    "escalada":[canalesClave[0],canalesClave[1]],
    "sendero":[canalesClave[2],canalesClave[3]],
    "prueba":[canalesClave[4],canalesClave[5]]
}


def crearUsuario(
    discriminador,
    nombre=False,
    primera_aparicion="Sin determinar",
    aliases=[],
    frase="Sin frase definida",
    descripcion="Sin descripción establecida",
    titulos=[],
    redes={},
    validado=False,
    num=None,
):
    
    if not nombre:
        nombre = discriminador
        
    if redes == {} or discriminador not in redes.values():
        redes["Discord"] = discriminador

    if "Miembro de la Asociación" not in titulos:
        titulos.insert(0,"Miembro de la Asociación")

    # Estructura final del documento
    return {
        "nombre": nombre,
        "primera_aparicion": primera_aparicion,
        "aliases": aliases,
        "frase": frase,
        "descripcion": descripcion,
        "titulos": titulos,
        "redes": redes,
        "discriminador_discord": discriminador,
        "validado": validado,
        "estadisticas": {
            "estrellas": 0,
            "mensajes": 0,
            "xp": 0,
            "nivel": 0,
            "porcentaje": 0,
            "corazones": 0,
            "descontextualizaciones": 0
        },
        "num":num
    }

limiteMensajes = 15
exceso = 5
def recortarRegistro(registro,limiteMensajes=limiteMensajes,exceso=exceso):
    if len(registro) >= limiteMensajes:
        porBorrar = list(registro.keys())[:exceso]

        for mensaje in porBorrar:
            registro.pop(mensaje,None)

def recortarRegistroDB(baseDatos,criterio,direccion,limite=limiteMensajes,exceso=exceso):
    usuario = baseDatos.find_one(criterio)
    direccionEdit = ".".join(direccion)

    if isinstance(direccion,list):
        registro = usuario[direccion[0]]
        for r in range(1,len(direccion)):
            registro = registro[direccion[r]]
    else:
        registro = usuario[direccion]


    if len(registro) >= limite:
        porBorrar = list(registro.keys())[:exceso]

        for mensaje in porBorrar:
            baseDatos.update_one(criterio,
                                {"$unset":{f"{direccionEdit}.{mensaje}":""}}
                                )

def crearCargador(porcentaje,llenado="█",vacio="▒",largo=30,base=100):

    if base:
        porcentaje /= base

    total = round(porcentaje*largo)

    resultado = ""

    for cuadrado in range(1,largo+1):
        if cuadrado < total:
            resultado += llenado
        else:
            resultado += vacio

    return resultado

async def responderMensaje(ctx,respuesta="",limite=2000,envol="",noResponder=False,embed=None):

    limite -= len(envol)*2 - len(marca)

    allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

    if len(respuesta) > limite:
            parrafos = respuesta.split("\n")

            puntero = 0
            while puntero < len(parrafos) -1:

                if len(parrafos[puntero]+"\n"+parrafos[puntero+1]) <= limite:
                    parrafos[puntero] += "\n" + parrafos[puntero+1]
                    parrafos.pop(puntero+1)
                else:
                    puntero += 1

            for re in range(len(parrafos)):
                parrafo = envol+parrafos[re].strip()+envol + marca

                if (re > 0 or noResponder) or not(hasattr(ctx,'reply')):
                    await ctx.send(parrafo,allowed_mentions=allowed_mentions)
                else:
                    await ctx.reply(parrafo,allowed_mentions=allowed_mentions)
    else:
        if noResponder or not(hasattr(ctx,'reply')):
            await ctx.send(envol+respuesta.strip()+envol + marca,
                        allowed_mentions=allowed_mentions,embed=embed)
        else:
            await ctx.reply(envol+respuesta.strip()+envol + marca,allowed_mentions=allowed_mentions,embed=embed)

