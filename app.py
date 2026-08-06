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

# --- CALCOLI FISSI (Eseguiti sempre per popolare grafico e PDF in tempo reale) ---
rDose0 = cps0 * kTar
rDose50 = cps50 * kTar
rDose100 = cps100 * kTar

valAtt50 = (rDose50 / kGamma) * (0.5 ** 2) if kGamma > 0 else 0.0
valAtt100 = (rDose100 / kGamma) if kGamma > 0 else 0.0

# Calcolo preventivo delle date per evitare NameError nel PDF
dStart_ts = datetime.combine(data_bonifica, datetime.min.time()).timestamp()
date50 = "N/D"
date100 = "N/D"

if valAtt50 > 0:
    outData50 = (tDim / math.log(2)) * math.log(valAtt50 * 1e3)
    date50 = datetime.fromtimestamp(dStart_ts + outData50).strftime("%d/%m/%Y")

if valAtt100 > 0:
    outData100 = (tDim / math.log(2)) * math.log(valAtt100 * 1e3)
    date100 = datetime.fromtimestamp(dStart_ts + outData100).strftime("%d/%m/%Y")


if st.button("CALCOLA RISULTATI", type="primary"):
    # OUTPUT DATI
    st.success("### 📊 Risultati Rateo di Dose")
    st.write(f"**Rateo di dose a contatto:** {rDose0:.2f} nSv/h")
    st.write(f"**Rateo di dose a 50 cm:** {rDose50:.2f} nSv/h")
    st.write(f"**Rateo di dose a 1 metro:** {rDose100:.2f} nSv/h")
    
    st.info("### 📉 Stime di Smaltimento")
    
    if valAtt50 > 0:
        st.write(f"**Attività (stima a 50 cm):** {valAtt50:.4g} MBq")
        st.write(f"📅 **Data prevista smaltimento (50 cm):** {date50}")
    else:
        st.write("**Stima a 50 cm:** Attività non calcolabile (inserire cps > 0)")
        
    st.markdown("---")
    
    if valAtt100 > 0:
        st.write(f"**Attività (stima a 1 m):** {valAtt100:.4g} MBq")
        st.write(f"📅 **Data prevista smaltimento (1 m):** {date100}")
    else:
        st.write("**Stima a 1 m:** Attività non calcolabile (inserire cps > 0)")

# --- GRAFICO INTERATTIVO AGGIORNATO ---
st.subheader("📈 Andamento Spaziale del Rateo di Dose")

tipo_scala = st.radio(
    "Seleziona scala asse verticale (Y):",
    options=["Lineare", "Logaritmica"],
    index=0,
    horizontal=True
)
scale_type = "linear" if tipo_scala == "Lineare" else "log"

x_teorico = list(range(2, 101))
y_teorico = [rDose100 * (100 / x)**2 for x in x_teorico]
df_teorica = pd.DataFrame({"Distanza (cm)": x_teorico, "Rateo di Dose (nSv/h)": y_teorico})

linea_teorica = alt.Chart(df_teorica).mark_line(color="#1f77b4", strokeWidth=2.5).encode(
    x=alt.X("Distanza (cm):Q"),
    y=alt.Y("Rateo di Dose (nSv/h):Q", scale=alt.Scale(type=scale_type))
)

distanze_reali = []
dosi_reali = []
if cps50 > 0:
    distanze_reali.append(50)
    dosi_reali.append(rDose50)
if cps100 > 0:
    distanze_reali.append(100)
    dosi_reali.append(rDose100)

df_misure = pd.DataFrame({"Distanza (cm)": distanze_reali, "Rateo di Dose (nSv/h)": dosi_reali})

punti_misurati = alt.Chart(df_misure).mark_circle(size=140, color="#ff7f0e", opacity=1.0).encode(
    x="Distanza (cm):Q",
    y=alt.Y("Rateo di Dose (nSv/h):Q", scale=alt.Scale(type=scale_type)),
    tooltip=["Distanza (cm)", "Rateo di Dose (nSv/h)"]
)

grafico_finale = alt.layer(linea_teorica, punti_misurati).interactive()
st.altair_chart(grafico_finale, use_container_width=True)

# --- TABELLA DI SCOSTAMENTO PERCENTUALE ---
if cps50 > 0 and cps100 > 0:
    st.subheader("📊 Analisi di Coerenza della Misura")
    dose_teorica_50 = rDose100 * (100 / 50)**2
    scostamento_perc = ((rDose50 - dose_teorica_50) / dose_teorica_50) * 100
    
    dati_confronto = {
        "Parametro a 50 cm": [
            "Rateo di Dose Misurato (nSv/h)", 
            "Rateo di Dose Teorico Atteso (nSv/h)", 
            "Scostamento Percentuale (%)"
        ],
        "Valore": [
            f"{rDose50:.2f}",
            f"{dose_teorica_50:.2f}",
            f"{scostamento_perc:+.1f}%"
        ]
    }
    df_confronto = pd.DataFrame(dati_confronto)
    st.table(df_confronto)
    
    if abs(scostamento_perc) <= 10:
        st.success("✅ **Ottima coerenza fisica**: Lo scostamento è inferiore al 10%. La sorgente si comporta come un punto geometrico ideale.")
    elif abs(scostamento_perc) <= 25:
        st.warning("⚠️ **Scostamento moderato**: Differenza tra il 10% e il 25%. Verificare la geometria di misura o possibili radiazioni diffuse.")
    else:
        st.error("🚨 **Scostamento elevato**: Differenza superiore al 25%. Possibile presenza di schermature parziali, sorgente estesa o errore strumentale.")

# --- SEZIONE GENERAZIONE REPORT PDF & WHATSAPP ---
st.subheader("📄 Esportazione e Condivisione")

def genera_pdf_bytes():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
        title="Report Radioprotezione"
    )
    
    styles = getSampleStyleSheet()
    stile_titolo = ParagraphStyle('TitoloPDF', parent=styles['Heading1'], fontSize=22, leading=26, textColor=colors.HexColor("#1f77b4"), alignment=1)
    stile_sottotitolo = ParagraphStyle('SubPDF', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, alignment=1)
    stile_sezione = ParagraphStyle('SezPDF', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor("#2c3e50"), spaceBefore=15, spaceAfter=8)
    stile_testo = ParagraphStyle('TestoPDF', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.HexColor("#333333"))
    stile_tabella_header = ParagraphStyle('TabHead', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.white, fontName="Helvetica-Bold")
    stile_tabella_testo = ParagraphStyle('TabTxt', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.HexColor("#333333"))

    elementi = []
    elementi.append(Paragraph("<b>REPORT DI RADIOPROTEZIONE</b>", stile_titolo))
    elementi.append(Paragraph(f"Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", stile_sottotitolo))
    elementi.append(Spacer(1, 15))
    
    elementi.append(Paragraph("<b>1. Configurazione Parametri</b>", stile_sezione))
    info_parametri = (
        f"<b>Detector Selezionato:</b> {sel_det} (Fattore Taratura kTar: {kTar})<br/>"
        f"<b>Radionuclide Selezionato:</b> {sel_rad} (Costante Gamma: {kGamma}, Dimezzamento: {tDimezzamento[idx_rad]} giorni)<br/>"
        f"<b>Data di riferimento bonifica:</b> {data_bonifica.strftime('%d/%m/%Y')}"
    )
    elementi.append(Paragraph(info_parametri, stile_testo))
    elementi.append(Spacer(1, 10))
    
    elementi.append(Paragraph("<b>2. Risultati Rateo di Dose</b>", stile_sezione))
    intestazioni = [Paragraph("<b>Posizione Misura</b>", stile_tabella_header), 
                    Paragraph("<b>Valore Inserito (cps)</b>", stile_tabella_header), 
                    Paragraph("<b>Rateo di Dose (nSv/h)</b>", stile_tabella_header)]
    
    riga0 = [Paragraph("A contatto (1 cm)", stile_tabella_testo), Paragraph(f"{cps0:.1f}", stile_tabella_testo), Paragraph(f"{rDose0:.2f}", stile_tabella_testo)]
    riga50 = [Paragraph("A 50 cm", stile_tabella_testo), Paragraph(f"{cps50:.1f}", stile_tabella_testo), Paragraph(f"{rDose50:.2f}", stile_tabella_testo)]
    riga100 = [Paragraph("A 1 metro", stile_tabella_testo), Paragraph(f"{cps100:.1f}", stile_tabella_testo), Paragraph(f"{rDose100:.2f}", stile_tabella_testo)]
    
    dati_tabella = [intestazioni, riga0, riga50, riga100]
    t = Table(dati_tabella, colWidths=[150, 150, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1f77b4")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9f9f9")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elementi.append(t)
    elementi.append(Spacer(1, 15))
    
    elementi.append(Paragraph("<b>3. Analisi e Stime di Smaltimento</b>", stile_sezione))
    testo_smaltimento = ""
    if valAtt50 > 0:
        testo_smaltimento += f"• <b>Stima a 50 cm:</b> Attività calcolata pari a <b>{valAtt50:.4g} MBq</b>. Data prevista per il conferimento/smaltimento: <b>{date50}</b>.<br/>"
    else:
        testo_smaltimento += "• <b>Stima a 50 cm:</b> Attività non calcolabile (misure assenti o pari a zero).<br/>"
        
    if valAtt100 > 0:
        testo_smaltimento += f"• <b>Stima a 1 metro:</b> Attività calcolata pari a <b>{valAtt100:.4g} MBq</b>. Data prevista per il conferimento/smaltimento: <b>{date100}</b>.<br/>"
    else:
        testo_smaltimento += "• <b>Stima a 1 metro:</b> Attività non calcolabile (misure assenti o pari a zero).<br/>"
        
    if cps50 > 0 and cps100 > 0:
        dose_teorica_50 = rDose100 * (100 / 50)**2
        scostamento_perc = ((rDose50 - dose_teorica_50) / dose_teorica_50) * 100
        testo_smaltimento += f"<br/>• <b>Coerenza della misura:</b> Lo scostamento geometrico calcolato a 50 cm rispetto alla legge dell'inverso del quadrato è pari a <b>{scostamento_perc:+.1f}%</b>.<br/>"
        
    elementi.append(Paragraph(testo_smaltimento, stile_testo))
    elementi.append(Spacer(1, 40))
    elementi.append(Paragraph("___________________________<br/><i>Firma dell'Operatore Esperto</i>", stile_testo))
    
    elementi.append(Spacer(1, 30))
    elementi.append(Paragraph("<font size=8 color=gray>This is for informational purposes only. For medical advice or diagnosis, consult a professional. AI responses may include mistakes.</font>", stile_sottotitolo))
    
    doc.build(elementi)
    buffer.seek(0)
    return buffer.getvalue()

col_pdf, col_wa = st.columns(2)

with col_pdf:
    import io # Assicura che io sia disponibile
    pdf_data = genera_pdf_bytes()
    st.download_button(
        label="📥 Scarica Report PDF",
        data=pdf_data,
        file_name=f"Report_Radioprotezione_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="secondary",
        use_container_width=True
    )

with col_wa:
    import urllib.parse
    testo_messaggio = (
        f"--- *REPORT RADIOPROTEZIONE* ---\n"
        f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}\n"
        f"🔬 Radionuclide: {sel_rad}\n"
        f"📈 Dose 1m: {rDose100:.2f} nSv/h\n"
        f"📈 Dose 50cm: {rDose50:.2f} nSv/h\n"
        f"📥 Scarica il PDF completo dall'applicazione."
    )
    testo_codificato = urllib.parse.quote(testo_messaggio)
    link_whatsapp = f"wa.me{testo_codificato}"
    
    st.link_button(
        label="💬 Condividi su WhatsApp",
        url=link_whatsapp,
        type="primary",
        use_container_width=True
    )
