import streamlit as st
import pandas as pd
import plotly.express as px

st.write("Developed by: Lydia Monika & Ricky Daniel Aror")

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

# Threshold
threshold = st.number_input("Set Ambang ROB (meter)", value=0.8)

# Plot
fig = px.line(df_filtered, x="datetime", y="elev_m",
              title=f"Grafik Pasut - {kota}")

fig.add_hline(y=threshold, line_color="red")

st.plotly_chart(fig)

# ===============================
# 📊 STATISTIK TAMBAHAN (v1.1)
# ===============================

if not df_filtered.empty:

    st.subheader("📊 Informasi Statistik")

    max_elev = df_filtered["elev_m"].max()
    waktu_max = df_filtered.loc[df_filtered["elev_m"].idxmax(), "datetime"]
    jumlah_jam = (df_filtered["elev_m"] >= threshold).sum()

col1, col2 = st.columns(2)

with col1:
    st.metric("Elevasi Maksimum (m)", f"{max_elev:.2f}")
    st.metric("Jam ≥ Ambang", int(jumlah_jam))

with col2:
    st.metric("Waktu Maksimum",
              waktu_max.strftime("%d-%m-%Y %H:%M"))
  
# ===============================
# 🚨 Peringatan
# ===============================

if (df_filtered["elev_m"] >= threshold).any():
    st.error("⚠ POTENSI ROB TERDETEKSI")
else:
    st.success("Kondisi Aman")
