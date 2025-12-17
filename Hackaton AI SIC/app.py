import streamlit as st
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ===============================
# CONFIGURACIÓN DE LA APP
# ===============================
st.set_page_config(
    page_title="Asesor Económico Inteligente",
    page_icon="📊",
    layout="centered"
)

st.title("📊 Asesor Económico Inteligente")
st.markdown(
    """
    **Sistema de apoyo a decisiones empresariales**  
    Detecta clientes con alto riesgo de fuga y recomienda acciones preventivas.
    """
)

st.divider()

# ===============================
# CARGAR MODELO Y FEATURES
# ===============================
@st.cache_resource
def cargar_modelo():
    model = joblib.load("model.pkl")
    features = joblib.load("features.pkl")
    return model, features

model, features = cargar_modelo()

def construir_input_modelo(base_data, features):
    input_data = {
        "tenure": base_data["tenure"],
        "MonthlyCharges": base_data["MonthlyCharges"],
        "TotalCharges": base_data["TotalCharges"],
    }

    # Inicializar TODAS las columnas en 0
    input_df = pd.DataFrame(0.0, index=[0], columns=features)

    # Asignar variables numéricas
    input_df.loc[0, "tenure"] = base_data["tenure"]
    input_df.loc[0, "MonthlyCharges"] = base_data["MonthlyCharges"]
    input_df.loc[0, "TotalCharges"] = base_data["TotalCharges"]

    # Activar dummies SOLO si existen en el modelo
    contract_col = f"Contract_{base_data['Contract']}"
    if contract_col in features:
        input_df.loc[0, contract_col] = 1.0

    internet_col = f"InternetService_{base_data['InternetService']}"
    if internet_col in features:
        input_df.loc[0, internet_col] = 1.0

    payment_col = f"PaymentMethod_{base_data['PaymentMethod']}"
    if payment_col in features:
        input_df.loc[0, payment_col] = 1.0


    return input_df



# ===============================
# CARGAR DATASET PARA SEGMENTACIÓN
# ===============================
@st.cache_data
def cargar_datos_segmentacion():
    df = pd.read_csv("WA_Fn-UseC_-Telco-Customer-Churn.csv")

    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].median())

    return df

df_seg = cargar_datos_segmentacion()

# ===============================
# PREPARAR CLIENTES PARA DEMO
# ===============================
@st.cache_data
def preparar_clientes_demo(df):
    cols = [
        'tenure',
        'MonthlyCharges',
        'TotalCharges',
        'Contract',
        'InternetService',
        'PaymentMethod'
    ]

    df_demo = df[cols].copy()
    df_demo = df_demo.reset_index(drop=True)

    return df_demo

df_clientes = preparar_clientes_demo(df_seg)

# ===============================
# EVALUACIÓN MASIVA DE CLIENTES
# ===============================
@st.cache_data
def evaluar_clientes_masivo(df, _model, _features):
    resultados = []

    for _, row in df.iterrows():
        input_df = construir_input_modelo({
            "tenure": row["tenure"],
            "MonthlyCharges": row["MonthlyCharges"],
            "TotalCharges": row["TotalCharges"],
            "Contract": row["Contract"],
            "InternetService": row["InternetService"],
            "PaymentMethod": row["PaymentMethod"]
        }, _features)

        prob = _model.predict_proba(input_df)[0][1]


        if prob >= 0.6:
            riesgo = "Alto"
        elif prob >= 0.4:
            riesgo = "Medio"
        else:
            riesgo = "Bajo"

        resultados.append({
            "Tenure": row["tenure"],
            "MonthlyCharges": row["MonthlyCharges"],
            "TotalCharges": row["TotalCharges"],
            "Contract": row["Contract"],
            "InternetService": row["InternetService"],
            "PaymentMethod": row["PaymentMethod"],
            "Probabilidad de fuga": prob,
            "Riesgo": riesgo
        })

    return pd.DataFrame(resultados)





# ===============================
# SEGMENTACIÓN AUTOMÁTICA (K-MEANS)
# ===============================
@st.cache_resource
def entrenar_kmeans(df):
    X_cluster = df[['tenure', 'MonthlyCharges', 'TotalCharges']]

    scaler_cluster = StandardScaler()
    X_scaled = scaler_cluster.fit_transform(X_cluster)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    df_cluster = df.copy()
    df_cluster['Cluster'] = clusters

    return kmeans, scaler_cluster, df_cluster

kmeans, scaler_cluster, df_cluster = entrenar_kmeans(df_seg)


# ===============================
# FORMULARIO DE ENTRADA
# ===============================
st.subheader("🧾 Datos del cliente")


# ===============================
# SELECCIÓN DE CLIENTE (DEMO)
# ===============================
st.subheader("👥 Selección de cliente (dataset real)")

usar_cliente = st.checkbox("Usar cliente del dataset", value=False)

cliente_idx = None

if usar_cliente:
    cliente_idx = st.selectbox(
        "Selecciona un cliente",
        options=df_clientes.index,
        format_func=lambda x: f"Cliente #{x}"
    )

    cliente = df_clientes.loc[cliente_idx]


with st.form("form_cliente"):

    tenure = st.number_input(
        "Meses como cliente",
        min_value=0,
        max_value=120,
        value=int(cliente['tenure']) if usar_cliente else 12
    )

    monthly_charges = st.number_input(
        "Cargo mensual ($)",
        min_value=0.0,
        value=float(cliente['MonthlyCharges']) if usar_cliente else 70.0
    )

    total_charges = st.number_input(
        "Total pagado ($)",
        min_value=0.0,
        value=float(cliente['TotalCharges']) if usar_cliente else 1000.0
    )


    contract = st.selectbox(
        "Tipo de contrato",
        ["Month-to-month", "One year", "Two year"],
        index=["Month-to-month", "One year", "Two year"].index(
            cliente['Contract'] if usar_cliente else "Month-to-month"
        )
    )


    internet_service = st.selectbox(
        "Servicio de internet",
        ["DSL", "Fiber optic", "No"]
    )

    payment_method = st.selectbox(
        "Método de pago",
        [
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)"
        ]
    )

    evaluar = st.form_submit_button("🔍 Evaluar cliente")

# ===============================
# PREDICCIÓN
# ===============================
if evaluar:
    
    input_df = construir_input_modelo({
        "tenure": tenure,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges,
        "Contract": contract,
        "InternetService": internet_service,
        "PaymentMethod": payment_method
    }, features)

    prob = model.predict_proba(input_df)[0][1]


    # Predicción
    prob = model.predict_proba(input_df)[0][1]
    impacto_anual = monthly_charges * 12

    # Guardar resultados en sesión
    st.session_state['evaluado'] = True
    st.session_state['prob'] = prob
    st.session_state['impacto_anual'] = impacto_anual
    st.session_state['tenure'] = tenure
    st.session_state['monthly_charges'] = monthly_charges
    st.session_state['total_charges'] = total_charges
    st.session_state['contract'] = contract

# ===============================
# SECCIÓN DE ANÁLISIS (PESTAÑAS)
# ===============================
if st.session_state.get('evaluado', False):

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📌 Resultado",
        "💰 Impacto económico",
        "📊 Simulación",
        "🎯 Recomendaciones",
        "🧠 Explicabilidad",
        "🔍 Segmentación"
    ])
    with tab1:
        prob = st.session_state['prob']
        impacto_anual = st.session_state['impacto_anual']

        st.metric("Probabilidad de fuga", f"{prob:.2%}")
        st.metric("Pérdida económica anual", f"${impacto_anual:,.2f}")

        if prob >= 0.6:
            riesgo = "🔴 Alto"
        elif prob >= 0.4:
            riesgo = "🟡 Medio"
        else:
            riesgo = "🟢 Bajo"

        st.markdown(f"### Nivel de riesgo: **{riesgo}**")
    
    with tab2:
        perdida_potencial = impacto_anual * prob
        ahorro_estimado = perdida_potencial * 0.3

        col1, col2, col3 = st.columns(3)
        col1.metric("Cliente en riesgo", "Sí" if prob >= 0.4 else "No")
        col2.metric("Pérdida potencial", f"${perdida_potencial:,.2f}")
        col3.metric("Ahorro si se actúa", f"${ahorro_estimado:,.2f}")

    with tab3:
        st.subheader("📊 Análisis global por nivel de riesgo")

        if st.button("📊 Calcular análisis global"):
            st.session_state["df_riesgos"] = evaluar_clientes_masivo(
                df_seg, model, features
            )
        
        if "df_riesgos" in st.session_state:
            nivel = st.selectbox(
                "Selecciona el nivel de riesgo",
                ["Alto", "Medio", "Bajo"],
                key="nivel_riesgo"
            )

            df_filtrado = st.session_state["df_riesgos"][
                st.session_state["df_riesgos"]["Riesgo"] == nivel
            ]

            st.write(f"Clientes con riesgo **{nivel}**: {len(df_filtrado)}")

            st.dataframe(
                df_filtrado.sort_values(
                    "Probabilidad de fuga", ascending=False
                ),
                use_container_width=True
            )



    with tab4:
        if prob >= 0.6:
            st.error("🔴 Retención inmediata y contacto humano")
        elif prob >= 0.4:
            st.warning("🟡 Incentivos y seguimiento")
        else:
            st.success("🟢 Cliente estable")

    with tab5:
        explicacion = []

        if st.session_state['tenure'] < 12:
            explicacion.append("Poco tiempo como cliente")

        if st.session_state['contract'] == "Month-to-month":
            explicacion.append("Contrato mensual")

        if st.session_state['monthly_charges'] > 70:
            explicacion.append("Cargo mensual elevado")

        if explicacion:
            for e in explicacion:
                st.write(f"• {e}")
        else:
            st.write("Perfil estable")
    
    with tab6:
        cliente_cluster = pd.DataFrame([{
            'tenure': st.session_state['tenure'],
            'MonthlyCharges': st.session_state['monthly_charges'],
            'TotalCharges': st.session_state['total_charges']
        }])

        cliente_scaled = scaler_cluster.transform(cliente_cluster)
        segmento = kmeans.predict(cliente_scaled)[0]

        segmentos = {
            0: "Clientes fieles",
            1: "Clientes sensibles al precio",
            2: "Clientes en alto riesgo"
        }

        st.metric("Segmento", segmentos[segmento])
