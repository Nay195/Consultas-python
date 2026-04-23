import customtkinter as ctk
from tkinter import ttk, messagebox
import pandas as pd
import os
#pip install customtkinter spyder-kernels
#pip install pandas
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SistemaCamaras(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestión de Infraestructura - Red de Cámaras")
        self.geometry("900x600")
        self.resizable(False, False)

        self.cargar_datos()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frame_login = FrameLogin(self, self.validar_login)
        self.frame_login.grid(row=0, column=0, sticky="nsew")

        self.frame_dashboard = None

    def cargar_datos(self):
        try:
            self.df = pd.read_csv("camaras.csv")
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró el archivo camaras.csv")
            self.df = pd.DataFrame()

    def validar_login(self, usuario, password):
        if not usuario or not password:
            return False, "Campos vacíos"
            
        try:
            with open("usuarios.txt", "r") as f:
                for linea in f:
                    u, p = linea.strip().split(',')
                    if u == usuario and p == password:
                        self.mostrar_dashboard()
                        return True, "Éxito"
            return False, "Credenciales incorrectas"
        except FileNotFoundError:
            return False, "Archivo usuarios.txt no encontrado"

    def mostrar_dashboard(self):
        self.frame_login.destroy()
        self.frame_dashboard = FrameDashboard(self, self.df)
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew")


class FrameLogin(ctk.CTkFrame):
    def __init__(self, master, login_callback):
        super().__init__(master, fg_color="transparent")
        self.login_callback = login_callback

        self.contenedor = ctk.CTkFrame(self, width=300, height=400, corner_radius=15)
        self.contenedor.place(relx=0.5, rely=0.5, anchor="center")

        self.label_titulo = ctk.CTkLabel(self.contenedor, text="Iniciar Sesión", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.pack(pady=(40, 20))

        self.entry_usuario = ctk.CTkEntry(self.contenedor, placeholder_text="Usuario", width=220)
        self.entry_usuario.pack(pady=10)

        self.entry_password = ctk.CTkEntry(self.contenedor, placeholder_text="Contraseña", show="*", width=220)
        self.entry_password.pack(pady=10)

        self.btn_login = ctk.CTkButton(self.contenedor, text="Acceder", command=self.intento_login, width=220)
        self.btn_login.pack(pady=(20, 40))

        self.label_error = ctk.CTkLabel(self.contenedor, text="", text_color="red")
        self.label_error.pack()

    def intento_login(self):
        usr = self.entry_usuario.get()
        pwd = self.entry_password.get()
        exito, msg = self.login_callback(usr, pwd)
        if not exito:
            self.label_error.configure(text=msg)


class FrameDashboard(ctk.CTkFrame):
    def __init__(self, master, df):
        super().__init__(master)
        self.df = df
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        titulo_sidebar = ctk.CTkLabel(self.sidebar, text="Consultas de Red", font=ctk.CTkFont(size=18, weight="bold"))
        titulo_sidebar.pack(pady=20, padx=10)

        self.consultas = {
            "1. Todas las cámaras activas": lambda: self.df[self.df['Estado'] == 'Activa'],
            "2. Cámaras instaladas antes de 2020": lambda: self.df[self.df['Año_Instalacion'] < 2020],
            "3. Conteo por ciudad": lambda: self.df.groupby('Ciudad').size().reset_index(name='Total'),
            "4. Ciudades con cámaras 4K": lambda: self.df[self.df['Resolucion'] == '4K'][['Ciudad', 'ID']].drop_duplicates(),
            "5. Cámaras inactivas en CDMX": lambda: self.df[(self.df['Estado'] == 'Inactiva') & (self.df['Ciudad'] == 'Ciudad de Mexico')],
            "6. Top marcas utilizadas": lambda: self.df['Marca'].value_counts().reset_index(name='Cantidad'),
            "7. Cámara más antigua activa": lambda: self.df[self.df['Estado'] == 'Activa'].sort_values('Año_Instalacion').head(1),
            "8. Cámaras en mantenimiento": lambda: self.df[self.df['Estado'] == 'Mantenimiento'],
            "9. Promedio de año por marca": lambda: self.df.groupby('Marca')['Año_Instalacion'].mean().round().reset_index(name='Año_Promedio'),
            "10. Reporte crítico (Inactivas/Mant)": lambda: self.df[self.df['Estado'].isin(['Inactiva', 'Mantenimiento'])]
        }

        self.opcion_var = ctk.StringVar(value="Seleccionar consulta...")
        self.menu_consultas = ctk.CTkOptionMenu(
            self.sidebar, 
            values=list(self.consultas.keys()), 
            variable=self.opcion_var,
            command=self.ejecutar_consulta,
            width=220
        )
        self.menu_consultas.pack(pady=10, padx=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.lbl_resultado = ctk.CTkLabel(self.main_frame, text="Esperando consulta...", font=ctk.CTkFont(size=16))
        self.lbl_resultado.pack(pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=30, fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Helvetica', 10, 'bold'))

        self.tree_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.tree_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", expand=True, fill="both")

    def ejecutar_consulta(self, seleccion):
        self.lbl_resultado.configure(text=f"Mostrando: {seleccion}")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            df_resultado = self.consultas[seleccion]()
            
            if df_resultado.empty:
                self.tree["columns"] = ("Mensaje",)
                self.tree.heading("Mensaje", text="Información")
                self.tree.insert("", "end", values=("No se encontraron registros para esta consulta.",))
                return

            columnas = list(df_resultado.columns)
            self.tree["columns"] = columnas
            
            for col in columnas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor="center")

            for _, fila in df_resultado.iterrows():
                self.tree.insert("", "end", values=list(fila))
                
        except Exception as e:
            messagebox.showerror("Error de Consulta", f"Ocurrió un error al procesar los datos: {str(e)}")

if __name__ == "__main__":
    app = SistemaCamaras()
    app.mainloop()