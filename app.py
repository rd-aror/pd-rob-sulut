import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Coastal Flood Early Warning System",
    layout="wide"
)

st.title("North Sulawesi Tide Information System")
st.subheader("Coastal Flood Early Warning System (CF-EWS) v1.5")

st.caption("Developed by: Lydia Monika & Ricky Daniel Aror")

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv("pasut_sulut_clean.csv", parse_dates=["datetime"])
    df = df.sort_values("datetime")
    return df

@st.cache_data
def load_offset():
    offset_df = pd.read_csv("offset_datum_sulut.csv")
    return dict(zip(
        offset_df["kota"],
        offset_df["offset_msl_ke_lat_m"]
    ))

df = load_data()
offset_map = load_offset()

# ==========================================
# DATUM SELECTION
# ==========================================
datum = st.radio(
    "Select Vertical Datum",
    ["MSL (Mean Sea Level)", "LAT (Lowest Astronomical Tide - Estimated)"],
    horizontal=True
)

# ==========================================
# CITY SELECTION
# ==========================================
city = st.selectbox("Select Coastal Region", sorted(df["kota"].unique()))
df_city = df[df["kota"] == city].copy()

# ==========================================
# DATE RANGE
# ==========================================
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start Date",
        df_city["datetime"].min()
    )

with col2:
    end_date = st.date_input(
        "End Date",
        df_city["datetime"].max()
    )

mask = (
    (df_city["datetime"].dt.date >= start_date) &
    (df_city["datetime"].dt.date <= end_date)
)

df_filtered = df_city[mask].copy()
df_filtered = df_filtered.sort_values("datetime").reset_index(drop=True)

# ==========================================
# DATUM CORRECTION
# ==========================================
if "LAT" in datum:
    offset = offset_map.get(city, 0)
    df_filtered["elev_plot"] = df_filtered["elev_m"] - offset
    st.info(f"Using LAT datum | Offset applied for {city}: {offset:.3f} m")
else:
    df_filtered["elev_plot"] = df_filtered["elev_m"]

# ==========================================
# FLOOD THRESHOLD
# ==========================================
threshold = st.number_input(
    "Set Coastal Flood Threshold (meters)",
    value=0.8
)

# ==========================================
# ANALYSIS BUTTON
# ==========================================
if st.button("Generate Analysis"):

    if df_filtered.empty:
        st.warning("No data available for selected period.")
    else:

        # ==========================================
        # PLOT
        # ==========================================
        fig = px.line(
            df_filtered,
            x="datetime",
            y="elev_plot",
            title=f"Tidal Elevation - {city}"
        )

        fig.add_hline(
            y=threshold,
            line_color="red",
            annotation_text="Flood Threshold",
            annotation_position="top left"
        )

        st.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # INTERPOLATED FLOOD DETECTION
        # ==========================================
        events = []
        current_start = None

        for i in range(len(df_filtered) - 1):

            t1 = df_filtered.loc[i, "datetime"]
            t2 = df_filtered.loc[i + 1, "datetime"]
            y1 = df_filtered.loc[i, "elev_plot"]
            y2 = df_filtered.loc[i + 1, "elev_plot"]

            # Upward crossing
            if y1 < threshold and y2 >= threshold:
                if y2 != y1:
                    frac = (threshold - y1) / (y2 - y1)
                    current_start = t1 + frac * (t2 - t1)

            # Downward crossing
            if y1 >= threshold and y2 < threshold:
                if current_start is not None and y2 != y1:
                    frac = (threshold - y1) / (y2 - y1)
                    end_time = t1 + frac * (t2 - t1)

                    duration_hours = (
                        (end_time - current_start).total_seconds() / 3600
                    )

                    events.append({
                        "start_time": current_start,
                        "end_time": end_time,
                        "duration_hours": round(duration_hours, 2)
                    })

                    current_start = None

        # If flood continues until last record
        if current_start is not None:
            end_time = df_filtered.iloc[-1]["datetime"]
            duration_hours = (
                (end_time - current_start).total_seconds() / 3600
            )

            events.append({
                "start_time": current_start,
                "end_time": end_time,
                "duration_hours": round(duration_hours, 2)
            })

        # ==========================================
        # RESULTS TABLE
        # ==========================================
        if len(events) == 0:
            st.success("No coastal flood events detected.")
        else:
            results = pd.DataFrame(events)

            def risk_category(d):
                if d <= 2:
                    return "Low"
                elif d <= 5:
                    return "Moderate"
                else:
                    return "High"

            results["risk_level"] = results["duration_hours"].apply(risk_category)

            results["start_time"] = results["start_time"].dt.strftime("%d-%m-%Y %H:%M")
            results["end_time"] = results["end_time"].dt.strftime("%d-%m-%Y %H:%M")

            st.subheader("Detected Coastal Flood Events (Interpolated)")
            st.dataframe(results, use_container_width=True)

            csv = results.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Flood Event Table",
                data=csv,
                file_name=f"coastal_flood_{city}.csv",
                mime="text/csv"
            )

# ==========================================
# METHODOLOGY SECTION
# ==========================================
with st.expander("Methodology & Scientific Notes"):

    st.write("""
    • Tidal data are referenced to Mean Sea Level (MSL).

    • Estimated LAT datum is derived from minimum observed tidal elevation per station.

    • Coastal flood events are detected when tidal elevation exceeds
      a user-defined threshold.

    • Start and end times are determined using linear interpolation
      between consecutive measurements.

    • Risk level classification is based on flood duration.
    """)

    st.warning("""
    Note:
    LAT values in this system are estimated from historical minima and
    should be updated using harmonic tidal analysis for operational use.
    """)
