import pandas as pd
import os
import unicodedata
import difflib


# ============================================================
# 🔵 Normalización optimizada
# ============================================================
def normalizar(texto):
    """Normaliza texto (lowercase + sin acentos)."""
    if not isinstance(texto, str):
        return ""

    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# ============================================================
# 🔵 Buscar columna asociada (optimizado)
# ============================================================
def encontrar_columna_asociada(nombre_dep, columnas):
    """
    Encuentra la columna más parecida mediante similitud difusa.
    Optimizada para evitar cálculos repetidos.
    """

    nombre_norm = normalizar(nombre_dep)

    # Normalización vectorizada
    columnas_norm = [normalizar(c) for c in columnas]

    # Buscar coincidencia
    match = difflib.get_close_matches(nombre_norm, columnas_norm, n=1, cutoff=0.6)

    if not match:
        return None

    return columnas[columnas_norm.index(match[0])]


# ============================================================
# 🔵 Subdividir DataFrames por subdependencias (optimizado)
# ============================================================
def dividir_por_subdependencia(dfs):
    """
    Divide los DataFrames según subdependencias detectadas.
    Optimizado para rendimiento y menos ruido en consola.
    """

    resultado = {}
    logs = []  # buffer general

    for nombre_dep, df in dfs.items():
        logs.append(f"\n📁 Procesando dependencia: {nombre_dep}")

        col_asociada = encontrar_columna_asociada(nombre_dep, df.columns)

        if not col_asociada or col_asociada.lower() == "dependencia":
            logs.append("  ⚠ Sin columna asociada → no se subdivide.")
            resultado[nombre_dep] = {nombre_dep: df}
            continue

        logs.append(f"  ➤ Columna asociada: {col_asociada}")

        # Subdivisión optimizada
        grupos = {
            valor: subdf
            for valor, subdf in df.groupby(col_asociada)
            if pd.notna(valor)
        }

        resultado[nombre_dep] = grupos
        logs.append(f"  → Subgrupos generados: {len(grupos)}")

    logs.append("\n✅ Subdivisión completa.")
    print("\n".join(logs))

    return resultado


# ============================================================
# 🔵 Exportar subdependencias (optimizado)
# ============================================================
def exportar_subdependencias(subdfs, ruta_salida, seleccionadas=None):
    """
    Exporta los DataFrames de subdependencias.
    Optimización:
    - Menos I/O
    - Evita creación de carpetas innecesarias
    - Limpieza automática de nombres
    """

    logs = []
    os.makedirs(ruta_salida, exist_ok=True)

    for dependencia, subgrupos in subdfs.items():
        carpeta_dep = os.path.join(
            ruta_salida, dependencia.replace("/", "_").replace(" ", "_")
        )

        exportados = 0

        for subdep, df_sub in subgrupos.items():

            # Filtrar por selección
            if seleccionadas and subdep not in seleccionadas:
                continue

            # Crear carpeta solo si es necesario
            if exportados == 0:
                os.makedirs(carpeta_dep, exist_ok=True)

            # Nombre de archivo limpio
            archivo = f"{str(subdep).replace('/', '_').replace(' ', '_')}.xlsx"
            ruta_archivo = os.path.join(carpeta_dep, archivo)

            df_sub.to_excel(ruta_archivo, index=False)
            logs.append(f"  ✔ Guardado: {ruta_archivo}")

            exportados += 1

        # Eliminar carpeta vacía si no se exportó nada
        if exportados == 0 and os.path.isdir(carpeta_dep):
            try:
                os.rmdir(carpeta_dep)
            except OSError:
                pass

    logs.append(f"\n📂 Exportación completada en: {ruta_salida}")
    print("\n".join(logs))
