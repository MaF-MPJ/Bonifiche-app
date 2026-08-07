import streamlit as st
import math
from datetime import datetime
import pandas as pd
import numpy as np
import altair as alt
import io
import urllib.parse

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://github.com">
        <link rel="icon" sizes="192x192" href="https://github.com">
    </head>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="Radioprotezione App", page_icon="☢️", layout="centered")
st.title("☢️ Bonifiche MPJ")

# Elenchi strumentazione e tecnici
detectors = ["RE-55916", "RE-53065", "RE-53154", "RE-53049", "RE-55049", "RE-54722", "RE-56510", "RE-52083PD", "T98-3822", "T98-3914", "T98-8043", "Default"]
taratura = [0.577, 0.631, 0.613, 0.609, 0.588, 0.598, 0.667, 0.514, 0.612, 0.523, 0.523, 0.602]

# Lista dei tecnici (puoi modificare i nomi all'interno di questo array)
tecnici = ["Andrea Colli", "Andrea Giliberto", "Davide Concion", "Stefano Bignolini", "Altro / Operatore"]

radionuclidi = ["I-131", "I-123", "Tc-99m", "Lu-177", "Lu-177m", "Ra-226", "NORM", "Th-232+", "K-40", "Cs-137", "Co-60", "Kr-85", "In-111", "Ir-192"]
costanteGamma = [77.0, 74.8, 33.2, 7.64, 211.0, 258.0, 316.0, 864.0, 22.2, 104.0, 373.0, 0.426, 136.0, 161.0]
tDimezzamento = [8.02, 0.551, 0.25, 6.65, 160.0, 584000.0, 1.63e12, 5.12e12, 4.56e11, 11000.0, 19200.0, 3920.0, 2.81, 73.8]

# IDENTIFICAZIONE INTERVENTO
st.subheader("📋 Dati Identificativi Intervento")
num_anomalia = st.text_input("Numero Anomalia", placeholder="Es. A:18/26")
sel_tecnico = st.selectbox("Tecnico Operatore:", tecnici)
targa_veicolo = st.text_input("Targa Veicolo:", placeholder="Es. AA123BB").upper()
desc_reperto = st.text_area("Descrizione Reperto Rilevato:", placeholder="Descrivere brevemente la tipologia e la collocazione del materiale...")

st.subheader("⚙️ Configurazione Parametri")
sel_det = st.selectbox("Seleziona Detector:", detectors)
sel_rad = st.selectbox("Seleziona Radionuclide:", radionuclidi)

idx_det = detectors.index(sel_det)
idx_rad = radionuclidi.index(sel_rad)

kTar = taratura[idx_det]
kGamma = costanteGamma[idx_rad]
emivita_giorni = tDimezzamento[idx_rad]
tDim = emivita_giorni * 24 * 3600

data_bonifica = st.date_input("Data bonifica:", datetime.now())

st.subheader("Inserimento Misure (cps)")
col1, col2 = st.columns(2)
with col1:
    cps_fondo_locale = st.number_input("Fondo naturale locale (cps)", min_value=0.0, step=1.0)
    cps_fondo_parete = st.number_input("Fondo di riferimento - [valore medio a parete] (cps)", min_value=0.0, step=1.0)
with col2:
    cps_max_parete = st.number_input("Valore max a parete (cps)", min_value=0.0, step=1.0)
    cps_cabina = st.number_input("Cabina conducente (cps)", min_value=0.0, step=1.0)

st.subheader("Inserimento Misure Reperto (cps)")
cps0 = st.number_input("cps a contatto:", min_value=0.0, value=0.0)
cps50 = st.number_input("cps a 50 cm:", min_value=0.0, value=0.0)
cps100 = st.number_input("cps a 1m:", min_value=0.0, value=0.0)

dose_fondo_locale = cps_fondo_locale * kTar
dose_fondo_parete = cps_fondo_parete * kTar
dose_max_parete = cps_max_parete * kTar
dose_cabina = cps_cabina * kTar
rDose0 = cps0 * kTar
rDose50 = cps50 * kTar
rDose100 = cps100 * kTar

valAtt50 = (rDose50 / kGamma) * (0.5 ** 2) if kGamma > 0 else 0.0
valAtt100 = (rDose100 / kGamma) if kGamma > 0 else 0.0

dStart_ts = datetime.combine(data_bonifica, datetime.min.time()).timestamp()
date50 = "N/D"
date100 = "N/D"

if emivita_giorni > 3650:
    if valAtt50 > 0: date50 = "Non applicabile (emivita > 10 anni)"
    if valAtt100 > 0: date100 = "Non applicabile (emivita > 10 anni)"
else:
    if valAtt50 > 0:
        outData50 = (tDim / math.log(2)) * math.log(valAtt50 * 1e3)
        date50 = datetime.fromtimestamp(dStart_ts + outData50).strftime("%d/%m/%Y")
    if valAtt100 > 0:
        outData100 = (tDim / math.log(2)) * math.log(valAtt100 * 1e3)
        date100 = datetime.fromtimestamp(dStart_ts + outData100).strftime("%d/%m/%Y")

if st.button("CALCOLA RISULTATI", type="primary"):
    st.subheader(f"📋 Report Anomalia N°: {num_anomalia}")
    st.success("### 📊 Risultati Rateo di Dose")
    st.write(f"**Fondo locale:** {dose_fondo_locale:.2f} nSv/h")
    st.write(f"**Fondo di riferimento:** {dose_fondo_parete:.2f} nSv/h")
    st.write(f"**Valore max a parete:** {dose_max_parete:.2f} nSv/h")
    st.write(f"**Rateo di dose cabina conducente:** {dose_cabina:.2f} nSv/h")
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
st.subheader("📄 Esportazione Report")

def genera_pdf_bytes(file_immagine_png="logo_MULTIPROJECT_NEW+CARSO-3cm.png"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
        title="Report Radioprotezione"
    )
    
    styles = getSampleStyleSheet()
    stile_titolo = ParagraphStyle('TitoloPDF', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor("#1f77b4"), alignment=1)
    stile_sottotitolo = ParagraphStyle('SubPDF', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, alignment=1)
    stile_sezione = ParagraphStyle('SezPDF', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor("#2c3e50"), spaceBefore=15, spaceAfter=8)
    stile_testo = ParagraphStyle('TestoPDF', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.HexColor("#333333"))
    stile_tabella_header = ParagraphStyle('TabHead', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.white, fontName="Helvetica-Bold")
    stile_tabella_testo = ParagraphStyle('TabTxt', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.HexColor("#333333"))

    elementi = []
    
    # --- Gestione Intestazione con Logo Verticale ---
    titolo_testo = f"<b>REPORT DI RADIOPROTEZIONE</b><br/><font size=14 color='#2c3e50'>Anomalia N° {num_anomalia}</font>" if num_anomalia else "<b>REPORT DI RADIOPROTEZIONE</b>"
    p_titolo = Paragraph(titolo_testo, stile_titolo)
    p_data = Paragraph(f"Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", stile_sottotitolo)
    
    # Blocco unico per i testi del titolo
    blocco_titolo = [p_titolo, Spacer(1, 5), p_data]

    if file_immagine_png is not None:
        try:
            # Dimensioni ottimizzate per mantenere le proporzioni verticali del logo
            logo = Image(file_immagine_png, width=70, height=105)
            
            # Creiamo una tabella a due colonne: a sinistra il logo, a destra il titolo
            # Larghezza totale disponibile ~530 (70 logo + 20 spazio + 440 titolo)
            tabella_header = Table([[logo, blocco_titolo]], colWidths=[70, 460])
            tabella_header.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,0), 'CENTER'), # Centra il testo del titolo nella sua colonna
                ('LEFTPADDING', (1,0), (1,0), 15),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            elementi.append(tabella_header)
        except Exception as e:
            elementi.append(Paragraph(f"<i>[Errore caricamento logo: {str(e)}]</i>", stile_sottotitolo))
            elementi.append(p_titolo)
            elementi.append(p_data)
    else:
        # Fallback se non viene caricata nessuna immagine
        elementi.append(p_titolo)
        elementi.append(p_data)
        
    elementi.append(Spacer(1, 20))
    
    # Da qui in poi il codice della "Sezione 1" rimane identico...
    
    # Sezione 1: Dati descrittivi dell'intervento
    elementi.append(Paragraph("<b>1. Dati Intervento e Configurazione Parametri</b>", stile_sezione))
    targa_output = targa_veicolo if targa_veicolo else "N/D"
    desc_output = desc_reperto if desc_reperto else "Nessuna descrizione inserita."
    
    info_parametri = (
        f"<b>Operatore Tecnico:</b> {sel_tecnico}<br/>"
        f"<b>Targa Veicolo Bonificato:</b> {targa_output}<br/>"
        f"<b>Descrizione Reperto:</b> {desc_output}<br/><br/>"
        f"<b>Detector Selezionato:</b> {sel_det} (Fattore Taratura kTar: {kTar})<br/>"
        f"<b>Radionuclide Selezionato:</b> {sel_rad} (Costante Gamma: {kGamma}, Dimezzamento: {tDimezzamento[idx_rad]} giorni)<br/>"
        f"<b>Data di riferimento bonifica:</b> {data_bonifica.strftime('%d/%m/%Y')}"
    )
    elementi.append(Paragraph(info_parametri, stile_testo))
    elementi.append(Spacer(1, 10))
    
    # Sezione 2: Risultati e Misure (Fondi e Reperto uniti cronologicamente)
    elementi.append(Paragraph("<b>2. Risultati Rateo di Dose</b>", stile_sezione))
    intestazioni = [Paragraph("<b>Posizione Misura</b>", stile_tabella_header), 
                    Paragraph("<b>Valore Inserito (cps)</b>", stile_tabella_header), 
                    Paragraph("<b>Rateo di Dose (nSv/h)</b>", stile_tabella_header)]
    
    # Array dati tabella aggiornato con le nuove 4 misure iniziali richieste
    dati_tabella = [
        intestazioni,
        [Paragraph("Fondo naturale locale", stile_tabella_testo), Paragraph(f"{cps_fondo_locale:.1f}", stile_tabella_testo), Paragraph(f"{dose_fondo_locale:.2f}", stile_tabella_testo)],
        [Paragraph("Fondo di riferimento (medio a parete)", stile_tabella_testo), Paragraph(f"{cps_fondo_parete:.1f}", stile_tabella_testo), Paragraph(f"{dose_fondo_parete:.2f}", stile_tabella_testo)],
        [Paragraph("Valore max a parete", stile_tabella_testo), Paragraph(f"{cps_max_parete:.1f}", stile_tabella_testo), Paragraph(f"{dose_max_parete:.2f}", stile_tabella_testo)],
        [Paragraph("Cabina conducente", stile_tabella_testo), Paragraph(f"{cps_cabina:.1f}", stile_tabella_testo), Paragraph(f"{dose_cabina:.2f}", stile_tabella_testo)],
        [Paragraph("A contatto (1 cm)", stile_tabella_testo), Paragraph(f"{cps0:.1f}", stile_tabella_testo), Paragraph(f"{rDose0:.2f}", stile_tabella_testo)],
        [Paragraph("A 50 cm", stile_tabella_testo), Paragraph(f"{cps50:.1f}", stile_tabella_testo), Paragraph(f"{rDose50:.2f}", stile_tabella_testo)],
        [Paragraph("A 1 metro", stile_tabella_testo), Paragraph(f"{cps100:.1f}", stile_tabella_testo), Paragraph(f"{rDose100:.2f}", stile_tabella_testo)]
    ]
    
    t = Table(dati_tabella, colWidths=[200, 160, 170])
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
    
    # Sezione 3: Analisi e Stime di Smaltimento
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
    
    elementi.append(Paragraph("___________________________<br/><i>Firma: L'Esperto di Radioprotezione</i>", stile_testo))
    
    elementi.append(Spacer(1, 30))
    elementi.append(Paragraph("<font size=8 color=gray>.</font>", stile_sottotitolo))
    
    doc.build(elementi)
    buffer.seek(0)
    return buffer.getvalue()


pdf_data = genera_pdf_bytes()
st.download_button(
    label="📥 Scarica Report PDF Stampabile",
    data=pdf_data,
    file_name=f"Report_Radioprotezione_{datetime.now().strftime('%Y%m%d')}.pdf",
    mime="application/pdf",
    type="primary",
    use_container_width=True
)

st.caption(
    "💡 **Nota operativa:** Una volta scaricato, puoi inviare il file PDF "
    "su **WhatsApp** aprendo la chat desiderata, toccando l'icona dell'allegato "
    "(la graffetta o il tasto +) e selezionando il documento dalla cartella Download."
)
