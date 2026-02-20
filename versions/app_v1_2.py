import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Sistem Informasi Pasang Surut Sulawesi Utara")
st.subheader("Peringatan Dini Banjir Pesisir (PD ROB)")

st.write("Developed by: Lydia Monika & Ricky Daniel Aror")

# ===============================
# 📂 Load Data
# ===============================
df = pd.read_csv("pasut_sulut_clean.csv", parse_dates=["datetime"])

# ===============================
# 🏙 Pilih Kota
# ===============================
kota = st.selectbox("Pilih Kota/Kabupaten", df["kota"].unique())
df_kota = df[df["kota"] == kota]

# ===============================
# 📅 Pilih Rentang Tanggal
# ===============================
start_date = st.date_input("Tanggal Mulai", df_kota["datetime"].min())
end_date = st.date_input("Tanggal Akhir", df_kota["datetime"].max())

mask = (
    (df_kota["datetime"].dt.date >= start_date) &
    (df_kota["datetime"].dt.date <= end_date)
)

df_filtered = df_kota[mask].copy()

# ===============================
# 🎚 Threshold ROB
# ===============================
threshold = st.number_input("Set Ambang ROB (meter)", value=0.8)

# ===============================
# 📈 Plot Grafik
# ===============================
fig = px.line(
    df_filtered,
    x="datetime",
    y="elev_m",
    title=f"Grafik Pasut - {kota}"
)

fig.add_hline(y=threshold, line_color="red")

st.plotly_chart(fig)

# ===============================
# 📊 STATISTIK v1.1
# ===============================
if not df_filtered.empty:

    st.subheader("📊 Informasi Statistik")

    max_elev = df_filtered["elev_m"].max()
    waktu_max = df_filtered.loc[
        df_filtered["elev_m"].idxmax(), "datetime"
    ]
    jumlah_jam = (df_filtered["elev_m"] >= threshold).sum()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Elevasi Maksimum (m)", f"{max_elev:.2f}")
        st.metric("Jam ≥ Ambang", int(jumlah_jam))

    with col2:
        st.metric(
            "Waktu Maksimum",
            waktu_max.strftime("%d-%m-%Y %H:%M")
        )

    # ===============================
    # 🚀 v1.2 – Durasi ROB Kontinu
    # ===============================

    df_filtered["is_rob"] = df_filtered["elev_m"] >= threshold

    df_filtered["rob_group"] = (
        df_filtered["is_rob"] != df_filtered["is_rob"].shift()
    ).cumsum()

    rob_periods = df_filtered[df_filtered["is_rob"]]

    if not rob_periods.empty:

        durasi = (
            rob_periods.groupby("rob_group")
            .agg(
                mulai=("datetime", "min"),
                selesai=("datetime", "max"),
                jumlah_jam=("datetime", "count")
            )
            .reset_index(drop=True)
        )

        durasi_terpanjang = durasi.loc[
            durasi["jumlah_jam"].idxmax()
        ]

        st.subheader("⏱ Analisis Durasi ROB")

        col3, col4 = st.columns(2)

        with col3:
            st.metric("Jumlah Kejadian ROB", len(durasi))
            st.metric(
                "Durasi Terpanjang (jam)",
                int(durasi_terpanjang["jumlah_jam"])
            )

        with col4:
            st.write("**Mulai:**",
                     durasi_terpanjang["mulai"].strftime("%d-%m-%Y %H:%M"))
            st.write("**Selesai:**",
                     durasi_terpanjang["selesai"].strftime("%d-%m-%Y %H:%M"))

    else:
        st.success("Tidak ada kejadian ROB kontinu pada periode ini.")

# ===============================
# 🚨 Peringatan Global
# ===============================
if not df_filtered.empty:
    if (df_filtered["elev_m"] >= threshold).any():
        st.error("⚠ POTENSI ROB TERDETEKSI")
    else:
        st.success("Kondisi Aman")
else:
    st.warning("Tidak ada data pada rentang tanggal ini.")
