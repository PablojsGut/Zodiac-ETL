import customtkinter as ctk

ZODIAC_MONTHS = [
    ("♒", "Enero"), ("♓", "Febrero"), ("♈", "Marzo"),
    ("♉", "Abril"), ("♊", "Mayo"), ("♋", "Junio"),
    ("♌", "Julio"), ("♍", "Agosto"), ("♎", "Septiembre"),
    ("♏", "Octubre"), ("♐", "Noviembre"), ("♑", "Diciembre")
]


class VentanaFiltroMes(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        # -----------------------------------------
        # QUITAR MINIMIZAR Y MAXIMIZAR (Windows)
        # -----------------------------------------
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)

            # WS_MINIMIZEBOX 0x00020000
            # WS_MAXIMIZEBOX 0x00010000
            style &= ~0x00020000
            style &= ~0x00010000

            ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        except:
            pass
        # -----------------------------------------

        self.title("Filtrar por mes")
        self.geometry("420x680")

        # Guardará el resultado final
        self.resultado = None

        # Bring window to front
        self.after(100, lambda: (self.lift(), self.focus(), self.grab_set()))

        # ---------- Año (solo números) ----------
        validar_num = self.register(lambda text: text.isdigit() or text == "")
        lbl_year = ctk.CTkLabel(self, text="Ingrese el año:", font=("Arial", 16))
        lbl_year.pack(pady=(10, 0))

        self.year_entry = ctk.CTkEntry(self, validate="key", validatecommand=(validar_num, "%P"))
        self.year_entry.pack(pady=(0, 15))

        # ---------- Selección de modo ----------
        self.modo = ctk.StringVar(value="mes")

        frame_modos = ctk.CTkFrame(self)
        frame_modos.pack(pady=10, padx=10, fill="x")

        ctk.CTkRadioButton(frame_modos, text="Filtrar por mes",
                           variable=self.modo, value="mes", font=("Arial", 15),
                           command=self.cambiar_modo).pack(anchor="w", padx=10, pady=5)

        ctk.CTkRadioButton(frame_modos, text="Filtrar por rango",
                           variable=self.modo, value="rango", font=("Arial", 15),
                           command=self.cambiar_modo).pack(anchor="w", padx=10, pady=5)

        # ---------- Contenedor dinámico ----------
        self.dynamic_frame = ctk.CTkFrame(self)
        self.dynamic_frame.pack(pady=10, fill="x")

        self.crear_ui_mes()

        # Label para errores
        self.lbl_error = ctk.CTkLabel(self, text="", text_color="red", font=("Arial", 14))
        self.lbl_error.pack()

        # ---------- Botones ----------
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Confirmar", fg_color="#4CAF50",
                      command=self.confirmar).grid(row=0, column=0, padx=10)

        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#B71C1C",
                      command=self.destroy).grid(row=0, column=1, padx=10)

    # ==============================================================  
    # UI PARA FILTRAR POR MES
    # ==============================================================  
    def crear_ui_mes(self):
        for w in self.dynamic_frame.winfo_children(): 
            w.destroy()

        self.mes_seleccionado = ctk.StringVar(value="todo")

        ctk.CTkLabel(self.dynamic_frame, text="Seleccione un mes:",
                    font=("Arial", 17)).pack(pady=10)

        # --- Dividir meses en dos columnas ---
        frame_cols = ctk.CTkFrame(self.dynamic_frame)
        frame_cols.pack(pady=10)

        mitad = len(ZODIAC_MONTHS) // 2
        col1 = ZODIAC_MONTHS[:mitad]
        col2 = ZODIAC_MONTHS[mitad:]

        # Columna 1
        col1_frame = ctk.CTkFrame(frame_cols)
        col1_frame.grid(row=0, column=0, padx=10, pady=5)

        for simbolo, mes in col1:
            ctk.CTkRadioButton(
                col1_frame,
                text=f"{simbolo} {mes}",
                variable=self.mes_seleccionado,
                value=mes,
                font=("Arial", 15)
            ).pack(anchor="w", pady=3)

        # Columna 2
        col2_frame = ctk.CTkFrame(frame_cols)
        col2_frame.grid(row=0, column=1, padx=10, pady=5)

        for simbolo, mes in col2:
            ctk.CTkRadioButton(
                col2_frame,
                text=f"{simbolo} {mes}",
                variable=self.mes_seleccionado,
                value=mes,
                font=("Arial", 15)
            ).pack(anchor="w", pady=3)

        # Opción: Todo el año
        ctk.CTkRadioButton(
            self.dynamic_frame,
            text="📆 Todo el año",
            variable=self.mes_seleccionado,
            value="todo",
            font=("Arial", 15)
        ).pack(pady=10)

    # ==============================================================  
    # UI PARA FILTRAR POR RANGO
    # ==============================================================  
    def crear_ui_rango(self):
        for w in self.dynamic_frame.winfo_children(): w.destroy()

        ctk.CTkLabel(self.dynamic_frame, text="Seleccione rango de meses:",
                     font=("Arial", 17)).pack(pady=10)

        meses = [f"{sim} {mes}" for sim, mes in ZODIAC_MONTHS]

        frm = ctk.CTkFrame(self.dynamic_frame)
        frm.pack(pady=10)

        self.cbo_inicio = ctk.CTkComboBox(frm, values=meses, state="readonly")
        self.cbo_inicio.grid(row=0, column=0, padx=10, pady=5)

        self.cbo_final = ctk.CTkComboBox(frm, values=meses, state="readonly")
        self.cbo_final.grid(row=0, column=1, padx=10, pady=5)

        self.cbo_inicio.configure(command=self.validar_rango)
        self.cbo_final.configure(command=self.validar_rango)

    # ==============================================================  
    def cambiar_modo(self):
        if self.modo.get() == "mes":
            self.crear_ui_mes()
        else:
            self.crear_ui_rango()

    # ==============================================================  
    def validar_rango(self, *args):
        if not hasattr(self, "cbo_inicio") or not hasattr(self, "cbo_final"):
            return

        inicio = self.cbo_inicio.get()
        fin = self.cbo_final.get()

        if not inicio or not fin:
            return

        idx_inicio = [m for _, m in ZODIAC_MONTHS].index(inicio.split(" ", 1)[1])
        idx_fin = [m for _, m in ZODIAC_MONTHS].index(fin.split(" ", 1)[1])

        if idx_fin < idx_inicio or idx_fin == idx_inicio:
            self.cbo_final.set("")

    # ==============================================================  
    def confirmar(self):

        self.lbl_error.configure(text="")

        año = self.year_entry.get().strip()

        if not año:
            self.lbl_error.configure(text="Debe ingresar un año válido.")
            return

        modo = self.modo.get()

        if modo == "mes":
            mes = self.mes_seleccionado.get()

            if mes == "":
                self.lbl_error.configure(text="Debe seleccionar un mes.")
                return

            self.resultado = {
                "modo": "mes",
                "anio": int(año),
                "mes": mes
            }
            self.destroy()
            return

        inicio = self.cbo_inicio.get()
        fin = self.cbo_final.get()

        if not inicio or not fin:
            self.lbl_error.configure(text="Debe seleccionar un rango válido.")
            return

        self.resultado = {
            "modo": "rango",
            "anio": int(año),
            "inicio": inicio,
            "fin": fin
        }

        self.destroy()
