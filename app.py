import streamlit as st
import math
from datetime import datetime
import pandas as pd
import numpy as np


# Inietta il meta tag HTML per l'icona sui dispositivi mobili
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://github.com/MaF-MPJ/Bonifiche-app/blob/bd70a2a5bedfb9b988570cb839db507a610f187a/MPJ_Logo192.png">
        <link rel="icon" sizes="192x192" href="https://github.com/MaF-MPJ/Bonifiche-app/blob/bd70a2a5bedfb9b988570cb839db507a610f187a/MPJ_Logo192.png">
    </head>
    """,
    unsafe_allow_html=True
)
# Configurazione Schermata Mobile-Friendly
st.set_page_config(page_title="Radioprotezione App", page_icon="☢️", layout="centered")

st.title("☢️ Calcoli di Radioprotezione")

# Dati Statistici Originali MATLAB
detectors = ["RE-55916", "RE-53065", "RE-53154", "RE-53049", "RE-55049", "RE-54722", "RE-56510", "RE-52083PD", "T98-3822", "T98-3914", "T98-8043", "Default"]
taratura = [0.577, 0.631, 0.613, 0.609, 0.588, 0.598, 0.667, 0.514, 0.612, 0.523, 0.523, 0.602]

radionuclidi = ["I-131", "I-123", "Tc-99m", "Lu-177", "Lu-177m", "Ra-226", "NORM", "Th-232+", "K-40", "Cs-137", "Co-60", "Kr-85", "In-111", "Ir-192"]
costanteGamma = [77.0, 74.8, 33.2, 7.64, 211.0, 258.0, 316.0, 864.0, 22.2, 104.0, 373.0, 0.426, 136.0, 161.0]
tDimezzamento = [8.02, 0.551, 0.25, 6.65, 160.0, 584000.0, 1.63e12, 5.12e12, 4.56e11, 11000.0, 19200.0, 3920.0, 2.81, 73.8]

# INTERFACCIA GRAFICA (UI)
st.subheader("Configurazione Parametri")
sel_det = st.selectbox("Seleziona Detector:", detectors)
sel_rad = st.selectbox("Seleziona Radionuclide:", radionuclidi)

idx_det = detectors.index(sel_det)
idx_rad = radionuclidi.index(sel_rad)

kTar = taratura[idx_det]
kGamma = costanteGamma[idx_rad]
tDim = tDimezzamento[idx_rad] * 24 * 3600  # secondi

data_bonifica = st.date_input("Data bonifica:", datetime.now())

st.subheader("Inserimento Misure (cps)")
cps0 = st.number_input("cps a contatto:", min_value=0.0, value=0.0)
cps50 = st.number_input("cps a 50 cm:", min_value=0.0, value=0.0)
cps100 = st.number_input("cps a 1m:", min_value=0.0, value=0.0)

if st.button("CALCOLA RISULTATI", type="primary"):
    rDose0 = cps0 * kTar
    rDose50 = cps50 * kTar
    rDose100 = cps100 * kTar
    
    valAtt50 = (rDose50 / kGamma) * (0.5 ** 2)
    valAtt100 = rDose100 / kGamma
    
    # OUTPUT DATI
    st.success("### 📊 Risultati Rateo di Dose")
    st.write(f"**Rateo di dose a contatto:** {rDose0:.2f} nSv/h")
    st.write(f"**Rateo di dose a 50 cm:** {rDose50:.2f} nSv/h")
    st.write(f"**Rateo di dose a 1 metro:** {rDose100:.2f} nSv/h")
    
    st.info("### 📉 Stime di Smaltimento")
    
    # Calcoli decadi/date
    dStart_ts = datetime.combine(data_bonifica, datetime.min.time()).timestamp()
    
    if valAtt50 > 0:
        outData50 = (tDim / math.log(2)) * math.log(valAtt50 * 1e3)
        date50 = datetime.fromtimestamp(dStart_ts + outData50).strftime("%d/%m/%Y")
        st.write(f"**Attività (stima a 50 cm):** {valAtt50:.4g} MBq")
        st.write(f"📅 **Data prevista smaltimento (50 cm):** {date50}")
    else:
        st.write("**Stima a 50 cm:** Attività non calcolabile (inserire cps > 0)")
        
    st.markdown("---")
    
    if valAtt100 > 0:
        outData100 = (tDim / math.log(2)) * math.log(valAtt100 * 1e3)
        date100 = datetime.fromtimestamp(dStart_ts + outData100).strftime("%d/%m/%Y")
        st.write(f"**Attività (stima a 1 m):** {valAtt100:.4g} MBq")
        st.write(f"📅 **Data prevista smaltimento (1 m):** {date100}")
    else:
        st.write("**Stima a 1 m:** Attività non calcolabile (inserire cps > 0)")

# --- GRAFICO INTERATTIVO AGGIORNATO ---
st.subheader("📈 Andamento Spaziale del Rateo di Dose")

# 1. Mappatura dei punti misurati (già convertiti in nSv/h)
# Associano la distanza (chiave) al rispettivo valore di dose
# Per il contatto (0 cm) usiamo 1 cm per evitare la divisione per zero nel grafico
punti_misurati = {}
if cps0 > 0: punti_misurati[1] = rDose0
if cps50 > 0: punti_misurati[50] = rDose50
if cps100 > 0: punti_misurati[100] = rDose100

# 2. Generazione asse X (Distanze da 1 a 100 cm)
x_teorico = list(range(1, 101))

# 3. Generazione delle serie di dati
y_teorico = [rDose100 * (100 / x)**2 for x in x_teorico]
y_misurato = [punti_misurati.get(x, np.nan) for x in x_teorico]

# 4. Creazione del DataFrame per Streamlit
df_grafico = pd.DataFrame({
    "Distanza (cm)": x_teorico,
    "Teorico 1/x² (nSv/h)": y_teorico,
    "Misurato (nSv/h)": y_misurato
})
df_grafico = df_grafico.set_index("Distanza (cm)")

# 5. Rendering del grafico a linee e punti
st.line_chart(df_grafico)
