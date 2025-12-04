import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
import os
import sys
from io import StringIO

import controladores as controlador
from scripts.instancias_externas.graficos import generar_graficos_y_pdfs
from scripts.iniciativas.graficos import generar_resumenes_pdf_vform

from ui.ventana_modo import VentanaModoDivision
from ui.ventana_dependencias import VentanaSeleccionDependencias
from ui.ventana_jerarquica import VentanaSeleccionJerarquica
from ui.zodiac import VentanaFiltroMes


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)


class RedirectPrint:
    def __init__(self, callback):
        self.callback = callback

    def write(self, text):
        if text.strip():
            self.callback(text)

    def flush(self):
        pass


ZODIAC_MONTHS = [
    ("♒", "Enero"), ("♓", "Febrero"), ("♈", "Marzo"),
    ("♉", "Abril"), ("♊", "Mayo"), ("♋", "Junio"),
    ("♌", "Julio"), ("♍", "Agosto"), ("♎", "Septiembre"),
    ("♏", "Octubre"), ("♐", "Noviembre"), ("♑", "Diciembre")
]


class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.ruta_iniciativas = None
        self.ruta_sintesis = None

        self.iconbitmap(resource_path("zodiac_logo.ico"))
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Zodiac: Validador y Procesador de Archivo Excel")
        self.geometry("580x520")

        # ----------------------------------------------------
        # Selector de formulario
        # ----------------------------------------------------
        self.label_tipo = ctk.CTkLabel(
            self,
            text="Seleccione el tipo de formulario:",
            font=("Arial", 15)
        )
        self.label_tipo.pack(pady=(10, 5))

        self.tipo_formulario = ctk.StringVar(value="")

        self.selector_formulario = ctk.CTkSegmentedButton(
            self,
            values=[
                "Formulario de Participaciones en Instancias Externas",
                "Formulario de Iniciativas VcM"
            ],
            variable=self.tipo_formulario,
            command=self.mostrar_mensaje_formulario
        )
        self.selector_formulario.pack(pady=5)

        self.mensaje_formulario = ctk.CTkLabel(self, text="", font=("Arial", 12), text_color="green")
        self.mensaje_formulario.pack(pady=(5, 15))

        # ----------------------------------------------------
        # Selección Excel
        # ----------------------------------------------------
        self.label = ctk.CTkLabel(self, text="Selecciona un archivo Excel", font=("Arial", 16))
        self.label.pack(pady=10)

        self.btn_seleccionar = ctk.CTkButton(
            self,
            text="📂 Seleccionar Excel",
            command=self.seleccionar_archivo,
            state="disabled"
        )
        self.btn_seleccionar.pack(pady=10)

        self.label_ruta = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label_ruta.pack(pady=10)

        # ----------------------------------------------------
        # Filtrar por mes  ➜ inicialmente desactivado
        # ----------------------------------------------------
        self.btn_filtro_meses = ctk.CTkButton(
            self,
            text="🔎 Filtrar por mes",
            command=self.abrir_filtro_mes,
            state="disabled"
        )
        self.btn_filtro_meses.pack(pady=10)

        # ----------------------------------------------------
        # Procesar Excel  ➜ desactivado hasta aplicar filtro
        # ----------------------------------------------------
        self.btn_procesar = ctk.CTkButton(
            self,
            text="⚙️ Procesar Excel",
            command=self.abrir_modo_division,
            state="disabled"
        )
        self.btn_procesar.pack(pady=10)

        self.label_resultado = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.label_resultado.pack(pady=10)

        self.init_consola()

        # Internos
        self.ruta_archivo = None
        self.df_validado = None
        self.filtro_meses = None

    # ----------------------------------------------------
    # Abrir filtro meses
    # ----------------------------------------------------
    def abrir_filtro_mes(self):
        ventana = VentanaFiltroMes(self)

        def esperar_cierre():
            if ventana.winfo_exists():
                self.after(100, esperar_cierre)
            else:
                if ventana.resultado:
                    self.filtro_meses = ventana.resultado

                    # 👉 AHORA SI activar procesar
                    self.btn_procesar.configure(state="normal")

                    modo = ventana.resultado.get("modo")
                    if modo == "mes":
                        mes = ventana.resultado["mes"]
                        if mes == "todo":
                            texto = f"Filtro: todo el año {ventana.resultado['anio']}"
                        else:
                            texto = f"Filtro: {mes} {ventana.resultado['anio']}"
                    else:
                        texto = f"Filtro: {ventana.resultado['inicio']} → {ventana.resultado['fin']} ({ventana.resultado['anio']})"

                    self.label_resultado.configure(text=texto, text_color="blue")

        esperar_cierre()

    # ----------------------------------------------------
    # Mensaje selector formulario
    # ----------------------------------------------------
    def mostrar_mensaje_formulario(self, seleccion):
        self.reiniciar_interfaz()

        if seleccion == "Formulario de Participaciones en Instancias Externas":
            txt = "Importe datos del registro de participaciones en instancias externas (Microsoft Form)"
        else:
            txt = "Importe datos de Iniciativas y Síntesis Evaluativa (VForm)"

        self.mensaje_formulario.configure(text=txt)

        # Habilitar selección archivo
        self.btn_seleccionar.configure(state="normal")

    # ----------------------------------------------------
    # Seleccionar archivo Excel
    # ----------------------------------------------------
    def seleccionar_archivo(self):
        tipo = self.tipo_formulario.get()

        # INSTANCIAS EXTERNAS
        if tipo == "Formulario de Participaciones en Instancias Externas":

            ruta = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if not ruta:
                return

            self.ruta_archivo = ruta
            self.label_ruta.configure(text=f"📄 Archivo seleccionado:\n{ruta}", text_color="green")

            self.label_resultado.configure(text="Validando archivo...", text_color="orange")
            self.update_idletasks()

            valido, df = controlador.validar_archivo_formulario(ruta, tipo)

            if valido:
                self.df_validado = df
                self.label_resultado.configure(text="Archivo válido.", text_color="green")

                # 👉 Activar filtro, NO procesar
                self.btn_filtro_meses.configure(state="normal")
                self.btn_procesar.configure(state="disabled")

            else:
                self.df_validado = None
                self.label_resultado.configure(text="Archivo inválido.", text_color="red")
                self.btn_filtro_meses.configure(state="disabled")
                self.btn_procesar.configure(state="disabled")

            return

        # FORMULARIO VCM
        elif tipo == "Formulario de Iniciativas VcM":

            ruta1 = filedialog.askopenfilename(
                title="Seleccione archivo de Iniciativas VcM",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if not ruta1:
                return

            ruta2 = filedialog.askopenfilename(
                title="Seleccione archivo de Síntesis Evaluativa",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if not ruta2:
                return

            self.ruta_iniciativas = ruta1
            self.ruta_sintesis = ruta2

            self.label_ruta.configure(
                text=f"📄 Iniciativas:\n{ruta1}\n\n📄 Síntesis:\n{ruta2}",
                text_color="green"
            )

            self.label_resultado.configure(text="Validando archivos...", text_color="orange")
            self.update_idletasks()

            valid1, df1 = controlador.validar_archivo_formulario(ruta1, tipo, "columnas_vform1")
            valid2, df2 = controlador.validar_archivo_formulario(ruta2, tipo, "columnas_vform2")

            if valid1 and valid2:
                self.df_validado = {"iniciativas": df1, "sintesis": df2}

                self.label_resultado.configure(
                    text="Archivos válidos. Seleccione filtro de meses.",
                    text_color="green"
                )

                # 👉 Activar filtro, NO Procesar
                self.btn_filtro_meses.configure(state="normal")
                self.btn_procesar.configure(state="disabled")

            else:
                self.df_validado = None
                self.label_resultado.configure(
                    text="Error validando archivos.",
                    text_color="red"
                )
                self.btn_filtro_meses.configure(state="disabled")
                self.btn_procesar.configure(state="disabled")

    # ----------------------------------------------------
    # Abrir ventana modo (dependencias o subdependencias)
    # ----------------------------------------------------
    def abrir_modo_division(self):
        if self.df_validado is None:
            return

        VentanaModoDivision(self, self.procesar_segun_modo, self.tipo_formulario.get())

    # ----------------------------------------------------
    # APLICAR FILTRO INTERNO
    # ----------------------------------------------------
    def aplicar_filtro_al_df(self, df: pd.DataFrame):

        if df is None or not isinstance(df, pd.DataFrame):
            return df

        if not self.filtro_meses:
            return df

        datos = self.filtro_meses

        tipo = self.tipo_formulario.get()
        columna_fecha = "Hora de inicio" if tipo == "Formulario de Participaciones en Instancias Externas" else "Fecha de creación"

        if columna_fecha not in df.columns:
            return df

        df2 = df.copy()
        df2[columna_fecha] = pd.to_datetime(df2[columna_fecha], errors="coerce", dayfirst=True)

        anio = datos.get("anio")
        if anio is None:
            return df

        meses_dict = {mes: i + 1 for i, (_, mes) in enumerate(ZODIAC_MONTHS)}

        if datos["modo"] == "mes":
            mes = datos["mes"]
            if mes == "todo":
                return df2[df2[columna_fecha].dt.year == anio]
            else:
                m = meses_dict.get(mes)
                return df2[
                    (df2[columna_fecha].dt.year == anio) &
                    (df2[columna_fecha].dt.month == m)
                ]

        else:
            inicio_mes = datos["inicio"].split(" ", 1)[1]
            fin_mes = datos["fin"].split(" ", 1)[1]

            m1 = meses_dict[inicio_mes]
            m2 = meses_dict[fin_mes]

            return df2[
                (df2[columna_fecha].dt.year == anio) &
                (df2[columna_fecha].dt.month >= m1) &
                (df2[columna_fecha].dt.month <= m2)
            ]

    # ----------------------------------------------------
    # PROCESAR
    # ----------------------------------------------------
    def procesar_segun_modo(self, modo):
        if self.df_validado is None:
            return

        ruta_salida_base = filedialog.askdirectory(title="Seleccione carpeta de destino")
        if not ruta_salida_base:
            return

        tipo = self.tipo_formulario.get()

        # --------------------------------------------
        # Participaciones en instancias externas
        # --------------------------------------------
        if tipo == "Formulario de Participaciones en Instancias Externas":

            df = self.aplicar_filtro_al_df(self.df_validado)

            if modo == "dependencias":
                deps = controlador.get_dependencias(df)
                VentanaSeleccionDependencias(
                    self,
                    deps,
                    lambda s: self.exportar_dependencias(df, s, ruta_salida_base)
                )

            else:
                subdeps = controlador.get_subdependencias(df)
                VentanaSeleccionJerarquica(
                    self,
                    subdeps,
                    lambda s: self.exportar_subdependencias(df, s, ruta_salida_base)
                )

        # --------------------------------------------
        # Iniciativas VcM
        # --------------------------------------------
        else:
            df1_raw = self.df_validado["iniciativas"]
            df2 = self.df_validado["sintesis"]

            df1 = self.aplicar_filtro_al_df(df1_raw)

            if modo == "dependencias":
                deps = controlador.get_dependencias_vform(df1)
                VentanaSeleccionDependencias(
                    self,
                    deps,
                    lambda s: self.exportar_dependencias_vform(df1, df2, s, ruta_salida_base)
                )

            elif modo == "subdependencias":
                subdeps = controlador.get_subdependencias_vform(df1)
                VentanaSeleccionJerarquica(
                    self,
                    subdeps,
                    lambda s: self.exportar_subdependencias_vform(df1, df2, s, ruta_salida_base)
                )

            # 🆕 NUEVO MODO: UNIÓN DE DATASETS
            elif modo == "union":
                # No hay selección de dependencias o subdependencias,
                # se exporta la unión directamente.
                self.exportar_union(df1, df2, ruta_salida_base)
    # ----------------------------------------------------
    # Exportar dependencias
    # ----------------------------------------------------
    def exportar_dependencias(self, df_dep, seleccionadas, ruta):
        ruta_final, dfs = controlador.procesar_excel_dependencias(df_dep, ruta, seleccionadas)
        if not ruta_final or not dfs:
            self.label_resultado.configure(text="Error al exportar dependencias.", text_color="red")
            return

        pdfs = generar_graficos_y_pdfs(dfs, seleccionadas, "dependencias", ruta_final)

        self.label_resultado.configure(
            text=f"Dependencias exportadas. PDFs generados: {len(pdfs)}",
            text_color="green"
        )

    def exportar_subdependencias(self, df_sub, seleccionadas, ruta):
        ruta_final, dfs = controlador.procesar_excel_subdependencias(df_sub, ruta, seleccionadas)
        if not ruta_final or not dfs:
            self.label_resultado.configure(text="Error al exportar.", text_color="red")
            return

        pdfs = generar_graficos_y_pdfs(dfs, seleccionadas, "subdependencias", ruta_final)

        self.label_resultado.configure(
            text=f"Subdependencias exportadas. PDFs generados: {len(pdfs)}",
            text_color="green"
        )

    def exportar_dependencias_vform(self, df1, df2, seleccionadas, ruta):
        ruta_final, d1, d2 = controlador.get_excels_dependencias_vform(df1, df2, ruta, seleccionadas)

        if ruta_final is None:
            self.label_resultado.configure(text="Error exportando VcM.", text_color="red")
            return

        pdfs = generar_resumenes_pdf_vform(d1, d2, seleccionadas, "dependencias", ruta_final)

        self.label_resultado.configure(
            text=f"Dependencias VcM exportadas. PDFs generados: {len(pdfs)}",
            text_color="green"
        )

    def exportar_subdependencias_vform(self, df1, df2, seleccionadas, ruta):
        ruta_final, d1, d2 = controlador.get_excels_subdependencias_vform(df1, df2, ruta, seleccionadas)

        if ruta_final is None:
            self.label_resultado.configure(text="Error exportando subdeps VcM.", text_color="red")
            return

        pdfs = generar_resumenes_pdf_vform(d1, d2, seleccionadas, "subdependencias", ruta_final)

        self.label_resultado.configure(
            text=f"Subdependencias VcM exportadas. PDFs generados: {len(pdfs)}",
            text_color="green"
        )

    def exportar_union(self, df1, df2, ruta):
        ruta_final = controlador.get_excels_union(df1, df2, ruta)

        if ruta_final is None:
            self.label_resultado.configure(
                text="Error exportando dataset unificado.",
                text_color="red"
            )
            return

        self.label_resultado.configure(
            text=f"Dataset unificado exportado correctamente en:\n{ruta_final}",
            text_color="green"
        )

    # ----------------------------------------------------
    # Consola interna
    # ----------------------------------------------------
    def init_consola(self):
        self.consola_frame = ctk.CTkFrame(self)
        self.consola_frame.pack(fill="x", padx=10, pady=5)

        self.btn_toggle_consola = ctk.CTkButton(
            self.consola_frame,
            text="📜 Mostrar consola ▼",
            command=self.toggle_consola,
            height=28,
            width=200
        )
        self.btn_toggle_consola.pack(pady=5)

        self.consola_content = ctk.CTkFrame(self.consola_frame)
        self.consola_content.pack(fill="x", expand=False)
        self.consola_content.pack_forget()

        self.consola_text = ctk.CTkTextbox(
            self.consola_content,
            width=520,
            height=200,
            font=("Consolas", 12)
        )
        self.consola_text.pack(padx=10, pady=10)

        sys.stdout = RedirectPrint(self.log_to_console)
        self.consola_abierta = False

    def toggle_consola(self):
        if self.consola_abierta:
            self.consola_content.pack_forget()
            self.btn_toggle_consola.configure(text="📜 Mostrar consola ▼")
        else:
            self.consola_content.pack(fill="x")
            self.btn_toggle_consola.configure(text="📜 Ocultar consola ▲")

        self.consola_abierta = not self.consola_abierta

    def log_to_console(self, text):
        self.consola_text.insert("end", text)
        self.consola_text.see("end")

    # ----------------------------------------------------
    # Reiniciar interfaz
    # ----------------------------------------------------
    def reiniciar_interfaz(self):
        self.ruta_archivo = None
        self.df_validado = None
        self.filtro_meses = None

        self.btn_seleccionar.configure(state="disabled")
        self.btn_filtro_meses.configure(state="disabled")
        self.btn_procesar.configure(state="disabled")

        self.label_ruta.configure(text="")
        self.label_resultado.configure(text="")
        self.mensaje_formulario.configure(text="")

        self.consola_text.delete("1.0", "end")

        if self.consola_abierta:
            self.toggle_consola()


# ----------------------------------------------------
# Lanzar App
# ----------------------------------------------------
def lanzar_app():
    app = AppGUI()
    app.mainloop()
