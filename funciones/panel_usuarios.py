import tkinter as tk
from tkinter import ttk, messagebox
from bson import ObjectId
from __init__ import usuarios_info

class PanelUsuariosTkinter(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Gestor de Usuarios - MongoDB")
        self.geometry("1150x750")
        self.minsize(900, 600)

        # Configuración de Paleta de Colores Dark Mode
        self.COLOR_BG = "#1e1e2e"          # Fondo principal
        self.COLOR_PANEL = "#2b2b3b"       # Fondo de paneles/tarjetas
        self.COLOR_ACCENT = "#5865f2"      # Color de acento (Azul Discord / Primario)
        self.COLOR_TEXT = "#ffffff"        # Texto blanco
        self.COLOR_MUTED = "#a0a0b0"       # Texto secundario
        self.COLOR_ENTRY = "#181825"       # Fondo de los campos de texto
        self.COLOR_BTN_SAVE = "#2af598"    # Verde para guardar
        self.COLOR_DANGER = "#ff5555"      # Rojo para eliminar

        self.configure(bg=self.COLOR_BG)

        self.usuario_actual_id = None
        self.entries_cache = {}
        self.redes_frame = None
        self.redes_entries = {}

        # Configurar estilos ttk
        self.setup_styles()

        # Grid principal (Izquierda: Lista | Derecha: Formulario)
        self.grid_columnconfigure(0, weight=1, minsize=320)
        self.grid_columnconfigure(1, weight=2, minsize=500)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # PANEL IZQUIERDO: Lista de Usuarios + Buscador
        # ==========================================
        left_panel = tk.Frame(self, bg=self.COLOR_PANEL, padx=15, pady=15)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        lbl_title_left = tk.Label(
            left_panel, text="Usuarios", font=("Segoe UI", 16, "bold"),
            bg=self.COLOR_PANEL, fg=self.COLOR_TEXT
        )
        lbl_title_left.pack(anchor="w", pady=(0, 5))

        # --- BUSCADOR ---
        search_frame = tk.Frame(left_panel, bg=self.COLOR_PANEL)
        search_frame.pack(fill="x", pady=(0, 10))

        lbl_search_icon = tk.Label(
            search_frame, text="🔍", font=("Segoe UI", 11),
            bg=self.COLOR_PANEL, fg=self.COLOR_MUTED
        )
        lbl_search_icon.pack(side="left", padx=(0, 5))

        self.var_busqueda = tk.StringVar()
        # Escuchar cambios en la barra de búsqueda para filtrar en tiempo real
        self.var_busqueda.trace_add("write", lambda *args: self.cargar_lista_usuarios())

        self.ent_busqueda = tk.Entry(
            search_frame, textvariable=self.var_busqueda, font=("Segoe UI", 10),
            bg=self.COLOR_ENTRY, fg=self.COLOR_TEXT, insertbackground="white",
            bd=1, relief="solid"
        )
        self.ent_busqueda.pack(side="left", fill="x", expand=True, ipady=4)

        # Pestañas (Registrados vs No Registrados)
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill="both", expand=True)

        self.tab_registrados = tk.Frame(self.notebook, bg=self.COLOR_PANEL)
        self.tab_no_registrados = tk.Frame(self.notebook, bg=self.COLOR_PANEL)

        self.notebook.add(self.tab_registrados, text=" Registrados ")
        self.notebook.add(self.tab_no_registrados, text=" No Registrados ")

        # Scrollbars para listas
        self.scroll_registrados = self.crear_scrollable_frame(self.tab_registrados)
        self.scroll_no_registrados = self.crear_scrollable_frame(self.tab_no_registrados)

        # ==========================================
        # PANEL DERECHO: Editor de Usuario
        # ==========================================
        right_panel = tk.Frame(self, bg=self.COLOR_PANEL, padx=20, pady=15)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)

        self.lbl_editor_title = tk.Label(
            right_panel, text="Selecciona un usuario de la lista",
            font=("Segoe UI", 15, "bold"), bg=self.COLOR_PANEL, fg=self.COLOR_MUTED
        )
        self.lbl_editor_title.pack(anchor="w", pady=(0, 10))

        # ÁREA CON SCROLL PARA EL FORMULARIO
        self.scroll_editor = self.crear_scrollable_frame(right_panel)

        # Botón Guardar Cambios
        self.btn_guardar = tk.Button(
            right_panel, text="💾 Guardar Cambios", font=("Segoe UI", 11, "bold"),
            bg=self.COLOR_BTN_SAVE, fg="#11111b", activebackground="#20c978",
            bd=0, padx=20, pady=10, cursor="hand2", command=self.guardar_cambios, state="disabled"
        )
        self.btn_guardar.pack(fill="x", pady=(10, 0))

        # Cargar usuarios desde la base de datos
        self.cargar_lista_usuarios()

    def setup_styles(self):
        """Aplica estilos modernos a los componentes ttk nativos."""
        style = ttk.Style(self)
        style.theme_use("clam")

        # Pestañas Notebook
        style.configure("TNotebook", background=self.COLOR_PANEL, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.COLOR_BG, foreground=self.COLOR_MUTED,
                        padding=[12, 6], font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", self.COLOR_ACCENT)],
                  foreground=[("selected", self.COLOR_TEXT)])

    def crear_scrollable_frame(self, parent):
        """Crea un contenedor con barra de desplazamiento vertical integrada."""
        canvas = tk.Canvas(parent, bg=self.COLOR_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.COLOR_PANEL)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind('<Configure>', _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scroll_frame

    def cargar_lista_usuarios(self):
        """Obtiene y filtra los usuarios desde MongoDB según el término de búsqueda."""
        for child in self.scroll_registrados.winfo_children():
            child.destroy()
        for child in self.scroll_no_registrados.winfo_children():
            child.destroy()

        filtro = self.var_busqueda.get().strip().lower()
        usuarios = list(usuarios_info.find({}))

        for user in usuarios:
            nombre = str(user.get("nombre", "")).lower()
            discriminador = str(user.get("discriminador_discord", "")).lower()
            aliases = [str(a).lower() for a in user.get("aliases", [])]

            # Si hay un término de búsqueda, comprobar si coincide con algún campo
            if filtro:
                coincide = (
                    filtro in nombre or 
                    filtro in discriminador or 
                    any(filtro in a for a in aliases)
                )
                if not coincide:
                    continue

            es_validado = user.get("validado", False)
            parent = self.scroll_registrados if es_validado else self.scroll_no_registrados

            nombre_mostrado = user.get("nombre") or user.get("discriminador_discord") or "Sin Nombre"
            doc_id = str(user["_id"])

            btn = tk.Button(
                parent, text=f"  👤 {nombre_mostrado}", anchor="w",
                font=("Segoe UI", 10), bg=self.COLOR_BG, fg=self.COLOR_TEXT,
                activebackground=self.COLOR_ACCENT, activeforeground=self.COLOR_TEXT,
                bd=0, pady=8, padx=10, cursor="hand2",
                command=lambda uid=doc_id: self.cargar_formulario_usuario(uid)
            )
            btn.pack(fill="x", pady=3)

    def cargar_formulario_usuario(self, user_id):
        """Construye el formulario editable para el usuario seleccionado."""
        self.usuario_actual_id = user_id
        self.entries_cache.clear()
        self.redes_entries.clear()

        for widget in self.scroll_editor.winfo_children():
            widget.destroy()

        usuario = usuarios_info.find_one({"_id": ObjectId(user_id)})
        if not usuario:
            messagebox.showerror("Error", "El usuario no existe.")
            return

        nombre_titular = usuario.get('nombre') or usuario.get('discriminador_discord') or 'Usuario'
        self.lbl_editor_title.config(
            text=f"Editando a: {nombre_titular}",
            fg=self.COLOR_TEXT
        )
        self.btn_guardar.config(state="normal")

        # Iterar sobre las propiedades del usuario
        for clave, valor in usuario.items():
            if clave in ["_id", "mensajes_md"]:
                continue

            # --- REDES SOCIALES ---
            if clave == "redes":
                self.crear_seccion_redes(valor)
                continue

            frame_campo = tk.Frame(self.scroll_editor, bg=self.COLOR_PANEL, pady=6)
            frame_campo.pack(fill="x", expand=True)

            lbl = tk.Label(
                frame_campo, text=clave.capitalize().replace("_", " "),
                font=("Segoe UI", 10, "bold"), bg=self.COLOR_PANEL, fg=self.COLOR_MUTED
            )
            lbl.pack(anchor="w", pady=(0, 2))

            # Booleano
            if isinstance(valor, bool):
                var = tk.BooleanVar(value=valor)
                chk = tk.Checkbutton(
                    frame_campo, text="Validado / Confirmado", variable=var,
                    bg=self.COLOR_PANEL, fg=self.COLOR_TEXT, activebackground=self.COLOR_PANEL,
                    activeforeground=self.COLOR_TEXT, selectcolor=self.COLOR_ENTRY, font=("Segoe UI", 10)
                )
                chk.pack(anchor="w")
                self.entries_cache[clave] = var

            # Cadenas / Texto Largo
            elif isinstance(valor, str):
                if len(valor) > 60 or clave == "descripcion":
                    txt = tk.Text(
                        frame_campo, height=3, font=("Segoe UI", 10),
                        bg=self.COLOR_ENTRY, fg=self.COLOR_TEXT, insertbackground="white",
                        bd=1, relief="solid", wrap="word"
                    )
                    txt.insert("1.0", valor)
                    txt.pack(fill="x", expand=True)
                    self.entries_cache[clave] = (txt, "text")
                else:
                    ent = tk.Entry(
                        frame_campo, font=("Segoe UI", 10), bg=self.COLOR_ENTRY,
                        fg=self.COLOR_TEXT, insertbackground="white", bd=1, relief="solid"
                    )
                    ent.insert(0, valor)
                    ent.pack(fill="x", expand=True, ipady=4)
                    self.entries_cache[clave] = ent

            # Números
            elif isinstance(valor, (int, float)):
                ent = tk.Entry(
                    frame_campo, font=("Segoe UI", 10), bg=self.COLOR_ENTRY,
                    fg=self.COLOR_TEXT, insertbackground="white", bd=1, relief="solid"
                )
                ent.insert(0, str(valor))
                ent.pack(fill="x", expand=True, ipady=4)
                self.entries_cache[clave] = ent

            # Listas
            elif isinstance(valor, list):
                ent = tk.Entry(
                    frame_campo, font=("Segoe UI", 10), bg=self.COLOR_ENTRY,
                    fg=self.COLOR_TEXT, insertbackground="white", bd=1, relief="solid"
                )
                ent.insert(0, ", ".join([str(x) for x in valor]))
                ent.pack(fill="x", expand=True, ipady=4)
                self.entries_cache[clave] = (ent, "list")

            # Subdocumentos
            elif isinstance(valor, dict):
                sub_group = tk.LabelFrame(
                    frame_campo, text=f" {clave.capitalize()} ", font=("Segoe UI", 9, "bold"),
                    bg=self.COLOR_PANEL, fg=self.COLOR_ACCENT, bd=1, relief="solid", padx=10, pady=8
                )
                sub_group.pack(fill="x", expand=True, pady=4)

                self.entries_cache[clave] = {}
                for sub_k, sub_v in valor.items():
                    sub_f = tk.Frame(sub_group, bg=self.COLOR_PANEL)
                    sub_f.pack(fill="x", expand=True, pady=2)

                    sub_lbl = tk.Label(
                        sub_f, text=f"{sub_k}:", font=("Segoe UI", 9),
                        bg=self.COLOR_PANEL, fg=self.COLOR_TEXT, width=22, anchor="w"
                    )
                    sub_lbl.pack(side="left")

                    sub_ent = tk.Entry(
                        sub_f, font=("Segoe UI", 9), bg=self.COLOR_ENTRY,
                        fg=self.COLOR_TEXT, insertbackground="white", bd=1, relief="solid"
                    )
                    sub_ent.insert(0, str(sub_v) if sub_v is not None else "")
                    sub_ent.pack(side="right", fill="x", expand=True, ipady=2)

                    self.entries_cache[clave][sub_k] = sub_ent

    def crear_seccion_redes(self, dict_redes):
        """Sección interactiva para redes sociales."""
        group = tk.LabelFrame(
            self.scroll_editor, text=" Redes Sociales ", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_PANEL, fg=self.COLOR_ACCENT, bd=1, relief="solid", padx=10, pady=10
        )
        group.pack(fill="x", expand=True, pady=8)

        self.redes_frame = tk.Frame(group, bg=self.COLOR_PANEL)
        self.redes_frame.pack(fill="x", expand=True)

        if isinstance(dict_redes, dict):
            for red, usuario_red in dict_redes.items():
                self.agregar_fila_red(red, usuario_red)

        btn_add = tk.Button(
            group, text="➕ Agregar otra red social", font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_ACCENT, fg=self.COLOR_TEXT, bd=0, pady=5, cursor="hand2",
            command=lambda: self.agregar_fila_red("", "")
        )
        btn_add.pack(anchor="w", pady=(8, 0))

    def agregar_fila_red(self, red="", usuario_red=""):
        """Añade una fila de red social."""
        row_frame = tk.Frame(self.redes_frame, bg=self.COLOR_PANEL)
        row_frame.pack(fill="x", expand=True, pady=3)

        ent_plat = tk.Entry(
            row_frame, font=("Segoe UI", 9), bg=self.COLOR_ENTRY,
            fg=self.COLOR_TEXT, insertbackground="white", bd=1, relief="solid", width=15
        )
        ent_plat.insert(0, red)
        ent_plat.pack(side="left", padx=(0, 5), ipady=3)

        ent_val = tk.Entry(
            row_frame, font=("Segoe UI", 9), bg=self.COLOR_ENTRY,
            fg=self.COLOR_TEXT, insertbackground="white", bd=1, relief="solid"
        )
        ent_val.insert(0, usuario_red)
        ent_val.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=3)

        btn_del = tk.Button(
            row_frame, text="✖", font=("Segoe UI", 8, "bold"),
            bg=self.COLOR_DANGER, fg="white", bd=0, padx=8, cursor="hand2",
            command=lambda: self.eliminar_fila_red(row_frame)
        )
        btn_del.pack(side="right")

        self.redes_entries[row_frame] = (ent_plat, ent_val)

    def eliminar_fila_red(self, row_frame):
        """Elimina la fila de red social."""
        if row_frame in self.redes_entries:
            del self.redes_entries[row_frame]
        row_frame.destroy()

    def guardar_cambios(self):
        """Guarda las modificaciones en MongoDB."""
        if not self.usuario_actual_id:
            return

        data_update = {}

        # Parsear campos
        for clave, obj in self.entries_cache.items():
            if isinstance(obj, tk.BooleanVar):
                data_update[clave] = obj.get()

            elif isinstance(obj, tk.Entry):
                val = obj.get().strip()
                if val.isdigit():
                    data_update[clave] = int(val)
                else:
                    try:
                        data_update[clave] = float(val)
                    except ValueError:
                        data_update[clave] = val

            elif isinstance(obj, tuple):
                tipo = obj[1]
                widget = obj[0]
                if tipo == "text":
                    data_update[clave] = widget.get("1.0", "end-1c").strip()
                elif tipo == "list":
                    elementos = [item.strip() for item in widget.get().split(",") if item.strip()]
                    data_update[clave] = elementos

            elif isinstance(obj, dict):
                sub_dict = {}
                for sub_k, sub_ent in obj.items():
                    val = sub_ent.get().strip()
                    if val.isdigit():
                        sub_dict[sub_k] = int(val)
                    else:
                        try:
                            sub_dict[sub_k] = float(val)
                        except ValueError:
                            sub_dict[sub_k] = val
                data_update[clave] = sub_dict

        # Parsear Redes
        redes_dict = {}
        for _, (ent_plat, ent_val) in self.redes_entries.items():
            plat = ent_plat.get().strip()
            val = ent_val.get().strip()
            if plat:
                redes_dict[plat] = val

        data_update["redes"] = redes_dict

        # Guardar
        try:
            usuarios_info.update_one(
                {"_id": ObjectId(self.usuario_actual_id)},
                {"$set": data_update}
            )
            messagebox.showinfo("Éxito", "Usuario guardado correctamente.")
            self.cargar_lista_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

if __name__ == "__main__":
    app = PanelUsuariosTkinter()
    app.mainloop()