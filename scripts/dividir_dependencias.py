import pandas as pd

def dividir_por_dependencia(df: pd.DataFrame, col_index: int = 8):
    """
    Divide el DataFrame por la columna de Dependencia (por defecto índice 8).
    """
    print(f"DataFrame recibido: {df.shape[0]} filas y {df.shape[1]} columnas")

    col_dependencia = df.columns[col_index]
    print(f"Usando columna: {col_dependencia}")

    df = df.dropna(subset=[col_dependencia])

    dependencias = {dep: grupo for dep, grupo in df.groupby(col_dependencia)}

    print(f"\n✅ Se generaron {len(dependencias)} DataFrames por dependencia.")
    return dependencias
