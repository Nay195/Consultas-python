import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os

class SistemaCamaras(tk.Tk):
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


class FrameLogin(tk.Frame):
    def __init__(self, master, login_callback):
        super().__init__(master)
        self.login_callback = login_callback

        self.contenedor = tk.Frame(self, bd=2, relief="groove", padx=40, pady=40)
        self.contenedor.place(relx=0.5, rely=0.5, anchor="center")

        self.label_titulo = tk.Label(self.contenedor, text="Iniciar Sesión", font=("Helvetica", 20, "bold"))
        self.label_titulo.pack(pady=(0, 20))

        tk.Label(self.contenedor, text="Usuario:", font=("Helvetica", 10)).pack(anchor="w")
        self.entry_usuario = tk.Entry(self.contenedor, width=30, font=("Helvetica", 12))
        self.entry_usuario.pack(pady=(0, 15))

        tk.Label(self.contenedor, text="Contraseña:", font=("Helvetica", 10)).pack(anchor="w")
        self.entry_password = tk.Entry(self.contenedor, show="*", width=30, font=("Helvetica", 12))
        self.entry_password.pack(pady=(0, 20))

        self.btn_login = tk.Button(self.contenedor, text="Acceder", command=self.intento_login, width=20, bg="#0052cc", fg="white", font=("Helvetica", 10, "bold"))
        self.btn_login.pack(pady=(10, 20))

        self.label_error = tk.Label(self.contenedor, text="", fg="red")
        self.label_error.pack()

    def intento_login(self):
        usr = self.entry_usuario.get()
        pwd = self.entry_password.get()
        exito, msg = self.login_callback(usr, pwd)
        if not exito:
            self.label_error.config(text=msg)


class FrameDashboard(tk.Frame):
    def __init__(self, master, df):
        super().__init__(master)
        self.df = df
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(self, width=250, bg="#e0e0e0", relief="sunken", bd=1)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        titulo_sidebar = tk.Label(self.sidebar, text="Consultas de Red", font=("Helvetica", 16, "bold"), bg="#e0e0e0")
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

        self.opcion_var = tk.StringVar(value="Seleccionar consulta...")
        
        self.menu_consultas = ttk.Combobox(
            self.sidebar, 
            textvariable=self.opcion_var, 
            values=list(self.consultas.keys()),
            state="readonly",
            width=28
        )
        self.menu_consultas.pack(pady=10, padx=10)
        self.menu_consultas.bind("<<ComboboxSelected>>", lambda event: self.ejecutar_consulta(self.opcion_var.get()))

        self.main_frame = tk.Frame(self, padx=20, pady=20)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        
        self.lbl_resultado = tk.Label(self.main_frame, text="Esperando consulta...", font=("Helvetica", 14))
        self.lbl_resultado.pack(pady=10)

        self.tree = ttk.Treeview(self.main_frame, show="headings")
        
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")

    def ejecutar_consulta(self, seleccion):
        self.lbl_resultado.config(text=f"Mostrando: {seleccion}")
        
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