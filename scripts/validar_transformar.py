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
    Verifica que el archivo Excel cumpla con el nombre exacto y contenga 
    el conjunto exacto de columnas esperadas, tras limpiar y normalizar los nombres.

    :param ruta_excel: La ruta completa (string) al archivo Excel a validar.
    :return: Una tupla (bool, DataFrame) indicando si la verificación fue exitosa 
             y el DataFrame leído, o (None/False, None/DataFrame) en caso de error.
    """

    # Ruta fija al JSON
    # Construye la ruta absoluta al archivo JSON de configuración. 
    # Utiliza __file__ para referenciar la ubicación actual del script 
    # y navega hacia arriba (..) y luego a 'data/columnas_esperadas.json'.
    ruta_columnas_json = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "columnas_esperadas.json")
    )

    # --- Verificar nombre del archivo 📝 ---
    # Define el nombre de archivo exacto esperado.
    nombre_correcto = "Registro simplificado de participaciones en instancias externas.xlsx"
    # Compara solo el nombre del archivo (os.path.basename) con el nombre esperado.
    if os.path.basename(ruta_excel) != nombre_correcto:
        print(f"❌ El archivo debe llamarse exactamente: '{nombre_correcto}'")
        return None, None # Retorna None en caso de fallo en el nombre.

    # --- Leer archivo Excel 📖 ---
    try:
        # Intenta leer la primera hoja del archivo Excel en un DataFrame de pandas.
        df = pd.read_excel(ruta_excel)
    except Exception as e:
        # Captura cualquier error que ocurra durante la lectura del archivo (e.g., archivo corrupto, no es Excel).
        print(f"❌ Error al leer el archivo Excel: {e}")
        return None, None

    # --- Leer columnas esperadas desde JSON ⚙️ ---
    try:
        # Abre el archivo JSON en modo lectura ('r') con codificación UTF-8.
        with open(ruta_columnas_json, "r", encoding="utf-8") as f:
            # Carga el contenido JSON y extrae la lista de columnas esperadas.
            columnas_esperadas = json.load(f)["columnas"]
    except Exception as e:
        # Captura cualquier error al abrir o parsear el JSON.
        print(f"❌ Error al leer el archivo JSON de columnas: {e}")
        print(f"Ruta usada: {ruta_columnas_json}")
        return None, df # Retorna el DF por si es necesario para depuración.

    # --- Limpiar y normalizar todas las columnas ✨ ---
    # Aplica la función auxiliar 'limpiar_nombre_columna' a las columnas del archivo.
    columnas_archivo = [limpiar_nombre_columna(c) for c in df.columns.tolist()]
    # Aplica la misma limpieza a las columnas leídas del archivo JSON.
    columnas_esperadas = [limpiar_nombre_columna(c) for c in columnas_esperadas]

    # --- Comparación de Conjuntos de Columnas 🔎 ---
    print("\n📊 Comparando columnas (normalizadas):")
    print(f"👉 Total en Excel: {len(columnas_archivo)}")
    print(f"👉 Total esperadas: {len(columnas_esperadas)}")

    # Identifica qué columnas esperadas NO están presentes en el archivo (FALTANTES).
    faltantes = [col for col in columnas_esperadas if col not in columnas_archivo]
    # Identifica qué columnas en el archivo NO están en la lista de esperadas (EXTRAS).
    extras = [col for col in columnas_archivo if col not in columnas_esperadas]

    # --- Resultado Final 📋 ---
    print("\n📋 Resultado de la verificación:")
    if faltantes:
        print("⚠️ Faltan las siguientes columnas:")
        for col in faltantes:
            print(f"   - {col}")
    if extras:
        print("⚠️ Hay columnas adicionales no esperadas:")
        for col in extras:
            print(f"   - {col}")

    # Condición de Éxito: No debe haber ni faltantes ni extras.
    if not faltantes and not extras:
        print("✅ El archivo es válido y contiene todas las columnas esperadas.")
        # Retorna True y el DataFrame cargado para su uso posterior.
        return True, df

    # Condición de Fallo: Si hay faltantes o extras, la estructura no es correcta.
    print("❌ El archivo no cumple con la estructura esperada.")
    # Retorna False y el DataFrame (por si la lógica posterior requiere el DF aunque sea incorrecto).
    return False, df


def limpiar_y_renombrar_columnas(df_init: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia nombres de columnas y las renombra a nombres estandarizados
    usando la configuración definida en data/columnas_esperadas.json.
    """

    # --- 1️⃣ Definir ruta del archivo JSON ---
    ruta_columnas_json = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "columnas_esperadas.json")
    )

    # --- 2️⃣ Cargar JSON ---
    try:
        with open(ruta_columnas_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ No se encontró el archivo: {ruta_columnas_json}")

    columnas_nuevas = data.get("columnas_nuevas", [])

    # --- 3️⃣ Limpiar nombres actuales ---
    df_init.columns = (
        df_init.columns
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # --- 4️⃣ Crear diccionario de renombrado dinámico ---
    rename_map = {}
    for item in columnas_nuevas:
        idx = item["index"]
        new_name = item["value"]
        if idx < len(df_init.columns):
            rename_map[df_init.columns[idx]] = new_name

    # --- 5️⃣ Renombrar ---
    df_init.rename(columns=rename_map, inplace=True)

    print(f"✅ Columnas limpiadas y renombradas correctamente usando {os.path.basename(ruta_columnas_json)}")
    return df_init
