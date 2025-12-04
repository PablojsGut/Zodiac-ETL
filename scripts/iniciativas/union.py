import os
import pandas as pd

def unir_dataset(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Une df1 y df2 utilizando la columna 'ID'.
    - Mantiene todas las filas de df1 (LEFT JOIN).
    - Incluye todas las columnas de df1 y todas las de df2.
    - IDs sin coincidencia en df2 quedan con NaN.
    
    Retorna:
        df_unido, logs
    """

    logs = []
    logs.append("🔗 Iniciando unión de datasets (df1 + df2)")

    # -------------------------------
    # 1️⃣ Validaciones
    # -------------------------------
    if "ID" not in df1.columns:
        logs.append("❌ df1 no contiene columna 'ID'.")
        print("\n".join(logs))
        return None, logs

    if "ID" not in df2.columns:
        logs.append("❌ df2 no contiene columna 'ID'.")
        print("\n".join(logs))
        return None, logs

    logs.append(f"📊 df1: {df1.shape[0]} filas – {df1.shape[1]} columnas")
    logs.append(f"📊 df2: {df2.shape[0]} filas – {df2.shape[1]} columnas")

    # -------------------------------
    # 2️⃣ Información sobre IDs
    # -------------------------------
    ids_df1 = set(df1["ID"].dropna().unique())
    ids_df2 = set(df2["ID"].dropna().unique())

    ids_comunes = ids_df1 & ids_df2
    ids_sin_df2 = ids_df1 - ids_df2

    logs.append(f"🔍 Coincidencias de ID: {len(ids_comunes)}")
    logs.append(f"⚠ IDs sin correspondencia en df2: {len(ids_sin_df2)}")

    # -------------------------------
    # 3️⃣ MERGE sin sufijos
    # -------------------------------
    logs.append("📥 Realizando merge LEFT (df1 como principal)...")

    df_unido = df1.merge(df2, on="ID", how="left")

    logs.append(f"📁 Unión completada: {df_unido.shape[0]} filas – {df_unido.shape[1]} columnas")

    # -------------------------------
    # 4️⃣ Columnas nuevas
    # -------------------------------
    columnas_nuevas = [c for c in df_unido.columns if c not in df1.columns]
    logs.append(f"🆕 Columnas agregadas desde df2: {len(columnas_nuevas)}")

    # -------------------------------
    # 5️⃣ Finalización
    # -------------------------------
    logs.append("✅ Unión de datasets finalizada correctamente.")

    print("\n".join(logs))
    return df_unido


def exportar_union(df_unido, ruta_salida, nombre="Union"):
    """
    Exporta un único archivo Excel con el DataFrame unido y hojas según Estado,
    respetando el estilo de logs utilizado en las otras funciones del proyecto.

    Hojas generadas:
        - "Dataset Unificado"
        - "Dataset Unificado (ESTADO)"  → por cada estado

    Parámetros:
        df_unido:  DataFrame ya unido por 'unir_dataset'
        ruta_salida: carpeta donde se guardará el archivo
        nombre: nombre base del archivo Excel (sin extensión)

    Retorna:
        logs: lista con todos los mensajes generados
    """

    os.makedirs(ruta_salida, exist_ok=True)

    logs = []

    # Sanitizar nombre del archivo
    def sanitizar(nombre):
        for c in r'\/:*?"<>|':
            nombre = nombre.replace(c, "_")
        return str(nombre).strip()

    nombre_sanit = sanitizar(nombre)
    archivo_excel = os.path.join(ruta_salida, f"{nombre_sanit}.xlsx")

    logs.append("🔗 Iniciando exportación de dataset unificado...")

    # -----------------------------------------------------
    # Validación
    # -----------------------------------------------------
    if not isinstance(df_unido, pd.DataFrame):
        logs.append("❌ df_unido no es un DataFrame válido.")
        print("\n".join(logs))
        return logs

    logs.append(f"📊 Filas: {df_unido.shape[0]}, Columnas: {df_unido.shape[1]}")

    # -----------------------------------------------------
    # Crear EXCEL
    # -----------------------------------------------------
    with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:

        # ----------------------------------
        # 🟦 Hoja principal
        # ----------------------------------
        df_unido.to_excel(writer, sheet_name="Dataset Unificado", index=False)

        # ----------------------------------
        # 🟦 Hojas por ESTADO
        # ----------------------------------
        if "Estado" in df_unido.columns:
            estados = df_unido["Estado"].dropna().unique()

            logs.append(f"📌 Estados detectados: {len(estados)}")

            for estado in estados:
                df_estado = df_unido[df_unido["Estado"] == estado]
                hoja = f"Dataset ({sanitizar(str(estado))})"
                df_estado.to_excel(writer, sheet_name=hoja[:31], index=False)

    logs.append(f"📁 Archivo generado: {archivo_excel}")
    logs.append("✅ Exportación del dataset unificado completada.")

    print("\n".join(logs))
    return logs
