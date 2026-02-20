import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Sistem Informasi Pasang Surut Sulawesi Utara")
st.subheader("Peringatan Dini Banjir Pesisir (PD ROB) - v1.4")

st.write("Developed by: Lydia Monika & Ricky Daniel Aror")

# ===============================
# 📂 Load Data
# ===============================
df = pd.read_csv("pasut_sulut_clean.csv", parse_dates=["datetime"])
df = df.sort_values("datetime")

# ===============================
# 🏙 Pilih Kota
# ===============================
kota = st.selectbox("Pilih Kota/Kabupaten", df["kota"].unique())
df_kota = df[df["kota"] == kota].copy()

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
df_filtered = df_filtered.sort_values("datetime").reset_index(drop=True)

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
        # 🔬 INTERPOLASI ROB (v1.4)
        # ===============================

        events = []
        current_start = None

        for i in range(len(df_filtered) - 1):

            t1 = df_filtered.loc[i, "datetime"]
            t2 = df_filtered.loc[i + 1, "datetime"]
            y1 = df_filtered.loc[i, "elev_m"]
            y2 = df_filtered.loc[i + 1, "elev_m"]

            # Crossing naik (mulai ROB)
            if y1 < threshold and y2 >= threshold:
                if y2 != y1:  # hindari pembagian nol
                    frac = (threshold - y1) / (y2 - y1)
                    current_start = t1 + frac * (t2 - t1)

            # Crossing turun (selesai ROB)
            if y1 >= threshold and y2 < threshold:
                if current_start is not None and y2 != y1:
                    frac = (threshold - y1) / (y2 - y1)
                    end_time = t1 + frac * (t2 - t1)

                    durasi_jam = (
                        (end_time - current_start).total_seconds() / 3600
                    )

                    events.append({
                        "mulai": current_start,
                        "selesai": end_time,
                        "durasi_jam": round(durasi_jam, 2)
                    })

                    current_start = None

        # Jika ROB masih berlangsung sampai akhir data
        if current_start is not None:
            end_time = df_filtered.iloc[-1]["datetime"]
            durasi_jam = (
                (end_time - current_start).total_seconds() / 3600
            )

            events.append({
                "mulai": current_start,
                "selesai": end_time,
                "durasi_jam": round(durasi_jam, 2)
            })

        # ===============================
        # 📋 Tampilkan Hasil
        # ===============================
        if len(events) == 0:
            st.success("Tidak ada kejadian ROB pada periode ini.")
        else:

            hasil = pd.DataFrame(events)

            # ===============================
            # 🚦 Kategori Risiko
            # ===============================
            def kategori_risiko(d):
                if d <= 2:
                    return "Rendah"
                elif d <= 5:
                    return "Sedang"
                else:
                    return "Tinggi"

            hasil["kategori_risiko"] = hasil["durasi_jam"].apply(kategori_risiko)

            # Format tampilan waktu
            hasil["mulai"] = hasil["mulai"].dt.strftime("%d-%m-%Y %H:%M")
            hasil["selesai"] = hasil["selesai"].dt.strftime("%d-%m-%Y %H:%M")

            st.subheader("📋 Tabel Kejadian ROB (Interpolasi)")
            st.dataframe(hasil)

            # ===============================
            # 📥 Download Button
            # ===============================
            csv = hasil.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="⬇ Download Tabel ROB",
                data=csv,
                file_name=f"rob_interpolasi_{kota}.csv",
                mime="text/csv"
            )
