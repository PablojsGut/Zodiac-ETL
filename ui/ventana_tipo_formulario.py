import customtkinter as ctk

class VentanaTipoFormulario(ctk.CTkToplevel):
    def __init__(self, master, callback_seleccion):
        super().__init__(master)
        self.title("Seleccionar tipo de formulario")
        self.geometry("420x260")
        self.callback = callback_seleccion

        label = ctk.CTkLabel(self, text="Seleccione el tipo de formulario a procesar:", font=("Arial", 16))
        label.pack(pady=20)

        btn_instancias = ctk.CTkButton(
            self,
            text="📄 Formulario de Participaciones en Instancias Externas",
            command=lambda: self.seleccionar("instancias")
        )
        btn_instancias.pack(pady=10, padx=20)

        btn_vcm = ctk.CTkButton(
            self,
            text="📘 Formulario de Iniciativas VcM",
            command=lambda: self.seleccionar("vcm")
        )
        btn_vcm.pack(pady=10, padx=20)

    def seleccionar(self, tipo):
        self.callback(tipo)
        self.destroy()
