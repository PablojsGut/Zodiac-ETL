import os
import io
import matplotlib.pyplot as plt
import textwrap
import numpy as np
import pandas as pd
import unicodedata
import matplotlib.gridspec as gridspec
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors


# ================================================================
# 🔤 Función utilitaria: normalizar nombres de columnas
# ================================================================
def normalizar_columna(nombre):
    """Convierte un nombre de columna a formato normalizado (sin tildes, espacios ni mayúsculas)."""
    if not isinstance(nombre, str):
        return ""
    nombre = nombre.lower()
    nombre = ''.join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    )
    nombre = nombre.replace(" ", "").replace("\u00a0", "")
    return nombre


# ================================================================
# 📊 Gráfico de conteo por sede
# ================================================================
def graficar_conteo_sedes(df):
    """Genera gráfico de conteo por Sede y devuelve BytesIO con la imagen (png)."""
    if 'Sede a la que Pertenece' not in df.columns:
        return None

    sedes = df['Sede a la que Pertenece'].astype(str)
    sedes = sedes.str.split(';').explode().str.strip()
    sedes = sedes[sedes != '']
    sedes = sedes.dropna()
    sedes = sedes.str.title()

    conteo = sedes.value_counts().reset_index()
    conteo.columns = ['Sede', 'Cantidad']

    if conteo.empty:
        return None

    fig = plt.figure(figsize=(10, 7))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

    ax1 = fig.add_subplot(gs[0])
    ax1.barh(conteo['Sede'], conteo['Cantidad'], color='skyblue', edgecolor='black')
    ax1.set_xlabel('Cantidad de registros')
    ax1.set_ylabel('Sede')
    ax1.set_title('Cantidad de registros por sede', pad=15)
    ax1.invert_yaxis()

    ax2 = fig.add_subplot(gs[1])
    ax2.axis('off')
    tabla = ax2.table(
        cellText=conteo.values,
        colLabels=conteo.columns,
        cellLoc='center',
        loc='center'
    )
    tabla.scale(1, 1.3)
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(9)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(fig)
    buffer.seek(0)
    return buffer


# ================================================================
# 🥧 Gráfico de participación
# ================================================================
def graficar_participacion(dataset, dependencia=None, subdependencia=None):
    """
    Genera un gráfico de torta con tabla resumen debajo con texto legible.
    """

    # 🧩 Determinar el DataFrame correcto
    if isinstance(dataset, pd.DataFrame):
        df = dataset
    elif isinstance(dataset, dict):
        if dependencia and subdependencia:
            try:
                df = dataset[dependencia][subdependencia]
            except (KeyError, TypeError):
                print(f"⚠ No se encontró {dependencia} / {subdependencia} en dataset.")
                return None
        elif dependencia:
            try:
                df = dataset[dependencia]
            except (KeyError, TypeError):
                print(f"⚠ No se encontró la dependencia '{dependencia}'.")
                return None
        else:
            print("⚠ Se requiere al menos una dependencia para acceder al dataset jerárquico.")
            return None
    else:
        print("⚠ Tipo de dataset no reconocido.")
        return None

    # 🔎 Columna de participación
    col_part = next((c for c in df.columns if "Tipo de Participación" in c), None)
    if not col_part:
        print("⚠ No se encontró la columna de participación.")
        return None

    participacion = df[col_part].dropna().astype(str).str.strip()
    conteo = participacion.value_counts()
    if conteo.empty:
        print("⚠ No hay valores válidos en la columna de participación.")
        return None

    # 🥧 Gráfico de torta (AUMENTO tamaños de texto)
    fig, ax = plt.subplots(figsize=(10, 10))  # FIGURA MÁS GRANDE
    wedges, texts, autotexts = ax.pie(
        conteo.values,
        autopct='%1.1f%%',
        startangle=90,
        shadow=True,
        textprops={'fontsize': 14}  # TEXTO MÁS GRANDE
    )

    # autopct legible
    for t in autotexts:
        t.set_fontsize(14)

    titulo = f"Distribución de Participación ({dependencia or 'Todos los datos'}" \
              + (f" / {subdependencia}" if subdependencia else "") + ")"
    ax.set_title(titulo, pad=25, fontsize=18)  # TÍTULO MÁS GRANDE
    ax.axis('equal')

    # 🎨 Tabla resumen
    colores = [w.get_facecolor() for w in wedges]
    porcentajes = (conteo / conteo.sum() * 100).round(1).astype(str) + '%'

    resumen = pd.DataFrame({
        "Color": ["■"] * len(conteo),
        "Participación": conteo.index,
        "Cantidad": conteo.values,
        "Porcentaje": porcentajes.values
    })

    # Envolver texto
    resumen["Participación"] = [
        textwrap.fill(str(texto), width=40) for texto in resumen["Participación"]
    ]

    # Contar líneas
    line_counts = [t.count("\n") + 1 for t in resumen["Participación"]]
    max_lines = max(line_counts)

    # MÁS ESPACIO PARA LA TABLA
    plt.subplots_adjust(bottom=0.40 + 0.03 * max_lines)

    # TABLA (FUENTE MÁS GRANDE)
    tabla = plt.table(
        cellText=resumen.values,
        colLabels=resumen.columns,
        cellLoc='center',
        loc='bottom'
    )

    tabla.auto_set_font_size(False)
    tabla.set_fontsize(12)   # LETRA MÁS GRANDE

    # Pintar columna color
    for i, color in enumerate(colores, start=1):
        tabla[(i, 0)].set_facecolor(color)
        tabla[(i, 0)]._text.set_text("")

    # Anchos de columna
    col_widths = [0.08, 0.55, 0.18, 0.19]
    for j, width in enumerate(col_widths):
        for key, cell in tabla.get_celld().items():
            if key[1] == j:
                cell.set_width(width)
                cell.set_text_props(wrap=True, ha='center', va='center')

    # Alturas (más grande para evitar aplastamiento)
    base_height = 0.07  # ANCHO MAYOR
    for i, lines in enumerate(line_counts, start=1):
        row_height = base_height * min(lines, 10)  # PERMITE MÁS LÍNEAS
        for j in range(len(resumen.columns)):
            cell = tabla.get_celld().get((i, j))
            if cell:
                cell.set_height(row_height)

    # Guardar imagen nítida
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')  # DPI MÁS ALTO
    plt.close(fig)
    buffer.seek(0)

    return buffer


# ================================================================
# 📈 Gráfico de Gantt (solo gráfico)
# ================================================================
def graficar_gantt(dataset, dependencia=None, subdependencia=None):
    """
    Genera gráfico de Gantt y devuelve BytesIO con la imagen (png).
    Versión SIN normalizar nombres de columnas.
    Solo funciona si los nombres están EXACTAMENTE como en el Excel.
    """

    # -----------------------------
    # 🧩 Determinar DataFrame real
    # -----------------------------
    if isinstance(dataset, pd.DataFrame):
        df = dataset
    elif isinstance(dataset, dict):
        if dependencia and subdependencia:
            df = dataset.get(dependencia, {}).get(subdependencia)
        elif dependencia:
            df = dataset.get(dependencia)
        else:
            print("⚠ Se requiere dependencia para acceder al dataset jerárquico.")
            return None
    else:
        print("⚠ Tipo de dataset no reconocido.")
        return None

    if df is None:
        print(f"⚠ Dataset vacío para {dependencia} / {subdependencia}.")
        return None

    # -------------------------------------------------------
    # 📌 Nombres EXACTOS de las columnas (sin normalización)
    # -------------------------------------------------------
    col_inicio = "Fecha de inicio de participación en la actividad"
    col_fin    = "Fecha de término de participación en la actividad"

    # --------------------------
    # ❌ Validación de columnas
    # --------------------------
    if col_inicio not in df.columns or col_fin not in df.columns:
        print(f"⚠ No se encontraron columnas de fecha en {dependencia or 'dataset'}")
        print("   Columnas disponibles:", list(df.columns))
        return None

    # ----------------------
    # 🧼 Limpieza y orden
    # ----------------------
    df_plot = df.copy()
    df_plot[col_inicio] = pd.to_datetime(df_plot[col_inicio], errors="coerce")
    df_plot[col_fin] = pd.to_datetime(df_plot[col_fin], errors="coerce")
    df_plot = df_plot.dropna(subset=[col_inicio, col_fin])

    if df_plot.empty:
        print("⚠ No hay filas válidas con fechas para Gantt.")
        return None

    df_plot = df_plot.sort_values(col_inicio).reset_index(drop=True)

    y_labels = (
        df_plot["Id"].astype(str).tolist()
        if "Id" in df_plot.columns
        else list(range(1, len(df_plot) + 1))
    )
    y_pos = np.arange(len(y_labels))
    duraciones = (df_plot[col_fin] - df_plot[col_inicio]).dt.days

    # -------------------------
    # 📈 Gráfico de Gantt
    # -------------------------
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.barh(
        y=y_pos,
        width=duraciones,
        left=df_plot[col_inicio],
        color='skyblue',
        edgecolor='black'
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Fecha")
    ax.set_ylabel("ID del Registro")
    titulo = f"Duración de participación - {dependencia or 'Datos'}" + \
             (f" / {subdependencia}" if subdependencia else "")

    ax.set_title(titulo, fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # ---------------------
    # 💾 Guardar a buffer
    # ---------------------
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    return buffer



# ================================================================
# 🧾 Tabla resumen (separada del gráfico)
# ================================================================
def crear_tabla_resumen(dataset):
    """Crea una tabla resumen con ajuste automático de texto y ancho limitado."""
    
    # Columnas esperadas y sus nombres amigables
    columnas_originales = {
        "Id": "Id",
        "Correo electrónico": "Correo electrónico",
        "Tipo de Participación": "Tipo de Participación",
        "Sede a la que Pertenece": "Sede",
        "Fecha de inicio de participación en la actividad": "Fecha Inicio"
    }

    # Filtrar solo las columnas que existen
    columnas_existentes = {k: v for k, v in columnas_originales.items() if k in dataset.columns}
    if not columnas_existentes:
        return None

    # Crear dataset reducido
    df_mostrar = dataset[list(columnas_existentes.keys())].copy().fillna("")

    # Formatear fecha dd/mm/yyyy
    if "Fecha de inicio de participación en la actividad" in df_mostrar.columns:
        df_mostrar["Fecha de inicio de participación en la actividad"] = pd.to_datetime(
            df_mostrar["Fecha de inicio de participación en la actividad"], errors="coerce"
        ).dt.strftime("%d/%m/%Y").fillna("")

    # Insertar numeración
    df_mostrar.insert(0, "N°", range(1, len(df_mostrar) + 1))

    # Renombrar columnas
    df_mostrar.rename(columns=columnas_existentes, inplace=True)

    # --- 🔤 Preparar estilos para texto ajustable ---
    estilo_celda = ParagraphStyle(
        name='TablaTexto',
        alignment=TA_LEFT,
        fontSize=7,
        leading=8,
        wordWrap='CJK'  # ← activa el ajuste de texto largo
    )

    estilo_encabezado = ParagraphStyle(
        name='Encabezado',
        alignment=TA_CENTER,
        fontSize=8,
        leading=9,
        textColor=colors.black,
        spaceAfter=2,
        wordWrap='CJK'
    )

    # --- Convertir a lista de listas (con Paragraph para permitir salto de línea) ---
    encabezados = [Paragraph(str(col), estilo_encabezado) for col in df_mostrar.columns]
    filas = [
        [Paragraph(str(c), estilo_celda) for c in fila]
        for fila in df_mostrar.values.tolist()
    ]

    tabla_datos = [encabezados] + filas

    # --- 🧱 Crear tabla ---
    tabla = Table(tabla_datos, repeatRows=1)

    # --- 🎨 Estilos visuales ---
    tabla_estilo = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ])
    tabla.setStyle(tabla_estilo)

    # --- 📏 Ajustar ancho máximo de columnas (evita que se salga de la hoja) ---
    total_ancho = 500  # ~ancho útil en A4 vertical con márgenes
    col_proporciones = [0.5, 1.0, 2.2, 2.0, 2.0, 1.5]
    col_widths = [total_ancho * (p / sum(col_proporciones)) for p in col_proporciones[:len(df_mostrar.columns)]]
    tabla._argW = col_widths

    return tabla

def generar_grafico_ambitos(dataset):
    """
    Genera gráficos de torta con porcentajes dentro del gráfico
    y tabla inferior con texto legible. Sin labels externos.
    """

    columna_tipo = "Tipo de Participación"
    columna_ambitos = "Ámbitos Estratégicos que Aborda la Actividad"

    if columna_tipo not in dataset.columns or columna_ambitos not in dataset.columns:
        print("❌ No existen las columnas necesarias en el dataset.")
        return {}

    resultados = {}

    for tipo, df_tipo in dataset.groupby(columna_tipo):

        ambitos_expandidos = (
            df_tipo[columna_ambitos]
            .dropna()
            .str.split(";")
            .explode()
            .str.strip()
        )

        if ambitos_expandidos.empty:
            print(f"⚠ Sin datos para '{tipo}'")
            continue

        conteo = ambitos_expandidos.value_counts()
        porcentajes = (conteo / conteo.sum() * 100).round(1).astype(str) + "%"

        # --- FIGURA MÁS GRANDE PARA EVITAR APLASTAMIENTO ---
        fig, ax = plt.subplots(figsize=(10, 11))

        wedges, texts, autotexts = ax.pie(
            conteo.values,
            labels=None,              # ❌ SIN LABELS
            autopct="%1.1f%%",
            startangle=90,
            textprops={'fontsize': 14}  # ✔ Porcentajes más grandes
        )

        # Fuente del porcentaje
        for t in autotexts:
            t.set_fontsize(14)

        # ✔ Título más grande y con suficiente espacio
        ax.set_title(
            f"Distribución de Ámbitos Estratégicos\n({tipo})",
            pad=30,
            fontsize=18
        )

        ax.axis("equal")

        # --- Tabla resumen ---
        colores = [w.get_facecolor() for w in wedges]

        tabla_df = pd.DataFrame({
            "Color": ["■"] * len(conteo),
            "Ámbito Estratégico": conteo.index.astype(str),
            "Cantidad": conteo.values,
            "Porcentaje": porcentajes.values
        })

        # Envolver texto largo
        tabla_df["Ámbito Estratégico"] = [
            textwrap.fill(v, width=38) for v in tabla_df["Ámbito Estratégico"]
        ]

        # Contar líneas
        line_counts = [
            t.count("\n") + 1 for t in tabla_df["Ámbito Estratégico"]
        ]
        max_lines = max(line_counts)

        # ✔ MÁS ESPACIO PARA LA TABLA SIN EXPLOTAR PÁGINA
        plt.subplots_adjust(bottom=0.30 + 0.025 * max_lines)

        tabla = plt.table(
            cellText=tabla_df.values,
            colLabels=tabla_df.columns,
            cellLoc='center',
            loc='bottom'
        )

        tabla.auto_set_font_size(False)
        tabla.set_fontsize(12)  # ✔ Texto de la tabla más legible

        # Pintar columna color
        for i, color in enumerate(colores, start=1):
            cell = tabla[(i, 0)]
            cell.set_facecolor(color)
            cell._text.set_text("")

        # Anchos de columna
        col_widths = [0.07, 0.60, 0.15, 0.18]
        for j, width in enumerate(col_widths):
            for key, cell in tabla.get_celld().items():
                if key[1] == j:
                    cell.set_width(width)

        # Alturas dinámicas
        base_height = 0.07
        for i, lines in enumerate(line_counts, start=1):
            row_height = base_height * min(lines, 8)
            for j in range(len(tabla_df.columns)):
                cell = tabla.get_celld().get((i, j))
                if cell:
                    cell.set_height(row_height)

        # Guardar gráfica
        buffer_img = io.BytesIO()
        plt.savefig(buffer_img, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        buffer_img.seek(0)

        resultados[tipo] = buffer_img

    return resultados

def generar_grafico_ods(dataset):
    """
    Genera gráficos de torta que muestran la distribución porcentual de:
    
    'Objetivos de Desarrollo Sostenible (ODS) que Apoya la Actividad'
    
    por cada Tipo de Participación.
    
    Devuelve:
        { tipo_participacion: buffer_png }
    """

    columna_tipo = "Tipo de Participación"
    columna_ods = "Objetivos de Desarrollo Sostenible (ODS) que Apoya la Actividad"

    if columna_tipo not in dataset.columns or columna_ods not in dataset.columns:
        print("❌ No existen las columnas necesarias en el dataset.")
        return {}

    resultados = {}

    for tipo, df_tipo in dataset.groupby(columna_tipo):

        # Expandir registros separados por ;
        ods_expandidos = (
            df_tipo[columna_ods]
            .dropna()
            .str.split(";")
            .explode()
            .str.strip()
        )

        if ods_expandidos.empty:
            print(f"⚠ Sin datos ODS para '{tipo}'")
            continue

        # Conteo y porcentaje
        conteo = ods_expandidos.value_counts()
        porcentajes = (conteo / conteo.sum() * 100).round(1).astype(str) + "%"

        # FIGURA tamaño grande para evitar título separado
        fig, ax = plt.subplots(figsize=(10, 11))

        wedges, texts, autotexts = ax.pie(
            conteo.values,
            labels=None,               # ❌ SIN labels externos
            autopct="%1.1f%%",         # ✔ Porcentaje dentro del gráfico
            startangle=90,
            textprops={'fontsize': 14} # ✔ tamaños legibles
        )

        for t in autotexts:
            t.set_fontsize(14)

        # Título grande
        ax.set_title(
            f"Distribución de ODS Apoyados\n({tipo})",
            pad=30,
            fontsize=18
        )

        ax.axis("equal")

        # Tabla inferior
        colores = [w.get_facecolor() for w in wedges]

        tabla_df = pd.DataFrame({
            "Color": ["■"] * len(conteo),
            "ODS": conteo.index.astype(str),
            "Cantidad": conteo.values,
            "Porcentaje": porcentajes.values
        })

        # Envolver textos largos (ODS suelen ser largos)
        tabla_df["ODS"] = [
            textwrap.fill(v, width=40) for v in tabla_df["ODS"]
        ]

        # Altura según nº de líneas
        line_counts = [t.count("\n") + 1 for t in tabla_df["ODS"]]
        max_lines = max(line_counts)

        # Ajuste dinámico para evitar que el título salte de página
        plt.subplots_adjust(bottom=0.30 + 0.025 * max_lines)

        tabla = plt.table(
            cellText=tabla_df.values,
            colLabels=tabla_df.columns,
            loc='bottom',
            cellLoc='center'
        )

        tabla.auto_set_font_size(False)
        tabla.set_fontsize(12)

        # Pintar columna color
        for i, color in enumerate(colores, start=1):
            cell = tabla[(i, 0)]
            cell.set_facecolor(color)
            cell._text.set_text("")

        # Anchos proporcionados
        col_widths = [0.07, 0.60, 0.15, 0.18]
        for j, width in enumerate(col_widths):
            for key, cell in tabla.get_celld().items():
                if key[1] == j:
                    cell.set_width(width)

        # Alturas dinámicas
        base_height = 0.07
        for i, lines in enumerate(line_counts, start=1):
            row_height = base_height * min(lines, 8)
            for j in range(len(tabla_df.columns)):
                cell = tabla.get_celld().get((i, j))
                if cell:
                    cell.set_height(row_height)

        # Guardar a buffer
        buffer_img = io.BytesIO()
        plt.savefig(buffer_img, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        buffer_img.seek(0)

        resultados[tipo] = buffer_img

    return resultados

# ================================================================
# 🧩 Generar PDFs combinando los gráficos
# ================================================================
def generar_graficos_y_pdfs(dfs_divididos, seleccionadas, modo, ruta_salida):

    os.makedirs(ruta_salida, exist_ok=True)
    pdfs_generados = []

    for sel in seleccionadas:

        # --- Selección del dataset ---
        if modo == "dependencias":
            dependencia = sel
            subdependencia = None
            if dependencia not in dfs_divididos:
                print(f"⚠ Dependencia '{dependencia}' no encontrada.")
                continue
            dataset = dfs_divididos[dependencia]

        elif modo == "subdependencias":
            if not isinstance(sel, (tuple, list)) or len(sel) != 2:
                print(f"⚠ Formato inválido para subdependencia: {sel}")
                continue
            dependencia, subdependencia = sel
            if dependencia not in dfs_divididos or subdependencia not in dfs_divididos[dependencia]:
                print(f"⚠ Subdependencia '{dependencia}/{subdependencia}' no encontrada.")
                continue
            dataset = dfs_divididos[dependencia][subdependencia]

        else:
            print("⚠ Modo inválido.")
            return []

        if dataset.empty:
            print(f"⚠ Dataset vacío para '{dependencia}'")
            continue

        # --- Generar gráficos ---
        buffer_sedes = graficar_conteo_sedes(dataset)
        buffer_part = graficar_participacion(dataset, dependencia, subdependencia)
        buffer_gantt = graficar_gantt(dataset, dependencia, subdependencia)

        tabla_resumen = crear_tabla_resumen(dataset)

        graficos_ambitos = generar_grafico_ambitos(dataset)
        graficos_ods = generar_grafico_ods(dataset)   # <<<<<<<<<< NUEVO

        # --- Crear PDF ---
        safe_name = f"{dependencia}_{subdependencia or ''}".replace("/", "_")
        pdf_path = os.path.join(ruta_salida, f"{safe_name}.pdf")

        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"<b>{dependencia}</b>" + 
                      (f" / {subdependencia}" if subdependencia else ""), 
                      styles['Heading2']),
            Spacer(1, 10)
        ]

        # --- Gráficos generales ---
        for buffer_img in [buffer_sedes, buffer_part, buffer_gantt]:
            if buffer_img:
                story.append(Image(buffer_img, width=460, height=280))
                story.append(Spacer(1, 20))

        # --- Tabla resumen ---
        if tabla_resumen:
            story.append(tabla_resumen)

        # --- Gráficos de Ámbitos estratégicos ---
        for tipo, buffer_img in graficos_ambitos.items():
            story.append(
                KeepTogether([
                    Paragraph(f"<b>Ámbitos Estratégicos - {tipo}</b>", styles["Heading4"]),
                    Spacer(1, 5),
                    Image(buffer_img, width=400, height=400),
                    Spacer(1, 20)
                ])
            )

        # --- Gráficos de ODS ---
        for tipo, buffer_img in graficos_ods.items():
            story.append(
                KeepTogether([
                    Paragraph(f"<b>ODS que Apoya la Actividad - {tipo}</b>", styles["Heading4"]),
                    Spacer(1, 5),
                    Image(buffer_img, width=400, height=400),
                    Spacer(1, 20)
                ])
            )

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                leftMargin=25, rightMargin=25, topMargin=30, bottomMargin=25)
        doc.build(story)

        # --- Cerrar buffers ---
        for b in [buffer_sedes, buffer_part, buffer_gantt] + \
                 list(graficos_ambitos.values()) + \
                 list(graficos_ods.values()):
            if b:
                b.close()

        pdfs_generados.append(pdf_path)
        print(f"✅ PDF generado: {pdf_path}")

    print(f"\n📂 Se generaron {len(pdfs_generados)} PDFs correctamente.")
    return pdfs_generados
