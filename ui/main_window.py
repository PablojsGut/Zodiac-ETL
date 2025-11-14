import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
import os
import sys
from io import StringIO

import app.controladores as controlador
from scripts.graficos import generar_graficos_y_pdfs

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
        self.iconbitmap(resource_path("zodiac_logo.ico"))
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Zodiac: Validador y Procesador de Archivo Excel")
        self.geometry("580x480")

        self.label = ctk.CTkLabel(self, text="Selecciona un archivo Excel", font=("Arial", 16))
        self.label.pack(pady=20)

        self.btn_seleccionar = ctk.CTkButton(self, text="📂 Seleccionar Excel", command=self.seleccionar_archivo)
        self.btn_seleccionar.pack(pady=10)

        self.label_ruta = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label_ruta.pack(pady=10)

        self.btn_procesar = ctk.CTkButton(self, text="⚙️ Procesar Excel", command=self.abrir_modo_division, state="disabled")
        self.btn_procesar.pack(pady=10)

        self.label_resultado = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.label_resultado.pack(pady=10)

        self.init_consola()

        self.ruta_archivo = None
        self.dfs_sub = None

    # ---------------------------------------------------------
    # 📂 Seleccionar archivo Excel
    # ---------------------------------------------------------
    def seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if not ruta:
            return

        self.ruta_archivo = ruta
        self.label_ruta.configure(text=ruta)
        self.label_resultado.configure(text="⏳ Validando archivo...", text_color="orange")
        self.update_idletasks()

        if controlador.validar_excel(ruta):
            self.label_resultado.configure(text="✅ Archivo válido y listo para procesar.", text_color="green")
            self.btn_procesar.configure(state="normal")
        else:
            self.label_resultado.configure(text="❌ Archivo inválido o columnas incompletas.", text_color="red")
            self.btn_procesar.configure(state="disabled")

    # ---------------------------------------------------------
    # ⚙️ Seleccionar modo de división
    # ---------------------------------------------------------
    def abrir_modo_division(self):
        VentanaModoDivision(self, self.procesar_segun_modo)

    # ---------------------------------------------------------
    # 🧩 Procesar según modo (dependencias o subdependencias)
    # ---------------------------------------------------------
    def procesar_segun_modo(self, modo):
        if not self.ruta_archivo:
            return

        ruta_salida_base = filedialog.askdirectory(title="Selecciona carpeta base para exportar")
        if not ruta_salida_base:
            self.label_resultado.configure(text="⚠️ Exportación cancelada.", text_color="orange")
            return

        df = controlador.transformar_excel(self.ruta_archivo)

        if modo == "dependencias":
            dependencias = controlador.get_dependencias(df)
            VentanaSeleccionDependencias(
                self,
                dependencias,
                lambda seleccion: self.exportar_dependencias(df, seleccion, ruta_salida_base)
            )
        else:
            subdependencias = controlador.get_subdependencias(df)

            VentanaSeleccionJerarquica(
                self,
                subdependencias,
                lambda seleccion: self.exportar_subdependencias(df, seleccion, ruta_salida_base)
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
