import pandas as pd
import os
from datetime import datetime

from scripts.validar_transformar import verificar_archivo_excel
from scripts.dependencias import obtener_dependencias, dividir_por_dependencia, exportar_dependencias
from scripts.validar_transformar import limpiar_y_renombrar_columnas
from scripts.subdependencias import dividir_por_subdependencia, exportar_subdependencias


def validar_excel(ruta_excel: str):
    """Valida la estructura del archivo Excel."""
    return verificar_archivo_excel(ruta_excel)

def get_dependencias(df):
    """Devuelve una lista de dependencias encontradas en el DataFrame."""
    return obtener_dependencias(df)

def get_subdependencias(df):
    
    df_dep = dividir_por_dependencia(df)
    dfs_sub = dividir_por_subdependencia(df_dep)

    jerarquia={}

    for dependencia, subgrupos in dfs_sub.items():
        # Extrae solo los nombres de las subdependencias
        subnombres = list(subgrupos.keys())
        jerarquia[dependencia] = subnombres

    return jerarquia

# -------------------------------------------------------------
# 🔧 Función auxiliar: filtrar por rango de fechas
# -------------------------------------------------------------
def filtrar_por_rango(df, fecha_inicio=None, fecha_fin=None):
    """
    Filtra el DataFrame por el rango de fechas indicado en la columna 43 ("Fecha inicio Actividad").
    Si la fecha es nula, el registro se conserva igualmente.
    """
    try:
        fecha_col = df.columns[43]
        df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")

        if fecha_inicio and fecha_fin:
            mask = (df[fecha_col].isna()) | (
                (df[fecha_col] >= pd.Timestamp(fecha_inicio)) &
                (df[fecha_col] <= pd.Timestamp(fecha_fin))
            )
            df = df.loc[mask]
            print(f"📆 Filtrado por rango: {fecha_inicio} → {fecha_fin} ({len(df)} filas)")
    except Exception as e:
        print(f"⚠ Error al filtrar por rango de fechas: {e}")
    return df


def transformar_excel(ruta_excel: str):
    print("📥 Cargando archivo Excel...")
    df = pd.read_excel(ruta_excel)

    print("🧹 Limpiando y renombrando columnas...")
    df = limpiar_y_renombrar_columnas(df)

    return df

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
        ruta_salida_final = os.path.join(ruta_salida_base, f"Dependencias_{fecha}")
        os.makedirs(ruta_salida_final, exist_ok=True)

        print(f"💾 Exportando dependencias en: {ruta_salida_final}")
        exportar_dependencias(dfs, ruta_salida_final, seleccionadas=seleccionadas)

        print("\n✅ Proceso ETL completado con éxito.")
        return ruta_salida_final, dfs
    except Exception as e:
        print(f"❌ Error durante el proceso ETL: {e}")
        return None, None


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
        ruta_salida_final = os.path.join(ruta_salida_base, f"Subdependencias_{fecha}")
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
