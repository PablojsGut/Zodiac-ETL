import os

def exportar_dependencias(dfs, ruta_salida, seleccionadas=None):
    """
    Exporta los DataFrames de dependencias en la carpeta indicada.
    Si 'seleccionadas' es una lista, exporta sólo esas dependencias.
    """
    os.makedirs(ruta_salida, exist_ok=True)

    # Si se pasa lista de seleccionadas, filtrar
    if seleccionadas is not None:
        dfs = {k: v for k, v in dfs.items() if k in seleccionadas}

    for nombre, df in dfs.items():
        nombre_archivo = f"{nombre.replace('/', '_').replace(' ', '_')}.xlsx"
        ruta_archivo = os.path.join(ruta_salida, nombre_archivo)
        df.to_excel(ruta_archivo, index=False)
        print("📁 Guardado:", ruta_archivo)

    print("✅ Todos los archivos solicitados se exportaron correctamente.")


def eliminar_columnas_por_indice(dfs, dependencia, indices):
    """
    Elimina columnas de una dependencia específica por índices.
    """
    df = dfs.get(dependencia)
    if df is None:
        print(f"⚠️ No existe la dependencia: {dependencia}")
        return
    try:
        df.drop(df.columns[indices], axis=1, inplace=True)
        print(f"🗑️ Columnas {indices} eliminadas de '{dependencia}'")
    except Exception as e:
        print(f"❌ Error eliminando columnas de {dependencia}: {e}")
