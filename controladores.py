import pandas as pd
import os
from datetime import datetime

from scripts.instancias_externas.validar_transformar import verificar_archivo_excel, limpiar_y_renombrar_columnas
from scripts.instancias_externas.dependencias import obtener_dependencias, dividir_por_dependencia, exportar_dependencias
from scripts.instancias_externas.subdependencias import dividir_por_subdependencia, exportar_subdependencias

from scripts.iniciativas.validar_transformar import validar_excel_vform, limpiar_columnas_vform
from scripts.iniciativas.dependencias import obtener_dependencias_vform, dividir_dependencias_vform, exportar_dependencias_vform
from scripts.iniciativas.subdependencias import dividir_subdependencias_vform, exportar_subdependencias_vform

def validar_excel(ruta_excel: str):
    """
    Valida el archivo Excel y, si es correcto, lo transforma.
    Retorna: (bool, DataFrame o None)
    """
    es_valido, df_original = verificar_archivo_excel(ruta_excel)

    # ❌ Si no se pudo leer archivo o es inválido
    if not es_valido or df_original is None:
        return False, None

    # ✔ Si es válido, transformarlo
    try:
        df_transformado = limpiar_y_renombrar_columnas(df_original)
        return True, df_transformado
    except Exception as e:
        print(f"❌ Error al transformar Excel: {e}")
        return False, None
    

def ctr_validar_excel_vform(ruta_excel: str, columnas_vform: str):
    es_valido, df_original = validar_excel_vform(ruta_excel, columnas_vform)
    # ❌ Si no se pudo leer archivo o es inválido
    if not es_valido or df_original is None:
        return False, None

    # ✔ Si es válido, transformarlo
    try:
        df_transformado = limpiar_columnas_vform(df_original)
        return True, df_transformado
    except Exception as e:
        print(f"❌ Error al transformar Excel: {e}")
        return False, None
    
def validar_archivo_formulario(ruta_excel: str, tipo_formulario: str, tipo_columns = None):
    """
    Decide qué validador usar según el tipo de formulario seleccionado.
    Retorna: (bool, DataFrame)
    """

    if tipo_formulario == "Formulario de Participaciones en Instancias Externas":
        # Usa el validador normal
        return validar_excel(ruta_excel)

    elif tipo_formulario == "Formulario de Iniciativas VcM":
        # Usa validador VForm
        return ctr_validar_excel_vform(ruta_excel, tipo_columns)

    else:
        print("⚠ Tipo de formulario desconocido")
        return False, None


def get_dependencias(df):
    """Devuelve una lista de dependencias encontradas en el DataFrame."""
    return obtener_dependencias(df)

def get_dependencias_vform(df):
    return obtener_dependencias_vform(df)

def get_subdependencias(df):
    df_dep = dividir_por_dependencia(df)
    dfs_sub = dividir_por_subdependencia(df_dep)

    jerarquia={}

    for dependencia, subgrupos in dfs_sub.items():
        # Extrae solo los nombres de las subdependencias
        subnombres = list(subgrupos.keys())
        jerarquia[dependencia] = subnombres

    return jerarquia

def get_subdependencias_vform(df):
    diccionario_dividido = dividir_subdependencias_vform(df)

    jerarquia = {}

    for dependencia, valor in diccionario_dividido.items():

        # Caso 1: NO tiene subdependencias → es DataFrame
        if isinstance(valor, pd.DataFrame):
            jerarquia[dependencia] = []

        # Caso 2: SÍ tiene subdependencias → es dict
        elif isinstance(valor, dict):
            jerarquia[dependencia] = list(valor.keys())

        # Backup
        else:
            jerarquia[dependencia] = []

    return jerarquia
# -------------------------------------------------------------
# 🚀 Procesar por dependencias
# -------------------------------------------------------------
def procesar_excel_dependencias(df: pd.DataFrame, ruta_salida_base: str, seleccionadas: list = None):
    """Procesa el Excel y exporta los archivos en una subcarpeta dentro de la carpeta seleccionada."""
    try:
        print("📊 Dividiendo por dependencias...")
        dfs = dividir_por_dependencia(df)

        # 🗂️ Crear carpeta de salida
        fecha = datetime.now().strftime("%Y-%m-%d")
        ruta_salida_final = os.path.join(ruta_salida_base, f"Instancias Externas (VcM) - Dependencias {fecha}")
        os.makedirs(ruta_salida_final, exist_ok=True)

        print(f"💾 Exportando dependencias en: {ruta_salida_final}")
        exportar_dependencias(dfs, ruta_salida_final, seleccionadas=seleccionadas)

        print("\n✅ Proceso ETL completado con éxito.")
        return ruta_salida_final, dfs
    except Exception as e:
        print(f"❌ Error durante el proceso ETL: {e}")
        return None, None


def get_excels_dependencias_vform(df1: pd.DataFrame, df2: pd.DataFrame, ruta_salida_base: str, seleccionadas: list = None):
    """Procesa el Excel y exporta los archivos en una subcarpeta dentro de la carpeta seleccionada."""
    try:
        print("📊 Dividiendo por dependencias...")
        dfs1 = dividir_dependencias_vform(df1)

        # 🗂️ Crear carpeta de salida
        fecha = datetime.now().strftime("%Y-%m-%d")
        ruta_salida_final = os.path.join(ruta_salida_base, f"Iniciativas (VcM) - Dependencias {fecha}")
        os.makedirs(ruta_salida_final, exist_ok=True)

        print(f"💾 Exportando dependencias en: {ruta_salida_final}")
        dfs2 = exportar_dependencias_vform(dfs1, df2, ruta_salida_final, seleccionadas=seleccionadas)

        print("\n✅ Proceso ETL completado con éxito.")
        return ruta_salida_final, dfs1, dfs2
    except Exception as e:
        print(f"❌ Error durante el proceso ETL: {e}")
        return None, None, None

# -------------------------------------------------------------
# 🚀 Procesar por subdependencias
# -------------------------------------------------------------
def procesar_excel_subdependencias(df: pd.DataFrame, ruta_salida_base: str, seleccionadas: list = None):
    """Procesa y exporta solo las subdependencias seleccionadas."""
    try:
        print("📊 Dividiendo por subdependencias...")
        df_dependencias = dividir_por_dependencia(df)
        dfs_sub = dividir_por_subdependencia(df_dependencias)

        # 🗂️ Crear carpeta de salida
        fecha = datetime.now().strftime("%Y-%m-%d")
        ruta_salida_final = os.path.join(ruta_salida_base, f"Instancias Externas (VcM) - Subdependencias {fecha}")
        os.makedirs(ruta_salida_final, exist_ok=True)

        # 🧩 Ajustar la lista de seleccionadas si viene como lista de tuplas (dep, subdep)
        if seleccionadas and all(isinstance(s, tuple) and len(s) == 2 for s in seleccionadas):
            seleccionadas_sub = [subdep for _, subdep in seleccionadas]
        else:
            seleccionadas_sub = seleccionadas

        print(f"💾 Exportando dependencias en: {ruta_salida_final}")
        exportar_subdependencias(dfs_sub, ruta_salida_final, seleccionadas=seleccionadas_sub)

        print("\n✅ Proceso ETL completado con éxito.")
        return ruta_salida_final, dfs_sub

    except Exception as e:
        print(f"❌ Error durante el proceso ETL: {e}")
        return None, None

def get_excels_subdependencias_vform(df1: pd.DataFrame, df2: pd.DataFrame, ruta_salida_base: str, seleccionadas: list = None):
    """Procesa y exporta solo las subdependencias seleccionadas."""
    try:
        print("📊 Dividiendo por subdependencias...")
        dfs_sub1 = dividir_subdependencias_vform(df1)

        # 🗂️ Crear carpeta de salida
        fecha = datetime.now().strftime("%Y-%m-%d")
        ruta_salida_final = os.path.join(ruta_salida_base, f"Iniciativas (VcM) - Subdependencias {fecha}")
        os.makedirs(ruta_salida_final, exist_ok=True)

        # 🧩 Ajustar la lista de seleccionadas si viene como lista de tuplas (dep, subdep)
        if seleccionadas and all(isinstance(s, tuple) and len(s) == 2 for s in seleccionadas):
            seleccionadas_sub = [subdep for _, subdep in seleccionadas]
        else:
            seleccionadas_sub = seleccionadas

        print(f"💾 Exportando dependencias en: {ruta_salida_final}")
        dfs_sub2 = exportar_subdependencias_vform(dfs_sub1, df2, ruta_salida_final, seleccionadas=seleccionadas_sub)

        print("\n✅ Proceso ETL completado con éxito.")
        return ruta_salida_final, dfs_sub1, dfs_sub2

    except Exception as e:
        print(f"❌ Error durante el proceso ETL: {e}")
        return None, None, None