import customtkinter as ctk


class VentanaModoDivision(ctk.CTkToplevel):
    """Ventana para elegir el modo de división."""
    def __init__(self, master, callback, tipo_formulario):
        super().__init__(master)

        self.title("Seleccionar modo de división")
        self.geometry("420x200")
        self.callback = callback
        self.tipo_formulario = tipo_formulario

        # Configuración modal
        self.transient(master)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        # Título
        ctk.CTkLabel(
            self,
            text="¿Cómo deseas procesar los datos?",
            font=("Arial", 15, "bold")
        ).pack(pady=20)

        # Frame para los dos primeros botones
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10)

        # Botón Dependencias
        ctk.CTkButton(
            self.frame,
            text="📂 Por Dependencias",
            command=lambda: self.seleccionar("dependencias")
        ).grid(row=0, column=0, padx=10)

        # Botón Subdependencias
        ctk.CTkButton(
            self.frame,
            text="🧩 Por Subdependencias",
            command=lambda: self.seleccionar("subdependencias")
        ).grid(row=0, column=1, padx=10)

        # ---------------------------------------------------------
        # ➕ NUEVO BOTÓN: "Unir datasets"
        # Solo aparece si es VcM
        # ---------------------------------------------------------
        if self.tipo_formulario == "Formulario de Iniciativas VcM":
            ctk.CTkButton(
                self,
                text="🔗 Unir datasets",
                command=lambda: self.seleccionar("union")
            ).pack(pady=15)

    def seleccionar(self, modo):
        self.grab_release()
        self.destroy()
        self.callback(modo)
