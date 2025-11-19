import os
import pandas as pd


def obtener_dependencias(df: pd.DataFrame, col_index: int = 8):
    """
    Retorna una lista ordenada de dependencias únicas, ignorando valores nulos.
    """
    col = df.columns[col_index]
    return sorted(df[col].dropna().unique().tolist())


def dividir_por_dependencia(df: pd.DataFrame, col_index: int = 8):
    """
    Divide el DataFrame por la columna indicada y elimina columnas completamente vacías.
    """
    log = []  # 🔵 acumulador de logs

    col = df.columns[col_index]
    log.append(f"📊 DataFrame recibido: {df.shape[0]} filas, {df.shape[1]} columnas")
    log.append(f"➡ Usando columna de dependencia: {col}")

    # Filtrar filas sin dependencia
    df_filtrado = df.dropna(subset=[col])

    # Agrupamiento por dependencia
    dependencias = {dep: g.dropna(axis=1, how='all') for dep, g in df_filtrado.groupby(col)}

    # Reporte de limpieza
    log.append("\n🧹 Limpieza de columnas vacías:")
    for dep, g in dependencias.items():
        eliminadas = df.shape[1] - g.shape[1]
        if eliminadas:
            log.append(f"  - {dep}: eliminadas {eliminadas} columnas vacías.")

    log.append(f"\n✅ Generados {len(dependencias)} DataFrames limpios por dependencia.\n")

    print("\n".join(log))  # 🔵 un solo print final
    return dependencias



def exportar_dependencias(dfs, ruta_salida, seleccionadas=None):
    """
    Exporta los DataFrames en archivos Excel según la selección indicada.
    """
    log = []  # 🔵 acumulador de logs

    os.makedirs(ruta_salida, exist_ok=True)

    # Aplicar filtro si corresponde
    if seleccionadas is not None:
        dfs = {k: v for k, v in dfs.items() if k in seleccionadas}

    for nombre, df in dfs.items():
        archivo = f"{nombre.replace('/', '_').replace(' ', '_')}.xlsx"
        ruta = os.path.join(ruta_salida, archivo)

        df.to_excel(ruta, index=False)
        log.append(f"📁 Guardado: {ruta}")

    log.append("\n✅ Exportación finalizada correctamente.")

    print("\n".join(log))  # 🔵 único print final

