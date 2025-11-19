import pandas as pd
import json
import os
import re


# -----------------------------------------------------------
# 🔧 UTILIDAD GENERAL
# -----------------------------------------------------------

def limpiar_nombre_columna(nombre: str) -> str:
    """Normaliza nombres de columnas eliminando saltos de línea y espacios extra."""
    return re.sub(r"\s+", " ", str(nombre)).strip()


def cargar_json_columnas():
    """Carga el JSON de columnas esperadas y nuevas."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ruta_json = os.path.join(base_dir, "data", "columnas_esperadas.json")

    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            return json.load(f), ruta_json
    except Exception as e:
        raise FileNotFoundError(f"❌ Error al leer JSON ({ruta_json}): {e}")


# -----------------------------------------------------------
# 🔍 VALIDADOR DE ARCHIVO EXCEL
# -----------------------------------------------------------

def verificar_archivo_excel(ruta_excel: str):
    """
    Valida si el Excel contiene exactamente las columnas esperadas según JSON.
    Retorna (True/False, DataFrame).
    """

    log = []  # 🔵 acumulador de logs

    # Leer Excel
    try:
        log.append("📥 Cargando archivo Excel...")
        df = pd.read_excel(ruta_excel)
    except Exception as e:
        log.append(f"❌ Error al leer Excel: {e}")
        print("\n".join(log))
        return None, None

    # Cargar JSON
    data, ruta_json = cargar_json_columnas()

    # Normalizar columnas
    columnas_archivo = [limpiar_nombre_columna(c) for c in df.columns]
    columnas_esperadas = [limpiar_nombre_columna(c) for c in data.get("columnas", [])]

    log.append("\n📊 Comparando columnas normalizadas...")
    log.append(f"👉 Columnas archivo:   {len(columnas_archivo)}")
    log.append(f"👉 Columnas esperadas: {len(columnas_esperadas)}")

    # Comparación
    set_archivo = set(columnas_archivo)
    set_esperadas = set(columnas_esperadas)

    faltantes = sorted(set_esperadas - set_archivo)
    extras = sorted(set_archivo - set_esperadas)

    # Reportes
    if faltantes:
        log.append("\n⚠️ Columnas faltantes:")
        for col in faltantes:
            log.append(f"  - {col}")

    if extras:
        log.append("\n⚠️ Columnas extras:")
        for col in extras:
            log.append(f"  - {col}")

    if not faltantes and not extras:
        log.append("✅ Archivo válido. Todas las columnas coinciden.")
        print("\n".join(log))
        return True, df

    log.append("❌ El archivo NO cumple con la estructura esperada.")
    print("\n".join(log))
    return False, df


# -----------------------------------------------------------
# ✨ LIMPIEZA Y RENOMBRADO DE COLUMNAS
# -----------------------------------------------------------
def limpiar_y_renombrar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia nombres de columnas y las renombra según el JSON.
    """

    log = []  # 🔵 acumulador de logs

    data, ruta_json = cargar_json_columnas()
    columnas_nuevas = data.get("columnas_nuevas", [])

    log.append("🧹 Limpiando y renombrando columnas...")

    # Limpiar columnas actuales
    df.columns = [limpiar_nombre_columna(c) for c in df.columns]

    # Crear mapa dinámico de renombre basado en índices
    rename_map = {
        df.columns[item["index"]]: item["value"]
        for item in columnas_nuevas
        if item["index"] < len(df.columns)
    }

    df.rename(columns=rename_map, inplace=True)

    log.append(f"✅ Columnas renombradas correctamente desde {os.path.basename(ruta_json)}")

    print("\n".join(log))  # 🔵 un solo print final
    return df
