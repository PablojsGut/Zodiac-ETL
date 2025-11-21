import os
import io
import re
import pandas as pd
import numpy as np
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def resumen_iniciativas(
    dataset,
    dependencia=None,
    subdependencia=None,
    col_estado="Estado",
    col_sede="Sede",
    color_total="#1f77b4",   # azul
    color_estado="#7ec8e3",  # celeste
    color_sede="#ffdd57",    # amarillo
):
    """
    Genera un resumen visual estilo tarjetas y devuelve un BytesIO con la imagen PNG.
    """

    # ================================
    # 🧩 Obtener DataFrame
    # ================================
    if isinstance(dataset, pd.DataFrame):
        df = dataset
    elif isinstance(dataset, dict):
        try:
            if dependencia and subdependencia:
                df = dataset[dependencia][subdependencia]
            elif dependencia:
                df = dataset[dependencia]
            else:
                print("⚠ Se requiere dependencia si es dataset jerárquico.")
                return None
        except KeyError:
            print("⚠ Dependencia o subdependencia no encontrada.")
            return None
    else:
        print("⚠ Tipo de dataset no válido.")
        return None

    # ================================
    # 🔢 Datos
    # ================================
    total_registros = len(df)

    conteo_estados = df[col_estado].dropna().astype(str).value_counts() \
        if col_estado in df.columns else {}

    conteo_sedes = df[col_sede].dropna().astype(str).value_counts() \
        if col_sede in df.columns else {}

    # ================================
    # 🎨 Crear figura
    # ================================
    num_items = 1 + len(conteo_estados) + len(conteo_sedes)
    fig, ax = plt.subplots(figsize=(12, 2 + num_items * 1.5))
    ax.axis("off")

    y = 1 - 1/(num_items+1)
    paso = 1/(num_items+1)

    # ================================
    # 🟦 Función para dibujar tarjeta
    # ================================
    def tarjeta(y, color, titulo, valor):
        rect = patches.FancyBboxPatch(
            (0.05, y), 0.90, 0.12,
            boxstyle="round,pad=0.02",
            edgecolor="black",
            linewidth=2,
            facecolor=color
        )
        ax.add_patch(rect)

        ax.text(0.07, y + 0.065, titulo,
                fontsize=15, fontweight="bold",
                va="center", ha="left")

        inner = patches.Rectangle(
            (0.60, y + 0.025), 0.20, 0.07,
            linewidth=3, edgecolor="black",
            facecolor="#d9d9d9"
        )
        ax.add_patch(inner)

        inner2 = patches.Rectangle(
            (0.598, y + 0.023), 0.204, 0.074,
            linewidth=1.5, edgecolor="black",
            facecolor="none"
        )
        ax.add_patch(inner2)

        ax.text(0.70, y + 0.06, str(valor),
                fontsize=18, fontweight="bold",
                va="center", ha="center")

    # ================================
    # 1️⃣ Total
    # ================================
    tarjeta(y, color_total, "Total de Registros:", total_registros)
    y -= paso

    # 2️⃣ Estados
    for estado, cant in conteo_estados.items():
        tarjeta(y, color_estado, f"Total Estado '{estado}':", cant)
        y -= paso

    # 3️⃣ Sedes
    for sede, cant in conteo_sedes.items():
        tarjeta(y, color_sede, f"Total Sede '{sede}':", cant)
        y -= paso

    plt.tight_layout()

    # ================================
    # 📤 Exportar como Buffer
    # ================================
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def graficar_gantt_iniciativas(dataset, dependencia=None, subdependencia=None, max_por_grafico=6):
    """
    Genera gráficos de Gantt en lotes de máximo `max_por_grafico` registros por imagen.
    - Ignora automáticamente cualquier registro sin fechas válidas.
    - Devuelve una lista de buffers BytesIO (uno por gráfico).
    """

    # Identificar dataset correcto
    if isinstance(dataset, pd.DataFrame):
        df = dataset

    elif isinstance(dataset, dict):
        if dependencia and subdependencia:
            df = dataset.get(dependencia, {}).get(subdependencia)
        elif dependencia:
            df = dataset.get(dependencia)
        else:
            print("⚠ Se requiere dependencia para dataset jerárquico.")
            return []

    else:
        print("⚠ Tipo de dataset no reconocido.")
        return []

    if df is None or df.empty:
        print(f"⚠ Dataset vacío o nulo para {dependencia}/{subdependencia}.")
        return []

    # Columnas exactas
    col_id  = "ID"
    col_ini = "Fecha de Inicio de la Iniciativa"
    col_fin = "Fecha de Término de la Iniciativa"

    for col in [col_id, col_ini, col_fin]:
        if col not in df.columns:
            print(f"⚠ FALTA la columna '{col}' en {dependencia or 'dataset'}")
            return []

    # ---------------------------------------------------
    # 🔥 Convertir fechas y eliminar filas sin fechas
    # ---------------------------------------------------
    df_plot = df.copy()

    df_plot[col_ini] = pd.to_datetime(df_plot[col_ini], dayfirst=True, errors="coerce")
    df_plot[col_fin] = pd.to_datetime(df_plot[col_fin], dayfirst=True, errors="coerce")

    # Eliminar TODOS los registros sin ambas fechas
    df_plot = df_plot.dropna(subset=[col_ini, col_fin])

    if df_plot.empty:
        print(f"⚠ Todas las filas carecen de fechas válidas. Nada para graficar.")
        return []

    # Ordenar por fecha de inicio
    df_plot = df_plot.sort_values(col_ini).reset_index(drop=True)

    # -----------------------------------------------
    # 🔥 DIVIDIR EN LOTES DE max_por_grafico FILAS
    # -----------------------------------------------
    buffers = []
    total = len(df_plot)

    for i in range(0, total, max_por_grafico):

        df_chunk = df_plot.iloc[i:i + max_por_grafico]

        if df_chunk.empty:
            continue

        # Datos chunk
        y_labels = df_chunk[col_id].astype(str).tolist()
        y_pos = np.arange(len(y_labels))
        duraciones = (df_chunk[col_fin] - df_chunk[col_ini]).dt.days

        # ---------------------------
        # 📊 Crear gráfico por chunk
        # ---------------------------
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.barh(
            y=y_pos,
            width=duraciones,
            left=df_chunk[col_ini],
            edgecolor='black'
        )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels)

        ax.set_xlabel("Fecha")
        ax.set_ylabel("ID de la Iniciativa")

        titulo = f"Gantt de Iniciativas ({i+1}-{min(i+max_por_grafico, total)})"
        if dependencia:
            titulo += f" - {dependencia}"
        if subdependencia:
            titulo += f" / {subdependencia}"

        ax.set_title(titulo, fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.5)

        plt.tight_layout()

        # Guardar en buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)

        buffers.append(buffer)

    return buffers

def crear_tabla_resumen_iniciativas(dataset):
    """Crea una tabla resumen de iniciativas con estilo, numeración y ajuste automático de texto."""

    # --- Columnas esperadas y nombres amigables ---
    columnas_originales = {
        "ID": "ID",
        "Email": "Email",
        "Nombre de la Iniciativa VcM": "Iniciativa",
        "Estado": "Estado",
        "Sede": "Sede",
        "Fecha de Inicio de la Iniciativa": "Fecha Inicio",
        "Fecha de Término de la Iniciativa": "Fecha Término"
    }

    # Filtrar solo columnas existentes
    columnas_existentes = {k: v for k, v in columnas_originales.items() if k in dataset.columns}
    if not columnas_existentes:
        return None

    # Dataset reducido
    df_mostrar = dataset[list(columnas_existentes.keys())].copy().fillna("")

    # --- Formatear fechas a dd/mm/yyyy (con dayfirst=True para evitar warnings) ---
    for col in ["Fecha de Inicio de la Iniciativa", "Fecha de Término de la Iniciativa"]:
        if col in df_mostrar.columns:
            df_mostrar[col] = pd.to_datetime(
                df_mostrar[col], dayfirst=True, errors="coerce"
            ).dt.strftime("%d/%m/%Y").fillna("")

    # Insertar numeración
    df_mostrar.insert(0, "N°", range(1, len(df_mostrar) + 1))

    # Renombrar columnas
    df_mostrar.rename(columns=columnas_existentes, inplace=True)

    # --- Estilos para texto ---
    estilo_celda = ParagraphStyle(
        name='TablaTexto',
        alignment=TA_LEFT,
        fontSize=7,
        leading=8,
        wordWrap='CJK'
    )

    estilo_encabezado = ParagraphStyle(
        name='Encabezado',
        alignment=TA_CENTER,
        fontSize=8,
        leading=9,
        textColor=colors.black,
        wordWrap='CJK'
    )

    # Convertir filas y encabezados a Paragraph
    encabezados = [Paragraph(str(col), estilo_encabezado) for col in df_mostrar.columns]
    filas = [
        [Paragraph(str(c), estilo_celda) for c in fila]
        for fila in df_mostrar.values.tolist()
    ]

    tabla_datos = [encabezados] + filas

    # Crear tabla
    tabla = Table(tabla_datos, repeatRows=1)

    # Estilos visuales
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

    # --- Ajuste de anchos de columna ---
    total_ancho = 500  # ancho útil de página
    # Proporciones pensadas para estas columnas
    col_proporciones = [
        0.5,   # N°
        1.0,   # ID
        2.0,   # Email
        3.0,   # Iniciativa
        1.2,   # Estado
        1.5,   # Sede
        1.3,   # Fecha Inicio
        1.3    # Fecha Término
    ]

    # Ajustar solo las columnas que existen
    ncols = len(df_mostrar.columns)
    proporciones_uso = col_proporciones[:ncols]
    suma = sum(proporciones_uso) if proporciones_uso else 1
    col_widths = [
        total_ancho * (p / suma)
        for p in proporciones_uso
    ]

    tabla._argW = col_widths

    return tabla

def graficar_porcentajes_tipos_iniciativa(dataset):
    """
    Genera un gráfico de barras horizontal con % Sí / No para cada tipo de iniciativa.
    Filtra solo las iniciativas con Estado = 'Enviada'.
    Devuelve un buffer BytesIO con un PNG.
    """

    # --- Columnas de interés ---
    columnas = [
        "¿La iniciativa está orientada a formación académica? (Vinculación Académica - VA)",
        "¿La iniciativa implica la difusión y/o intercambio de conocimiento? (Articulación e Intercambio de Conocimiento - AIC)",
        "¿La iniciativa es una actividad cultural o artística? (Vinculación Artístico-Cultural - VAC)",
        "¿La iniciativa incluye investigación básica, aplicada o emprendimiento? (Investigación, Proyectos de Emprendimiento y Estudios - IPEE)",
        "¿La iniciativa implica alianzas internacionales? (Internacionalización - INT)",
        "¿La iniciativa está orientada a graduados/titulados y/o empleadores? (Graduados/Titulados, Empleabilidad y Redes - GTER)"
    ]

    # --- Filtrar solo Estado = Enviada ---
    df = dataset.copy()
    df = df[df["Estado"].astype(str).str.strip().str.lower() == "enviada"]

    if df.empty:
        print("⚠ No hay iniciativas con Estado = 'Enviada'.")
        return None

    # --- Preparar cálculos ---
    etiquetas = []
    porcentajes_si = []
    porcentajes_no = []
    cantidades_si = []
    cantidades_no = []

    for col in columnas:
        if col not in df.columns:
            continue

        total = df[col].count()
        si = (df[col].astype(str).str.lower() == "sí").sum()
        no = (df[col].astype(str).str.lower() == "no").sum()

        if total == 0:
            continue

        match = re.search(r"\((.*?)\)", col)
        etiqueta = match.group(1).strip() if match else col

        etiquetas.append(etiqueta)
        cantidades_si.append(si)
        cantidades_no.append(no)

        porcentajes_si.append((si / total) * 100)
        porcentajes_no.append((no / total) * 100)

    # --- Crear gráfico ---
    fig, ax = plt.subplots(figsize=(14, 7))

    y_pos = np.arange(len(etiquetas))

    ax.barh(y_pos, porcentajes_no, label="No", alpha=0.6)
    ax.barh(y_pos, porcentajes_si, label="Sí", left=porcentajes_no)

    # --- Etiquetas numéricas dentro de las barras ---
    for i, (p_si, p_no, c_si, c_no) in enumerate(zip(porcentajes_si, porcentajes_no, cantidades_si, cantidades_no)):
        ax.text(porcentajes_no[i] / 2,
                i,
                f"No: {c_no} ({p_no:.1f}%)",
                va='center',
                ha='center',
                fontsize=10,
                color='black')

        ax.text(porcentajes_no[i] + p_si / 2,
                i,
                f"Sí: {c_si} ({p_si:.1f}%)",
                va='center',
                ha='center',
                fontsize=10,
                color='black')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(etiquetas, fontsize=11)
    ax.set_xlabel("Porcentaje (%)", fontsize=12)
    
    ax.set_title("Distribución porcentual de respuestas (solo Estado = Enviada)",fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)

    plt.tight_layout()

    # --- Guardar a buffer ---
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    return buffer

def graficar_modalidades_cantidad(dataset):
    """
    Genera un gráfico de barras horizontal mostrando la cantidad de iniciativas
    por modalidad (columna 'Modalidad de Implementación de la Iniciativa'),
    filtrando solo las iniciativas con Estado = 'Enviada'.
    Devuelve un buffer BytesIO con el PNG del gráfico.
    """

    # Validaciones
    if "Estado" not in dataset.columns or "Modalidad de Implementación de la Iniciativa" not in dataset.columns:
        print("⚠ Columnas requeridas no encontradas.")
        return None

    # --- Filtrar Estado = Enviada ---
    df = dataset.copy()
    df["Estado"] = df["Estado"].astype(str).str.strip().str.lower()
    df = df[df["Estado"] == "enviada"]

    if df.empty:
        print("⚠ No hay iniciativas con Estado = 'Enviada'.")
        return None

    # --- Contar modalidades ---
    df["Modalidad de Implementación de la Iniciativa"] = (
        df["Modalidad de Implementación de la Iniciativa"]
        .astype(str)
        .str.strip()
        .replace("", "Sin dato")
    )

    conteo = df["Modalidad de Implementación de la Iniciativa"].value_counts()

    modalidades = conteo.index.tolist()
    cantidades = conteo.values.tolist()

    # --- Crear gráfico ---
    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(modalidades))

    ax.barh(y_pos, cantidades, alpha=0.7)

    # Etiquetas de modalidad
    ax.set_yticks(y_pos)
    ax.set_yticklabels(modalidades, fontsize=10)

    # Etiqueta de eje X
    ax.set_xlabel("Cantidad de Iniciativas", fontsize=10)
    ax.set_title("Cantidad por Modalidad (solo Estado = Enviada)", fontsize=12)

    # --- Valores numéricos al final de cada barra ---
    for i, valor in enumerate(cantidades):
        ax.text(
            valor + 0.2,   # un poquito a la derecha de la barra
            i,
            str(valor),
            va="center",
            fontsize=10
        )

    plt.tight_layout()

    # --- Guardar en buffer ---
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    return buffer

def graficar_alcance_territorial_cantidad(dataset):
    """
    Genera un gráfico de barras horizontal mostrando la cantidad de iniciativas por
    alcance territorial (columna 'Alcance Territorial de la Iniciativa'),
    filtrando solo las iniciativas con Estado = 'Enviada'.
    Devuelve un buffer BytesIO con el PNG del gráfico.
    """

    import matplotlib.pyplot as plt
    import numpy as np
    import io

    # Validaciones
    if "Estado" not in dataset.columns or "Alcance Territorial de la Iniciativa" not in dataset.columns:
        print("⚠ Columnas requeridas no encontradas.")
        return None

    # --- Filtrar Estado = Enviada ---
    df = dataset.copy()
    df["Estado"] = df["Estado"].astype(str).str.strip().str.lower()
    df = df[df["Estado"] == "enviada"]

    if df.empty:
        print("⚠ No hay iniciativas con Estado = 'Enviada'.")
        return None

    # --- Contar alcance territorial ---
    df["Alcance Territorial de la Iniciativa"] = (
        df["Alcance Territorial de la Iniciativa"]
        .astype(str)
        .str.strip()
        .replace("", "Sin dato")
    )

    conteo = df["Alcance Territorial de la Iniciativa"].value_counts()

    alcances = conteo.index.tolist()
    cantidades = conteo.values.tolist()

    # --- Crear gráfico ---
    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(alcances))

    ax.barh(y_pos, cantidades, alpha=0.8)

    # Etiquetas de alcance
    ax.set_yticks(y_pos)
    ax.set_yticklabels(alcances, fontsize=10)

    # Etiqueta de eje X
    ax.set_xlabel("Cantidad de Iniciativas", fontsize=10)
    ax.set_title("Cantidad por Alcance Territorial (solo Estado = Enviada)", fontsize=12)

    # --- Valores numéricos al final de cada barra ---
    for i, valor in enumerate(cantidades):
        ax.text(
            valor + 0.2,   # ligeramente a la derecha de la barra
            i,
            str(valor),
            va="center",
            fontsize=10
        )

    plt.tight_layout()

    # --- Guardar en buffer ---
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    return buffer


def generar_resumenes_pdf_vform(dfs1, dfs2, seleccionadas, modo, ruta_salida):
    """
    Genera un PDF para cada dependencia o subdependencia seleccionada,
    incluyendo el resumen visual creado por la función resumen_iniciativas(),
    gráficos Gantt y la tabla resumen de iniciativas.
    Usa logs internos optimizados y solo hace un print al final.
    """

    os.makedirs(ruta_salida, exist_ok=True)
    pdfs_generados = []
    logs = []

    for sel in seleccionadas:

        # --- Selección del dataset ---
        if modo == "dependencias":
            dependencia = sel
            subdependencia = None

            if dependencia not in dfs1:
                logs.append(f"⚠ Dependencia '{dependencia}' no encontrada.")
                continue

            dataset = dfs1[dependencia]

        elif modo == "subdependencias":
            if not isinstance(sel, (tuple, list)) or len(sel) != 2:
                logs.append(f"⚠ Formato inválido para subdependencia: {sel}")
                continue

            dependencia, subdependencia = sel

            if (dependencia not in dfs1 or
                subdependencia not in dfs1[dependencia]):

                logs.append(f"⚠ Subdependencia '{dependencia}/{subdependencia}' no encontrada.")
                continue

            dataset = dfs1[dependencia][subdependencia]

        else:
            logs.append("⚠ Modo inválido.")
            print("\n".join(logs))
            return []

        if dataset.empty:
            logs.append(f"⚠ Dataset vacío para '{dependencia}'.")
            continue

        # ==========================================================
        # ⬛ GENERAR RESUMEN VISUAL
        # ==========================================================
        buffer_resumen = resumen_iniciativas(
            dataset,
            dependencia=dependencia,
            subdependencia=subdependencia
        )

        if buffer_resumen is None:
            logs.append(f"⚠ No se pudo generar resumen para {dependencia}/{subdependencia}.")
            continue

        # ==========================================================
        # 📊 GENERAR GRÁFICOS GANTT
        # ==========================================================
        buffer_gantt = graficar_gantt_iniciativas(
            dataset,
            dependencia=dependencia,
            subdependencia=subdependencia
        )

        # ==========================================================
        # 📋 GENERAR TABLA RESUMEN (NUEVO)
        # ==========================================================
        tabla_resumen = crear_tabla_resumen_iniciativas(dataset)

        if tabla_resumen is None:
            logs.append(f"⚠ No fue posible generar la tabla resumen de iniciativas para {dependencia}/{subdependencia}.")

        buffer_barras = graficar_porcentajes_tipos_iniciativa(dataset)
        buffer_modalidades = graficar_modalidades_cantidad(dataset)
        buffer_alcance = graficar_alcance_territorial_cantidad(dataset)

        # ==========================================================
        # 📄 CREAR PDF
        # ==========================================================
        safe_name = f"{dependencia}_{subdependencia or ''}".replace("/", "_")
        pdf_path = os.path.join(ruta_salida, f"{safe_name}.pdf")

        styles = getSampleStyleSheet()
        story = [
            Paragraph(
                f"<b>{dependencia}</b>" +
                (f" / {subdependencia}" if subdependencia else ""),
                styles['Heading2']
            ),
            Spacer(1, 12)
        ]

        # === Resumen visual ===
        story.append(Paragraph("<b>Resumen de Iniciativas</b>", styles['Heading3']))
        story.append(Spacer(1, 8))
        story.append(Image(buffer_resumen, width=460, height=300))
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>Distribución porcentual por tipo de iniciativa</b>", styles['Heading3']))
        story.append(Spacer(1, 8))
        story.append(Image(buffer_barras, width=460, height=300))
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>Modalidad de Implementación</b>", styles['Heading3']))
        story.append(Spacer(1, 8))
        story.append(Image(buffer_modalidades, width=460, height=300))
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>Alcance de Iniciativas</b>", styles['Heading3']))
        story.append(Spacer(1, 8))
        story.append(Image(buffer_alcance, width=460, height=300))
        story.append(Spacer(1, 20))

        # === Gráficos Gantt ===
        if not buffer_gantt:
            logs.append(f"⚠ No se pudieron generar gráficos Gantt para {dependencia}/{subdependencia}.")
        else:
            for idx, gantt_img in enumerate(buffer_gantt, start=1):
                story.append(Paragraph(f"<b>Gráfico Gantt ({idx})</b>", styles['Heading4']))
                story.append(Spacer(1, 6))
                story.append(Image(gantt_img, width=460, height=280))
                story.append(Spacer(1, 20))

        # === NUEVO: Tabla Resumen ===
        if tabla_resumen:
            story.append(Paragraph("<b>Tabla Resumen de Iniciativas</b>", styles['Heading3']))
            story.append(Spacer(1, 10))
            story.append(tabla_resumen)
            story.append(Spacer(1, 20))

        # === Construcción del PDF ===
        doc = SimpleDocTemplate(
            pdf_path, pagesize=A4,
            leftMargin=25, rightMargin=25,
            topMargin=30, bottomMargin=25
        )
        doc.build(story)

        buffer_resumen.close()
        pdfs_generados.append(pdf_path)

        logs.append(f"✅ PDF generado: {pdf_path}")

    logs.append(f"\n📂 Se generaron {len(pdfs_generados)} PDFs correctamente.")

    print("\n".join(logs))
    return pdfs_generados
