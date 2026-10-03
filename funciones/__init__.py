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


#Referencia para subir de nivel
nivelesXP = [100, 500, 1400, 3000, 5500, 9100, 14000, 20400, 28500, 38500, 50600, 65000, 81900, 101500, 124000, 149600, 178500, 210900, 247000, 287000, 331100, 379500, 432400, 490000, 552500, 620100, 693000, 771400, 855500, 945500, 1041600, 1144000, 1252900, 1368500, 1491000, 1620600, 1757500, 1901900, 2054000, 2214000, 2382100, 2558500, 2743400, 2937000, 3139500, 3351100, 3572000, 3802400, 4042500, 4292500, 4552600, 4823000, 5103900, 5395500, 5698000, 6011600, 6336500, 6672900, 7021000, 7381000, 7753100, 8137500, 8534400, 8944000, 9366500, 9802100, 10251000, 10713400, 11189500, 11679500, 12183600, 12702000, 13234900, 13782500, 14345000, 14922600, 15515500, 16123900, 16748000, 17388000, 18044100, 18716500, 19405400, 20111000, 20833500, 21573100, 22330000, 23104400, 23896500, 24706500, 25534600, 26381000, 27245900, 28129500, 29032000, 29953600, 30894500, 31854900, 32835000, 33835000, 34855100]

#Esto es el historial de repuestas de bot
limiteContexto = 3000
contexto = ""
textInicio = ""

mensajes_respondiendo = {
    "en-US": ["Responding to ","Go to message","[Image or archive]"," is writing","Fowarded"],
    "es-419": ["Respondiendo a ","Ir al mensaje","[Imagen o archivo]"," esta ecribiendo","Reenviado"]
}

canales = {

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

    "senderoContexto": {
        "ID": 1051626976227635230
    },

    "escaladaContexto": {
        "ID": 1087034941793112084
    },

    "asociadosContexto": {
        "ID": 1502753232756412426
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
        }
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

async def responderMensaje(ctx,respuesta,limite=2000,envol="",noResponder=False):

    limite -= len(envol)*2 - len(marca)

    allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

    if len(respuesta) > limite:
            parrafos = respuesta.split("\n\n")

            puntero = 0

            while puntero < len(parrafos) -1:
                if len(parrafos[puntero] + parrafos[puntero+1]) <= limite:
                    parrafos[puntero] += "\n\n" + parrafos[puntero+1]
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
                        allowed_mentions=allowed_mentions)
        else:
            await ctx.reply(envol+respuesta.strip()+envol + marca,allowed_mentions=allowed_mentions)

