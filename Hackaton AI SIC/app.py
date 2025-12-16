import streamlit as st
import pandas as pd
import joblib

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

# ===============================
# FORMULARIO DE ENTRADA
# ===============================
st.subheader("🧾 Datos del cliente")

with st.form("form_cliente"):
    tenure = st.number_input("Meses como cliente", min_value=0, max_value=120, value=12)
    monthly_charges = st.number_input("Cargo mensual ($)", min_value=0.0, value=70.0)
    total_charges = st.number_input("Total pagado ($)", min_value=0.0, value=1000.0)

    contract = st.selectbox(
        "Tipo de contrato",
        ["Month-to-month", "One year", "Two year"]
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
    # Construir input base
    input_data = {
        "tenure": tenure,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges,
    }

    # Dummies manuales (alineadas al dataset original)
    input_data[f"Contract_{contract}"] = 1
    input_data[f"InternetService_{internet_service}"] = 1
    input_data[f"PaymentMethod_{payment_method}"] = 1

    input_df = pd.DataFrame([input_data])

    # Alinear columnas con el modelo
    input_df = input_df.reindex(columns=features, fill_value=0)

    # Predicción
    prob = model.predict_proba(input_df)[0][1]
    impacto_anual = monthly_charges * 12

    if prob >= 0.6:
        riesgo = "🔴 Alto"
    elif prob >= 0.4:
        riesgo = "🟡 Medio"
    else:
        riesgo = "🟢 Bajo"


    # ===============================
    # RESULTADOS
    # ===============================
    st.divider()
    st.subheader("📌 Resultado del análisis")

    st.metric(
        label="Probabilidad de fuga",
        value=f"{prob:.2%}"
    )
    st.metric(
        label="Pérdida económica anual estimada",
        value=f"${impacto_anual:,.2f}"
    )

    st.markdown(f"### Nivel de riesgo: **{riesgo}**")

    # ===============================
    # RECOMENDACIÓN
    # ===============================
    st.subheader("💡 Recomendación")

    if prob >= 0.6:
        st.warning(
            """
            **Acción sugerida:**
            - Ofrecer descuento personalizado
            - Migrar a contrato anual
            - Contacto proactivo del área de retención
            
            *Pérdida potencial anual estimada: ${impacto_anual:,.2f}*
            """
        )
    
    elif prob >= 0.4:
        st.warning(
            """
            🟡 **Riesgo MEDIO**

            **Acción sugerida:**
            - Ofrecer mejora de plan o descuento temporal
            - Contacto preventivo para conocer satisfacción
            - Incentivos por permanencia
            - Monitoreo en los próximos 30–60 días

            ⚠️ *Cliente recuperable con acción temprana*
            """
        )

    else:
        st.success(
            """
            **Acción sugerida:**
            - Mantener condiciones actuales
            - Ofrecer beneficios de fidelización
            
            📈 *Cliente estable*
            """
        )

    # ===============================
    # FRASE IMPACTO (DEMO)
    # ===============================
    st.info(
        "💬 *Aquí la empresa decide antes de perder ingresos.*"
    )


