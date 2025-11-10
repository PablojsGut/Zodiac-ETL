import customtkinter as ctk
from tkinter import filedialog, messagebox
import app.controladores as controlador
import pandas as pd
import os
from app.graficos import generar_graficos_y_pdfs  # ✅ función que genera los PDFs directamente


# ---------------------------------------------------------
# 🪟 Ventana para seleccionar modo de división
# ---------------------------------------------------------
class VentanaModoDivision(ctk.CTkToplevel):
    """Ventana para elegir el modo de división."""
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Seleccionar modo de división")
        self.geometry("400x200")
        self.callback = callback

        # Ventana modal y siempre encima
        self.transient(master)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="¿Cómo deseas dividir el archivo Excel?",
                     font=("Arial", 15, "bold")).pack(pady=20)

        frame = ctk.CTkFrame(self)
        frame.pack(pady=10)

        ctk.CTkButton(frame, text="📂 Por Dependencias",
                      command=lambda: self.seleccionar("dependencias")).grid(row=0, column=0, padx=10)
        ctk.CTkButton(frame, text="🧩 Por Subdependencias",
                      command=lambda: self.seleccionar("subdependencias")).grid(row=0, column=1, padx=10)

    def seleccionar(self, modo):
        self.grab_release()
        self.destroy()
        self.callback(modo)


# ---------------------------------------------------------
# ✅ Ventana para seleccionar dependencias
# ---------------------------------------------------------
class VentanaSeleccionDependencias(ctk.CTkToplevel):
    """Ventana que permite seleccionar qué dependencias exportar."""
    def __init__(self, master, dependencias, callback_confirmar):
        super().__init__(master)

        # Ventana modal al frente
        self.transient(master)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        self.title("Seleccionar Dependencias a Exportar")
        self.geometry("420x520")
        self.callback_confirmar = callback_confirmar
        self.dependencias = dependencias
        self.vars = {}

        ctk.CTkLabel(self, text="Selecciona las dependencias a exportar:",
                     font=("Arial", 14, "bold")).pack(pady=10)

        frame_lista = ctk.CTkScrollableFrame(self, width=380, height=380)
        frame_lista.pack(pady=5)

        # Checkboxes
        for dep in dependencias:
            var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(frame_lista, text=dep, variable=var)
            chk.pack(anchor="w", pady=2)
            self.vars[dep] = var

        frame_botones = ctk.CTkFrame(self)
        frame_botones.pack(pady=10)

        ctk.CTkButton(frame_botones, text="✅ Seleccionar todas", command=self.seleccionar_todas).grid(row=0, column=0, padx=5)
        ctk.CTkButton(frame_botones, text="❌ Deseleccionar todas", command=self.deseleccionar_todas).grid(row=0, column=1, padx=5)

        ctk.CTkButton(self, text="📦 Exportar seleccionadas", command=self.confirmar).pack(pady=10)

    def seleccionar_todas(self):
        for v in self.vars.values():
            v.set(True)

    def deseleccionar_todas(self):
        for v in self.vars.values():
            v.set(False)

    def confirmar(self):
        seleccionadas = [dep for dep, var in self.vars.items() if var.get()]
        if not seleccionadas:
            messagebox.showwarning("Advertencia", "Debes seleccionar al menos una dependencia.")
            return
        self.grab_release()
        self.destroy()
        self.callback_confirmar(seleccionadas)


# ---------------------------------------------------------
# 🌳 Ventana jerárquica (dependencias → subdependencias)
# ---------------------------------------------------------
class VentanaSeleccionJerarquica(ctk.CTkToplevel):
    """Ventana que muestra dependencias y sus subdependencias en árbol."""
    def __init__(self, master, estructura, callback_confirmar):
        super().__init__(master)
        self.title("Seleccionar Subdependencias a Exportar")
        self.geometry("460x580")

        self.estructura = estructura
        self.callback_confirmar = callback_confirmar
        self.vars = {}

        self.transient(master)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Selecciona las subdependencias a exportar:",
                     font=("Arial", 14, "bold")).pack(pady=10)

        self.frame_scroll = ctk.CTkScrollableFrame(self, width=430, height=450)
        self.frame_scroll.pack(pady=5)

        for dep, subgrupos in estructura.items():
            frame_dep = ctk.CTkFrame(self.frame_scroll)
            frame_dep.pack(fill="x", pady=4)

            lbl_dep = ctk.CTkLabel(frame_dep, text=f"📁 {dep}", font=("Arial", 13, "bold"))
            lbl_dep.pack(anchor="w", padx=5)

            for sub in subgrupos.keys():
                var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(frame_dep, text=f"   └ {sub}", variable=var)
                chk.pack(anchor="w", padx=20, pady=1)
                self.vars[(dep, sub)] = var

        frame_botones = ctk.CTkFrame(self)
        frame_botones.pack(pady=10)

        ctk.CTkButton(frame_botones, text="✅ Seleccionar todas", command=self.seleccionar_todas).grid(row=0, column=0, padx=5)
        ctk.CTkButton(frame_botones, text="❌ Deseleccionar todas", command=self.deseleccionar_todas).grid(row=0, column=1, padx=5)

        ctk.CTkButton(self, text="📦 Exportar seleccionadas", command=self.confirmar).pack(pady=10)

    def seleccionar_todas(self):
        for v in self.vars.values():
            v.set(True)

    def deseleccionar_todas(self):
        for v in self.vars.values():
            v.set(False)

    def confirmar(self):
        seleccionadas = [(dep, sub) for (dep, sub), var in self.vars.items() if var.get()]
        if not seleccionadas:
            messagebox.showwarning("Advertencia", "Debes seleccionar al menos una subdependencia.")
            return
        self.grab_release()
        self.destroy()
        self.callback_confirmar(seleccionadas)


# ---------------------------------------------------------
# 🖥️ Ventana principal
# ---------------------------------------------------------
class AppGUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Validador y Procesador de Archivo Excel")
        self.geometry("560x400")

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

        self.ruta_archivo = None
        self.dfs_sub = None

    # -----------------------------
    def seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if not ruta:
            return
        self.ruta_archivo = ruta
        self.label_ruta.configure(text=ruta)
        self.label_resultado.configure(text="⏳ Validando archivo...", text_color="orange")
        self.update_idletasks()

        # 🔹 Validar automáticamente
        if controlador.validar_archivo(ruta):
            self.label_resultado.configure(text="✅ Archivo válido y listo para procesar.", text_color="green")
            self.btn_procesar.configure(state="normal")
        else:
            self.label_resultado.configure(text="❌ Archivo inválido o columnas incompletas.", text_color="red")
            self.btn_procesar.configure(state="disabled")

    # -----------------------------
    def abrir_modo_division(self):
        VentanaModoDivision(self, self.procesar_segun_modo)

    def procesar_segun_modo(self, modo):
        if not self.ruta_archivo:
            return

        ruta_salida_base = filedialog.askdirectory(title="Selecciona carpeta base para exportar")
        if not ruta_salida_base:
            self.label_resultado.configure(text="⚠️ Exportación cancelada.", text_color="orange")
            return

        df = pd.read_excel(self.ruta_archivo)

        if modo == "dependencias":
            dependencias = controlador.obtener_dependencias(df)
            VentanaSeleccionDependencias(self, dependencias,
                lambda seleccion: self.exportar_dependencias(seleccion, ruta_salida_base))
        else:
            df = controlador.limpiar_y_renombrar_columnas(df)
            df_dependencias = controlador.dividir_por_dependencia(df)
            self.dfs_sub = controlador.subdividir_por_dependencia(df_dependencias)

            VentanaSeleccionJerarquica(
                self,
                self.dfs_sub,
                lambda seleccion: self.exportar_subdependencias(seleccion, ruta_salida_base)
            )

    # -----------------------------
    def exportar_dependencias(self, seleccionadas, ruta_salida_base):
        """
        Exporta las dependencias seleccionadas y genera los PDFs en la misma carpeta.
        """
        self.label_resultado.configure(text="⏳ Exportando dependencias...", text_color="orange")
        self.update_idletasks()

        # Procesar y exportar los Excel
        ruta_final = controlador.procesar_excel(self.ruta_archivo, ruta_salida_base, seleccionadas=seleccionadas)
        if not ruta_final:
            self.label_resultado.configure(text="❌ Error al exportar dependencias.", text_color="red")
            return

        print("📊 Generando reportes PDF...")

        # Leer cada Excel exportado
        dfs_subdivididos = {}
        for dep in seleccionadas:
            archivo_dep = os.path.join(ruta_final, f"{dep.replace('/', '_').replace(' ', '_')}.xlsx")
            if not os.path.exists(archivo_dep):
                print(f"⚠️ Archivo no encontrado para {dep}: {archivo_dep}")
                continue

            try:
                dfs_subdivididos[dep] = pd.read_excel(archivo_dep)
            except Exception as e:
                print(f"❌ Error al leer {archivo_dep}: {e}")

        # Validar si hay datos
        if not dfs_subdivididos:
            print("⚠️ No se encontraron dependencias para generar PDF.")
            self.label_resultado.configure(
                text="⚠️ No se pudieron generar PDFs (no se encontraron archivos).",
                text_color="orange"
            )
            return

        # ✅ Generar los PDFs correctamente
        try:
            generar_graficos_y_pdfs(
                dfs_subdivididos=dfs_subdivididos,
                seleccionadas=seleccionadas,
                modo="dependencias",
                ruta_salida=ruta_final
            )
            print("✅ PDFs generados correctamente.")
            self.label_resultado.configure(
                text=f"✅ Dependencias exportadas y PDFs generados.\n📁 Carpeta: {ruta_final}",
                text_color="green"
            )
        except Exception as e:
            print(f"❌ Error al generar PDFs: {e}")
            self.label_resultado.configure(
                text=f"❌ Error al generar PDFs: {e}",
                text_color="red"
            )

    # -----------------------------
    def exportar_subdependencias(self, seleccionadas, ruta_salida_base):
        self.label_resultado.configure(text="⏳ Exportando subdependencias...", text_color="orange")
        self.update_idletasks()

        ruta_final = controlador.procesar_excel_por_subdependencias(
            self.ruta_archivo, ruta_salida_base, seleccionadas
        )
        if not ruta_final:
            self.label_resultado.configure(text="❌ Error al exportar subdependencias.", text_color="red")
            return

        # Generar PDFs en la misma carpeta
        generar_graficos_y_pdfs(
            dfs_subdivididos=self.dfs_sub,
            seleccionadas=seleccionadas,
            modo="subdependencias",
            ruta_salida=ruta_final   # 📂 PDFs se guardan junto con los Excel
        )

        self.label_resultado.configure(
            text=f"✅ Subdependencias exportadas y PDFs generados.\n📁 Carpeta: {ruta_final}",
            text_color="green"
        )


# ---------------------------------------------------------
# 🚀 Lanzar aplicación
# ---------------------------------------------------------
def lanzar_app():
    app = AppGUI()
    app.mainloop()
