import pandas as pd
from scripts.limpiar_columnas import limpiar_y_renombrar_columnas
from scripts.dividir_dependencias import dividir_por_dependencia
from scripts.exportar_dependencias import eliminar_columnas_por_indice, exportar_dependencias

# Leer el Excel original
ruta_excel = "data/Registro simplificado de participaciones en instancias externas.xlsx"
df_intit = pd.read_excel(ruta_excel)

# 1️⃣ Limpiar y renombrar columnas
df_intit = limpiar_y_renombrar_columnas(df_intit)

# 2️⃣ Dividir por dependencia
df_dependencias = dividir_por_dependencia(df_intit)

# 3️⃣ Eliminar columnas según dependencia (tu configuración)
eliminar_columnas_por_indice(df_dependencias, "Centro de Investigación", [9, 10, 11, 13, 14, 15, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Especialidad Médica", [9, 10, 11, 12, 13, 14, 15, 16, 17])
eliminar_columnas_por_indice(df_dependencias, "Facultad de Ciencias Sociales y Artes", [9, 10, 11, 12, 13, 15, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Facultad de Ciencias, Ingeniería y Tecnología", [9, 10, 11, 12, 13, 14, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Facultad de Medicina y Ciencias de la Salud", [9, 10, 11, 12, 13, 14, 15, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Programa Magíster", [9, 11, 12, 13, 14, 15, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Programa de Doctorado", [9, 10, 11, 12, 14, 15, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Unidad Técnica y Tecnológica TEC MAYOR", [9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Especialidad Odontológica", [9, 10, 11, 12, 13, 14, 15, 16, 18])
eliminar_columnas_por_indice(df_dependencias, "Núcleo de Investigación", [9, 10, 12, 13, 14, 15, 16, 17, 18])
eliminar_columnas_por_indice(df_dependencias, "Otras Unidades No Académicas", [10, 11, 12, 13, 14, 15, 16, 17, 18])

# 4️⃣ Exportar dependencias
exportar_dependencias(df_dependencias)
