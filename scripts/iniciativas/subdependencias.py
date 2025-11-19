import pandas as pd
import os
import unicodedata
import re
import difflib

def normalizar_cadena(texto: str):
    """Normaliza cadenas para evitar duplicados por diferencias mínimas."""
    if texto is None:
        return ""

    # Convertir a string siempre
    texto = str(texto)

    # Normalizar unicode (quita tildes)
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')

    # Quitar caracteres invisibles
    texto = texto.replace("\xa0", " ")

    # Simplificar plurales muy frecuentes (ej. 'Matematica' => 'Matematicas')
    texto = re.sub(r"\bmatematica(s)?\b", "matematicas", texto, flags=re.I)

    # Minúsculas
    texto = texto.lower()

    # Quitar espacios repetidos
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

def simplificar_frase(texto: str):
    """Normaliza, singulariza y simplifica para mejorar coincidencias."""
    t = normalizar_cadena(texto)
    # Quitar plural simple (terminación s / es)
    if t.endswith("es"):
        t = t[:-2]
    elif t.endswith("s"):
        t = t[:-1]
    return t


def mejor_coincidencia(dep_norm, columnas_norm_map):
    """Encuentra mejor columna candidata usando coincidencia difusa."""
    candidatos = list(columnas_norm_map.keys())
    match = difflib.get_close_matches(dep_norm, candidatos, n=1, cutoff=0.7)
    return match[0] if match else None


def dividir_subdependencias_vform(df: pd.DataFrame):

    columnas = df.columns.tolist()
    dep_col = "Unidad o Dependencia Responsable"

    # 1️⃣ Normalización global dependencia
    dep_series = (
        df[dep_col]
        .astype(str)
        .replace("nan", "")
        .fillna("")
        .str.replace(r"^\s*$", "", regex=True)
        .apply(lambda x: x if x.strip() != "" else "EN BLANCO")
    )

    dependencias_unicas = dep_series.unique()
    resultado = {}

    # Crear mapa normalizado → columna original
    columnas_norm_map = {simplificar_frase(col): col for col in columnas}

    for dep in dependencias_unicas:

        df_dep = df[dep_series == dep].copy()
        dep_norm = simplificar_frase(dep)

        # ---------------------------
        # 2️⃣ Detectar subdependencia
        # ---------------------------

        subdep_col = None

        # Caso especial: Otras Unidades
        if "otras unidad" in dep_norm:
            if "Otras Unidades No Académicas" in columnas:
                subdep_col = "Otras Unidades No Académicas"

        else:
            # 1) Intento directo exacto
            if dep_norm in columnas_norm_map:
                subdep_col = columnas_norm_map[dep_norm]

            else:
                # 2) Intento por coincidencia parcial flexible
                mejor_norm = mejor_coincidencia(dep_norm, columnas_norm_map)
                if mejor_norm:
                    subdep_col = columnas_norm_map[mejor_norm]

        # --------------------------------------------
        # CASO: Sin subdependencia detectada
        # --------------------------------------------
        if subdep_col is None:
            df_dep = df_dep.dropna(axis=1, how="all")
            resultado[dep] = df_dep
            continue

        # --------------------------------------------
        # 3️⃣ Construcción de serie de subdependencias
        # --------------------------------------------
        if "otras unidad" in dep_norm:

            col1 = "Otras Unidades No Académicas"
            col2 = "Otras Unidades No Académicas.1" if "Otras Unidades No Académicas.1" in df_dep else None

            def obtener_subdep(row):
                if row[col1] == "Otra" and col2:
                    return row[col2]
                return row[col1]

            subseries_raw = df_dep.apply(obtener_subdep, axis=1)

        else:
            subseries_raw = df_dep[subdep_col].fillna(dep)

        # Normalizar subdependencias
        subseries = subseries_raw.apply(normalizar_cadena)

        # --------------------------------------------
        # 4️⃣ Crear DF por subdependencia
        # --------------------------------------------
        grupos = {}
        mapa_original = {}

        for i, valor_raw in enumerate(subseries_raw):
            norm = subseries.iloc[i]
            if norm not in mapa_original:
                mapa_original[norm] = str(valor_raw).strip() if str(valor_raw).strip() else dep

        for norm_key in subseries.unique():
            df_sub = df_dep[subseries == norm_key].copy()
            df_sub = df_sub.dropna(axis=1, how="all")
            grupos[mapa_original[norm_key]] = df_sub

        resultado[dep] = grupos

    return resultado



def exportar_subdependencias_vform(subdfs, df2, ruta_salida, seleccionadas=None):
    """
    Exporta UN SOLO EXCEL POR SUBDEPENDENCIA con las siguientes hojas:

    - "Iniciativas"                          → df_sub completo
    - "Sintesis Evaluativa"                  → df2 filtrado completo
    - "Iniciativas (ESTADO)"                 → df_sub por estado
    - "Sintesis Evaluativa (ESTADO)"         → df2 filtrado por estado

    Retorna:
        dict_df2_filtrado[(dependencia, subdependencia)] = df2 filtrado
    """

    os.makedirs(ruta_salida, exist_ok=True)

    def sanitizar(nombre):
        for c in r'\/:*?"<>|':
            nombre = nombre.replace(c, "_")
        return str(nombre).strip()

    logs = []
    dict_df2_filtrado = {}   # <-- lo que se retorna al final

    # =====================================================
    # 🔁 PROCESAR CADA DEPENDENCIA
    # =====================================================
    for dependencia, subgrupos in subdfs.items():

        carpeta_dep = os.path.join(ruta_salida, sanitizar(dependencia))
        exportados = 0

        # Dependencia sin subdependencias
        if isinstance(subgrupos, pd.DataFrame):
            subgrupos = { dependencia: subgrupos }

        # =====================================================
        # 🔁 PROCESAR SUBDEPENDENCIAS
        # =====================================================
        for subdep, df_sub in subgrupos.items():

            # Saltar si no está seleccionada
            if seleccionadas and subdep not in seleccionadas:
                continue

            os.makedirs(carpeta_dep, exist_ok=True)

            subdep_sanit = sanitizar(subdep)
            archivo_excel = os.path.join(carpeta_dep, f"{subdep_sanit}.xlsx")

            # ============================================
            # 2️⃣ Filtrar df2 por los IDs de esta subdependencia
            # ============================================
            if "ID" in df_sub.columns and "ID" in df2.columns:
                ids_sub = df_sub["ID"].dropna().unique()
                df2_filtrado = df2[df2["ID"].isin(ids_sub)].copy()
            else:
                df2_filtrado = pd.DataFrame()

            dict_df2_filtrado[(dependencia, subdep)] = df2_filtrado

            # ============================================
            # 📘 CREAR EXCEL CON MÚLTIPLES HOJAS
            # ============================================
            with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:

                # 🟦 Hoja principal 1
                df_sub.to_excel(writer, sheet_name="Iniciativas", index=False)

                # 🟩 Hoja principal 2
                df2_filtrado.to_excel(writer, sheet_name="Sintesis Evaluativa", index=False)

                # ----------------------------
                # 🟦 Hojas por ESTADO df_sub
                # ----------------------------
                if "Estado" in df_sub.columns:
                    for estado in df_sub["Estado"].dropna().unique():
                        df_estado = df_sub[df_sub["Estado"] == estado]
                        hoja = f"Iniciativas ({sanitizar(estado)})"
                        df_estado.to_excel(writer, sheet_name=hoja[:31], index=False)

                # ----------------------------
                # 🟩 Hojas por ESTADO df2
                # ----------------------------
                if "Estado" in df2_filtrado.columns:
                    for estado in df2_filtrado["Estado"].dropna().unique():
                        df2_estado = df2_filtrado[df2_filtrado["Estado"] == estado]
                        hoja = f"Sintesis Evaluativa ({sanitizar(estado)})"
                        df2_estado.to_excel(writer, sheet_name=hoja[:31], index=False)

            exportados += 1

        # Si no exportó nada, eliminar carpeta
        if exportados == 0 and os.path.isdir(carpeta_dep):
            try:
                os.rmdir(carpeta_dep)
            except OSError:
                pass

        logs.append(f"📁 Dependencia procesada: {dependencia}")

    logs.append(f"\n✅ Exportación completa en: {ruta_salida}")
    print("\n".join(logs))

    return dict_df2_filtrado


