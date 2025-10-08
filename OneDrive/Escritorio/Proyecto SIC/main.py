# Importar librerias
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

# ==============================
# MENÚ DE ANÁLISIS (1–4)
# ==============================

# ---- Utilidades de entrada con valores por defecto ----
def _ask_int(msg, default):
    txt = input(f"{msg} [Enter={default}]: ").strip()
    return default if txt == "" else int(txt)

def _ask_str(msg, default=None):
    txt = input(f"{msg}" + (f" [Enter={default}]" if default is not None else "") + ": ").strip()
    return default if (default is not None and txt == "") else txt

# ---- ANÁLISIS 1: Mejores remontadores ----
def analisis_1_remontadores(dfRaces, dfResults, dfDrivers):
    print("\n" + "="*80)
    print("ANÁLISIS 1: MEJORES REMONTADORES POR CARRERA")
    print("="*80)

    anio_min = _ask_int("Año mínimo a considerar", 2000)
    min_gp   = _ask_int("Mínimo de carreras por piloto", 50)
    topn     = _ask_int("Top N para la gráfica", 15)

    df_merged = pd.merge(dfResults, dfRaces[['raceId', 'year']], on='raceId', how='left')
    dfDrivers = dfDrivers.copy()
    dfDrivers['driver'] = dfDrivers['driverRef']
    df_merged = pd.merge(df_merged, dfDrivers[['driverId', 'driver']], on='driverId', how='left')

    df_merged['grid_ajustado'] = df_merged['grid'].replace(0, 20)
    df_merged['posiciones_ganadas'] = df_merged['grid_ajustado'] - df_merged['positionOrder']

    df_analisis = df_merged[df_merged['year'] >= anio_min].copy()
    driver_stats = df_analisis.groupby('driver').agg(
        total_carreras=('raceId', 'count'),
        promedio_puntos=('points', 'mean'),
        promedio_pos_ganadas=('posiciones_ganadas', 'mean')
    ).reset_index()

    driver_stats = driver_stats[driver_stats['total_carreras'] > min_gp]
    mejores = driver_stats.sort_values(by='promedio_pos_ganadas', ascending=False)

    print("\n--- Tabla 1: Top 10 Mejores Remontadores ---")
    print(mejores.head(10).to_string(index=False))

    top = mejores.head(topn)
    plt.figure(figsize=(12, 8))
    plt.barh(top['driver'][::-1], top['promedio_pos_ganadas'][::-1])
    plt.title(f'Top {len(top)} Pilotos por Promedio de Posiciones Ganadas (≥{anio_min})', fontsize=16)
    plt.xlabel('Promedio de Posiciones Ganadas/Perdidas por Carrera', fontsize=12)
    plt.ylabel('Piloto', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.axvline(0, linestyle='--')
    plt.tight_layout()
    plt.show()

# ---- ANÁLISIS 2: Circuitos con más carreras ----
def analisis_2_circuitos(dfRaces, dfCircuits):
    print("\n" + "="*80)
    print("ANÁLISIS 2: CIRCUITOS CON MÁS CARRERAS")
    print("="*80)

    topn = _ask_int("Top N de circuitos", 15)

    df_races_full = pd.merge(
        dfRaces, dfCircuits[['circuitId', 'name']],
        on='circuitId', how='left', suffixes=('', '_circuit')
    )
    conteo = df_races_full['name_circuit'].value_counts()
    top = conteo.head(topn)

    print(f"\n--- Tabla 2: Top {len(top)} Circuitos con Más Grandes Premios ---")
    print(top.to_string())

    plt.figure(figsize=(12, 8))
    plt.barh(top.index[::-1], top.values[::-1])
    plt.title(f'Top {len(top)} Circuitos con Más Carreras en la Historia de la F1', fontsize=16)
    plt.xlabel('Número de Grandes Premios', fontsize=12)
    plt.ylabel('Circuito', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# ---- ANÁLISIS 3: Distribución de edades de pilotos ----
def analisis_3_edades(dfDrivers):
    print("\n" + "="*80)
    print("ANÁLISIS 3: DISTRIBUCIÓN DE EDADES DE LOS PILOTOS")
    print("="*80)

    bins = _ask_int("Número de bins del histograma", 30)

    drivers = dfDrivers.copy()
    drivers['dob'] = pd.to_datetime(drivers['dob'], errors='coerce')
    drivers = drivers.dropna(subset=['dob'])
    drivers['age'] = ((datetime.now() - drivers['dob']).dt.days / 365.25).astype(int)

    print("\n--- Tabla 3: Resumen Estadístico de la Edad ---")
    print(drivers['age'].describe().to_string())

    plt.figure(figsize=(12, 7))
    plt.hist(drivers['age'], bins=bins, edgecolor='black')
    edad_promedio = drivers['age'].mean()
    plt.axvline(edad_promedio, linestyle='--', linewidth=2, label=f'Promedio: {edad_promedio:.1f} años')
    plt.title('Distribución de Edades de los Pilotos de F1', fontsize=16)
    plt.xlabel('Edad (años)', fontsize=12)
    plt.ylabel('Número de Pilotos', fontsize=12)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

# ---- H2H: helpers (reutiliza tu lógica) ----
def _resolver_piloto(dfDrivers, query):
    t = dfDrivers.copy()
    t['driverRefLower'] = t['driverRef'].astype(str).str.lower()
    t['codeLower']      = t['code'].astype(str).str.lower()
    t['nameLower']      = (t['forename'].astype(str) + " " + t['surname'].astype(str)).str.lower()
    t['surnameLower']   = t['surname'].astype(str).str.lower()

    q = str(query).strip().lower()
    cand = t[
        (t['driverRefLower'] == q) |
        (t['codeLower']      == q) |
        (t['nameLower']      == q) |
        (t['surnameLower']   == q)
    ]
    if cand.empty:
        cand = t[t['nameLower'].str.contains(q, na=False) | t['surnameLower'].str.contains(q, na=False)]
    if cand.empty:
        raise ValueError(f"No se encontró el piloto '{query}'. Intenta con driverRef, code o nombre completo.")
    row = cand.iloc[0]
    return int(row['driverId']), f"{row['forename']} {row['surname']}", row['driverRef']

def _catalogo_pilotos(dfDrivers, dfResults):
    starts = dfResults.groupby('driverId')['raceId'].nunique().reset_index(name='starts')
    cat = pd.merge(dfDrivers.copy(), starts, on='driverId', how='left')
    cat['starts'] = cat['starts'].fillna(0).astype(int)
    def fmt(row):
        code = (f" ({row['code']})" if pd.notna(row['code']) and str(row['code']).strip() != '' else '')
        return f"{row['driverRef']} — {row['forename']} {row['surname']}{code}"
    cat['display'] = cat.apply(fmt, axis=1)
    return cat.sort_values('starts', ascending=False)[['driverId','driverRef','forename','surname','code','starts','display']]

def _mostrar_lista_corta(cat, n=30):
    print("\n[H2H] Pilotos sugeridos (ordenados por nº de carreras):")
    for i, row in enumerate(cat.head(n).itertuples(), start=1):
        print(f"{i:>2}. {row.display} — {row.starts} GP")

def _elegir_dos_pilotos(cat, n=30):
    _mostrar_lista_corta(cat, n=n)
    raw = input("\n[H2H] Escribe dos índices de la lista o dos nombres/driverRef separados por coma\n"
                "Ejemplos: '1, 7'  ó  'alonso, hamilton'  ó  'VER, LEC'\n> ").strip()
    if ',' not in raw:
        raise ValueError("Por favor ingresa dos valores separados por coma.")
    A_tok, B_tok = [x.strip() for x in raw.split(',', 1)]
    def resolve_tok(tok):
        if tok.isdigit():
            idx = int(tok)
            if not (1 <= idx <= min(n, len(cat))):
                raise ValueError(f"Índice fuera de rango: {tok}")
            return cat.iloc[idx-1]['driverRef']
        return tok
    return resolve_tok(A_tok), resolve_tok(B_tok)

def h2h_report(dfResults, dfRaces, dfDrivers, piloto_A, piloto_B, anio_desde=None, anio_hasta=None):
    # Merge + filtros
    cols_races = ['raceId', 'year', 'round', 'name', 'date']
    df = pd.merge(dfResults, dfRaces[cols_races], on='raceId', how='left')
    if anio_desde is not None: df = df[df['year'] >= int(anio_desde)]
    if anio_hasta is not None: df = df[df['year'] <= int(anio_hasta)]

    A_id, A_name, A_ref = _resolver_piloto(dfDrivers, piloto_A)
    B_id, B_name, B_ref = _resolver_piloto(dfDrivers, piloto_B)
    df = df[df['driverId'].isin([A_id, B_id])].copy()
    if df.empty:
        print("No hay carreras para ese filtro de años.")
        return

    df['grid_ajustado'] = df['grid'].replace(0, 20)
    pv = df.pivot_table(
        index=['raceId', 'year', 'round', 'name', 'date'],
        columns='driverId',
        values=['positionOrder', 'grid_ajustado', 'points'],
        aggfunc='min'
    )
    try:
        pv = pv.dropna(subset=[('positionOrder', A_id), ('positionOrder', B_id)], how='any')
    except KeyError:
        print("No hay suficientes datos de resultados para comparar a ambos pilotos.")
        return
    if pv.empty:
        print("No hay carreras comunes con resultados válidos para ambos pilotos.")
        return

    posA = pv[('positionOrder', A_id)]
    posB = pv[('positionOrder', B_id)]
    gridA = pv[('grid_ajustado', A_id)]
    gridB = pv[('grid_ajustado', B_id)]
    ptsA  = pv[('points', A_id)].fillna(0)
    ptsB  = pv[('points', B_id)].fillna(0)

    winsA = (posA < posB).sum()
    winsB = (posB < posA).sum()
    ties  = (posA == posB).sum()
    n_gp  = len(pv)

    resumen = pd.DataFrame({
        'Piloto': [A_name, B_name],
        'Victorias H2H': [winsA, winsB],
        'Empates': [ties, ties],
        'Carreras juntos': [n_gp, n_gp],
        'Promedio Pos. Final': [posA.mean(), posB.mean()],
        'Mediana Pos. Final': [posA.median(), posB.median()],
        'Promedio Parrilla': [gridA.mean(), gridB.mean()],
        'Puntos Totales (H2H)': [ptsA.sum(), ptsB.sum()],
        'Mejor Resultado (mín)': [posA.min(), posB.min()]
    })

    print("\n--- Tabla 4: Resumen H2H ---")
    print(resumen.to_string(index=False))

    # Gráfica A
    plt.figure(figsize=(8, 5))
    plt.bar([A_ref, B_ref], [winsA, winsB])
    plt.title(f'H2H: {A_name} vs {B_name} — Victorias en carreras comunes')
    plt.xlabel('Piloto'); plt.ylabel('Carreras donde terminó por delante')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout(); plt.show()

    # Gráfica B
    pv2 = pv.reset_index().sort_values(['year', 'round'])
    step = np.where(pv2[('positionOrder', A_id)] < pv2[('positionOrder', B_id)], 1,
            np.where(pv2[('positionOrder', A_id)] > pv2[('positionOrder', B_id)], -1, 0))
    diff_acum = step.cumsum()
    etiquetas = pv2['year'].astype(str) + "-" + pv2['round'].astype(str)

    plt.figure(figsize=(12, 5))
    plt.plot(etiquetas, diff_acum, marker='o')
    plt.title(f'H2H: Diferencia acumulada ( {A_ref} – {B_ref} ) por carrera')
    plt.xlabel('Año-Round (sólo carreras comunes)'); plt.ylabel(f'Acumulado a favor de {A_ref}')
    plt.xticks(rotation=60, ha='right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout(); plt.show()

# ---- ANÁLISIS 4: Interfaz H2H ----
def analisis_4_h2h(dfResults, dfRaces, dfDrivers):
    print("\n" + "="*80)
    print("ANÁLISIS 4: HEAD-TO-HEAD (H2H)")
    print("="*80)
    cat = _catalogo_pilotos(dfDrivers, dfResults)
    try:
        _mostrar_lista_corta(cat, n=30)
        raw = _ask_str("\nEscribe dos índices o dos nombres/driverRef separados por coma (ej. '1,7' o 'alonso, hamilton')", None)
        if ',' not in raw:
            raise ValueError("Debes ingresar dos valores separados por coma.")
        A_tok, B_tok = [x.strip() for x in raw.split(',', 1)]
        # Resolver tokens
        def _resolve(tok):
            if tok.isdigit():
                idx = int(tok)
                if not (1 <= idx <= min(30, len(cat))):
                    raise ValueError(f"Índice fuera de rango: {tok}")
                return cat.iloc[idx-1]['driverRef']
            return tok
        A_sel, B_sel = _resolve(A_tok), _resolve(B_tok)
        y_from = _ask_str("Año desde (Enter=todos)", None)
        y_to   = _ask_str("Año hasta (Enter=todos)", None)
        h2h_report(dfResults, dfRaces, dfDrivers, A_sel, B_sel, y_from or None, y_to or None)
    except Exception as e:
        print(f"[H2H] Aviso: {e}")

# ---- MENÚ PRINCIPAL ----
def menu_principal():
    while True:
        print("\n" + "="*80)
        print("MENÚ DE ANÁLISIS — F1nal Gambling")
        print("="*80)
        print("1) Mejores remontadores")
        print("2) Circuitos con más carreras")
        print("3) Distribución de edades de pilotos")
        print("4) Head-to-Head (H2H) entre pilotos")
        print("0) Salir")
        op = input("> Elige una opción: ").strip()

        if op == '1':
            analisis_1_remontadores(dfRaces, dfResults, dfDrivers)
        elif op == '2':
            analisis_2_circuitos(dfRaces, dfCircuits)
        elif op == '3':
            analisis_3_edades(dfDrivers)
        elif op == '4':
            analisis_4_h2h(dfResults, dfRaces, dfDrivers)
        elif op == '0':
            print("¡Hasta la próxima! 🏁")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

# Ejecutar menú
if __name__ == "__main__":
    menu_principal()

