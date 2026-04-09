from google import genai
from funciones import cliente

print("Modelos disponibles para tu clave:")
for model in cliente.models.list():
    print(f"- {model.name}")