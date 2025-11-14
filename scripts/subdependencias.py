import pandas as pd
import os
import unicodedata
import difflib

def normalizar(texto):
    """
    Convierte texto a minúsculas, elimina tildes/acentos y otros caracteres diacríticos.

    :param texto: El string de entrada a normalizar.
    :return: El string normalizado, o una cadena vacía si la entrada no es un string.
    """
    # 1. Validación de la entrada:
    # Verifica si la entrada es realmente una cadena de texto (string).
    # Si no lo es (e.g., es un número o NaN), retorna una cadena vacía para evitar errores.
    if not isinstance(texto, str):
        return ""
    
    # 2. Convertir a minúsculas:
    # Pone todo el texto en minúsculas para uniformizar el resultado.
    texto = texto.lower()
    
    # 3. Normalización Unicode y eliminación de acentos:
    # unicodedata.normalize('NFD', texto) descompone los caracteres acentuados
    # en su carácter base + el diacrítico (e.g., 'á' se convierte en 'a' + tilde).
    # La comprensión de lista y el 'join' iteran sobre el texto descompuesto:
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        # unicodedata.category(c) != 'Mn' filtra y excluye los caracteres diacríticos
        # ('Mn' significa Mark, Nonspacing, que son las tildes, diéresis, etc., flotantes).
        if unicodedata.category(c) != 'Mn'
    )
    
    # 4. Retorno:
    return texto


def encontrar_columna_asociada(nombre_dep, columnas):
    """
    Busca la columna más parecida al nombre de la dependencia.

    Utiliza la similitud de cadenas (difflib) sobre los nombres normalizados
    para encontrar una columna que potencialmente represente un subgrupo.

    :param nombre_dep: El nombre de la dependencia padre (string) a buscar.
    :param columnas: Lista de nombres de columnas del DataFrame.
    :return: El nombre original de la columna coincidente (string), o None si no se encuentra.
    """
    # 1. Normalización de los nombres
    # Normaliza el nombre de la dependencia a buscar (minúsculas, sin acentos).
    nombre_norm = normalizar(nombre_dep)
    
    # Normaliza todos los nombres de las columnas del DataFrame para la comparación.
    columnas_norm = [normalizar(c) for c in columnas]

    # 2. Búsqueda de coincidencias cercanas
    # difflib.get_close_matches busca la mejor coincidencia del 'nombre_norm'
    # dentro de la lista 'columnas_norm'.
    # n=1: Pide solo la mejor coincidencia.
    # cutoff=0.6: Define un umbral de similitud mínimo (0.0 a 1.0).
    #             Una similitud menor a 0.6 es descartada.
    coincidencias = difflib.get_close_matches(nombre_norm, columnas_norm, n=1, cutoff=0.6)

    # 3. Retorno del nombre original
    if coincidencias:
        # Se encuentra el índice de la coincidencia (normalizada) dentro de la lista de columnas normalizadas.
        idx = columnas_norm.index(coincidencias[0])
        # Se usa ese índice para obtener y retornar el nombre original de la columna
        # (que conserva mayúsculas, espacios, etc.)
        return columnas[idx]
    else:
        # No se encontró ninguna columna que cumpla con el umbral de similitud (cutoff).
        return None


 

def dividir_por_subdependencia(dfs):
    """
    Divide los DataFrames de un diccionario (generados previamente por dependencia) 
    según la columna asociada más parecida al nombre de la dependencia.
    
    Esta función crea una estructura de diccionario anidada:
    { 'Dependencia_Padre': { 'Subgrupo_Hijo_A': df_A, 'Subgrupo_Hijo_B': df_B } }

    :param dfs: Diccionario de DataFrames, donde la clave es el nombre de la Dependencia.
    :return: Diccionario anidado con los DataFrames subdivididos.
    """
    # Inicializa el diccionario que almacenará los resultados anidados.
    subdivididos = {}

    # Itera sobre cada dependencia (nombre_dep) y su DataFrame asociado (df).
    for nombre_dep, df in dfs.items():
        print(f"\n📁 Procesando dependencia: {nombre_dep}")

        # 1. Detección de Columna Asociada:
        # Llama a la función auxiliar para encontrar la columna que mejor 
        # representa un subgrupo lógico (e.g., 'Programa', 'Carrera').
        col_asociada = encontrar_columna_asociada(nombre_dep, df.columns)

        # 2. Manejo de Caso Sin Subdivisión:
        # Si la columna asociada no se encuentra (None/False) o es la columna 
        # original de agrupación ('Dependencia'), se omite la subdivisión.
        if not col_asociada or col_asociada == 'Dependencia':
            print(f"  ⚠ No se encontró columna asociada (sin subdividir).")
            # El DataFrame completo se asigna como un único subgrupo 
            # (manteniendo la estructura anidada requerida).
            subdivididos[nombre_dep] = {nombre_dep: df}
            continue # Pasa a la siguiente Dependencia Padre.

        print(f"  ➤ Columna asociada detectada: {col_asociada}")

        # 3. Subdivisión del DataFrame:
        # Agrupa el DataFrame (df) por los valores únicos de la columna detectada.
        grupos = {
            # Se usa una comprensión de diccionario para crear los pares:
            # valor (nombre del subgrupo) : grupo (DataFrame del subgrupo).
            valor: grupo for valor, grupo in df.groupby(col_asociada)
            # Filtro: Excluye la creación de subgrupos cuyo nombre (valor) sea nulo (NaN).
            if pd.notna(valor)
        }

        # 4. Almacenamiento y Reporte:
        # Almacena el diccionario de subgrupos bajo la clave de la Dependencia Padre.
        subdivididos[nombre_dep] = grupos
        print(f"  → Se generaron {len(grupos)} subgrupos")

    # 5. Finalización:
    print("\n✅ Subdivisión completa.")
    return subdivididos


def exportar_subdependencias(subdfs, ruta_salida, seleccionadas=None):
    """
    Exporta cada DataFrame de subdependencia a un archivo Excel.

    Solo crea las carpetas de las dependencias que tengan al menos una subdependencia exportada.
    """
    os.makedirs(ruta_salida, exist_ok=True)

    for dependencia, subgrupos in subdfs.items():
        nombre_carpeta = dependencia.replace("/", "_").replace(" ", "_")
        carpeta_dep = os.path.join(ruta_salida, nombre_carpeta)

        subdeps_exportadas = 0  # Contador de archivos creados por dependencia

        for subdep, df_sub in subgrupos.items():
            # Si hay filtro de selección y esta subdependencia no está seleccionada, la saltamos
            if seleccionadas and subdep not in seleccionadas:
                continue

            # Solo creamos la carpeta si realmente vamos a guardar algo dentro
            if subdeps_exportadas == 0:
                os.makedirs(carpeta_dep, exist_ok=True)

            nombre_archivo_limpio = f"{str(subdep).replace('/', '_').replace(' ', '_')}.xlsx"
            nombre_archivo = os.path.join(carpeta_dep, nombre_archivo_limpio)

            df_sub.to_excel(nombre_archivo, index=False)
            subdeps_exportadas += 1

            print(f"✅ Guardado: {nombre_archivo}")

        # Si no se exportó nada, no se crea carpeta vacía
        if subdeps_exportadas == 0 and os.path.exists(carpeta_dep):
            try:
                os.rmdir(carpeta_dep)  # Borra carpeta vacía (por seguridad)
            except OSError:
                pass  # Ignora si no está vacía o no se puede eliminar

    print("\n📂 Archivos exportados correctamente en la carpeta:", ruta_salida)
