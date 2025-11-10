import pandas as pd

def limpiar_y_renombrar_columnas(df_init: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia nombres de columnas y las renombra a nombres estandarizados.
    """

    # Normalizar nombres de columnas (quita saltos de línea y espacios extra)
    df_init.columns = (
        df_init.columns
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Renombrar columnas específicas
    df_init.rename(columns={
        df_init.columns[4]: "Nombre Correo",
        df_init.columns[5]: "Nombre",
        df_init.columns[6]: "Género",
        df_init.columns[7]: "Sexo",
        df_init.columns[8]: "Dependencia",
        df_init.columns[9]: "Unidad No Académica",
        df_init.columns[10]: "Programa de Magíster",
        df_init.columns[11]: "Núcleos de Investigación",
        df_init.columns[12]: "Centros de Investigación",
        df_init.columns[13]: "Programa de Doctorado",
        df_init.columns[14]: "Escuela/Carrera Facultad de Ciencias Sociales y Artes",
        df_init.columns[15]: "Escuela/Carrera Facultad de Ciencias, Ingeniería y Tecnología",
        df_init.columns[16]: "Escuela/Carrera Medicina y Ciencias de la Salud",
        df_init.columns[17]: "Especialidad Odontológica",
        df_init.columns[18]: "Especialidad Médica",
        df_init.columns[19]: "Sede",
        df_init.columns[20]: "Participación",
        df_init.columns[21]: "Actividad Alumni",
        df_init.columns[22]: "Años Actividad Alumni",
        df_init.columns[23]: "Descripción Actividad Alumni",
        df_init.columns[24]: "Cant. participantes",
        df_init.columns[25]: "Nombre Actor externo Alumni",
        df_init.columns[26]: "Nombre Mesa",
        df_init.columns[27]: "Nombre Actor externo Mesa",
        df_init.columns[28]: "Descripción Mesa",
        df_init.columns[43]: "Fecha inicio Actividad",
        df_init.columns[44]: "Fecha termino Actividad",
        df_init.columns[45]: "Nombre Actividad",
        df_init.columns[46]: "Año Actividad",
        df_init.columns[47]: "Ciudad Actividad",
        df_init.columns[48]: "País Actividad",
        df_init.columns[49]: "Objetivo Actividad",
        df_init.columns[50]: "Asignatura asociada",
        df_init.columns[51]: "Docente responsable Actividad",
        df_init.columns[52]: "Nombre Actor externo Actividad",
        df_init.columns[55]: "Ámbitos Estratégicos Actividad",
        df_init.columns[56]: "Objetivos de Desarrollo Sostenible (ODS) Actividad",
        df_init.columns[57]: "Retroalimentación",
        df_init.columns[58]: "Documentos",
    }, inplace=True)

    print("✅ Columnas limpiadas y renombradas correctamente.")
    return df_init
