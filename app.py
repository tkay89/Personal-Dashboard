import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

st.set_page_config(page_title="Fiber Ops Intelligence", layout="wide")
st.title("📡 Fiber Network Operations Intelligence")

HISTORY_FILE = "case_history.csv"


# ----------------------
# HISTORY HANDLING
# ----------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()


def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)


# ----------------------
# STREET EXTRACTION
# ----------------------
def extract_street(addr):
    if pd.isna(addr):
        return None

    parts = str(addr).split(",")
    if len(parts) > 0:
        street_part = parts[0]

        # Remove house number
        street_words = street_part.split(" ")[1:]
        return " ".join(street_words).strip()

    return addr


# ----------------------
# SALESFORCE LOADER
# ----------------------
def load_salesforce(file):

    raw = pd.read_excel(file, header=None)

    header_row = None
    for i, row in raw.iterrows():
        if row.astype(str).str.contains("Case Number").any():
            header_row = i
            break

    df = pd.read_excel(file, skiprows=header_row)

    df = df[
        ~df["Case Number"]
        .astype(str)
        .str.contains("Total|Sum", case=False, na=False)
    ]

    return df.reset_index(drop=True)


# ----------------------
# PARSE NETWORK STRUCTURE
# ----------------------
def parse_structure(df):

    if "Block Name" in df.columns:

        parts = df["Block Name"].astype(str).str.split("-", expand=True)

        if parts.shape[1] >= 5:
            df["ZoneParsed"] = parts[1]
            df["AG"] = parts[2]
            df["Block"] = parts[3]

    if "Premises" in df.columns:
        df["Street"] = df["Premises"].apply(extract_street)

    return df


# ----------------------
# TABS
# ----------------------
tab_overview, tab_upload, tab_history = st.tabs(
    ["📊 Operations Overview", "📁 Upload Snapshot", "📈 History"]
)


# ----------------------
# UPLOAD TAB
# ----------------------
with tab_upload:

    file = st.file_uploader("Upload Salesforce Export", type=["xlsx"])

    if file:

        df = load_salesforce(file)
        df = parse_structure(df)

        df["Snapshot Time"] = datetime.now()

        history = load_history()
        combined = pd.concat([history, df])

        save_history(combined)

        st.success("Snapshot saved successfully.")


# ----------------------
# OVERVIEW TAB
# ----------------------
with tab_overview:

    history = load_history()

    if history.empty:
        st.info("Upload a report to begin.")
    else:

        latest_time = history["Snapshot Time"].max()
        latest = history[history["Snapshot Time"] == latest_time]

        st.subheader("Latest Snapshot KPIs")

        col1, col2, col3 = st.columns(3)

        col1.metric("Active Cases", len(latest))

        if "Fiberhood Name" in latest.columns:
            col2.metric("Zones Active", latest["Fiberhood Name"].nunique())

        if "AG" in latest.columns:
            col3.metric("AGs Active", latest["AG"].nunique())

        st.divider()

        # Filtering hierarchy
        zone = st.selectbox(
            "Zone",
            ["All"] + sorted(latest["Fiberhood Name"].dropna().unique())
        )

        if zone != "All":
            latest = latest[latest["Fiberhood Name"] == zone]

        ag = st.selectbox(
            "AG",
            ["All"] + sorted(latest["AG"].dropna().unique())
        )

        if ag != "All":
            latest = latest[latest["AG"] == ag]

        block = st.selectbox(
            "Block",
            ["All"] + sorted(latest["Block"].dropna().unique())
        )

        if block != "All":
            latest = latest[latest["Block"] == block]

        street = st.selectbox(
            "Street",
            ["All"] + sorted(latest["Street"].dropna().unique())
        )

        if street != "All":
            latest = latest[latest["Street"] == street]

        st.dataframe(latest)

        # Repeat detection
        st.subheader("Repeat Fault Streets (Historical)")

        repeats = (
            history.groupby("Street")
            .size()
            .reset_index(name="Occurrences")
            .sort_values("Occurrences", ascending=False)
        )

        st.dataframe(repeats.head(10))


# ----------------------
# HISTORY TAB
# ----------------------
with tab_history:

    history = load_history()

    if history.empty:
        st.warning("No historical data yet.")
    else:

        st.dataframe(history)

        buffer = io.BytesIO()
        history.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "Download Full History",
            buffer,
            "fiber_history.xlsx"
        )
