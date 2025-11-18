import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
import os
import sys
from io import StringIO

import controladores as controlador
from scripts.instancias_externas.graficos import generar_graficos_y_pdfs

from ui.ventana_modo import VentanaModoDivision
from ui.ventana_dependencias import VentanaSeleccionDependencias
from ui.ventana_jerarquica import VentanaSeleccionJerarquica

def resource_path(relative):
    import sys, os
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

        # ---------------------------------------------
        # 🔵 Selector de TIPO DE FORMULARIO
        # ---------------------------------------------
        self.label_tipo = ctk.CTkLabel(self, text="Seleccione el tipo de formulario:", font=("Arial", 15))
        self.label_tipo.pack(pady=(10, 5))

        self.tipo_formulario = ctk.StringVar(value="")  # ⚠ Comienza vacío

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

        # ---------------------------------------------
        # Selección de archivo Excel
        # ---------------------------------------------
        self.label = ctk.CTkLabel(self, text="Selecciona un archivo Excel", font=("Arial", 16))
        self.label.pack(pady=10)

        self.btn_seleccionar = ctk.CTkButton(
            self,
            text="📂 Seleccionar Excel",
            command=self.seleccionar_archivo,
            state="disabled"      # 🔒 Bloqueado hasta elegir formulario
        )
        self.btn_seleccionar.pack(pady=10)

        self.label_ruta = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label_ruta.pack(pady=10)

        self.btn_procesar = ctk.CTkButton(
            self,
            text="⚙️ Procesar Excel",
            command=self.abrir_modo_division,
            state="disabled"      # 🔒 Solo si Excel válido
        )
        self.btn_procesar.pack(pady=10)

        self.label_resultado = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.label_resultado.pack(pady=10)

        self.init_consola()

        # Variables internas
        self.ruta_archivo = None
        self.df_validado = None  # ⚠️ Aquí guardamos el DF que entrega validar_excel

    # ---------------------------------------------------------
    # Mensaje del formulario seleccionado
    # ---------------------------------------------------------
    def mostrar_mensaje_formulario(self, seleccion):
        if seleccion == "Formulario de Participaciones en Instancias Externas":
            msg = ("Importe los datos del formulario 'Registro simplificado de participaciones "
                   "en instancias externas' extraídos de Microsoft Form")
        else:
            msg = ("Importe los datos de 'Iniciativas VcM' y 'Síntesis evaluativa de Iniciativas VcM' "
                   "extraídos de VForm")

        self.mensaje_formulario.configure(text=msg)

        # 🔓 Activa botón Seleccionar Excel
        self.btn_seleccionar.configure(state="normal")

    # ---------------------------------------------------------
    # 📂 Seleccionar archivo Excel
    # ---------------------------------------------------------
    def seleccionar_archivo(self):
        tipo = self.tipo_formulario.get()

        # ======================================================
        # 🔵 FORMULARIO DE INSTANCIAS EXTERNAS -> 1 solo archivo
        # ======================================================
        if tipo == "Formulario de Participaciones en Instancias Externas":
            ruta = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
            if not ruta:
                return
            
            self.ruta_archivo = ruta
            self.label_ruta.configure(text=f"📄 Archivo seleccionado:\n{ruta}", text_color="green")

            self.label_resultado.configure(text="⏳ Validando archivo...", text_color="orange")
            self.update_idletasks()

            valido, df = controlador.validar_archivo_formulario(ruta, tipo)

            if valido:
                self.df_validado = df
                self.label_resultado.configure(text="✅ Archivo válido.", text_color="green")
                self.btn_procesar.configure(state="normal")
            else:
                self.df_validado = None
                self.label_resultado.configure(text="❌ Archivo inválido.", text_color="red")
                self.btn_procesar.configure(state="disabled")

            return

        # ======================================================
        # 🟣 FORMULARIO INICIATIVAS VCM -> REQUIERE 2 ARCHIVOS
        # ======================================================
        elif tipo == "Formulario de Iniciativas VcM":
            # ---------- Seleccionar archivo de Iniciativas ---------
            ruta1 = filedialog.askopenfilename(
                title="Selecciona el archivo de Iniciativas VcM",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if not ruta1:
                return

            self.ruta_iniciativas = ruta1

            # ---------- Seleccionar archivo de Síntesis Evaluativa ---------
            ruta2 = filedialog.askopenfilename(
                title="Selecciona el archivo de Síntesis Evaluativa",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if not ruta2:
                return

            self.ruta_sintesis = ruta2

            # Mostrar ambos en el label
            self.label_ruta.configure(text=(
                f"📄 Iniciativas VcM:\n{ruta1}\n\n"
                f"📄 Síntesis Evaluativa:\n{ruta2}"
                ),
                text_color="green"
            )

            # ============================
            # 🔍 Validación de ambos
            # ============================
            self.label_resultado.configure(text="⏳ Validando archivos...", text_color="orange")
            self.update_idletasks()

            validado1, df1 = controlador.validar_archivo_formulario(ruta1, tipo, "columnas_vform1")
            validado2, df2 = controlador.validar_archivo_formulario(ruta2, tipo, "columnas_vform2")

            if validado1 and validado2:

                # Guardamos AMBOS dataframes
                self.df_iniciativas = df1
                self.df_sintesis = df2

                # También guardamos un diccionario unificado
                self.df_validado = {
                    "iniciativas": df1,
                    "sintesis": df2
                }

                self.label_resultado.configure(
                    text="✅ Ambos archivos válidos.\nListos para procesar.",
                    text_color="green"
                )
                self.btn_procesar.configure(state="normal")

            else:
                self.df_validado = None
                self.label_resultado.configure(
                    text="❌ Error validando los archivos.\nRevise que correspondan al formulario VcM.",
                    text_color="red"
                )
                self.btn_procesar.configure(state="disabled")


    # ---------------------------------------------------------
    # ⚙️ Selección modo (dependencias / subdependencias)
    # ---------------------------------------------------------
    def abrir_modo_division(self):
        if self.df_validado is None:
            self.label_resultado.configure(text="❌ No hay archivo válido cargado.", text_color="red")
            return

        VentanaModoDivision(self, self.procesar_segun_modo)

    # ---------------------------------------------------------
    # 🎯 PROCESAR usando DF validado
    # ---------------------------------------------------------
    def procesar_segun_modo(self, modo):
        if self.df_validado is None:
            return

        ruta_salida_base = filedialog.askdirectory(title="Selecciona carpeta base para exportar")
        if not ruta_salida_base:
            self.label_resultado.configure(text="⚠️ Exportación cancelada.", text_color="orange")
            return

        tipo = self.tipo_formulario.get()

        if tipo == "Formulario de Participaciones en Instancias Externas":

            df = self.df_validado

            if modo == "dependencias":
                dependencias = controlador.get_dependencias(df)
                VentanaSeleccionDependencias(
                    self,
                    dependencias,
                    lambda seleccion: self.exportar_dependencias(df, seleccion, ruta_salida_base)
                )

            else:  # subdependencias
                subdependencias = controlador.get_subdependencias(df)
                VentanaSeleccionJerarquica(
                    self,
                    subdependencias,
                    lambda seleccion: self.exportar_subdependencias(df, seleccion, ruta_salida_base)
                )

        # ------------------------------------------------------
        # 🟣 FORMULARIO VFORM (INICIATIVAS VcM)
        # ------------------------------------------------------
        elif tipo == "Formulario de Iniciativas VcM":

            if modo != "dependencias":
                self.label_resultado.configure(
                    text="⚠️ Iniciativas VcM no usa subdependencias.", text_color="orange"
                )
                return

            df1 = self.df_validado["iniciativas"]
            df2 = self.df_validado["sintesis"]
            # Aquí usamos las funciones exclusivas VFORM
            dependencias_vform = controlador.get_dependencias_vform(df1)

            VentanaSeleccionDependencias(
                self,
                dependencias_vform,
                lambda seleccion: self.exportar_dependencias_vform(df1, df2, seleccion, ruta_salida_base)
            )

    # ---------------------------------------------------------
    # 🧱 Exportar dependencias
    # ---------------------------------------------------------
    def exportar_dependencias(self, df_dep, seleccionadas, ruta_salida_base):
        """Usa el controlador central para procesar y exportar dependencias."""
        self.label_resultado.configure(text="⏳ Exportando dependencias...", text_color="orange")
        self.update_idletasks()

        # ✅ Ahora se usa la función unificada del controlador
        ruta_final, df_dependencias = controlador.procesar_excel_dependencias(
            df_dep, ruta_salida_base, seleccionadas
        )

        if not ruta_final or not df_dependencias:
            self.label_resultado.configure(text="❌ Error al exportar dependencias.", text_color="red")
            return
        
         # 🧾 Generar PDFs
        pdfs_generados = generar_graficos_y_pdfs(
            dfs_divididos=df_dependencias,
            seleccionadas=seleccionadas,
            modo="dependencias",
            ruta_salida=ruta_final
        )

        # ✅ Resultado final según retorno de generar_graficos_y_pdfs()
        if pdfs_generados:
            self.label_resultado.configure(
                text=f"✅ Dependencias exportadas y {len(pdfs_generados)} PDF(s) generados.\n📁 Carpeta: {ruta_final}",
                text_color="green"
            )
        else:
            self.label_resultado.configure(
                text=f"⚠️ Dependencias exportadas, pero no se generaron PDFs.\n📁 Carpeta: {ruta_final}",
                text_color="orange"
            )

    def exportar_dependencias_vform(self, df1, df2, seleccionadas, ruta_salida_base):
        self.label_resultado.configure(text="⏳ Exportando dependencias VcM...", text_color="orange")
        self.update_idletasks()

        ruta_final, df1_dependencias, df2_dependencias = controlador.get_excels_dependencias_vform(
            df1, df2, ruta_salida_base, seleccionadas
        )

        if ruta_final is None or df1_dependencias is None or df2_dependencias is None:
            self.label_resultado.configure(text="❌ Error al exportar dependencias VcM.", text_color="red")
            return
        else:
            self.label_resultado.configure(
                text=f"✅ Dependencias exportadas.\n📁 Carpeta: {ruta_final}",
                text_color="green"
            )


    # ---------------------------------------------------------
    # 🧱 Exportar subdependencias
    # ---------------------------------------------------------
    def exportar_subdependencias(self, df_sub, seleccionadas, ruta_salida_base):
        """Procesa y exporta subdependencias usando el controlador."""
        self.label_resultado.configure(text="⏳ Exportando subdependencias...", text_color="orange")
        self.update_idletasks()

        ruta_final, df_subdependencias = controlador.procesar_excel_subdependencias(
            df_sub, ruta_salida_base, seleccionadas
        )

        if not ruta_final or not df_subdependencias:
            self.label_resultado.configure(text="❌ Error al exportar subdependencias.", text_color="red")
            return

        pdfs_generados = generar_graficos_y_pdfs(
            dfs_divididos=df_subdependencias,
            seleccionadas=seleccionadas,
            modo="subdependencias",
            ruta_salida=ruta_final
        )

        # ✅ Mostrar resultado
        if pdfs_generados:
            self.label_resultado.configure(
                text=f"✅ Subdependencias exportadas y {len(pdfs_generados)} PDF(s) generados.\n📁 Carpeta: {ruta_final}",
                text_color="green"
            )
        else:
            self.label_resultado.configure(
                text=f"⚠️ Subdependencias exportadas, pero no se generaron PDFs.\n📁 Carpeta: {ruta_final}",
                text_color="orange"
            )

    def init_consola(self):
        """Crea una consola plegable para mostrar logs."""
        # Marco contenedor
        self.consola_frame = ctk.CTkFrame(self)
        self.consola_frame.pack(fill="x", padx=10, pady=5)

        # Botón plegable
        self.btn_toggle_consola = ctk.CTkButton(
            self.consola_frame,
            text="📜 Mostrar consola ▼",
            command=self.toggle_consola,
            height=28,
            width=200
        )
        self.btn_toggle_consola.pack(pady=5)

        # Frame que se expande
        self.consola_content = ctk.CTkFrame(self.consola_frame)
        self.consola_content.pack(fill="x", expand=False)
        self.consola_content.pack_forget()  # Oculto inicialmente

        # Cuadro de texto
        self.consola_text = ctk.CTkTextbox(
            self.consola_content,
            width=520,
            height=200,
            font=("Consolas", 12)
        )
        self.consola_text.pack(padx=10, pady=10)

        # Redirigir print a la consola
        sys.stdout = RedirectPrint(self.log_to_console)

        self.consola_abierta = False

    def toggle_consola(self):
        """Muestra u oculta la consola."""
        if self.consola_abierta:
            self.consola_content.pack_forget()
            self.btn_toggle_consola.configure(text="📜 Mostrar consola ▼")
            self.consola_abierta = False
        else:
            self.consola_content.pack(fill="x")
            self.btn_toggle_consola.configure(text="📜 Ocultar consola ▲")
            self.consola_abierta = True

    def log_to_console(self, text):
        """Escribe texto en la consola visual."""
        self.consola_text.insert("end", text)
        self.consola_text.see("end")



# ---------------------------------------------------------
# 🚀 Lanzar aplicación
# ---------------------------------------------------------
def lanzar_app():
    app = AppGUI()
    app.mainloop()
