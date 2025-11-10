import pandas as pd
import os
import unicodedata
import difflib

def normalizar(texto):
    """Convierte texto a minúsculas sin acentos ni caracteres especiales."""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto


def encontrar_columna_asociada(nombre_dep, columnas):
    """Busca la columna más parecida al nombre de la dependencia."""
    nombre_norm = normalizar(nombre_dep)
    columnas_norm = [normalizar(c) for c in columnas]

    coincidencias = difflib.get_close_matches(nombre_norm, columnas_norm, n=1, cutoff=0.6)

    if coincidencias:
        idx = columnas_norm.index(coincidencias[0])
        return columnas[idx]
    else:
        return None


def subdividir_por_dependencia(dfs):
    """
    Divide los DataFrames de un diccionario según la columna asociada
    más parecida al nombre de la dependencia.
    Devuelve: { 'Facultad X': { 'Programa Y': df, 'Programa Z': df } }
    """
    subdivididos = {}

    for nombre_dep, df in dfs.items():
        print(f"\n📁 Procesando dependencia: {nombre_dep}")

        col_asociada = encontrar_columna_asociada(nombre_dep, df.columns)

        if not col_asociada or col_asociada == 'Dependencia':
            print(f"  ⚠ No se encontró columna asociada (sin subdividir).")
            subdivididos[nombre_dep] = {nombre_dep: df}
            continue

        print(f"  ➤ Columna asociada detectada: {col_asociada}")

        grupos = {
            valor: grupo for valor, grupo in df.groupby(col_asociada)
            if pd.notna(valor)
        }

        subdivididos[nombre_dep] = grupos
        print(f"  → Se generaron {len(grupos)} subgrupos")

    print("\n✅ Subdivisión completa.")
    return subdivididos


def exportar_subdependencias(subdfs, ruta_salida, seleccionadas=None):
    """
    Exporta cada subdependencia en carpetas ordenadas.
    subdfs = {'Dependencia': {'Subdep1': df1, 'Subdep2': df2}}
    """
    os.makedirs(ruta_salida, exist_ok=True)

    for dependencia, subgrupos in subdfs.items():
        carpeta_dep = os.path.join(ruta_salida, dependencia.replace("/", "_").replace(" ", "_"))
        os.makedirs(carpeta_dep, exist_ok=True)

        for subdep, df_sub in subgrupos.items():
            if seleccionadas and subdep not in seleccionadas:
                continue

            nombre_archivo = os.path.join(
                carpeta_dep,
                f"{str(subdep).replace('/', '_').replace(' ', '_')}.xlsx"
            )
            df_sub.to_excel(nombre_archivo, index=False)
            print(f"✅ Guardado: {nombre_archivo}")

    print("\n📂 Archivos exportados correctamente en la carpeta:", ruta_salida)
