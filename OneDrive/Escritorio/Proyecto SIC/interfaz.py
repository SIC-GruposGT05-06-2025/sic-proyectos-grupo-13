# ==============================
# INTERFAZ GRÁFICA CON TKINTER
# ==============================
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

try:
    # Rutas de los archivos CSV 
    urlRaces = "./Data/races.csv"
    urlResults = "./Data/results.csv"
    urlDrivers = "./Data/drivers.csv"
    urlCircuits = "./Data/circuits.csv" 

    # Lectura de todos los archivos necesarios
    dfRaces = pd.read_csv(urlRaces)
    dfResults = pd.read_csv(urlResults)
    dfDrivers = pd.read_csv(urlDrivers)
    dfCircuits = pd.read_csv(urlCircuits)
    
    print("Todos los archivos de datos fueron cargados exitosamente.")

except FileNotFoundError as e:
    print(f"Error: No se encontró el archivo {e.filename}. Asegúrate de que las rutas son correctas.")
    exit()

# --- utilidades de tabla y gráficos ---
def df_to_treeview(tree: ttk.Treeview, df: pd.DataFrame, max_rows: int = 200):
    # limpiar
    for c in tree.get_children():
        tree.delete(c)
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"
    # configurar columnas
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")
    # insertar filas (limitado)
    for _, row in df.head(max_rows).iterrows():
        tree.insert("", "end", values=list(row.values))

def draw_figure(container: tk.Widget, fig: Figure, attr_name: str):
    # elimina canvas anterior si existe
    old = getattr(container, attr_name, None)
    if old:
        old.get_tk_widget().destroy()
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(fill="both", expand=True)
    setattr(container, attr_name, canvas)

# ---- helpers H2H (reuso de tu lógica) ----
def _resolver_piloto_gui(dfDrivers, query):
    t = dfDrivers.copy()
    t["driverRefLower"] = t["driverRef"].astype(str).str.lower()
    t["codeLower"]      = t["code"].astype(str).str.lower()
    t["nameLower"]      = (t["forename"].astype(str) + " " + t["surname"].astype(str)).str.lower()
    t["surnameLower"]   = t["surname"].astype(str).str.lower()
    q = str(query).strip().lower()
    cand = t[
        (t["driverRefLower"] == q) | (t["codeLower"] == q) |
        (t["nameLower"] == q) | (t["surnameLower"] == q)
    ]
    if cand.empty:
        cand = t[t["nameLower"].str.contains(q, na=False) | t["surnameLower"].str.contains(q, na=False)]
    if cand.empty:
        raise ValueError(f"No se encontró el piloto '{query}'. Usa driverRef, código o nombre.")
    row = cand.iloc[0]
    return int(row["driverId"]), f"{row['forename']} {row['surname']}", row["driverRef"]

def _catalogo_pilotos_gui(dfDrivers, dfResults):
    starts = dfResults.groupby("driverId")["raceId"].nunique().reset_index(name="starts")
    cat = pd.merge(dfDrivers.copy(), starts, on="driverId", how="left")
    cat["starts"] = cat["starts"].fillna(0).astype(int)
    def fmt(r):
        code = f" ({r['code']})" if pd.notna(r["code"]) and str(r["code"]).strip() != "" else ""
        return f"{r['driverRef']} — {r['forename']} {r['surname']}{code}"
    cat["display"] = cat.apply(fmt, axis=1)
    return cat.sort_values("starts", ascending=False)[["driverId","driverRef","forename","surname","code","starts","display"]]

class F1AnalyzerApp(tk.Tk):
    def __init__(self, dfRaces, dfResults, dfDrivers, dfCircuits):
        super().__init__()
        self.title("F1nal Gambling")
        self.geometry("1100x780")

        # datos
        self.dfRaces = dfRaces
        self.dfResults = dfResults
        self.dfDrivers = dfDrivers
        self.dfCircuits = dfCircuits

        # catálogo pilotos para H2H
        self.cat = _catalogo_pilotos_gui(dfDrivers, dfResults)

        self._build_ui()

    # ------------- UI -------------
    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Tabs
        self.tab_remont = ttk.Frame(notebook)
        self.tab_cir    = ttk.Frame(notebook)
        self.tab_age    = ttk.Frame(notebook)
        self.tab_h2h    = ttk.Frame(notebook)

        notebook.add(self.tab_remont, text="Remontadores")
        notebook.add(self.tab_cir,    text="Circuitos")
        notebook.add(self.tab_age,    text="Edades")
        notebook.add(self.tab_h2h,    text="H2H")

        self._tab_remontadores()
        self._tab_circuitos()
        self._tab_edades()
        self._tab_h2h()

    # ---- TAB 1: Remontadores ----
    def _tab_remontadores(self):
        top = ttk.Frame(self.tab_remont, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Año mínimo:").grid(row=0, column=0, sticky="w")
        self.r_anio = tk.IntVar(value=2000)
        ttk.Spinbox(top, from_=1950, to=2100, textvariable=self.r_anio, width=8).grid(row=0, column=1, padx=6)

        ttk.Label(top, text="Mín GP/piloto:").grid(row=0, column=2, sticky="w")
        self.r_min_gp = tk.IntVar(value=50)
        ttk.Spinbox(top, from_=0, to=500, textvariable=self.r_min_gp, width=8).grid(row=0, column=3, padx=6)

        ttk.Label(top, text="Top N:").grid(row=0, column=4, sticky="w")
        self.r_topn = tk.IntVar(value=15)
        ttk.Spinbox(top, from_=1, to=100, textvariable=self.r_topn, width=8).grid(row=0, column=5, padx=6)

        ttk.Button(top, text="Generar", command=self.run_remontadores).grid(row=0, column=6, padx=12)

        mid = ttk.Frame(self.tab_remont, padding=8)
        mid.pack(fill="both", expand=True)
        # tabla
        self.tree_remon = ttk.Treeview(mid, height=12)
        self.tree_remon.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(mid, orient="vertical", command=self.tree_remon.yview).pack(side="left", fill="y")
        self.tree_remon.configure(yscrollcommand=lambda *args: None)

        # gráfico
        self.plot_remon = ttk.LabelFrame(self.tab_remont, text="Gráfico")
        self.plot_remon.pack(fill="both", expand=True, padx=8, pady=8)

    def run_remontadores(self):
        try:
            anio_min = int(self.r_anio.get())
            min_gp   = int(self.r_min_gp.get())
            topn     = int(self.r_topn.get())

            df_merged = pd.merge(self.dfResults, self.dfRaces[["raceId","year"]], on="raceId", how="left")
            dfd = self.dfDrivers.copy()
            dfd["driver"] = dfd["driverRef"]
            df_merged = pd.merge(df_merged, dfd[["driverId","driver"]], on="driverId", how="left")
            df_merged["grid_ajustado"] = df_merged["grid"].replace(0, 20)
            df_merged["posiciones_ganadas"] = df_merged["grid_ajustado"] - df_merged["positionOrder"]

            df_analisis = df_merged[df_merged["year"] >= anio_min].copy()
            driver_stats = df_analisis.groupby("driver").agg(
                total_carreras=("raceId", "count"),
                promedio_puntos=("points", "mean"),
                promedio_pos_ganadas=("posiciones_ganadas", "mean")
            ).reset_index()
            driver_stats = driver_stats[driver_stats["total_carreras"] > min_gp]
            mejores = driver_stats.sort_values(by="promedio_pos_ganadas", ascending=False)
            df_to_treeview(self.tree_remon, mejores.head(10))

            top = mejores.head(topn)
            fig = Figure(figsize=(7.5, 4.5), dpi=100)
            ax = fig.add_subplot(111)
            ax.barh(list(top["driver"])[::-1], list(top["promedio_pos_ganadas"])[::-1])
            ax.set_title(f"Top {len(top)} — Promedio de posiciones ganadas (≥{anio_min})")
            ax.set_xlabel("Promedio posiciones ganadas/perdidas")
            ax.set_ylabel("Piloto")
            ax.grid(axis="x", linestyle="--", alpha=0.7)
            ax.axvline(0, linestyle="--")
            fig.tight_layout()
            draw_figure(self.plot_remon, fig, "_canvas")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- TAB 2: Circuitos ----
    def _tab_circuitos(self):
        top = ttk.Frame(self.tab_cir, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Top N circuitos:").grid(row=0, column=0, sticky="w")
        self.c_topn = tk.IntVar(value=15)
        ttk.Spinbox(top, from_=1, to=100, textvariable=self.c_topn, width=8).grid(row=0, column=1, padx=6)
        ttk.Button(top, text="Generar", command=self.run_circuitos).grid(row=0, column=2, padx=12)

        mid = ttk.Frame(self.tab_cir, padding=8)
        mid.pack(fill="both", expand=True)
        self.tree_cir = ttk.Treeview(mid, height=12)
        self.tree_cir.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(mid, orient="vertical", command=self.tree_cir.yview).pack(side="left", fill="y")

        self.plot_cir = ttk.LabelFrame(self.tab_cir, text="Gráfico")
        self.plot_cir.pack(fill="both", expand=True, padx=8, pady=8)

    def run_circuitos(self):
        try:
            topn = int(self.c_topn.get())
            df_full = pd.merge(self.dfRaces, self.dfCircuits[["circuitId","name"]],
                               on="circuitId", how="left", suffixes=("", "_circuit"))
            conteo = df_full["name_circuit"].value_counts()
            top = conteo.head(topn)
            # tabla como DataFrame
            df_table = top.reset_index()
            df_table.columns = ["Circuito", "Grandes Premios"]
            df_to_treeview(self.tree_cir, df_table)

            fig = Figure(figsize=(7.5, 4.5), dpi=100)
            ax = fig.add_subplot(111)
            ax.barh(list(top.index)[::-1], list(top.values)[::-1])
            ax.set_title(f"Top {len(top)} circuitos con más carreras")
            ax.set_xlabel("Número de Grandes Premios")
            ax.set_ylabel("Circuito")
            ax.grid(axis="x", linestyle="--", alpha=0.6)
            fig.tight_layout()
            draw_figure(self.plot_cir, fig, "_canvas")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- TAB 3: Edades ----
    def _tab_edades(self):
        top = ttk.Frame(self.tab_age, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Bins del histograma:").grid(row=0, column=0, sticky="w")
        self.e_bins = tk.IntVar(value=30)
        ttk.Spinbox(top, from_=5, to=100, textvariable=self.e_bins, width=8).grid(row=0, column=1, padx=6)
        ttk.Button(top, text="Generar", command=self.run_edades).grid(row=0, column=2, padx=12)

        mid = ttk.Frame(self.tab_age, padding=8)
        mid.pack(fill="both", expand=True)
        self.tree_age = ttk.Treeview(mid, height=10)
        self.tree_age.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(mid, orient="vertical", command=self.tree_age.yview).pack(side="left", fill="y")

        self.plot_age = ttk.LabelFrame(self.tab_age, text="Gráfico")
        self.plot_age.pack(fill="both", expand=True, padx=8, pady=8)

    def run_edades(self):
        try:
            bins = int(self.e_bins.get())
            drivers = self.dfDrivers.copy()
            drivers["dob"] = pd.to_datetime(drivers["dob"], errors="coerce")
            drivers = drivers.dropna(subset=["dob"])
            drivers["age"] = ((datetime.now() - drivers["dob"]).dt.days / 365.25).astype(int)

            # resumen
            desc = drivers["age"].describe().to_frame().T
            df_to_treeview(self.tree_age, desc)

            fig = Figure(figsize=(7.5, 4.5), dpi=100)
            ax = fig.add_subplot(111)
            ax.hist(list(drivers["age"]), bins=bins)
            mean_age = drivers["age"].mean()
            ax.axvline(mean_age, linestyle="--", linewidth=2, label=f"Promedio: {mean_age:.1f}")
            ax.legend()
            ax.set_title("Distribución de edades de pilotos")
            ax.set_xlabel("Edad (años)")
            ax.set_ylabel("Número de pilotos")
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            fig.tight_layout()
            draw_figure(self.plot_age, fig, "_canvas")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- TAB 4: H2H ----
    def _tab_h2h(self):
        top = ttk.Frame(self.tab_h2h, padding=8)
        top.pack(fill="x")

        # Top 30
        ttk.Label(top, text="Top 30 por nº de carreras (doble clic para asignar A/B):").grid(row=0, column=0, columnspan=2, sticky="w")
        self.lb_top = tk.Listbox(top, height=8, exportselection=False)
        self.lb_top.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=4)
        for _, r in self.cat.head(30).iterrows():
            self.lb_top.insert("end", f"{r['display']} — {r['starts']} GP")
        # eventos doble clic
        self.assign_next = "A"
        self.lb_top.bind("<Double-Button-1>", self._assign_from_list)

        # Selectores
        ttk.Label(top, text="Piloto A:").grid(row=2, column=0, sticky="w", pady=(8,0))
        ttk.Label(top, text="Piloto B:").grid(row=2, column=1, sticky="w", pady=(8,0))
        all_values = list(self.cat["display"])
        self.cb_A = ttk.Combobox(top, values=all_values, width=45)
        self.cb_B = ttk.Combobox(top, values=all_values, width=45)
        self.cb_A.grid(row=3, column=0, padx=4, pady=2, sticky="ew")
        self.cb_B.grid(row=3, column=1, padx=4, pady=2, sticky="ew")

        ttk.Label(top, text="Año desde:").grid(row=4, column=0, sticky="w", pady=(6,0))
        ttk.Label(top, text="Año hasta:").grid(row=4, column=1, sticky="w", pady=(6,0))
        self.h_from = ttk.Entry(top, width=10)
        self.h_to   = ttk.Entry(top, width=10)
        self.h_from.grid(row=5, column=0, sticky="w", padx=4)
        self.h_to.grid(row=5, column=1, sticky="w", padx=4)

        ttk.Button(top, text="Comparar H2H", command=self.run_h2h).grid(row=6, column=0, columnspan=2, pady=8)

        # Resumen
        mid = ttk.Frame(self.tab_h2h, padding=8)
        mid.pack(fill="both", expand=True)
        self.tree_h2h = ttk.Treeview(mid, height=6)
        self.tree_h2h.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(mid, orient="vertical", command=self.tree_h2h.yview).pack(side="left", fill="y")

        # Gráficos
        self.plot_h2h_1 = ttk.LabelFrame(self.tab_h2h, text="Victorias H2H")
        self.plot_h2h_1.pack(fill="both", expand=True, padx=8, pady=4)
        self.plot_h2h_2 = ttk.LabelFrame(self.tab_h2h, text="Diferencia acumulada")
        self.plot_h2h_2.pack(fill="both", expand=True, padx=8, pady=4)

    def _assign_from_list(self, event):
        # asigna por turno A y luego B
        idx = self.lb_top.curselection()
        if not idx:
            return
        display = self.lb_top.get(idx[0]).split(" — ")[0]  # cortar " — XX GP"
        # display está como "driverRef — Forename Surname (code?)"
        # para combobox guardamos exactamente la coincidencia de self.cat["display"]
        # buscamos por empieza-con
        matches = [v for v in self.cat["display"] if display in v]
        if not matches:
            return
        if self.assign_next == "A":
            self.cb_A.set(matches[0])
            self.assign_next = "B"
        else:
            self.cb_B.set(matches[0])
            self.assign_next = "A"

    def run_h2h(self):
        try:
            # tomar driverRef del texto seleccionado (lo primero antes de " — ")
            def extract_ref(val):
                if not val or val.strip() == "":
                    return ""
                return val.split(" — ")[0].strip()

            A_tok = extract_ref(self.cb_A.get())
            B_tok = extract_ref(self.cb_B.get())
            if not A_tok or not B_tok:
                messagebox.showwarning("Atención", "Selecciona ambos pilotos (A y B).")
                return

            y_from = self.h_from.get().strip() or None
            y_to   = self.h_to.get().strip() or None

            # --- cálculo H2H ---
            cols_races = ["raceId","year","round","name","date"]
            df = pd.merge(self.dfResults, self.dfRaces[cols_races], on="raceId", how="left")
            if y_from: df = df[df["year"] >= int(y_from)]
            if y_to:   df = df[df["year"] <= int(y_to)]

            A_id, A_name, A_ref = _resolver_piloto_gui(self.dfDrivers, A_tok)
            B_id, B_name, B_ref = _resolver_piloto_gui(self.dfDrivers, B_tok)

            df = df[df["driverId"].isin([A_id, B_id])].copy()
            if df.empty:
                messagebox.showinfo("Sin datos", "No hay carreras para ese filtro.")
                return

            df["grid_ajustado"] = df["grid"].replace(0, 20)
            pv = df.pivot_table(
                index=["raceId","year","round","name","date"],
                columns="driverId",
                values=["positionOrder","grid_ajustado","points"],
                aggfunc="min"
            )
            try:
                pv = pv.dropna(subset=[("positionOrder", A_id), ("positionOrder", B_id)], how="any")
            except KeyError:
                messagebox.showinfo("Sin datos", "Faltan resultados para comparar.")
                return
            if pv.empty:
                messagebox.showinfo("Sin datos", "No hay carreras comunes con resultados válidos.")
                return

            posA = pv[("positionOrder", A_id)]
            posB = pv[("positionOrder", B_id)]
            gridA = pv[("grid_ajustado", A_id)]
            gridB = pv[("grid_ajustado", B_id)]
            ptsA  = pv[("points", A_id)].fillna(0)
            ptsB  = pv[("points", B_id)].fillna(0)

            winsA = int((posA < posB).sum())
            winsB = int((posB < posA).sum())
            ties  = int((posA == posB).sum())
            n_gp  = len(pv)

            resumen = pd.DataFrame({
                "Piloto": [A_name, B_name],
                "Victorias H2H": [winsA, winsB],
                "Empates": [ties, ties],
                "Carreras juntos": [n_gp, n_gp],
                "Promedio Pos. Final": [posA.mean(), posB.mean()],
                "Mediana Pos. Final": [posA.median(), posB.median()],
                "Promedio Parrilla": [gridA.mean(), gridB.mean()],
                "Puntos Totales (H2H)": [ptsA.sum(), ptsB.sum()],
                "Mejor Resultado (mín)": [posA.min(), posB.min()]
            })
            df_to_treeview(self.tree_h2h, resumen)

            # gráfico 1: victorias
            fig1 = Figure(figsize=(7.5, 3.8), dpi=100)
            ax1 = fig1.add_subplot(111)
            ax1.bar([A_ref, B_ref], [winsA, winsB])
            ax1.set_title(f"H2H: {A_name} vs {B_name} — Victorias")
            ax1.set_xlabel("Piloto")
            ax1.set_ylabel("Carreras donde terminó por delante")
            ax1.grid(axis="y", linestyle="--", alpha=0.6)
            fig1.tight_layout()
            draw_figure(self.plot_h2h_1, fig1, "_canvas")

            # gráfico 2: diferencia acumulada
            pv2 = pv.reset_index().sort_values(["year","round"])
            step = np.where(pv2[("positionOrder", A_id)] < pv2[("positionOrder", B_id)], 1,
                    np.where(pv2[("positionOrder", A_id)] > pv2[("positionOrder", B_id)], -1, 0))
            diff_acum = step.cumsum()
            etiquetas = pv2["year"].astype(str) + "-" + pv2["round"].astype(str)

            fig2 = Figure(figsize=(7.5, 3.8), dpi=100)
            ax2 = fig2.add_subplot(111)
            ax2.plot(list(etiquetas), list(diff_acum), marker="o")
            ax2.set_title(f"Diferencia acumulada ({A_ref} – {B_ref})")
            ax2.set_xlabel("Año-Round (sólo carreras comunes)")
            ax2.set_ylabel(f"Acumulado a favor de {A_ref}")
            for label in ax2.get_xticklabels():
                label.set_rotation(60)
                label.set_ha("right")
            ax2.grid(True, linestyle="--", alpha=0.6)
            fig2.tight_layout()
            draw_figure(self.plot_h2h_2, fig2, "_canvas")

        except Exception as e:
            messagebox.showerror("Error", str(e))

# ---- Lanzar GUI si se ejecuta como script principal ----
if __name__ == "__main__":
    try:
        app = F1AnalyzerApp(dfRaces, dfResults, dfDrivers, dfCircuits)
        app.mainloop()
    except Exception as err:
        print("Error al iniciar la interfaz:", err)
