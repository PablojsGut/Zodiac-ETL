import os
import pandas as pd

def obtener_dependencias_vform(df: pd.DataFrame, col_index: int = 13):
    """
    Devuelve una lista de dependencias encontradas en el DataFrame.

    Esta función asume que la columna de interés (Dependencia) se encuentra
    en el índice 8 del DataFrame.

    :param df: El DataFrame de pandas de entrada.
    :return: Una lista de strings que contiene los valores únicos y ordenados
             de la columna de Dependencia, excluyendo los valores nulos (NaN).
    """
    # 1. Identificar la columna:
    # Obtiene el nombre real de la columna usando su índice (posición 8).
    col_dependencia = df.columns[col_index]
    
    # 2. Extraer y limpiar los valores únicos:
    # df[col_dependencia]: Selecciona la Serie (columna) de Dependencia.
    # .dropna(): Elimina cualquier valor nulo (NaN) de esa Serie.
    # .unique(): Devuelve un array de NumPy con todos los valores únicos que quedan.
    # .tolist(): Convierte el array de NumPy en una lista estándar de Python.
    list_dependencias = df[col_dependencia].dropna().unique().tolist()
    
    # 3. Ordenar la lista:
    # sorted(...) ordena alfabéticamente la lista de dependencias resultante.
    list_dependencias = sorted(list_dependencias)
    
    # 4. Retorno:
    return list_dependencias

def dividir_dependencias_vform(df: pd.DataFrame, col_dependencia: str = "Unidad o Dependencia Responsable"):
    """
    Divide el DataFrame según la columna de dependencia, normalizando valores,
    sin crear nuevas columnas, y eliminando columnas completamente vacías.

    :param df: DataFrame original.
    :param col_dependencia: Nombre de la columna que contiene la dependencia.
    :return: Diccionario {dependencia: DataFrame}.
    """

    print(f"📊 DataFrame recibido: {df.shape[0]} filas – {df.shape[1]} columnas")
    print(f"📌 Usando columna de dependencia: '{col_dependencia}'")

    # --- 1. Normalizar dependencias ---
    dependencias_norm = (
        df[col_dependencia]
        .fillna("")
        .replace(r"^\s*$", "", regex=True)
        .apply(lambda x: x if x != "" else "EN BLANCO")
    )

    # Valores únicos
    lista_dep = dependencias_norm.unique()
    print(f"📂 Dependencias encontradas: {len(lista_dep)}")

    # --- 2. Crear un DF por dependencia ---
    dfs_por_dependencia = {}

    print("\n🧱 Generando DataFrames por dependencia...")
    for dep in lista_dep:

        # Filtrar usando la Serie normalizada
        df_dep = df[dependencias_norm == dep].copy()

        # --- 3. Eliminar columnas vacías ---
        df_limpio = df_dep.dropna(axis=1, how="all")

        columnas_eliminadas = df_dep.shape[1] - df_limpio.shape[1]
        if columnas_eliminadas > 0:
            print(f"  - '{dep}': {columnas_eliminadas} columna(s) vacía(s) eliminada(s)")

        dfs_por_dependencia[dep] = df_limpio

    print(f"\n✅ Se generaron {len(dfs_por_dependencia)} DataFrames (limpios) por dependencia.")

    return dfs_por_dependencia


def exportar_dependencias_vform(dfs, ruta_salida, seleccionadas=None):
    """
    Exporta DataFrames generando una carpeta por cada dependencia y,
    dentro de cada carpeta, divide por el campo 'Estado' generando
    un Excel por cada estado encontrado.

    /ruta_salida/
        /Dependencia/
            Iniciativa (Enviada) - Dependencia.xlsx
            Iniciativa (En creación) - Dependencia.xlsx
    """

    # Crear carpeta base si no existe
    os.makedirs(ruta_salida, exist_ok=True)

    # Filtrar dependencias si corresponde
    if seleccionadas is not None:
        dfs = {k: v for k, v in dfs.items() if k in seleccionadas}

    # Función para limpiar caracteres no válidos
    def sanitizar(nombre):
        invalidos = r'\/:*?"<>|'
        for c in invalidos:
            nombre = nombre.replace(c, "_")
        return nombre.strip()

    # Iterar dependencias
    for nombre_dep, df in dfs.items():

        # Sanitizar nombre de la dependencia
        carpeta_dep = sanitizar(nombre_dep)

        # Crear carpeta de la dependencia
        ruta_dep = os.path.join(ruta_salida, carpeta_dep)
        os.makedirs(ruta_dep, exist_ok=True)

        # ---------------------------------------------------
        # 🔥 DIVIDIR POR ESTADO
        # ---------------------------------------------------
        if "Estado" not in df.columns:
            print(f"⚠ La dependencia '{nombre_dep}' no tiene columna 'Estado'.")
            continue

        estados_unicos = df["Estado"].dropna().unique()

        for estado in estados_unicos:

            # Filtrar filas por estado
            df_estado = df[df["Estado"] == estado]

            # Sanitizar nombre del estado
            estado_sanit = sanitizar(str(estado))

            # Nombre del archivo Excel
            archivo_excel = f"Iniciativas ({estado_sanit}) - {carpeta_dep}.xlsx"
            ruta_excel = os.path.join(ruta_dep, archivo_excel)

            # Guardar archivo
            df_estado.to_excel(ruta_excel, index=False)

            print(f"📁 Guardado: {ruta_excel}")

    print("✅ Exportación completa por dependencia y estado.")

