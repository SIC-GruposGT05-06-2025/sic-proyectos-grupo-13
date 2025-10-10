# sic-proyectos-grupo-13

## 1) Planteamiento 
En Fórmula 1 existen numerosos datos (pilotos, equipos, circuitos, clima, *pit-stops*, etc.) dispersos en múltiples fuentes. 
Para un aficionado o comunicador deportivo es costoso integrar todo y comparar quién llega mejor a cada carrera. 
F1nal Gambler propone una plataforma que unifica datos históricos y recientes y los presenta como información clara y útil para decidir antes y durante cada GP.

## 2) Objetivos
**Objetivo general**
- Transformar datos dispersos de F1 en información comprensible que permita analizar y comparar rendimiento por piloto, equipo y circuito.

**Objetivos específicos**
- Integrar datasets históricos (carreras, resultados, pilotos y circuitos) y estandarizarlos para análisis.
- Proveer módulos prácticos: Panel Piloto, Comparador por Circuito, Duelo directo (H2H) y Previo del GP (señales).
- Reducir el tiempo de análisis con visualizaciones y tablas directas.

## 3) Herramientas utilizadas
| Componente | Herramienta | Uso principal |
|---|---|---|
| Lenguaje | Python | Lógica de análisis y scripts (consola y GUI) |
| Librerías | `pandas`, `numpy` | Limpieza, *merge*, agregaciones y estadísticas |
| Visualización | `matplotlib` | Gráficas (barras, histograma, series) y embebido en GUI |
| GUI | `tkinter` | Interfaz con pestañas (remontadores, circuitos, H2H) |
| Datos | CSV (`races`, `results`, `drivers`, `circuits`) | Fuente histórica para métricas y comparativas |


## 4) Breve explicación del resultado del proyecto
Se desarrolló un*prototipo funcional en dos modalidades:

- **Consola (`main.py`)**: menú de análisis con cuatro módulos
  1. *Mejores remontadores*: calcula posiciones ganadas promedio por piloto (ajustando `grid==0`→20) y muestra Top N con gráfico.
  2. *Circuitos con más carreras*: ranking histórico (conteo por circuito) con visualización.
  3. *Distribución de edades de pilotos*: histograma y estadísticos descriptivos.
  4. *Head‑to‑Head (H2H)*: comparación entre dos pilotos en carreras comunes (victorias H2H, promedios de posición, puntos, diferencia acumulada).

- **Interfaz gráfica (`interfaz.py`)**: las mismas capacidades en*pestañas, con formularios simples (filtros por año, Top N, selección de pilotos) y gráficas embebidas.
