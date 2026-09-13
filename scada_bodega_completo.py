import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SCADA Bodega Didáctica",
    page_icon="🍷",
    layout="wide"
)

st.title("🍷 SCADA — Bodega Experimental")
st.caption(
    "Simulador didáctico integrado de Fermentación Alcohólica (FA) "
    "y Fermentación Maloláctica (FML)"
)


# ============================================================
# FACTORES DE FERMENTACIÓN ALCOHÓLICA
# ============================================================

def f_temp_fa(t):
    if t < 12:
        return 0.05
    elif t < 16:
        return 0.30
    elif t < 20:
        return 0.70
    elif t <= 26:
        return 1.00
    elif t <= 30:
        return 0.85
    elif t <= 33:
        return 0.50
    elif t <= 35:
        return 0.20
    else:
        return 0.03


def f_yan(y):
    if y < 50:
        return 0.20
    elif y < 100:
        return 0.45
    elif y < 150:
        return 0.75
    else:
        return 1.00


def f_ph_fa(ph):
    if ph < 2.8:
        return 0.25
    elif ph < 3.0:
        return 0.60
    elif ph <= 3.8:
        return 1.00
    elif ph <= 4.0:
        return 0.85
    else:
        return 0.70


def f_etanol_fa(e):
    if e < 10:
        return 1.00
    elif e < 12:
        return 0.90
    elif e < 14:
        return 0.70
    elif e < 15:
        return 0.45
    else:
        return 0.20


def f_osmotico(s):
    if s <= 220:
        return 1.00
    elif s <= 250:
        return 0.90
    elif s <= 280:
        return 0.75
    else:
        return 0.55


# ============================================================
# FACTORES DE FERMENTACIÓN MALOLÁCTICA
# ============================================================

def f_temp_fml(t):
    if t < 12:
        return 0.05
    elif t < 15:
        return 0.25
    elif t < 18:
        return 0.65
    elif t <= 22:
        return 1.00
    elif t <= 25:
        return 0.80
    elif t <= 27:
        return 0.45
    else:
        return 0.15


def f_ph_fml(ph):
    if ph < 3.0:
        return 0.05
    elif ph < 3.2:
        return 0.25
    elif ph < 3.4:
        return 0.60
    elif ph <= 3.8:
        return 1.00
    elif ph <= 4.0:
        return 0.85
    else:
        return 0.65


def f_alcohol_fml(a):
    if a <= 11:
        return 1.00
    elif a <= 12.5:
        return 0.95
    elif a <= 14:
        return 0.75
    elif a <= 15:
        return 0.50
    elif a <= 16:
        return 0.25
    else:
        return 0.08


def f_so2_fml(s):
    if s <= 5:
        return 1.00
    elif s <= 10:
        return 0.85
    elif s <= 15:
        return 0.60
    elif s <= 20:
        return 0.35
    elif s <= 30:
        return 0.15
    else:
        return 0.05


# ============================================================
# CREACIÓN DE DEPÓSITOS
# ============================================================

def crear_deposito(
    nombre,
    volumen,
    azucar,
    temperatura,
    yan,
    ph,
    malico,
    so2
):

    densidad = 0.998 + 0.00038 * azucar

    return {
        "nombre": nombre,
        "volumen": float(volumen),
        "nivel": 82,
        "fase": "FA",
        "dia": 0,

        "azucar_inicial": float(azucar),
        "azucar": float(azucar),

        "temperatura": float(temperatura),
        "yan": float(yan),
        "ph": float(ph),

        "alcohol": 0.0,
        "densidad": densidad,
        "co2": 0.0,

        "malico_inicial": float(malico),
        "malico": float(malico),
        "lactico": 0.0,

        "so2": float(so2),

        "bacterias": 0.0,

        "historial": [],
        "eventos": [],

        "ultima_actividad_fa": 0.0,
        "ultima_actividad_fml": 0.0
    }


# ============================================================
# INICIALIZACIÓN DE LA BODEGA
# ============================================================

def inicializar_bodega():

    return {

        "D1": crear_deposito(
            "Depósito 1",
            2000,
            220,
            22,
            180,
            3.45,
            3.0,
            5
        ),

        "D2": crear_deposito(
            "Depósito 2",
            1800,
            230,
            22,
            55,
            3.40,
            3.0,
            5
        ),

        "D3": crear_deposito(
            "Depósito 3",
            2200,
            220,
            14,
            180,
            3.50,
            3.0,
            5
        ),

        "D4": crear_deposito(
            "Depósito 4",
            1600,
            290,
            23,
            150,
            3.20,
            3.5,
            8
        )
    }


if "depositos" not in st.session_state:
    st.session_state.depositos = inicializar_bodega()

if "dia_bodega" not in st.session_state:
    st.session_state.dia_bodega = 0

if "deposito_seleccionado" not in st.session_state:
    st.session_state.deposito_seleccionado = "D1"


# ============================================================
# HISTORIAL
# ============================================================

def guardar_historial(d):

    d["historial"].append(
        {
            "Día": d["dia"],
            "Fase": d["fase"],
            "Temperatura": d["temperatura"],
            "Azúcar": d["azucar"],
            "Densidad": d["densidad"],
            "Alcohol": d["alcohol"],
            "YAN": d["yan"],
            "CO2": d["co2"],
            "pH": d["ph"],
            "Málico": d["malico"],
            "Láctico": d["lactico"],
            "SO2": d["so2"]
        }
    )


# ============================================================
# FERMENTACIÓN ALCOHÓLICA
# ============================================================

def avanzar_fa(d):

    actividad = (
        f_temp_fa(d["temperatura"])
        * f_yan(d["yan"])
        * f_ph_fa(d["ph"])
        * f_etanol_fa(d["alcohol"])
        * f_osmotico(d["azucar"])
    )

    # Fase inicial de adaptación
    if d["dia"] <= 1:
        actividad *= 0.45

    # Velocidad máxima simplificada
    velocidad = 35.0 * actividad

    # Ralentización cuando queda poco azúcar
    if d["azucar"] < 20:
        velocidad *= max(d["azucar"], 0) / 20.0

    consumo = min(
        max(velocidad, 0),
        d["azucar"]
    )

    d["azucar"] -= consumo

    # Producción aproximada de alcohol
    d["alcohol"] += consumo / 17.0

    # Consumo simplificado de YAN
    d["yan"] = max(
        20,
        d["yan"] - consumo * 0.25
    )

    # Densidad aproximada
    d["densidad"] = (
        0.998
        + 0.00038 * d["azucar"]
        - 0.0012 * d["alcohol"]
    )

    d["co2"] = consumo
    d["ultima_actividad_fa"] = actividad

    # Fin de FA
    if d["azucar"] <= 4:

        d["azucar"] = max(
            0,
            d["azucar"]
        )

        d["co2"] = 0
        d["fase"] = "POST-FA"

        d["eventos"].append(
            f"Día {d['dia']}: fermentación alcohólica finalizada."
        )


# ============================================================
# FERMENTACIÓN MALOLÁCTICA
# ============================================================

def avanzar_fml(d):

    actividad = (
        f_temp_fml(d["temperatura"])
        * f_ph_fml(d["ph"])
        * f_alcohol_fml(d["alcohol"])
        * f_so2_fml(d["so2"])
        * d["bacterias"]
    )

    velocidad = 0.40 * actividad

    # Ralentización cuando queda poco ácido málico
    if d["malico"] < 0.5:
        velocidad *= max(d["malico"], 0) / 0.5

    consumo = min(
        max(velocidad, 0),
        d["malico"]
    )

    d["malico"] -= consumo

    # Conversión simplificada málico -> láctico
    d["lactico"] += consumo * 0.67

    d["ultima_actividad_fml"] = actividad

    # Fin de FML
    if d["malico"] <= 0.10:

        d["malico"] = max(
            0,
            d["malico"]
        )

        d["fase"] = "FINALIZADO"

        d["eventos"].append(
            f"Día {d['dia']}: fermentación maloláctica finalizada."
        )


# ============================================================
# AVANCE DE UN DEPÓSITO
# ============================================================

def avanzar_deposito(d):

    d["dia"] += 1

    if d["fase"] == "FA":
        avanzar_fa(d)

    elif d["fase"] == "FML":
        avanzar_fml(d)

    guardar_historial(d)


# ============================================================
# RELOJ MAESTRO DE TODA LA BODEGA
# ============================================================

def avanzar_bodega(numero_dias):

    for _ in range(numero_dias):

        st.session_state.dia_bodega += 1

        for dep in st.session_state.depositos.values():
            avanzar_deposito(dep)


# ============================================================
# ALARMAS
# ============================================================

def obtener_alarmas(d):

    alarmas = []

    if d["fase"] == "FA":

        if d["temperatura"] < 16:
            alarmas.append(
                "Temperatura baja para FA"
            )

        if d["temperatura"] > 30:
            alarmas.append(
                "Temperatura elevada para FA"
            )

        if d["yan"] < 80:
            alarmas.append(
                "YAN bajo"
            )

        if (
            d["azucar"] > 4
            and d["co2"] < 2
            and d["dia"] > 2
        ):
            alarmas.append(
                "Actividad fermentativa muy baja"
            )

        if (
            d["dia"] > 10
            and d["azucar"] > 20
        ):
            alarmas.append(
                "Posible fermentación lenta o parada"
            )

    elif d["fase"] == "FML":

        if d["temperatura"] < 15:
            alarmas.append(
                "Temperatura baja para FML"
            )

        if d["temperatura"] > 25:
            alarmas.append(
                "Temperatura elevada para FML"
            )

        if d["ph"] < 3.2:
            alarmas.append(
                "pH desfavorable para FML"
            )

        if d["so2"] > 15:
            alarmas.append(
                "SO₂ potencialmente inhibidor"
            )

        if d["alcohol"] > 14:
            alarmas.append(
                "Alcohol elevado para FML"
            )

        if d["bacterias"] <= 0:
            alarmas.append(
                "Sin cultivo bacteriano activo"
            )

    return alarmas


# ============================================================
# NOMBRE DEL ESTADO
# ============================================================

def nombre_estado(d):

    if d["fase"] == "FA":
        return "FA ACTIVA"

    elif d["fase"] == "POST-FA":
        return "FA FINALIZADA"

    elif d["fase"] == "FML":
        return "FML ACTIVA"

    else:
        return "FINALIZADO"


# ============================================================
# SIDEBAR - CONTROL MAESTRO
# ============================================================

st.sidebar.title("🎛️ CONTROL SCADA")

st.sidebar.metric(
    "Día general de bodega",
    st.session_state.dia_bodega
)

st.sidebar.subheader("⏱️ Reloj maestro")

c1, c2 = st.sidebar.columns(2)

if c1.button(
    "▶ +1 día",
    use_container_width=True
):
    avanzar_bodega(1)
    st.rerun()

if c2.button(
    "⏩ +3 días",
    use_container_width=True
):
    avanzar_bodega(3)
    st.rerun()


# ============================================================
# SELECCIÓN DEL DEPÓSITO
# ============================================================

st.sidebar.markdown("---")

deposito_id = st.sidebar.selectbox(
    "Depósito seleccionado",
    list(st.session_state.depositos.keys()),
    format_func=lambda x:
        st.session_state.depositos[x]["nombre"]
)

st.session_state.deposito_seleccionado = deposito_id

d = st.session_state.depositos[deposito_id]


# ============================================================
# INFORMACIÓN DEL DEPÓSITO
# ============================================================

st.sidebar.subheader(
    f"📡 {d['nombre']}"
)

st.sidebar.metric(
    "Fase",
    nombre_estado(d)
)

st.sidebar.metric(
    "Día",
    d["dia"]
)

st.sidebar.metric(
    "Temperatura",
    f"{d['temperatura']:.1f} °C"
)


# ============================================================
# INTERVENCIONES
# ============================================================

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Intervenciones")

nueva_temp = st.sidebar.number_input(
    "Consigna de temperatura (°C)",
    min_value=8.0,
    max_value=35.0,
    value=float(d["temperatura"]),
    step=0.5
)

if st.sidebar.button(
    "🌡️ Aplicar temperatura",
    use_container_width=True
):

    d["temperatura"] = nueva_temp

    d["eventos"].append(
        f"Día {d['dia']}: temperatura ajustada "
        f"a {nueva_temp:.1f} °C."
    )

    st.rerun()


# ============================================================
# INTERVENCIONES DURANTE FA
# ============================================================

if d["fase"] == "FA":

    cantidad_yan = st.sidebar.number_input(
        "Aporte de YAN (mg/L)",
        min_value=0,
        max_value=100,
        value=20,
        step=10
    )

    if st.sidebar.button(
        "➕ Añadir nutriente",
        use_container_width=True
    ):

        d["yan"] += cantidad_yan

        d["eventos"].append(
            f"Día {d['dia']}: aporte nutricional "
            f"equivalente a +{cantidad_yan} mg/L de YAN."
        )

        st.rerun()


    if st.sidebar.button(
        "🧫 Reinocular levaduras",
        use_container_width=True
    ):

        d["yan"] += 15

        d["eventos"].append(
            f"Día {d['dia']}: reinoculación "
            f"con levaduras activas."
        )

        st.rerun()


    if st.sidebar.button(
        "🔄 Homogeneizar",
        use_container_width=True
    ):

        d["eventos"].append(
            f"Día {d['dia']}: homogeneización del depósito."
        )

        st.rerun()


# ============================================================
# INICIO DE FML
# ============================================================

if d["fase"] == "POST-FA":

    st.sidebar.success(
        "FA finalizada"
    )

    if st.sidebar.button(
        "🦠 Inocular Oenococcus oeni",
        use_container_width=True
    ):

        d["bacterias"] = 1.0
        d["fase"] = "FML"

        d["eventos"].append(
            f"Día {d['dia']}: inicio de FML mediante "
            f"inoculación de Oenococcus oeni."
        )

        st.rerun()


# ============================================================
# REINICIAR
# ============================================================

st.sidebar.markdown("---")

if st.sidebar.button(
    "🔄 REINICIAR BODEGA",
    use_container_width=True
):

    st.session_state.depositos = inicializar_bodega()
    st.session_state.dia_bodega = 0
    st.rerun()


# ============================================================
# RESUMEN GENERAL
# ============================================================

total_alarmas = sum(
    len(obtener_alarmas(dep))
    for dep in st.session_state.depositos.values()
)

fa_activas = sum(
    dep["fase"] == "FA"
    for dep in st.session_state.depositos.values()
)

fml_activas = sum(
    dep["fase"] == "FML"
    for dep in st.session_state.depositos.values()
)

finalizados = sum(
    dep["fase"] == "FINALIZADO"
    for dep in st.session_state.depositos.values()
)


col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Día de bodega",
    st.session_state.dia_bodega
)

col2.metric(
    "FA activas",
    fa_activas
)

col3.metric(
    "FML activas",
    fml_activas
)

col4.metric(
    "Finalizados",
    finalizados
)

col5.metric(
    "Alarmas",
    total_alarmas
)


# ============================================================
# VISTA GENERAL SCADA
# ============================================================

st.divider()
st.header("🏭 Vista general de la bodega")

columnas = st.columns(4)

for i, (clave, dep) in enumerate(
    st.session_state.depositos.items()
):

    alarmas = obtener_alarmas(dep)

    if len(alarmas) > 0:
        indicador = "🔴"
    else:
        indicador = "🟢"

    estado = nombre_estado(dep)

    nivel = dep["nivel"]

    # ========================================================
    # DEPÓSITO VISUAL
    # ========================================================

    deposito_html = (
        '<div style="text-align:center;padding:8px;">'
        f'<div style="font-size:19px;font-weight:700;margin-bottom:8px;">'
        f'{indicador} {dep["nombre"]}'
        '</div>'

        '<div style="'
        'width:140px;'
        'height:210px;'
        'border:5px solid #777777;'
        'border-radius:20px 20px 35px 35px;'
        'margin:0 auto;'
        'position:relative;'
        'overflow:hidden;'
        'background-color:#eeeeee;'
        '">'

        f'<div style="'
        f'position:absolute;'
        f'left:0;'
        f'right:0;'
        f'bottom:0;'
        f'height:{nivel}%;'
        f'background-color:#7b263a;'
        f'"></div>'

        '<div style="'
        'position:absolute;'
        'left:0;'
        'right:0;'
        'top:72px;'
        'text-align:center;'
        'color:white;'
        'font-size:21px;'
        'font-weight:bold;'
        'z-index:10;'
        '">'
        f'{dep["temperatura"]:.1f} °C'
        '</div>'

        '<div style="'
        'position:absolute;'
        'left:0;'
        'right:0;'
        'top:108px;'
        'text-align:center;'
        'color:white;'
        'font-size:13px;'
        'font-weight:bold;'
        'z-index:10;'
        '">'
        f'{estado}'
        '</div>'

        '</div>'

        '<div style="'
        'width:10px;'
        'height:20px;'
        'background-color:#777777;'
        'margin:0 auto;'
        '"></div>'

        '<div style="'
        'width:70px;'
        'height:8px;'
        'background-color:#777777;'
        'margin:0 auto 8px auto;'
        'border-radius:4px;'
        '"></div>'

        f'<div style="font-weight:600;">'
        f'{dep["volumen"]:.0f} L'
        '</div>'

        f'<div>Día {dep["dia"]}</div>'

        '</div>'
    )

    columnas[i].markdown(
        deposito_html,
        unsafe_allow_html=True
    )

    # ========================================================
    # INFORMACIÓN BAJO CADA DEPÓSITO
    # ========================================================

    if dep["fase"] == "FA":

        columnas[i].metric(
            "Densidad",
            f"{dep['densidad']:.3f}"
        )

        columnas[i].caption(
            f"Azúcar: {dep['azucar']:.1f} g/L | "
            f"Alcohol: {dep['alcohol']:.1f} % vol"
        )

    elif dep["fase"] == "POST-FA":

        columnas[i].metric(
            "Alcohol",
            f"{dep['alcohol']:.1f} % vol"
        )

        columnas[i].caption(
            "FA terminada · Pendiente de FML"
        )

    elif dep["fase"] == "FML":

        columnas[i].metric(
            "Ácido málico",
            f"{dep['malico']:.2f} g/L"
        )

        columnas[i].caption(
            f"Láctico: {dep['lactico']:.2f} g/L"
        )

    else:

        columnas[i].metric(
            "Alcohol",
            f"{dep['alcohol']:.1f} % vol"
        )

        columnas[i].caption(
            f"Málico final: {dep['malico']:.2f} g/L"
        )

    if alarmas:

        columnas[i].warning(
            f"{len(alarmas)} alarma(s)"
        )

    else:

        columnas[i].success(
            "Proceso sin alarmas"
        )


# ============================================================
# PANEL DETALLADO DEL DEPÓSITO
# ============================================================

st.divider()

st.header(
    f"📡 Panel de proceso — {d['nombre']}"
)

st.caption(
    f"Volumen: {d['volumen']:.0f} L · "
    f"Fase: {nombre_estado(d)} · "
    f"Día: {d['dia']}"
)


# ============================================================
# VARIABLES PRINCIPALES
# ============================================================

m1, m2, m3, m4, m5, m6 = st.columns(6)

m1.metric(
    "🌡️ Temperatura",
    f"{d['temperatura']:.1f} °C"
)

m2.metric(
    "⚖️ Densidad",
    f"{d['densidad']:.3f}"
)

m3.metric(
    "🍬 Azúcar",
    f"{d['azucar']:.1f} g/L"
)

m4.metric(
    "🍷 Alcohol",
    f"{d['alcohol']:.1f} % vol"
)

m5.metric(
    "🧪 pH",
    f"{d['ph']:.2f}"
)

m6.metric(
    "🌿 YAN",
    f"{d['yan']:.0f} mg/L"
)


m7, m8, m9, m10 = st.columns(4)

m7.metric(
    "💨 Actividad CO₂",
    f"{d['co2']:.1f}"
)

m8.metric(
    "Ácido málico",
    f"{d['malico']:.2f} g/L"
)

m9.metric(
    "Ácido láctico",
    f"{d['lactico']:.2f} g/L"
)

m10.metric(
    "SO₂ libre",
    f"{d['so2']:.0f} mg/L"
)


# ============================================================
# ALARMAS DEL DEPÓSITO
# ============================================================

st.subheader("🚨 Gestión de alarmas")

alarmas_actuales = obtener_alarmas(d)

if not alarmas_actuales:

    st.success(
        "Sistema estable. No existen alarmas activas."
    )

else:

    for alarma in alarmas_actuales:
        st.error(
            "⚠️ " + alarma
        )


# ============================================================
# TENDENCIAS
# ============================================================

st.subheader("📈 Tendencias del proceso")

if len(d["historial"]) == 0:

    st.info(
        "Avanza el reloj de la bodega para comenzar "
        "a registrar las tendencias."
    )

else:

    hist = pd.DataFrame(
        d["historial"]
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🍬 Fermentación alcohólica",
            "🦠 Fermentación maloláctica",
            "🌡️ Temperatura",
            "📋 Datos"
        ]
    )

    # ========================================================
    # FA
    # ========================================================

    with tab1:

        fig_fa = go.Figure()

        fig_fa.add_trace(
            go.Scatter(
                x=hist["Día"],
                y=hist["Azúcar"],
                name="Azúcar (g/L)",
                mode="lines+markers"
            )
        )

        fig_fa.add_trace(
            go.Scatter(
                x=hist["Día"],
                y=hist["Alcohol"],
                name="Alcohol (% vol)",
                mode="lines+markers",
                yaxis="y2"
            )
        )

        fig_fa.update_layout(
            title="Cinética de fermentación alcohólica",
            xaxis_title="Día",
            yaxis=dict(
                title="Azúcar (g/L)"
            ),
            yaxis2=dict(
                title="Alcohol (% vol)",
                overlaying="y",
                side="right"
            ),
            hovermode="x unified",
            height=430
        )

        st.plotly_chart(
            fig_fa,
            use_container_width=True
        )


        fig_densidad = go.Figure()

        fig_densidad.add_trace(
            go.Scatter(
                x=hist["Día"],
                y=hist["Densidad"],
                mode="lines+markers",
                name="Densidad"
            )
        )

        fig_densidad.update_layout(
            title="Evolución de la densidad",
            xaxis_title="Día",
            yaxis_title="Densidad",
            height=350
        )

        st.plotly_chart(
            fig_densidad,
            use_container_width=True
        )


    # ========================================================
    # FML
    # ========================================================

    with tab2:

        fig_fml = go.Figure()

        fig_fml.add_trace(
            go.Scatter(
                x=hist["Día"],
                y=hist["Málico"],
                name="Ácido málico",
                mode="lines+markers"
            )
        )

        fig_fml.add_trace(
            go.Scatter(
                x=hist["Día"],
                y=hist["Láctico"],
                name="Ácido láctico",
                mode="lines+markers"
            )
        )

        fig_fml.update_layout(
            title="Fermentación maloláctica",
            xaxis_title="Día",
            yaxis_title="Concentración (g/L)",
            hovermode="x unified",
            height=430
        )

        st.plotly_chart(
            fig_fml,
            use_container_width=True
        )


    # ========================================================
    # TEMPERATURA
    # ========================================================

    with tab3:

        fig_temp = go.Figure()

        fig_temp.add_trace(
            go.Scatter(
                x=hist["Día"],
                y=hist["Temperatura"],
                name="Temperatura",
                mode="lines+markers"
            )
        )

        fig_temp.update_layout(
            title="Temperatura del depósito",
            xaxis_title="Día",
            yaxis_title="Temperatura (°C)",
            height=400
        )

        st.plotly_chart(
            fig_temp,
            use_container_width=True
        )


    # ========================================================
    # DATOS
    # ========================================================

    with tab4:

        st.dataframe(
            hist.round(3),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# LABORATORIO ENOLÓGICO
# ============================================================

st.divider()
st.header("🧪 Laboratorio enológico")

lab1, lab2, lab3, lab4 = st.columns(4)

lab1.metric(
    "Azúcares reductores",
    f"{d['azucar']:.1f} g/L"
)

lab2.metric(
    "Alcohol",
    f"{d['alcohol']:.1f} % vol"
)

lab3.metric(
    "Ácido málico",
    f"{d['malico']:.2f} g/L"
)

lab4.metric(
    "Ácido láctico",
    f"{d['lactico']:.2f} g/L"
)


lab5, lab6, lab7 = st.columns(3)

lab5.metric(
    "pH",
    f"{d['ph']:.2f}"
)

lab6.metric(
    "YAN",
    f"{d['yan']:.0f} mg/L"
)

lab7.metric(
    "SO₂ libre",
    f"{d['so2']:.0f} mg/L"
)


# ============================================================
# REGISTRO DE OPERACIONES
# ============================================================

st.divider()
st.header("📋 Registro de operaciones")

if not d["eventos"]:

    st.info(
        "Todavía no se han registrado operaciones "
        "en este depósito."
    )

else:

    for evento in reversed(d["eventos"]):

        st.write(
            "• " + evento
        )


# ============================================================
# CENTRO DE DECISIÓN DIDÁCTICO
# ============================================================

st.divider()
st.header("🎓 Centro de decisión del alumno")

if d["fase"] == "FA":

    st.info(
        """
### Fermentación alcohólica

Analiza los datos del SCADA antes de intervenir.

**Preguntas de diagnóstico**

1. ¿La densidad está disminuyendo?
2. ¿La velocidad de disminución es adecuada?
3. ¿Existe producción de CO₂?
4. ¿Los azúcares están siendo consumidos?
5. ¿La temperatura es adecuada?
6. ¿Existe una posible limitación nutricional?
7. ¿Se trata de una FA normal, lenta o posiblemente parada?
8. ¿Es necesario intervenir?

Realiza una intervención desde el panel lateral y observa
su efecto durante los días siguientes.
        """
    )


elif d["fase"] == "POST-FA":

    st.success(
        """
### Fermentación alcohólica finalizada

La concentración de azúcares fermentables ha alcanzado
el criterio establecido para considerar finalizada la FA.

Antes de iniciar la fermentación maloláctica analiza:

- concentración de alcohol;
- pH;
- temperatura;
- SO₂ libre;
- concentración de ácido málico.

Si consideras que las condiciones son adecuadas, puedes
inocular **Oenococcus oeni** desde el panel lateral.
        """
    )


elif d["fase"] == "FML":

    st.info(
        """
### Fermentación maloláctica

Sigue la desaparición del ácido málico y la formación
de ácido láctico.

**Preguntas de diagnóstico**

1. ¿Está disminuyendo el ácido málico?
2. ¿A qué velocidad?
3. ¿La temperatura es adecuada?
4. ¿El pH puede limitar la actividad bacteriana?
5. ¿El contenido alcohólico puede ejercer un efecto inhibidor?
6. ¿El SO₂ puede dificultar la FML?
7. ¿Mantendrías las condiciones actuales o intervendrías?
        """
    )


else:

    st.success(
        """
## 🏁 Vinificación completada

Se han completado las dos etapas microbiológicas:

**Fermentación alcohólica → Fermentación maloláctica**

Revisa las curvas y el registro de operaciones para
evaluar las decisiones tomadas durante el proceso.
        """
    )


# ============================================================
# NOTA FINAL
# ============================================================

st.divider()

st.caption(
    "⚠️ Modelo didáctico simplificado. Las relaciones cinéticas "
    "se utilizan para enseñar el efecto de las variables de proceso "
    "y no constituyen un modelo predictivo de una vinificación industrial."
)