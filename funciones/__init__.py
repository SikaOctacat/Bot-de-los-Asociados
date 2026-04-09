import discord
from discord import Webhook
from discord.ext import commands
from deep_translator import GoogleTranslator
from google import genai
import asyncio
import re
import aiohttp 
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()

llave_IA = os.getenv("LLAVE_IA")
cliente = genai.Client(api_key=llave_IA)
llave_Discord = os.getenv("LLAVE_DISCORD")

# Vale, entonces esto le dice a Discord que por favor me deje leer los mensajes de los usarios por favorcito
intents = discord.Intents.default()
intents.message_content = True

#Esto declara el objeto que sera el bot... Creo
bot = commands.Bot(command_prefix="$",intents=intents)

traducciones_activas = {}

mensajes_respondiendo = {
    "en": ["Responding to: ","Go to message"],
    "es": ["Respondiendo a: ","Ir al mensaje"]
}

canales = {

    "escaladaIngles" : {
        "ID": 1428833199320076379,
        "idioma_entrada": "en",
        "idioma_salida": "es",
        "webhook_destino": "",
        "historial" : {}
    },

    "escaladaEspanol" : {
        "ID": 1086801841754472580,
        "idioma_entrada": "es",
        "idioma_salida": "en",
        "webhook_destino": "",
        "historial" : {}
    },

    "senderoIngles" : {
        "ID": 1490930083161182440,
        "idioma_entrada": "en",
        "idioma_salida": "es",
        "webhook_destino": "",
        "historial" : {}
    },

    "senderoEspanol" : {
        "ID": 1020042170230648854,
        "idioma_entrada": "es",
        "idioma_salida": "en",
        "webhook_destino": "",
        "historial" : {}
    }
}
mensajes_borrados = {}
lista_webhooks = []
for clave in canales:
    canal_idioma = canales[clave]["idioma_salida"]
    canales[clave]["respuesta"] = mensajes_respondiendo[canal_idioma][0]
    canales[clave]["boton"] = mensajes_respondiendo[canal_idioma][1]

    canales[clave]["webhook_destino"] = os.getenv(clave)
    canales[clave]["webhook_ID"] = int(re.search(r"webhooks/(\d+)/", canales[clave]["webhook_destino"]).group(1))
    lista_webhooks.append(canales[clave]["webhook_ID"])



canalesClave = list(canales.keys())
conexiones = {
    "escalada":[canalesClave[0],canalesClave[1]],
    "sendero":[canalesClave[2],canalesClave[3]]
}


limite_mensajes = 15
exceso = 5
def recortarRegistro(registro):
    if len(registro) >= limite_mensajes:
        porBorrar = list(registro.keys())[:exceso]

        for mensaje in porBorrar:
            registro.pop(mensaje,None)