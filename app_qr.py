# app_qr.py — QR Generator Pro — versione Streamlit
import streamlit as st
import re
import io
import tempfile
import os

from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm

st.set_page_config(
    page_title="QR Generator Pro",
    page_icon="📦",
    layout="centered",
)

st.markdown("""
<style>
    .main { background-color: #ffffff; }
    .kpi-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .kpi-val { font-size: 2rem; font-weight: 700; color: #007bff; margin: 0; }
    .kpi-lbl { font-size: 0.82rem; color: #6c757d; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📦 QR Generator Pro")
st.markdown("Carica un PDF Runsheet, estrae i codici LDV e genera un foglio QR pronto per la stampa.")
st.markdown("---")


def estrai_codici(pdf_bytes: bytes) -> list[str]:
    """Estrae codici alfanumerici >= 13 caratteri dal PDF."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    found = []
    for page in reader.pages:
        text = page.extract_text() or ""
        matches = re.findall(r'[A-Z0-9]{13,}', text)
        for m in matches:
            clean = m.strip()
            if clean not in found:
                found.append(clean)
    return found


def genera_pdf_qr(codes: list[str]) -> bytes:
    """Genera un PDF A4 con griglia di QR code (3 colonne)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    margin  = 15 * mm
    cols    = 3
    cell_w  = (w - 2 * margin) / cols
    cell_h  = 48 * mm

    x = margin
    y = h - margin - cell_h

    for code in codes:
        qr_widget = qr.QrCodeWidget(code)
        b      = qr_widget.getBounds()
        q_size = 33 * mm

        d = Drawing(
            q_size, q_size,
            transform=[q_size / (b[2] - b[0]), 0, 0, q_size / (b[3] - b[1]), 0, 0]
        )
        d.add(qr_widget)

        renderPDF.draw(d, c, x + (cell_w - q_size) / 2, y + 10 * mm)

        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + cell_w / 2, y + 4 * mm, code)

        x += cell_w
        if x >= w - margin:
            x = margin
            y -= cell_h

        if y < margin:
            c.showPage()
            x, y = margin, h - margin - cell_h

    c.save()
    return buf.getvalue()


# ── STEP 1 — CARICA PDF ──────────────────────────────────────
st.markdown("### 1️⃣ Carica PDF Runsheet")
uploaded = st.file_uploader("Seleziona il file PDF", type=["pdf"])

if uploaded:
    with st.spinner("Estrazione codici in corso..."):
        try:
            codici = estrai_codici(uploaded.read())
        except Exception as e:
            st.error(f"Errore nella lettura del PDF: {e}")
            st.stop()

    if not codici:
        st.warning("⚠️ Nessun codice alfanumerico (≥13 caratteri) trovato nel PDF.")
        st.stop()

    # KPI
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="kpi-box"><p class="kpi-val">{len(codici)}</p>'
            f'<p class="kpi-lbl">Codici LDV trovati</p></div>',
            unsafe_allow_html=True
        )
    with c2:
        pagine = -(-len(codici) // (3 * 6))  # ceil: 3 col x 6 righe = 18 per pagina
        st.markdown(
            f'<div class="kpi-box"><p class="kpi-val">{pagine}</p>'
            f'<p class="kpi-lbl">Pagine QR stimate</p></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Anteprima codici
    with st.expander(f"👁 Anteprima codici estratti ({len(codici)})", expanded=False):
        cols = st.columns(3)
        for i, code in enumerate(codici):
            cols[i % 3].code(code)

    st.markdown("---")

    # ── STEP 2 — GENERA E SCARICA ──────────────────────────────
    st.markdown("### 2️⃣ Genera PDF con QR Code")

    if st.button("⚡ Genera PDF QR", type="primary", use_container_width=True):
        with st.spinner("Generazione PDF in corso..."):
            try:
                pdf_bytes = genera_pdf_qr(codici)
                st.success(f"✅ PDF generato con {len(codici)} QR code!")
                st.download_button(
                    label="⬇️ Scarica PDF QR",
                    data=pdf_bytes,
                    file_name="qr_runsheet.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Errore nella generazione del PDF: {e}")
else:
    st.info("👆 Carica un PDF Runsheet per iniziare.")
