
import streamlit as st
import random
import statistics as stats
import pandas as pd

# CONFIGURACION
st.set_page_config(
    page_title="Banco de Ropa",
    page_icon="👕",
    layout="wide"
)

JORNADA_S = 170 * 60
MEDIA_CLAS = 23.7
DESV_CLAS = 7.0
MIN_CLAS = 5.0
CAMBIO = (60, 300, 300)
LOTE = (14, 170)

RUTAS = {
    "Mal estado": (0.45, 1.19),
    "Producto B": (0.20, 1.38),
    "Frío": (0.219, 0.71),
    "Cálido": (0.131, 0.71)
}

R1 = 2.50


def una_jornada(rng):
    t = 0.0
    prendas = 0
    lotes = 0
    distancia = 0.0
    ocupado = 0.0

    categorias = {k: 0 for k in RUTAS}

    while t < JORNADA_S:

        if lotes > 0:
            cambio = rng.triangular(60, 300, 300)

            if t + cambio > JORNADA_S:
                break

            t += cambio
            distancia += 2 * R1

        lotes += 1
        tamano = rng.randint(*LOTE)
        lote_completo = True

        for _ in range(tamano):

            d = max(
                MIN_CLAS,
                rng.gauss(MEDIA_CLAS, DESV_CLAS)
            )

            if t + d > JORNADA_S:
                lote_completo = False
                break

            t += d
            ocupado += d
            prendas += 1

            u = rng.random()
            acum = 0.0

            for nombre, (prob, ruta) in RUTAS.items():
                acum += prob

                if u < acum:
                    categorias[nombre] += 1
                    distancia += 2 * ruta
                    break

        if not lote_completo:
            break

    return {
        "prendas": prendas,
        "lotes": lotes,
        "distancia": distancia,
        "utilizacion": ocupado / JORNADA_S,
        "categorias": categorias
    }


def ejecutar_simulacion(repeticiones, semilla):

    rng = random.Random(semilla)

    resultados = [
        una_jornada(rng)
        for _ in range(repeticiones)
    ]

    def intervalo(valores):
        media = stats.mean(valores)
        h = 1.96 * stats.stdev(valores) / (len(valores) ** 0.5)
        return media, media - h, media + h

    datos = {
        "prendas": intervalo([r["prendas"] for r in resultados]),
        "lotes": intervalo([r["lotes"] for r in resultados]),
        "distancia": intervalo([r["distancia"] for r in resultados]),
        "utilizacion": intervalo([r["utilizacion"] for r in resultados]),
        "por_hora": intervalo([
            r["prendas"] / (JORNADA_S / 3600)
            for r in resultados
        ])
    }

    categorias = {
        k: stats.mean([r["categorias"][k] for r in resultados])
        for k in RUTAS
    }

    return datos, categorias


# INTERFAZ
st.title("👕 SIMULACIÓN DEL BANCO DE ROPA")
st.subheader("Clasificación del proceso actual")

st.markdown("""
**Objetivo:** analizar el comportamiento del proceso de
clasificación de prendas durante una jornada de 170 minutos.
""")

st.divider()

# PARAMETROS
st.sidebar.header("Parámetros de simulación")

repeticiones = st.sidebar.slider(
    "Número de simulaciones",
    min_value=100,
    max_value=5000,
    value=1000,
    step=100
)

semilla = st.sidebar.number_input(
    "Semilla aleatoria",
    min_value=1,
    value=2026
)

st.sidebar.info("Duración de jornada: 170 minutos")

# EJECUCION
if st.button("▶ Ejecutar simulación", type="primary"):
    with st.spinner("Ejecutando simulaciones..."):
        datos, categorias = ejecutar_simulacion(
            repeticiones,
            int(semilla)
        )

        st.session_state["datos"] = datos
        st.session_state["categorias"] = categorias
        st.session_state["repeticiones"] = repeticiones

if "datos" not in st.session_state:
    with st.spinner("Preparando simulación..."):
        datos, categorias = ejecutar_simulacion(1000, 2026)
        st.session_state["datos"] = datos
        st.session_state["categorias"] = categorias
        st.session_state["repeticiones"] = 1000

datos = st.session_state["datos"]
categorias = st.session_state["categorias"]

st.success(
    f"Resultados de {st.session_state['repeticiones']} jornadas simuladas"
)

# INDICADORES
st.markdown("### Indicadores principales")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Prendas clasificadas",
    f"{datos['prendas'][0]:.1f}"
)

c2.metric(
    "Lotes procesados",
    f"{datos['lotes'][0]:.1f}"
)

c3.metric(
    "Distancia recorrida",
    f"{datos['distancia'][0]:.1f} m"
)

c4.metric(
    "Utilización del operario",
    f"{datos['utilizacion'][0]*100:.1f}%"
)

st.divider()

# PRODUCCION
st.markdown("### Rendimiento del proceso")

c5, c6 = st.columns(2)

c5.metric(
    "Productividad promedio",
    f"{datos['por_hora'][0]:.1f} prendas/hora"
)

c6.metric(
    "Tiempo de jornada",
    "170 minutos"
)

# GRAFICO DE CATEGORIAS
st.markdown("### Clasificación por categorías")

df = pd.DataFrame({
    "Categoría": list(categorias.keys()),
    "Prendas promedio": list(categorias.values())
})

st.bar_chart(
    df.set_index("Categoría"),
    y="Prendas promedio"
)

# TABLA DE RESULTADOS
st.markdown("### Resultados estadísticos")

tabla = pd.DataFrame({
    "Indicador": [
        "Prendas clasificadas",
        "Lotes procesados",
        "Distancia recorrida (m)",
        "Utilización (%)",
        "Productividad (prendas/hora)"
    ],
    "Promedio": [
        datos["prendas"][0],
        datos["lotes"][0],
        datos["distancia"][0],
        datos["utilizacion"][0] * 100,
        datos["por_hora"][0]
    ],
    "Límite inferior IC 95%": [
        datos["prendas"][1],
        datos["lotes"][1],
        datos["distancia"][1],
        datos["utilizacion"][1] * 100,
        datos["por_hora"][1]
    ],
    "Límite superior IC 95%": [
        datos["prendas"][2],
        datos["lotes"][2],
        datos["distancia"][2],
        datos["utilizacion"][2] * 100,
        datos["por_hora"][2]
    ]
})

st.dataframe(
    tabla.round(2),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.markdown("""
### Información del modelo

- Jornada simulada: 170 minutos.
- Tiempo de clasificación: distribución normal.
- Tamaño de lote: distribución uniforme discreta.
- Cambio de lote: distribución triangular.
- Número de repeticiones configurable.
- Resultados expresados como promedios e intervalos de confianza del 95%.

**Nota:** los resultados corresponden a una simulación del proceso
actual y no a mediciones reales de producción.
""")

st.caption("Proyecto académico | Banco de Ropa | Simulación de eventos discretos")
              
