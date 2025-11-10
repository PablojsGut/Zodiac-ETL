import pandas as pd
import json
import os
import re

def limpiar_nombre_columna(nombre):
    """Normaliza un nombre de columna para evitar diferencias de espacios o saltos de línea."""
    if not isinstance(nombre, str):
        return str(nombre)
    # Elimina saltos de línea, múltiples espacios, tabulaciones, etc.
    nombre = re.sub(r"\s+", " ", nombre.strip())
    return nombre

def verificar_archivo_excel(ruta_excel):
    """
    Verifica que el archivo Excel tenga el nombre correcto y las columnas esperadas.
    Limpia los nombres antes de comparar.
    """

    # Ruta fija al JSON
    ruta_columnas_json = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "columnas_esperadas.json")
    )

    # --- Verificar nombre del archivo ---
    nombre_correcto = "Registro simplificado de participaciones en instancias externas.xlsx"
    if os.path.basename(ruta_excel) != nombre_correcto:
        print(f"❌ El archivo debe llamarse exactamente: '{nombre_correcto}'")
        return None

    # --- Leer archivo Excel ---
    try:
        df = pd.read_excel(ruta_excel)
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return None

    # --- Leer columnas esperadas desde JSON ---
    try:
        with open(ruta_columnas_json, "r", encoding="utf-8") as f:
            columnas_esperadas = json.load(f)["columnas"]
    except Exception as e:
        print(f"❌ Error al leer el archivo JSON de columnas: {e}")
        print(f"Ruta usada: {ruta_columnas_json}")
        return None

    # --- Limpiar y normalizar todas las columnas ---
    columnas_archivo = [limpiar_nombre_columna(c) for c in df.columns.tolist()]
    columnas_esperadas = [limpiar_nombre_columna(c) for c in columnas_esperadas]

    # --- Comparación ---
    print("\n📊 Comparando columnas (normalizadas):")
    print(f"👉 Total en Excel: {len(columnas_archivo)}")
    print(f"👉 Total esperadas: {len(columnas_esperadas)}")

    faltantes = [col for col in columnas_esperadas if col not in columnas_archivo]
    extras = [col for col in columnas_archivo if col not in columnas_esperadas]

    print("\n📋 Resultado de la verificación:")
    if faltantes:
        print("⚠️ Faltan las siguientes columnas:")
        for col in faltantes:
            print(f"   - {col}")
    if extras:
        print("⚠️ Hay columnas adicionales no esperadas:")
        for col in extras:
            print(f"   - {col}")

    if not faltantes and not extras:
        print("✅ El archivo es válido y contiene todas las columnas esperadas.")
        return True, df  # ← devuelve el DataFrame también

    print("❌ El archivo no cumple con la estructura esperada.")
    return False, df

