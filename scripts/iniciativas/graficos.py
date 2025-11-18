import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

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
    Muestra un resumen visual en estilo tarjetas:
    - Total registros (azul)
    - Totales por Estado (celeste)
    - Totales por Sede (amarillo)

    Acepta:
        - df directo
        - dataset[dependencia]
        - dataset[dependencia][subdependencia]
    """

    # ================================
    # 🧩 Determinar el DataFrame correcto
    # ================================
    if isinstance(dataset, pd.DataFrame):
        df = dataset

    elif isinstance(dataset, dict):
        if dependencia and subdependencia:
            try:
                df = dataset[dependencia][subdependencia]
            except (KeyError, TypeError):
                print(f"⚠ No se encontró {dependencia} / {subdependencia}")
                return

        elif dependencia:
            try:
                df = dataset[dependencia]
            except (KeyError, TypeError):
                print(f"⚠ No se encontró la dependencia '{dependencia}'")
                return

        else:
            print("⚠ Se requiere al menos una dependencia para dataset jerárquico.")
            return
    else:
        print("⚠ Tipo de dataset no reconocido.")
        return

    # ================================
    # 🔎 Obtención de datos
    # ================================
    total_registros = len(df)

    conteo_estados = df[col_estado].dropna().astype(str).value_counts() \
        if col_estado in df.columns else {}

    conteo_sedes = df[col_sede].dropna().astype(str).value_counts() \
        if col_sede in df.columns else {}

    # ================================
    # 🎨 Configuración visual
    # ================================
    num_items = 1 + len(conteo_estados) + len(conteo_sedes)
    fig, ax = plt.subplots(figsize=(12, 2 + num_items * 1.5))
    ax.axis("off")

    y = 1 - 1/(num_items+1)
    paso = 1/(num_items+1)

    # ================================
    # Función para dibujar tarjetas
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

        # Cuadro del número
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
    # 1️⃣ Total general
    # ================================
    tarjeta(y, color_total, "Total de Registros:", total_registros)
    y -= paso

    # ================================
    # 2️⃣ Totales por Estado
    # ================================
    for estado, cant in conteo_estados.items():
        tarjeta(y, color_estado, f"Total Estado '{estado}':", cant)
        y -= paso

    # ================================
    # 3️⃣ Totales por Sede
    # ================================
    for sede, cant in conteo_sedes.items():
        tarjeta(y, color_sede, f"Total Sede '{sede}':", cant)
        y -= paso

    plt.tight_layout()
    plt.show()
