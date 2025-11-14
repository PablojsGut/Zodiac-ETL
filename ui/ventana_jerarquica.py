import customtkinter as ctk
from tkinter import messagebox

class VentanaSeleccionJerarquica(ctk.CTkToplevel):
    """
    Ventana que muestra dependencias y sus subdependencias en árbol jerárquico.
    Recibe un diccionario con la forma:
        {
            "Dependencia A": ["Subdependencia 1", "Subdependencia 2"],
            "Dependencia B": ["Subdependencia X", "Subdependencia Y"]
        }
    """
    def __init__(self, master, estructura: dict, callback_confirmar):
        super().__init__(master)
        
        self.title("Seleccionar Subdependencias a Exportar")
        self.geometry("480x680")

        self.estructura = estructura
        self.callback_confirmar = callback_confirmar
        self.vars = {}

        # Configuración de ventana
        self.transient(master)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        # Título
        ctk.CTkLabel(
            self,
            text="Selecciona las subdependencias a exportar:",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Frame desplazable para la lista
        self.frame_scroll = ctk.CTkScrollableFrame(self, width=440, height=480)
        self.frame_scroll.pack(pady=5)

        # Construir jerarquía visual
        for dep, subdependencias in estructura.items():
            frame_dep = ctk.CTkFrame(self.frame_scroll)
            frame_dep.pack(fill="x", pady=4)

            lbl_dep = ctk.CTkLabel(
                frame_dep,
                text=f"📁 {dep}",
                font=("Arial", 13, "bold")
            )
            lbl_dep.pack(anchor="w", padx=5)

            # Si la dependencia no tiene subdependencias, la mostramos igualmente
            if not subdependencias:
                ctk.CTkLabel(
                    frame_dep,
                    text="   └ (Sin subdependencias)",
                    font=("Arial", 12, "italic")
                ).pack(anchor="w", padx=20)
                continue

            for sub in subdependencias:
                var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(
                    frame_dep,
                    text=f"   └ {sub}",
                    variable=var
                )
                chk.pack(anchor="w", padx=20, pady=1)
                self.vars[(dep, sub)] = var

        # --- Botones inferiores ---
        frame_botones = ctk.CTkFrame(self)
        frame_botones.pack(pady=10)

        ctk.CTkButton(frame_botones, text="✅ Seleccionar todas",
                      command=self.seleccionar_todas).grid(row=0, column=0, padx=5)
        ctk.CTkButton(frame_botones, text="❌ Deseleccionar todas",
                      command=self.deseleccionar_todas).grid(row=0, column=1, padx=5)

        ctk.CTkButton(self, text="📦 Exportar seleccionadas",
                      command=self.confirmar).pack(pady=10)

    # --- Métodos de control ---
    def seleccionar_todas(self):
        for v in self.vars.values():
            v.set(True)

    def deseleccionar_todas(self):
        for v in self.vars.values():
            v.set(False)

    def confirmar(self):
        """Recolecta las subdependencias seleccionadas y llama al callback."""
        seleccionadas = [(dep, sub) for (dep, sub), var in self.vars.items() if var.get()]

        if not seleccionadas:
            messagebox.showwarning("Advertencia", "Debes seleccionar al menos una subdependencia.")
            return

        self.grab_release()
        self.destroy()
        self.callback_confirmar(seleccionadas)
