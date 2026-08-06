import streamlit as st
import math
from datetime import datetime
import pandas as pd
import numpy as np
import altair as alt

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

# NOTA: st.set_page_config DEVE essere la primissima istruzione Streamlit eseguita.
# Spostata qui in alto per evitare potenziali avvisi/errori di Streamlit.
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

# --- CALCOLI FISSI (Eseguiti sempre per popolare il grafico in tempo reale) ---
rDose0 = cps0 * kTar
rDose50 = cps50 * kTar
rDose100 = cps100 * kTar

valAtt50 = (rDose50 / kGamma) * (0.5 ** 2) if kGamma > 0 else 0.0
valAtt100 = (rDose100 / kGamma) if kGamma > 0 else 0.0

if st.button("CALCOLA RISULTATI", type="primary"):
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

# 1. Generazione della curva teorica (da 2 a 100 cm per una migliore resa visiva dell'asse Y)
x_teorico = list(range(2, 101))
y_teorico = [rDose100 * (100 / x)**2 for x in x_teorico]
df_teorica = pd.DataFrame({"Distanza (cm)": x_teorico, "Rateo di Dose (nSv/h)": y_teorico})

# Creazione del grafico a linee per la teoria (colore Blu)
linea_teorica = alt.Chart(df_teorica).mark_line(color="#1f77b4", strokeWidth=2.5).encode(
    x=alt.X("Distanza (cm):Q", scale=alt.Scale(domain=[0, 100])),
    y="Rateo di Dose (nSv/h):Q"
)

# 2. Generazione della serie dei soli punti misurati a distanze fisse (escluso contatto)
distanze_reali = []
dosi_reali = []

if cps50 > 0:
    distanze_reali.append(50)
    dosi_reali.append(rDose50)
if cps100 > 0:
    distanze_reali.append(100)
    dosi_reali.append(rDose100)

df_misure = pd.DataFrame({"Distanza (cm)": distanze_reali, "Rateo di Dose (nSv/h)": dosi_reali})

# Creazione dei punti grafici per le misure (Cerchi Arancioni Grandi)
punti_misurati = alt.Chart(df_misure).mark_circle(size=140, color="#ff7f0e", opacity=1.0).encode(
    x="Distanza (cm):Q",
    y="Rateo di Dose (nSv/h):Q",
    tooltip=["Distanza (cm)", "Rateo di Dose (nSv/h)"] # Mostra i valori esatti al passaggio del mouse
)

# 3. Sovrapposizione dei due grafici nello stesso riquadro
grafico_finale = alt.layer(linea_teorica, punti_misurati).interactive()

# 4. Rendering su Streamlit
st.altair_chart(grafico_finale, use_container_width=True)
