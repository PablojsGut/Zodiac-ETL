import os
import pandas as pd

def obtener_dependencias_vform(df: pd.DataFrame, col_index: int = 13):
    """
    Devuelve una lista de dependencias encontradas en el DataFrame,
    reemplazando cualquier valor vacío o NaN por 'EN BLANCO'.
    """

    # 1️⃣ Obtener la columna por índice
    nombre_col = df.columns[col_index]

    # 2️⃣ Procesar la columna para eliminar NaN, espacios y vacíos
    serie = (
        df[nombre_col]
        .astype(str)              # Convertir todo a string
        .replace("nan", "")       # Evitar que 'nan' quede como string
        .fillna("")               # Reemplazar NaN reales
        .str.strip()              # Quitar espacios
        .replace("", "EN BLANCO") # Reemplazar vacíos
    )

    # 3️⃣ Obtener valores únicos ordenados
    dependencias = sorted(set(serie.tolist()))

    # 4️⃣ Asegurar que "EN BLANCO" esté presente (y primero en la lista)
    if "EN BLANCO" in dependencias:
        dependencias.remove("EN BLANCO")
    dependencias.insert(0, "EN BLANCO")

    return dependencias


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


def exportar_dependencias_vform(dfs1, df2, ruta_salida, seleccionadas=None):
    """
    Exporta UN SOLO EXCEL por dependencia con las hojas:

    - "Iniciativas"                         → df1 completo
    - "Sintesis Evaluativa"                 → df2 filtrado completo
    - "Iniciativas (ESTADO)"                → df1 por estado
    - "Sintesis Evaluativa (ESTADO)"        → df2 por estado

    Guarda los archivos directamente en `ruta_salida` sin crear carpetas.

    Retorna:
        dict_df2_filtrados = { dependencia : df2_filtrado }
    """

    os.makedirs(ruta_salida, exist_ok=True)

    # Filtrar dependencias seleccionadas
    if seleccionadas is not None:
        dfs1 = {k: v for k, v in dfs1.items() if k in seleccionadas}

    # Sanitizador
    def sanitizar(nombre):
        for c in r'\/:*?"<>|':
            nombre = nombre.replace(c, "_")
        return str(nombre).strip()

    # Validación
    if "ID" not in df2.columns:
        print("❌ df2 no contiene columna 'ID'.")
        return None

    logs = []
    dict_df2_filtrados = {}

    # ======================================================
    # 🔁 PROCESAR CADA DEPENDENCIA
    # ======================================================
    for dependencia, df1_dep in dfs1.items():

        dep_sanit = sanitizar(dependencia)

        logs.append(f"📌 Procesando dependencia: {dependencia}")

        # -------------------------------------------------------
        # 1️⃣ Filtrar df2 según los IDs de esta dependencia
        # -------------------------------------------------------
        if "ID" not in df1_dep.columns:
            logs.append(f"⚠ '{dependencia}' no tiene columna 'ID' en df1. Saltando df2.")
            df2_dep = pd.DataFrame()
        else:
            ids_dep = df1_dep["ID"].dropna().unique()
            df2_dep = df2[df2["ID"].isin(ids_dep)].copy()

        dict_df2_filtrados[dependencia] = df2_dep

        # -------------------------------------------------------
        # 2️⃣ Crear EXCEL único con todas las hojas
        # -------------------------------------------------------
        archivo_excel = os.path.join(ruta_salida, f"{dep_sanit}.xlsx")

        with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:

            # ---------------------------
            # 🟦 HOJA PRINCIPAL df1
            # ---------------------------
            df1_dep.to_excel(writer, sheet_name="Iniciativas", index=False)

            # ---------------------------
            # 🟩 HOJA PRINCIPAL df2
            # ---------------------------
            df2_dep.to_excel(writer, sheet_name="Sintesis Evaluativa", index=False)

            # ---------------------------
            # 🟦 Hojas por estado df1
            # ---------------------------
            if "Estado" in df1_dep.columns:
                for estado in df1_dep["Estado"].dropna().unique():
                    df_estado = df1_dep[df1_dep["Estado"] == estado]
                    hoja = f"Iniciativas ({sanitizar(str(estado))})"
                    df_estado.to_excel(writer, sheet_name=hoja[:31], index=False)

            # ---------------------------
            # 🟩 Hojas por estado df2
            # ---------------------------
            if "Estado" in df2_dep.columns:
                for estado in df2_dep["Estado"].dropna().unique():
                    df2_estado = df2_dep[df2_dep["Estado"] == estado]
                    hoja = f"Sintesis Evaluativa ({sanitizar(str(estado))})"
                    df2_estado.to_excel(writer, sheet_name=hoja[:31], index=False)

        logs.append(f"📁 Archivo generado: {archivo_excel}")

    logs.append("\n✅ Exportación completa (Dependencias VcM).")

    # Mostrar logs
    print("\n".join(logs))

    return dict_df2_filtrados
