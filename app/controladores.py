import pandas as pd
import os
from datetime import datetime

from scripts.verificar_archivo import verificar_archivo_excel
from scripts.limpiar_columnas import limpiar_y_renombrar_columnas
from scripts.dividir_dependencias import dividir_por_dependencia
from scripts.exportar_dependencias import eliminar_columnas_por_indice, exportar_dependencias
from scripts.subdependencias import subdividir_por_dependencia, exportar_subdependencias


def obtener_dependencias(df):
    """Devuelve una lista de dependencias encontradas en el DataFrame."""
    col_dependencia = df.columns[8]  # según tu código original
    dependencias = sorted(df[col_dependencia].dropna().unique().tolist())
    return dependencias


def validar_archivo(ruta_excel: str):
    """Valida la estructura del archivo Excel."""
    return verificar_archivo_excel(ruta_excel)


def procesar_excel(ruta_excel: str, ruta_salida_base: str, seleccionadas: list = None):
    """
    Procesa el Excel y exporta los archivos en una subcarpeta dentro de la carpeta seleccionada.
    Si 'seleccionadas' no es None, exportará solo esas dependencias.
    Devuelve la ruta final de salida si todo OK, o None si hay error.
    """
    try:
        print("📥 Cargando archivo Excel...")
        df = pd.read_excel(ruta_excel)

        print("🧹 Limpiando y renombrando columnas...")
        df = limpiar_y_renombrar_columnas(df)

        print("📊 Dividiendo por dependencias...")
        dfs = dividir_por_dependencia(df)

        print("✂️ Eliminando columnas según dependencia...")
        eliminar_columnas_por_indice(dfs, "Centro de Investigación", [9, 10, 11, 13, 14, 15, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Especialidad Médica", [9, 10, 11, 12, 13, 14, 15, 16, 17])
        eliminar_columnas_por_indice(dfs, "Facultad de Ciencias Sociales y Artes", [9, 10, 11, 12, 13, 15, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Facultad de Ciencias, Ingeniería y Tecnología", [9, 10, 11, 12, 13, 14, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Facultad de Medicina y Ciencias de la Salud", [9, 10, 11, 12, 13, 14, 15, 17, 18])
        eliminar_columnas_por_indice(dfs, "Programa Magíster", [9, 11, 12, 13, 14, 15, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Programa de Doctorado", [9, 10, 11, 12, 14, 15, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Unidad Técnica y Tecnológica TEC MAYOR", [9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Especialidad Odontológica", [9, 10, 11, 12, 13, 14, 15, 16, 18])
        eliminar_columnas_por_indice(dfs, "Núcleo de Investigación", [9, 10, 12, 13, 14, 15, 16, 17, 18])
        eliminar_columnas_por_indice(dfs, "Otras Unidades No Académicas", [10, 11, 12, 13, 14, 15, 16, 17, 18])

        # 🗂️ Crear subcarpeta organizada dentro de la ruta elegida
        fecha = datetime.now().strftime("%Y-%m-%d")
        ruta_salida_final = os.path.join(ruta_salida_base, f"Dependencias_{fecha}")
        os.makedirs(ruta_salida_final, exist_ok=True)

        print(f"💾 Exportando dependencias en: {ruta_salida_final}")
        exportar_dependencias(dfs, ruta_salida_final, seleccionadas=seleccionadas)

        print("\n✅ Proceso ETL completado con éxito.")
        return ruta_salida_final

    except Exception as e:
        print(f"❌ Error durante el proceso ETL: {e}")
        return None


def procesar_excel_por_subdependencias(ruta_excel, carpeta_salida, seleccionadas):
    """
    Procesa y exporta solo las subdependencias seleccionadas.
    'seleccionadas' es una lista de tuplas: [(dependencia, subdependencia), ...]
    """

    print("✅ Columnas limpiadas y renombradas correctamente.")
    df = pd.read_excel(ruta_excel)
    df = limpiar_y_renombrar_columnas(df)
    df_dependencias = dividir_por_dependencia(df)
    dfs_sub = subdividir_por_dependencia(df_dependencias)

    fecha = datetime.now().strftime("%Y-%m-%d")
    carpeta_export = os.path.join(carpeta_salida, f"Subdependencias_{fecha}")
    os.makedirs(carpeta_export, exist_ok=True)

    total_guardados = 0

    for (dependencia, subdep) in seleccionadas:
        if dependencia not in dfs_sub:
            print(f"⚠ Dependencia '{dependencia}' no encontrada, se omite.")
            continue

        subgrupos = dfs_sub[dependencia]
        if subdep not in subgrupos:
            print(f"⚠ Subdependencia '{subdep}' no encontrada dentro de '{dependencia}', se omite.")
            continue

        df_sub = subgrupos[subdep]
        # 🧹 Antes de guardar cada dependencia o subdependencia
        df_sub = df_sub.loc[:, df_sub.notna().any(axis=0)]

        # Crear carpeta solo si se guarda algo
        carpeta_dep = os.path.join(carpeta_export, dependencia.replace("/", "_").replace(" ", "_"))
        os.makedirs(carpeta_dep, exist_ok=True)

        nombre_archivo = os.path.join(
            carpeta_dep,
            f"{str(subdep).replace('/', '_').replace(' ', '_')}.xlsx"
        )

        df_sub.to_excel(nombre_archivo, index=False)
        print(f"✅ Guardado: {nombre_archivo}")
        total_guardados += 1

    if total_guardados == 0:
        print("⚠ No se exportó ningún archivo. Verifica las selecciones.")
        return None

    print(f"\n📂 Archivos exportados correctamente en la carpeta: {carpeta_export}")
    print("✅ Exportación por subdependencias completada.")
    return carpeta_export


def leer_excel_dependencia(dependencia, ruta_base):
    """
    Lee un archivo Excel de una dependencia desde la carpeta de salida.
    Devuelve un diccionario con las subdependencias (si existen) o un DataFrame único.
    """
    nombre_archivo = dependencia.replace("/", "_").replace(" ", "_")
    carpeta_dep = os.path.join(ruta_base, nombre_archivo)

    # Caso 1️⃣: existe una subcarpeta con el nombre de la dependencia
    if os.path.isdir(carpeta_dep):
        subarchivos = [f for f in os.listdir(carpeta_dep) if f.endswith(".xlsx")]
        if not subarchivos:
            print(f"⚠️ No hay archivos Excel en {carpeta_dep}")
            return None

        subdependencias = {}
        for archivo in subarchivos:
            ruta_excel = os.path.join(carpeta_dep, archivo)
            subnombre = os.path.splitext(archivo)[0]
            try:
                df = pd.read_excel(ruta_excel)
                subdependencias[subnombre] = df
            except Exception as e:
                print(f"❌ Error al leer {ruta_excel}: {e}")

        return subdependencias

    # Caso 2️⃣: el archivo está directamente en la carpeta raíz
    ruta_excel_directo = os.path.join(ruta_base, f"{nombre_archivo}.xlsx")
    if os.path.exists(ruta_excel_directo):
        try:
            df = pd.read_excel(ruta_excel_directo)
            return {"General": df}  # Retornar como subdependencia única
        except Exception as e:
            print(f"❌ Error al leer {ruta_excel_directo}: {e}")
            return None

    # Si no existe ni carpeta ni archivo
    print(f"⚠️ Carpeta o archivo no encontrado para {dependencia}: {carpeta_dep}")
    return None
