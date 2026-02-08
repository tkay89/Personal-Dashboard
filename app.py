import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Personal Command Center", layout="wide")

st.title("📊 Personal Command Center Dashboard")

HISTORY_FILE = "case_history.csv"


# ----------------------------
# HELPERS
# ----------------------------

def find_column(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None


def normalize_address(series):
    return (
        series.astype(str)
        .str.lower()
        .str.replace(",", " ")
        .str.replace("  ", " ")
        .str.strip()
    )


# ----------------------------
# TABS
# ----------------------------

overview_tab, upload_tab, history_tab = st.tabs(
    ["📊 Overview", "📂 Upload", "📜 History"]
)


# ----------------------------
# UPLOAD TAB
# ----------------------------

with upload_tab:

    uploaded_file = st.file_uploader(
        "Upload Salesforce export",
        type=["csv", "xlsx"]
    )

    if uploaded_file:

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        case_col = find_column(df, ["case"])
        date_col = find_column(df, ["date"])

        # Sort newest first
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.sort_values(date_col, ascending=False)

        # Load existing history
        if os.path.exists(HISTORY_FILE):
            history = pd.read_csv(HISTORY_FILE)
        else:
            history = pd.DataFrame()

        before = len(history)

        # Merge new data
        history = pd.concat([history, df], ignore_index=True)

        if case_col:
            history = history.drop_duplicates(subset=case_col)

        history.to_csv(HISTORY_FILE, index=False)

        added = len(history) - before

        st.success(f"✅ {added} new tickets saved to history.")

        if added == 0:
            st.warning(
                "No new tickets detected (probably already uploaded earlier)."
            )

        st.dataframe(df.head(20), use_container_width=True)


# ----------------------------
# OVERVIEW TAB
# ----------------------------

with overview_tab:

    if os.path.exists(HISTORY_FILE):

        history = pd.read_csv(HISTORY_FILE)

        zone_col = find_column(history, ["fiberhood", "zone"])
        address_col = find_column(history, ["premises", "address"])
        case_col = find_column(history, ["case"])

        if zone_col:
            st.subheader("Cases per Zone")
            st.bar_chart(history[zone_col].value_counts())

        # Repeat premises detection
        if address_col and case_col:

            st.subheader("Repeat Premises")

            history["clean_address"] = normalize_address(
                history[address_col]
            )

            repeat = (
                history.groupby("clean_address")[case_col]
                .nunique()
                .reset_index()
            )

            repeat.columns = ["Premises", "Ticket Count"]
            repeat = repeat[repeat["Ticket Count"] > 1]

            st.dataframe(repeat, use_container_width=True)

            if not repeat.empty:
                worst = repeat.sort_values(
                    "Ticket Count", ascending=False
                ).iloc[0]

                st.warning(
                    f"⚠️ Most repeated premises: {worst['Premises']} "
                    f"({worst['Ticket Count']} tickets)"
                )

    else:
        st.info("Upload a file first.")


# ----------------------------
# HISTORY TAB
# ----------------------------

with history_tab:

    if os.path.exists(HISTORY_FILE):

        history = pd.read_csv(HISTORY_FILE)

        st.subheader("Ticket History")

        st.dataframe(history, use_container_width=True)

        buffer = io.BytesIO()
        history.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "⬇ Download Full History",
            buffer,
            "network_history.xlsx"
        )

    else:
        st.info("No history saved yet.")
