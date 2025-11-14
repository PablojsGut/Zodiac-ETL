import customtkinter as ctk


class VentanaModoDivision(ctk.CTkToplevel):
    """Ventana para elegir el modo de división."""
    def __init__(self, master, callback):
        super().__init__(master)
        
        self.title("Seleccionar modo de división")
        self.geometry("400x200")
        self.callback = callback

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
