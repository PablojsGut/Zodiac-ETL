import pandas as pd
import json
import os
import re


# ============================================================
# 🔵 Normalizador de nombres (rápido y vectorizable)
# ============================================================
def limpiar_nombre_columna(nombre):
    if not isinstance(nombre, str):
        nombre = str(nombre)
    return re.sub(r"\s+", " ", nombre.strip())


# ============================================================
# 🟥 VALIDACIÓN — versión optimizada sin spam de prints
# ============================================================
def validar_excel_vform(ruta_excel, columnas_vform):
    """
    Valida que el Excel tenga las columnas exactas definidas en el JSON.
    Totalmente optimizada usando buffer de logs (1 sólo print al final).
    """

    logs = []  # 🔵 acumula todo → se imprime una sola vez

    # --- Cargar JSON ---
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ruta_json = os.path.join(base_dir, "data", "columnas_esperadas.json")

    # --- Leer Excel ---
    try:
        logs.append("📥 Cargando archivo Excel...")
        df = pd.read_excel(ruta_excel, skiprows=[0], header=1)
    except Exception as e:
        logs.append(f"❌ Error al leer el archivo Excel: {e}")
        print("\n".join(logs))
        return None, None

    # --- Leer columnas esperadas ---
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            columnas_esperadas = json.load(f)[columnas_vform]
    except Exception as e:
        logs.append(f"❌ Error al cargar JSON: {e}")
        logs.append(f"Ruta: {ruta_json}")
        print("\n".join(logs))
        return None, df

    # --- Normalización MASIVA y rápida ---
    columnas_archivo = [limpiar_nombre_columna(c) for c in df.columns]
    columnas_esperadas = [limpiar_nombre_columna(c) for c in columnas_esperadas]

    logs.append("\n📊 Comparando columnas normalizadas:")
    logs.append(f"👉 Total en Excel: {len(columnas_archivo)}")
    logs.append(f"👉 Total esperadas: {len(columnas_esperadas)}")

    # --- Comparación ---
    faltantes = list(set(columnas_esperadas) - set(columnas_archivo))
    extras = list(set(columnas_archivo) - set(columnas_esperadas))

    logs.append("\n📋 Resultado de la verificación:")

    if faltantes:
        logs.append("⚠️ Columnas faltantes:")
        logs.extend([f"   - {c}" for c in sorted(faltantes)])

    if extras:
        logs.append("⚠️ Columnas adicionales:")
        logs.extend([f"   - {c}" for c in sorted(extras)])

    # --- Resultado ---
    if not faltantes and not extras:
        logs.append("✅ Archivo válido.")
        print("\n".join(logs))
        return True, df

    logs.append("❌ El archivo NO cumple la estructura esperada.")
    print("\n".join(logs))
    return False, df


# ============================================================
# 🟩 LIMPIEZA — optimizada con una sola impresión
# ============================================================
def limpiar_columnas_vform(df_init: pd.DataFrame) -> pd.DataFrame:
    logs = []

    logs.append("🧹 Limpiando columnas...")

    df_init.columns = (
        df_init.columns
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    logs.append("✅ Columnas listas.")
    print("\n".join(logs))

    return df_init
