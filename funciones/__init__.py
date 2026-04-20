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

load_dotenv()

llave_IA = os.getenv("LLAVE_IA")
co = AsyncClient(os.getenv("LLAVE_COHERE"))
cliente = genai.Client(api_key=llave_IA)
#Recuerda cambiar esto a DISCORD cuando no lo estes testeando
llave_Discord = os.getenv("LLAVE_DISCORD")

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

#Identificador del mensaje para que traductor lo tome  en cuenta
marca = "\u200b"

#Esto es el historial de repuestas de bot

limiteContexto = 3500
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


}
mensajes_borrados = {}
lista_webhooks = []
for clave in canales:
    canal_idioma = canales[clave]["idioma_salida"]
    canales[clave]["respuesta"] = mensajes_respondiendo[canal_idioma][0]
    canales[clave]["boton"] = mensajes_respondiendo[canal_idioma][1]
    canales[clave]["archivo"] = mensajes_respondiendo[canal_idioma][2]
    canales[clave]["escribiendo"] = mensajes_respondiendo[canal_idioma][3]
    canales[clave]["reenviado"] = mensajes_respondiendo[canal_idioma][4]

    canales[clave]["webhook_destino"] = os.getenv(clave)
    canales[clave]["webhook_ID"] = int(re.search(r"webhooks/(\d+)/", canales[clave]["webhook_destino"]).group(1))
    lista_webhooks.append(canales[clave]["webhook_ID"])



canalesClave = list(canales.keys())
conexiones = {
    "escalada":[canalesClave[0],canalesClave[1]],
    "sendero":[canalesClave[2],canalesClave[3]],
    "prueba":[canalesClave[4],canalesClave[5]]
}


limite_mensajes = 15
exceso = 5
def recortarRegistro(registro):
    if len(registro) >= limite_mensajes:
        porBorrar = list(registro.keys())[:exceso]

        for mensaje in porBorrar:
            registro.pop(mensaje,None)

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