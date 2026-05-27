import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import time

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Radioactive Water Contamination Detector", layout="wide")

# ================= CUSTOM CSS =================
css_block = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

* {
  font-family: 'Bebas Neue', sans-serif !important;
}

html, body, [class*="css"] {
  background-color: #0a0a0a;
  color: #e8f5e9;
  min-height: 100vh;
}

/* Title & Subtitle */
h1.app-title {
  text-align: center;
  color: #FFD300;
  font-size: 52px;
  margin-bottom: 4px;
  text-shadow: 0 0 10px #FFD300, 0 0 28px #FF7518;
}
p.app-sub {
  text-align: center;
  color: #39FF14;
  margin-top: 0;
  font-size: 20px;
  text-shadow: 0 0 10px #39FF14;
}

/* Tabs */
.stTabs [role="tablist"] button {
    background: #101010 !important;
    color: #39FF14 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(57,255,20,0.3) !important;
    margin-right: 6px !important;
    padding: 8px 14px !important;
    transition: all .18s ease;
    font-size: 16px !important;
}
.stTabs [role="tablist"] button:hover {
    background: #39FF14 !important;
    color: black !important;
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 0 18px rgba(57,255,20,0.15);
}
.stTabs [role="tablist"] button[aria-selected="true"] {
    background: linear-gradient(90deg, #FFD300, #FF7518) !important;
    color: black !important;
    border: 1px solid #FFD300 !important;
    box-shadow: 0 0 26px rgba(255,211,0,0.35);
}
</style>
"""
st.markdown(css_block, unsafe_allow_html=True)

# ================= FUNCTIONS =================
def predict_contamination(ph, tds, hardness, nitrate):
    score = 0
    if ph < 6.5 or ph > 8.5: score += 30
    if tds > 500: score += 25
    if hardness > 200: score += 20
    if nitrate > 45: score += 25
    return score

# ================= UI =================
st.markdown("<h1 class='app-title'>💧☢️ Radioactive Water Contamination Detector</h1>", unsafe_allow_html=True)
st.markdown("<p class='app-sub'>AI/ML Powered Water Safety | Developed by Karthikeyan</p>", unsafe_allow_html=True)

tabs = st.tabs(["🔬 Contamination Check", "📊 Safety Meter", "⚠️ Radioactive Awareness"])

# ---- TAB 1 ----
with tabs[0]:
    st.subheader("🔍 Enter Water Parameters")

    ph = st.number_input("pH Level", 0.0, 14.0, 7.0)
    tds = st.number_input("TDS (mg/L)", 0.0, 2000.0, 300.0)
    hardness = st.number_input("Hardness (mg/L)", 0.0, 1000.0, 150.0)
    nitrate = st.number_input("Nitrate (mg/L)", 0.0, 500.0, 20.0)
    location = st.text_input("📍 Location")

    if st.button("Run Analysis"):
        score = predict_contamination(ph, tds, hardness, nitrate)

        if score < 30:
            result = '✅ Safe: No significant radioactive contamination detected.'
        elif score < 60:
            result = '⚠️ Moderate Risk: Some radioactive traces possible.'
        else:
            result = '☢️ High Risk: Potential radioactive contamination detected!'

        st.markdown(f"<p style='font-size:20px; color:#FFD300;'>{result}</p>", unsafe_allow_html=True)

        # ----------------- Animated Gauge -----------------
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=0,
            title={'text': "Radioactive Risk %"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "red" if score >= 60 else "orange" if score >= 30 else "#39FF14"},
                'steps': [
                    {'range': [0, 30], 'color': "#39FF14"},
                    {'range': [30, 60], 'color': "yellow"},
                    {'range': [60, 100], 'color': "red"}
                ],
            }
        ))
        gauge_placeholder = st.empty()

        # Animate the needle smoothly
        for i in range(0, int(score)+1, 2):
            fig.update_traces(value=i)
            gauge_placeholder.plotly_chart(fig, use_container_width=True)
            time.sleep(0.02)

        # ----------------- Save Dataset -----------------
        new_data = pd.DataFrame([[location, ph, tds, hardness, nitrate, score]],
                                columns=["Location", "pH", "TDS", "Hardness", "Nitrate", "RiskScore"])
        if os.path.exists("water_data.csv"):
            old_data = pd.read_csv("water_data.csv")
            df = pd.concat([old_data, new_data], ignore_index=True)
        else:
            df = new_data
        df.to_csv("water_data.csv", index=False)

        st.success("Data saved successfully ✅")
        st.download_button("📥 Download Dataset", data=df.to_csv(index=False),
                           file_name="water_data.csv", mime="text/csv")

# ---- TAB 2 ----
with tabs[1]:
    st.subheader("📊 Safe vs Unsafe Water Levels (Mini Dashboard)")

    safe_ranges = {
        "pH": (6.5, 8.5, ph),
        "TDS (mg/L)": (0, 500, tds),
        "Hardness (mg/L)": (0, 200, hardness),
        "Nitrate (mg/L)": (0, 45, nitrate)
    }

    params = list(safe_ranges.items())

    # Display 2 parameters per row
    for i in range(0, len(params), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(params):
                break
            param, (low, high, value) = params[i + j]

            with col:
                subcols = st.columns([1.1, 1.0, 0.7])  # Graph + value + status

                # Small Bar Graph
                with subcols[0]:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=[param],
                        y=[value],
                        name=f"{param} Value",
                        marker_color="red" if value < low or value > high else "#39FF14"
                    ))
                    # Safe range overlay
                    fig.add_shape(
                        type="rect",
                        x0=-0.5, x1=0.5,
                        y0=low, y1=high,
                        fillcolor="rgba(57,255,20,0.2)",
                        line_width=0
                    )
                    fig.update_layout(
                        title=f"{param} Level",
                        barmode="overlay",
                        height=180, width=180,
                        margin=dict(l=10, r=10, t=30, b=10)
                    )
                    st.plotly_chart(fig, use_container_width=False)

                # Display Value
                with subcols[1]:
                    st.markdown(
                        f"""
                        <div style="font-size:16px; color:#FFD300;">
                        <b>{param}</b><br>
                        Safe Range: {low} – {high}<br>
                        Your Value: <span style="color:{'red' if value < low or value > high else '#39FF14'};">{value}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Parameter Status
                with subcols[2]:
                    status = "✅ Safe" if low <= value <= high else "⚠️ Unsafe"
                    color = "#39FF14" if low <= value <= high else "red"
                    st.markdown(
                        f"<div style='font-size:18px; color:{color};'><b>{status}</b></div>",
                        unsafe_allow_html=True
                    )

    st.info("ℹ️ Compare your water parameters above with the WHO safe ranges.")

# ---- TAB 3 ----
with tabs[2]:
    st.subheader("⚠️ Dangers of Radioactive Water")
    st.image("radioactive_process.png", caption="Radioactive Contamination Process", use_container_width=True)

    sections = [
        {
            "title": "☢️ Health Risks",
            "title_color": "#FFD700",
            "content": [
                ('Cancer: Long-term exposure to radioactive elements can increase cancer risk.', "https://ensia.com/features/radioactive-contamination-drinking-water-radium-radon-uranium/?utm_source=chatgpt.com"),
                ('Organ Damage: Kidney and liver dysfunction may occur.', "https://pmc.ncbi.nlm.nih.gov/articles/PMC3261972/?utm_source=chatgpt.com"),
                ('Genetic Mutations: Can affect future generations.', "https://link.springer.com/chapter/10.1007/978-3-031-89591-3_10?utm_source=chatgpt.com")
            ]
        },
        {
            "title": "🌍 Environmental Impact",
            "title_color": "#FFD700",
            "content": [
                ('Bioaccumulation: Radioactive isotopes accumulate in plants & animals.', "https://ensia.com/features/radioactive-contamination-drinking-water-radium-radon-uranium/?utm_source=chatgpt.com"),
                ('Ecosystem Disruption: Contaminated water affects biodiversity.', None)
            ]
        },
        {
            "title": "🛡️ WHO Guidelines",
            "title_color": "#FFD700",
            "content": [
                ('WHO Guidelines for Drinking-water Quality', "https://apps.who.int/iris/bitstream/handle/10665/44584/9789241548151_eng.pdf?utm_source=chatgpt.com"),
                ('Chapter 9: Radiological Aspects', "https://cdn.who.int/media/docs/default-source/wash-documents/water-safety-and-quality/dwq-guidelines-4/gdwq4-with-add1-chap9.pdf?sfvrsn=6fc78cae_3&utm_source=chatgpt.com")
            ]
        },
        {
            "title": "📚 Further Reading",
            "title_color": "#FFD700",
            "content": [
                ('Health Effects of Naturally Radioactive Water Ingestion', "https://pmc.ncbi.nlm.nih.gov/articles/PMC3261972/?utm_source=chatgpt.com"),
                ('Radioactive Contaminants in Drinking Water and Their Health Effects', "https://www.ncbi.nlm.nih.gov/books/NBK234160/?utm_source=chatgpt.com")
            ]
        }
    ]

    for sec in sections:
        html_content = f'<div style="background-color:#111111; padding:15px; border-radius:12px; margin-bottom:10px;">'
        html_content += f'<h4 style="color:{sec["title_color"]};">{sec["title"]}</h4><ul style="color:#f0f0f0;">'
        for text, link in sec["content"]:
            if link:
                html_content += f'<li>{text} <a href="{link}" target="_blank" style="color:#00FF7F;">[Read More]</a></li>'
            else:
                html_content += f'<li>{text}</li>'
        html_content += '</ul></div>'
        st.markdown(html_content, unsafe_allow_html=True)

    st.info("ℹ️ Stay informed and take action to ensure safe drinking water.")

# Footer
st.markdown("---")
st.markdown('<p style="text-align:center; color:#FFD300;">👨‍💻 Developed by Karthikeyan</p>', unsafe_allow_html=True)

