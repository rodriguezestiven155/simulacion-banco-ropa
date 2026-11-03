import streamlit as st
import random
import statistics as stats
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# CONFIGURACION
# ==========================================

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
R1 = 2.50

RUTAS = {
    "Mal estado": (0.45, 1.19),
    "Producto B": (0.20, 1.38),
    "Frío": (0.219, 0.71),
    "Cálido": (0.131, 0.71)
}

# Posiciones visuales de las zonas
POSICIONES = {
    "Mal estado": (1.7, 8.0),
    "Producto B": (8.3, 8.0),
    "Frío": (1.7, 2.0),
    "Cálido": (8.3, 2.0)
}

CENTRO = (5.0, 5.0)


# ==========================================
# SIMULACION DE UNA JORNADA
# ==========================================

def una_jornada(rng, guardar_eventos=False):

    t = 0.0
    prendas = 0
    lotes = 0
    distancia = 0.0
    ocupado = 0.0

    categorias = {k: 0 for k in RUTAS}
    eventos = []

    while t < JORNADA_S:

        # Cambio de lote
        if lotes > 0:

            cambio = rng.triangular(60, 300, 300)

            if t + cambio > JORNADA_S:
                break

            t += cambio
            distancia += 2 * R1

            if guardar_eventos:
                eventos.append({
                    "tipo": "cambio",
                    "tiempo": t,
                    "prendas": prendas,
                    "lotes": lotes,
                    "distancia": distancia
                })

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

            # Seleccion de categoria
            u = rng.random()
            acum = 0.0
            categoria = "Cálido"
            ruta = RUTAS["Cálido"][1]

            for nombre, (prob, distancia_ruta) in RUTAS.items():

                acum += prob

                if u < acum:
                    categoria = nombre
                    ruta = distancia_ruta
                    break

            categorias[categoria] += 1

            # Desplazamiento de ida y regreso
            distancia += 2 * ruta

            if guardar_eventos:
                eventos.append({
                    "tipo": "prenda",
                    "categoria": categoria,
                    "tiempo": t,
                    "prendas": prendas,
                    "lotes": lotes,
                    "distancia": distancia
                })

        if not lote_completo:
            break

    resultado = {
        "prendas": prendas,
        "lotes": lotes,
        "distancia": distancia,
        "utilizacion": ocupado / JORNADA_S,
        "categorias": categorias
    }

    if guardar_eventos:
        resultado["eventos"] = eventos

    return resultado


# ==========================================
# SIMULACIONES REPETIDAS
# ==========================================

def ejecutar_simulacion(repeticiones, semilla):

    rng = random.Random(semilla)

    resultados = [
        una_jornada(rng)
        for _ in range(repeticiones)
    ]

    def intervalo(valores):

        media = stats.mean(valores)

        h = (
            1.96 * stats.stdev(valores)
            / (len(valores) ** 0.5)
        )

        return media, media - h, media + h

    datos = {
        "prendas": intervalo(
            [r["prendas"] for r in resultados]
        ),
        "lotes": intervalo(
            [r["lotes"] for r in resultados]
        ),
        "distancia": intervalo(
            [r["distancia"] for r in resultados]
        ),
        "utilizacion": intervalo(
            [r["utilizacion"] for r in resultados]
        ),
        "por_hora": intervalo([
            r["prendas"] / (JORNADA_S / 3600)
            for r in resultados
        ])
    }

    categorias = {
        k: stats.mean([
            r["categorias"][k]
            for r in resultados
        ])
        for k in RUTAS
    }

    return datos, categorias


# ==========================================
# ANIMACION DEL PROCESO
# ==========================================

def crear_animacion(eventos):

    colores = {
        "Mal estado": "#E57373",
        "Producto B": "#7986CB",
        "Frío": "#4FC3F7",
        "Cálido": "#FFB74D"
    }

    nombres = list(POSICIONES.keys())

    x_zonas = [POSICIONES[n][0] for n in nombres]
    y_zonas = [POSICIONES[n][1] for n in nombres]

    etiquetas = [
        "MAL ESTADO",
        "PRODUCTO B",
        "FRÍO",
        "CÁLIDO"
    ]

    colores_zonas = [colores[n] for n in nombres]

    # Trazas estaticas
    fig = go.Figure()

    # Zonas de clasificacion
    fig.add_trace(go.Scatter(
        x=x_zonas,
        y=y_zonas,
        mode="markers+text",
        text=etiquetas,
        textposition="middle center",
        marker=dict(
            size=65,
            color=colores_zonas,
            symbol="square",
            opacity=0.65,
            line=dict(color="white", width=3)
        ),
        hoverinfo="text",
        name="Destinos"
    ))

    # Rutas de desplazamiento
    x_rutas = []
    y_rutas = []

    for nombre in nombres:
        x, y = POSICIONES[nombre]

        x_rutas.extend([CENTRO[0], x, None])
        y_rutas.extend([CENTRO[1], y, None])

    fig.add_trace(go.Scatter(
        x=x_rutas,
        y=y_rutas,
        mode="lines",
        line=dict(
            color="gray",
            width=2,
            dash="dot"
        ),
        hoverinfo="skip",
        name="Recorridos"
    ))

    # Puesto de clasificacion
    fig.add_trace(go.Scatter(
        x=[CENTRO[0]],
        y=[CENTRO[1]],
        mode="markers+text",
        text=["PUESTO DE CLASIFICACIÓN"],
        textposition="bottom center",
        marker=dict(
            size=45,
            color="#455A64",
            symbol="square"
        ),
        name="Puesto"
    ))

    # Operario animado
    fig.add_trace(go.Scatter(
        x=[CENTRO[0]],
        y=[CENTRO[1]],
        mode="markers+text",
        text=["🧍 OPERARIO"],
        textposition="top center",
        marker=dict(
            size=24,
            color="#263238",
            symbol="circle"
        ),
        name="Operario"
    ))

    # Prenda animada
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            size=19,
            color="#F9A825",
            symbol="circle",
            line=dict(color="black", width=1)
        ),
        name="Prenda"
    ))

    frames = []

    for i, evento in enumerate(eventos):

        if evento["tipo"] == "prenda":

            destino = POSICIONES[evento["categoria"]]
            descripcion = evento["categoria"]
            texto = f"Clasificando: {descripcion}"

        else:

            destino = (5.0, 9.0)
            descripcion = "Cambio de lote"
            texto = "Desplazamiento para cambio de lote"

        minuto = evento["tiempo"] / 60

        titulo = (
            f"Minuto {minuto:.1f} de 170"
            f" | Prendas: {evento['prendas']}"
            f" | Lotes: {evento['lotes']}"
            f" | {texto}"
        )

        # Movimiento hacia el destino
        frames.append(go.Frame(
            name=f"frame_{i}_ida",
            data=[
                go.Scatter(
                    x=[destino[0]],
                    y=[destino[1]],
                    text=["🧍 OPERARIO"],
                    mode="markers+text"
                ),
                go.Scatter(
                    x=(
                        [destino[0]]
                        if evento["tipo"] == "prenda"
                        else [None]
                    ),
                    y=(
                        [destino[1]]
                        if evento["tipo"] == "prenda"
                        else [None]
                    ),
                    mode="markers"
                )
            ],
            traces=[3, 4],
            layout=go.Layout(title_text=titulo)
        ))

        # Regreso al puesto
        frames.append(go.Frame(
            name=f"frame_{i}_vuelta",
            data=[
                go.Scatter(
                    x=[CENTRO[0]],
                    y=[CENTRO[1]],
                    text=["🧍 OPERARIO"],
                    mode="markers+text"
                ),
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers"
                )
            ],
            traces=[3, 4],
            layout=go.Layout(
                title_text=(
                    f"Minuto {minuto:.1f} de 170"
                    f" | Prendas: {evento['prendas']}"
                    f" | Lotes: {evento['lotes']}"
                    " | Regreso al puesto"
                )
            )
        ))

    fig.frames = frames

    # Apariencia del plano
    fig.update_layout(
        title="SIMULACIÓN ANIMADA DEL BANCO DE ROPA",
        height=620,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="white",
        xaxis=dict(
            range=[0, 10],
            visible=False,
            fixedrange=True
        ),
        yaxis=dict(
            range=[0, 10],
            visible=False,
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        legend=dict(
            orientation="h",
            y=-0.08
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.05,
                y=1.12,
                buttons=[
                    dict(
                        label="▶ Reproducir",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {
                                    "duration": 180,
                                    "redraw": True
                                },
                                "fromcurrent": True,
                                "transition": {
                                    "duration": 150
                                }
                            }
                        ]
                    ),
                    dict(
                        label="⏸ Pausar",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": False
                                },
                                "mode": "immediate",
                                "transition": {
                                    "duration": 0
                                }
                            }
                        ]
                    )
                ]
            )
        ]
    )

    # Area de cambio de lote
    fig.add_shape(
        type="rect",
        x0=4.1,
        x1=5.9,
        y0=8.7,
        y1=9.5,
        line=dict(color="#78909C", width=2),
        fillcolor="#CFD8DC",
        opacity=0.8
    )

    fig.add_annotation(
        x=5,
        y=9.6,
        text="ÁREA DE CAMBIO DE LOTE",
        showarrow=False,
        font=dict(size=10)
    )

    return fig


# ==========================================
# INTERFAZ
# ==========================================

st.title("👕 SIMULACIÓN DEL BANCO DE ROPA")

st.subheader("Proceso actual de clasificación")

st.markdown("""
Esta aplicación representa el proceso de clasificación de prendas
durante una jornada de 170 minutos, mediante una simulación
de eventos discretos.
""")

st.divider()

# Parametros
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


# Primera ejecucion
if "datos" not in st.session_state:

    datos, categorias = ejecutar_simulacion(1000, 2026)

    muestra = una_jornada(
        random.Random(2026),
        guardar_eventos=True
    )

    st.session_state["datos"] = datos
    st.session_state["categorias"] = categorias
    st.session_state["muestra"] = muestra
    st.session_state["repeticiones"] = 1000


# Boton de ejecucion
if st.button("🔄 Ejecutar nueva simulación", type="primary"):

    with st.spinner("Ejecutando simulaciones..."):

        datos, categorias = ejecutar_simulacion(
            repeticiones,
            int(semilla)
        )

        muestra = una_jornada(
            random.Random(int(semilla)),
            guardar_eventos=True
        )

        st.session_state["datos"] = datos
        st.session_state["categorias"] = categorias
        st.session_state["muestra"] = muestra
        st.session_state["repeticiones"] = repeticiones


datos = st.session_state["datos"]
categorias = st.session_state["categorias"]
muestra = st.session_state["muestra"]


# ==========================================
# ANIMACION
# ==========================================

st.markdown("## 🎬 Simulación gráfica del proceso")

st.info(
    "Pulsa el botón ▶ Reproducir dentro del plano para observar "
    "los desplazamientos del operario."
)

st.caption(
    f"La animación representa una jornada de ejemplo con "
    f"{muestra['prendas']} prendas clasificadas y "
    f"{muestra['lotes']} lotes procesados."
)

if muestra["eventos"]:

    figura = crear_animacion(muestra["eventos"])

    st.plotly_chart(
        figura,
        use_container_width=True
    )

else:

    st.warning("No se generaron eventos para mostrar.")


st.caption(
    "Nota: los desplazamientos se representan visualmente. "
    "El modelo original contabiliza las distancias, pero no "
    "agrega tiempo de traslado al tiempo de clasificación."
)

st.divider()


# ==========================================
# INDICADORES
# ==========================================

st.markdown("## 📊 Resultados de las jornadas simuladas")

st.success(
    f"Resultados de {st.session_state['repeticiones']} jornadas"
)

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


# ==========================================
# PRODUCTIVIDAD
# ==========================================

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


# ==========================================
# CATEGORIAS
# ==========================================

st.markdown("### Clasificación promedio por categorías")

df = pd.DataFrame({
    "Categoría": list(categorias.keys()),
    "Prendas promedio": list(categorias.values())
})

st.bar_chart(
    df.set_index("Categoría"),
    y="Prendas promedio"
)


# ==========================================
# TABLA ESTADISTICA
# ==========================================

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


# ==========================================
# INFORMACION DEL MODELO
# ==========================================

st.divider()

st.markdown("## Información del modelo")

st.markdown("""
- Jornada simulada: 170 minutos.
- Tiempo de clasificación: distribución normal.
- Tamaño de lote: distribución uniforme discreta.
- Cambio de lote: distribución triangular.
- Cuatro categorías de clasificación.
- Un operario.
- Distancias de desplazamiento contabilizadas.
- Resultados expresados como promedios e intervalos de confianza del 95%.

**Nota:** los resultados corresponden a una simulación del proceso
actual y no a mediciones reales de producción.
""")

st.caption(
    "Proyecto académico | Banco de Ropa | "
    "Simulación de eventos discretos"
)
