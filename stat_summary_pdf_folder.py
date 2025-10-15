import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from PyPDF2 import PdfReader
import plotly.graph_objs as go

st.title("PDF Folder: X-Maximum and Y-Maximum Statistical Summary")

folder_path = st.text_input("Enter the full path to your PDF folder:")
query = st.text_input("Optional: Search/filter for MP number (e.g. 'MP-012') or leave blank for all:")
metric = st.radio("Select metric to analyze", ["X-Maximum", "Y-Maximum"])

if st.button("Run Analysis") and folder_path:
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf") and ("MP-" in f)]
    if query.strip():
        pdf_files = [f for f in pdf_files if query.strip().upper() in f.upper()]
    pdf_files = sorted(pdf_files)

    if metric == "X-Maximum":
        pattern = r"X-Maximum[:=]?\s*([-+]?\d*\.?\d+)"
        unit = "mm"
    else:
        pattern = r"Y-Maximum[:=]?\s*([-+]?\d*\.?\d+)"
        unit = "N"

    results = []
    for fname in pdf_files:
        try:
            pdf_path = os.path.join(folder_path, fname)
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                results.append({"file": fname, "value": val})
        except Exception as e:
            pass

    if not results:
        st.error(f"No valid {metric} values found in PDFs.")
    else:
        df = pd.DataFrame(results)
        st.write(f"**Files processed:** {len(df)}")
        st.dataframe(df)

        values = df["value"].values
        mean_val = np.mean(values)
        min_val = np.min(values)
        max_val = np.max(values)
        std_val = np.std(values, ddof=1)
        var_val = np.var(values, ddof=1)

        col1, col2 = st.columns(2)
        with col1:
            USL = st.number_input(f"Upper Specification Limit (USL) [{unit}]", value=float(max_val))
        with col2:
            LSL = st.number_input(f"Lower Specification Limit (LSL) [{unit}]", value=float(min_val))

        if std_val > 0:
            Cp = (USL - LSL) / (6 * std_val)
            Cpu = (USL - mean_val) / (3 * std_val)
            Cpl = (mean_val - LSL) / (3 * std_val)
            Cpk = min(Cpu, Cpl)
        else:
            Cp = np.nan
            Cpk = np.nan

        stats_df = pd.DataFrame(
            {
                "Mean": [mean_val],
                "Min": [min_val],
                "Max": [max_val],
                "Standard Deviation": [std_val],
                "Variance": [var_val],
                "Cp": [Cp],
                "Cpk": [Cpk],
            }
        ).T.rename(columns={0: metric})

        st.subheader("Statistical Summary")
        st.dataframe(stats_df)

        st.subheader("Line Graph of Selected Metric (Hover to see value)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(df)+1)),
            y=df["value"],
            mode='lines+markers',
            text=df["file"],
            hovertemplate='Index: %{x}<br>Value: %{y}<br>File: %{text}<extra></extra>',
            name=metric
        ))
        fig.update_layout(
            xaxis_title="Sample Index",
            yaxis_title=f"{metric} [{unit}]",
            hovermode="closest"
        )
        st.plotly_chart(fig, use_container_width=True)