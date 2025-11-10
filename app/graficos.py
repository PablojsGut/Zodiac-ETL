import os
import io
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import unicodedata
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


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


def graficar_conteo_sedes(df):
    """Genera gráfico de conteo por Sede y devuelve BytesIO con la imagen (png)."""
    if 'Sede' not in df.columns:
        return None

    sedes = df['Sede'].astype(str)
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


def generar_graficos_y_pdfs(dfs_subdivididos, seleccionadas, modo, ruta_salida):
    """
    Genera reportes en PDF:
      - gráfico de conteo por sedes
      - gráfico Gantt (si hay fechas)
      - tabla detallada (Num., Sede incluida)
    Se guardan los PDFs dentro de la carpeta del Excel.
    """

    os.makedirs(ruta_salida, exist_ok=True)
    pdfs_generados = []

    for sel in seleccionadas:
        dependencia = sel if modo == "dependencias" else sel[0]
        subgrupo = None if modo == "dependencias" else sel[1]

        print(f"📊 Generando reporte para: {dependencia}" + (f" / {subgrupo}" if subgrupo else ""))

        if dependencia not in dfs_subdivididos:
            print(f"⚠ Dependencia '{dependencia}' no encontrada.")
            continue

        if modo == "subdependencias":
            if subgrupo not in dfs_subdivididos[dependencia]:
                print(f"⚠ Subdependencia '{subgrupo}' no encontrada en '{dependencia}'.")
                continue
            dataset = dfs_subdivididos[dependencia][subgrupo].copy()
        else:
            dataset = dfs_subdivididos[dependencia].copy()

        if dataset.empty:
            print(f"⚠ Dataset vacío para '{dependencia}'.")
            continue

        # Normalizar y encontrar columnas de fechas
        colmap_norm = {normalizar_columna(c): c for c in dataset.columns}
        col_inicio = next((v for k, v in colmap_norm.items() if "fechainicio" in k), None)
        col_fin = next((v for k, v in colmap_norm.items() if "fechatermino" in k or "fechatermino" in k.replace("ter", "tér")), None)

        df_tabla = dataset.copy()
        df_tabla[col_inicio] = pd.to_datetime(df_tabla[col_inicio], errors="coerce")
        df_tabla[col_fin] = pd.to_datetime(df_tabla[col_fin], errors="coerce")

        df_tabla["Fecha Inicio"] = df_tabla[col_inicio].dt.strftime("%d/%m/%Y").fillna("")
        df_tabla["Fecha Término"] = df_tabla[col_fin].dt.strftime("%d/%m/%Y").fillna("")

        # Gráfico de sedes
        buffer_sedes = graficar_conteo_sedes(df_tabla)

        # Dataset para Gantt
        dataset_plot = dataset.copy()
        dataset_plot[col_inicio] = pd.to_datetime(dataset_plot[col_inicio], errors="coerce")
        dataset_plot[col_fin] = pd.to_datetime(dataset_plot[col_fin], errors="coerce")
        dataset_plot = dataset_plot.dropna(subset=[col_inicio, col_fin])

        buffer_gantt = None
        if not dataset_plot.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            dataset_plot = dataset_plot.sort_values(col_inicio).reset_index(drop=True)
            y_labels = dataset_plot["Id"].astype(str).tolist() if "Id" in dataset_plot.columns else list(range(1, len(dataset_plot) + 1))
            y_pos = np.arange(len(y_labels))
            duraciones = (dataset_plot[col_fin] - dataset_plot[col_inicio]).dt.days
            ax.barh(y=y_pos, width=duraciones, left=dataset_plot[col_inicio], color='skyblue', edgecolor='black')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(y_labels)
            ax.set_xlabel("Fecha")
            ax.set_ylabel("ID del Registro")
            titulo = f"{dependencia}" + (f" / {subgrupo}" if subgrupo else "")
            ax.set_title(f"Duración de participación - {titulo}", fontsize=12)
            ax.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            buffer_gantt = io.BytesIO()
            plt.savefig(buffer_gantt, format="png", bbox_inches="tight")
            plt.close(fig)
            buffer_gantt.seek(0)

        # Tabla final
        df_tabla.insert(0, "Num.", range(1, len(df_tabla) + 1))
        if 'Sede' in df_tabla.columns:
            cols = list(df_tabla.columns)
            sede_idx = cols.index('Sede')
            if sede_idx != 5:
                target_idx = min(5, len(cols)-1)
                cols.insert(target_idx, cols.pop(sede_idx))
                df_tabla = df_tabla[cols]

        columnas_mostrar = ["Num.", "Id", "Nombre", "Correo electrónico",
                            "Participación", "Fecha Inicio", "Fecha Término", "Sede"]
        columnas_mostrar = [c for c in columnas_mostrar if c in df_tabla.columns]

        df_mostrar = df_tabla[columnas_mostrar].fillna("")
        tabla_datos = [columnas_mostrar] + df_mostrar.values.tolist()

        # Ajustar texto largo
        wrap_style = ParagraphStyle('wrap', fontSize=7, leading=8, alignment=1)
        for i in range(1, len(tabla_datos)):
            for j in range(len(tabla_datos[i])):
                txt = str(tabla_datos[i][j])
                if len(txt) > 20:
                    tabla_datos[i][j] = Paragraph(txt, wrap_style)

        # Crear estilo reutilizable
        tabla_estilo = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ])

        num_cols = len(tabla_datos[0])
        max_width = 500

        # Crear PDF
        safe_name = f"{dependencia}_{subgrupo or ''}".replace("/", "_").replace("\\", "_")
        pdf_path = os.path.join(ruta_salida, f"{safe_name}.pdf")

        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"<b>{dependencia}</b>" + (f" / {subgrupo}" if subgrupo else ""), styles['Heading2']),
            Spacer(1, 10)
        ]

        if buffer_sedes:
            story.append(Image(buffer_sedes, width=460, height=280))
            story.append(Spacer(1, 20))
        if buffer_gantt:
            story.append(Image(buffer_gantt, width=460, height=260))
            story.append(Spacer(1, 20))

        # Tabla dividida por páginas
        rows_per_page = 35
        for start in range(0, len(tabla_datos) - 1, rows_per_page):
            end = start + rows_per_page
            sub_tabla = [tabla_datos[0]] + tabla_datos[start+1:end+1]
            tabla_p = Table(sub_tabla, repeatRows=1, colWidths=[max_width / num_cols] * num_cols)
            tabla_p.setStyle(tabla_estilo)
            story.append(tabla_p)
            if end < len(tabla_datos) - 1:
                story.append(PageBreak())

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=25, rightMargin=25, topMargin=30, bottomMargin=25)
        doc.build(story)

        if buffer_sedes:
            buffer_sedes.close()
        if buffer_gantt:
            buffer_gantt.close()

        pdfs_generados.append(pdf_path)
        print(f"✅ PDF generado: {pdf_path}")

    print(f"\n📂 Se generaron {len(pdfs_generados)} PDFs correctamente.")
    return pdfs_generados
