import customtkinter as ctk
from tkinter import messagebox


class VentanaSeleccionDependencias(ctk.CTkToplevel):
    """Ventana que permite seleccionar qué dependencias exportar."""
    def __init__(self, master, dependencias, callback_confirmar):
        super().__init__(master)
        self.transient(master)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        self.title("Seleccionar Dependencias a Exportar")
        self.geometry("420x600")
        self.callback_confirmar = callback_confirmar
        self.dependencias = dependencias
        self.vars = {}

        ctk.CTkLabel(self, text="Selecciona las dependencias a exportar:",
                     font=("Arial", 14, "bold")).pack(pady=10)

        frame_lista = ctk.CTkScrollableFrame(self, width=380, height=380)
        frame_lista.pack(pady=5)

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