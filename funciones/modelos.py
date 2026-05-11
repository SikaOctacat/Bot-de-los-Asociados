from google import genai
from __init__ import cliente

print("Modelos disponibles para tu clave:")
for model in cliente.models.list():
    print(f"- {model.name}")