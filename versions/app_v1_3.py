import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Sistem Informasi Pasang Surut Sulawesi Utara")
st.subheader("Peringatan Dini Banjir Pesisir (PD ROB) - v1.3")

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
# 🎚 Threshold
# ===============================
threshold = st.number_input("Set Ambang ROB (meter)", value=0.8)

# ===============================
# 🚀 Tombol Generate
# ===============================
if st.button("Generate Analisis"):

    if df_filtered.empty:
        st.warning("Tidak ada data pada rentang tanggal ini.")
    else:

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
        # 🔍 Deteksi ROB Kontinu
        # ===============================
        df_filtered["is_rob"] = df_filtered["elev_m"] >= threshold
        df_filtered["rob_group"] = (
            df_filtered["is_rob"] != df_filtered["is_rob"].shift()
        ).cumsum()

        rob_periods = df_filtered[df_filtered["is_rob"]]

        if rob_periods.empty:
            st.success("Tidak ada kejadian ROB pada periode ini.")
        else:

            durasi = (
                rob_periods.groupby("rob_group")
                .agg(
                    mulai=("datetime", "min"),
                    selesai=("datetime", "max"),
                    durasi_jam=("datetime", "count")
                )
                .reset_index(drop=True)
            )

            # ===============================
            # 🚦 Kategori Risiko
            # ===============================
            def kategori_risiko(durasi):
                if durasi <= 2:
                    return "Rendah"
                elif durasi <= 5:
                    return "Sedang"
                else:
                    return "Tinggi"

            durasi["kategori_risiko"] = durasi["durasi_jam"].apply(kategori_risiko)

            # Format waktu
            durasi["mulai"] = durasi["mulai"].dt.strftime("%d-%m-%Y %H:%M")
            durasi["selesai"] = durasi["selesai"].dt.strftime("%d-%m-%Y %H:%M")

            st.subheader("📋 Tabel Kejadian ROB")
            st.dataframe(durasi)

            # ===============================
            # 📥 Download Button
            # ===============================
            csv = durasi.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="⬇ Download Tabel ROB",
                data=csv,
                file_name=f"rob_{kota}.csv",
                mime="text/csv"
            )
