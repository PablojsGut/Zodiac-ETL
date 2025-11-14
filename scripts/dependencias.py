import os
import pandas as pd

def obtener_dependencias(df: pd.DataFrame, col_index: int = 8):
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

def dividir_por_dependencia(df: pd.DataFrame, col_index: int = 8):
    """
    Divide el DataFrame por la columna de Dependencia (por defecto índice 8).
    **Modificación:** Elimina las columnas que están completamente vacías
    (solo contienen NaN) de cada DataFrame resultante.

    :param df: El DataFrame de pandas a dividir.
    :param col_index: El índice (posición) de la columna 'Dependencia'
                      a usar para la división (por defecto es 8).
    :return: Un diccionario donde las claves son los valores únicos de la
             columna 'Dependencia' y los valores son los DataFrames
             correspondientes a cada dependencia, ya limpios de columnas vacías.
    """
    # Muestra el tamaño inicial del DataFrame recibido para seguimiento.
    print(f"DataFrame recibido: {df.shape[0]} filas y {df.shape[1]} columnas")

    # Obtiene el nombre real de la columna usando su índice (col_index).
    col_dependencia = df.columns[col_index]
    print(f"Usando columna: {col_dependencia}")

    # Elimina las filas donde el valor en la columna de dependencia es nulo (NaN).
    df_filtrado = df.dropna(subset=[col_dependencia])

    # Agrupa el DataFrame por los valores únicos de la columna 'col_dependencia'.
    dependencias = {dep: grupo for dep, grupo in df_filtrado.groupby(col_dependencia)}
    
    # Eliminar columnas completamente vacías de cada DataFrame ---
    dependencias_limpias = {}
    print("\n🧹 Limpiando DataFrames (eliminando columnas vacías)...")
    for dep, grupo_df in dependencias.items():
        # df.dropna(axis=1, how='all') elimina columnas (axis=1) donde todos
        # los valores son NaN (how='all').
        grupo_limpio = grupo_df.dropna(axis=1, how='all')
        
        # Mostrar el impacto de la limpieza
        columnas_eliminadas = grupo_df.shape[1] - grupo_limpio.shape[1]
        if columnas_eliminadas > 0:
            print(f"  - '{dep}': Eliminadas {columnas_eliminadas} columna(s) vacía(s).")
            
        dependencias_limpias[dep] = grupo_limpio

    # Muestra la cantidad final de DataFrames (dependencias) generados.
    print(f"\n✅ Se generaron {len(dependencias_limpias)} DataFrames por dependencia (y limpiados).")
    # Retorna el diccionario con los DataFrames divididos y limpiados.
    return dependencias_limpias

def exportar_dependencias(dfs, ruta_salida, seleccionadas=None):
    """
    Exporta los DataFrames contenidos en el diccionario 'dfs' a archivos Excel
    dentro de la carpeta especificada por 'ruta_salida'.

    Si 'seleccionadas' es una lista, exporta sólo los DataFrames
    cuyas claves estén en esa lista.

    :param dfs: Un diccionario donde la clave es el nombre de la dependencia
                y el valor es el DataFrame de pandas correspondiente.
    :param ruta_salida: La ruta (string) de la carpeta donde se guardarán los archivos.
    :param seleccionadas: Una lista (opcional) de nombres de dependencias
                          a exportar. Si es None, exporta todas.
    """
    # Crea la carpeta de salida si no existe.
    # exist_ok=True evita que el código falle si la carpeta ya existe.
    os.makedirs(ruta_salida, exist_ok=True)

    # Bloque de filtrado condicional
    # Si 'seleccionadas' tiene valores (no es None), filtra el diccionario 'dfs'.
    if seleccionadas is not None:
        # Usa una comprensión de diccionario para crear un nuevo diccionario 'dfs'
        # que solo incluye pares (clave, valor) donde la clave (k) está en la
        # lista de seleccionadas.
        dfs = {k: v for k, v in dfs.items() if k in seleccionadas}

    # Itera sobre cada par clave-valor (nombre de dependencia, DataFrame) en el diccionario filtrado (o completo).
    for nombre, df in dfs.items():
        # Crea el nombre del archivo:
        # 1. Toma el nombre de la dependencia (nombre).
        # 2. Reemplaza '/' y espacios (' ') por guiones bajos ('_') para evitar errores
        #    en los nombres de archivo y rutas.
        # 3. Añade la extensión '.xlsx' para indicar que es un archivo Excel.
        nombre_archivo = f"{nombre.replace('/', '_').replace(' ', '_')}.xlsx"
        
        # Construye la ruta completa del archivo:
        # os.path.join maneja correctamente la barra de ruta ('/' o '\') según el sistema operativo.
        ruta_archivo = os.path.join(ruta_salida, nombre_archivo)
        
        # Guarda el DataFrame (df) en la ruta completa como un archivo Excel.
        # index=False evita que la columna de índices de pandas se escriba en el archivo Excel.
        df.to_excel(ruta_archivo, index=False)
        
        # Imprime la ruta del archivo que se acaba de guardar para seguimiento.
        print("📁 Guardado:", ruta_archivo)

    # Mensaje de confirmación final.
    print("✅ Todos los archivos solicitados se exportaron correctamente.")