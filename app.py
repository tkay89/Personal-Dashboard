import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

st.set_page_config(page_title="Fiber Network Intelligence", layout="wide")

st.title("📡 Fiber Network Maintenance Intelligence")

HISTORY_FILE = "case_history.csv"


# ---------------------------
# LOAD HISTORY SNAPSHOTS
# ---------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()


def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)


# ---------------------------
# CLEAN SALESFORCE EXPORT
# ---------------------------
def load_salesforce_file(file):

    if file.name.endswith(".csv"):
        raw = pd.read_csv(file, header=None, dtype=str)
    else:
        raw = pd.read_excel(file, header=None, dtype=str)

    header_row = None
    for i, row in raw.iterrows():
        if row.astype(str).str.contains("Case Number").any():
            header_row = i
            break

    if header_row is None:
        st.error("Couldn't detect Case Number header.")
        st.stop()

    if file.name.endswith(".csv"):
        df = pd.read_csv(file, skiprows=header_row)
    else:
        df = pd.read_excel(file, skiprows=header_row)

    # Remove totals/subtotals
    if "Case Number" in df.columns:
        df = df[
            ~df["Case Number"]
            .astype(str)
            .str.contains("Total|Sum", case=False, na=False)
        ]

    return df.reset_index(drop=True)


# ---------------------------
# PARSE NETWORK HIERARCHY
# ---------------------------
def parse_block_name(df):

    if "Block Name" in df.columns:

        parts = df["Block Name"].astype(str).str.split("-", expand=True)

        if parts.shape[1] >= 5:
            df["Zone"] = parts[1] + "-" + parts[2]
            df["AG"] = parts[3]
            df["Block"] = parts[4]

    return df


# ---------------------------
# DETECT REPEAT INFRASTRUCTURE FAULTS
# ---------------------------
def detect_repeat_faults(history):

    if history.empty:
        return pd.DataFrame()

    required = ["Zone", "AG", "Block"]

    if not all(col in history.columns for col in required):
        return pd.DataFrame()

    repeat = (
        history.groupby(required)
        .size()
        .reset_index(name="Occurrences")
        .sort_values("Occurrences", ascending=False)
    )

    return repeat[repeat["Occurrences"] > 2]


# ---------------------------
# TABS
# ---------------------------
tabs = st.tabs([
    "📊 Operations Overview",
    "📁 Upload Snapshot",
    "📈 History & Reports"
])


# ---------------------------
# UPLOAD TAB
# ---------------------------
with tabs[1]:

    st.header("Upload Salesforce Snapshot")

    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

    if file:

        new_df = load_salesforce_file(file)
        new_df = parse_block_name(new_df)

        # Snapshot timestamp
        new_df["Snapshot Time"] = datetime.now()

        history_df = load_history()

        combined = pd.concat([history_df, new_df])

        save_history(combined)

        st.success(
            f"{len(new_df)} cases added. "
            f"{len(combined)} total historical records."
        )


# ---------------------------
# OVERVIEW TAB
# ---------------------------
with tabs[0]:

    st.header("Network Operations Snapshot")

    df = load_history()

    if df.empty:
        st.info("Upload reports to start building intelligence.")
    else:

        # KPIs
        col1, col2, col3 = st.columns(3)

        col1.metric("Historical Records", len(df))

        if "Zone" in df.columns:
            col2.metric("Zones Covered", df["Zone"].nunique())

        if "AG" in df.columns:
            col3.metric("AG Coverage", df["AG"].nunique())

        st.divider()

        # Zone clustering
        if "Zone" in df.columns:
            st.subheader("Fault Clustering by Zone")
            st.bar_chart(df["Zone"].value_counts())

        # Repeat faults
        repeats = detect_repeat_faults(df)

        if not repeats.empty:
            st.subheader("⚠️ Repeat Infrastructure Faults")
            st.dataframe(repeats)


# ---------------------------
# HISTORY TAB
# ---------------------------
with tabs[2]:

    st.header("Historical Data Explorer")

    df = load_history()

    if df.empty:
        st.warning("No historical data yet.")
    else:

        # Filter by zone
        if "Zone" in df.columns:
            zone = st.selectbox(
                "Filter by Zone",
                ["All"] + sorted(df["Zone"].dropna().unique())
            )

            if zone != "All":
                df = df[df["Zone"] == zone]

        st.dataframe(df)

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "Download Historical Dataset",
            buffer,
            "fiber_history.xlsx"
        )
