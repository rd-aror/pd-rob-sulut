import streamlit as st
import pandas as pd
import plotly.express as px

st.write("APP BERJALAN")

st.title("Sistem Informasi Pasang Surut Sulawesi Utara")
st.subheader("Peringatan Dini Banjir Pesisir (PD ROB)")

# Load data
df = pd.read_csv("pasut_sulut_clean.csv", parse_dates=["datetime"])

# Dropdown pilih kota
kota = st.selectbox("Pilih Kota/Kabupaten", df["kota"].unique())

df_kota = df[df["kota"] == kota]

# Pilih rentang tanggal
start_date = st.date_input("Tanggal Mulai", df_kota["datetime"].min())
end_date = st.date_input("Tanggal Akhir", df_kota["datetime"].max())

mask = (df_kota["datetime"].dt.date >= start_date) & (df_kota["datetime"].dt.date <= end_date)
df_filtered = df_kota[mask]

# Threshold sederhana (sementara sama semua kota)
threshold = st.number_input("Set Ambang ROB (meter)", value=0.8)

# Plot
fig = px.line(df_filtered, x="datetime", y="elev_m", title=f"Grafik Pasut - {kota}")

fig.add_hline(y=threshold, line_color="red")

st.plotly_chart(fig)

# Peringatan
if (df_filtered["elev_m"] >= threshold).any():
    st.error("⚠ POTENSI ROB TERDETEKSI")
else:
    st.success("Kondisi Aman")
