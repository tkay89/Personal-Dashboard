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


def clean_salesforce_export(df):

    df = df.dropna(how="all")

    junk = ["open cases", "filtered by", "units:"]
    df = df[
        ~df.astype(str).apply(
            lambda r: any(j in str(r).lower() for j in junk),
            axis=1
        )
    ]

    return df.reset_index(drop=True)


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

        df = clean_salesforce_export(df)

        date_col = find_column(df, ["date"])
        case_col = find_column(df, ["case"])
        address_col = find_column(df, ["premises", "address"])

        # Sort latest first
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.sort_values(date_col, ascending=False)

        # Remove duplicate ticket numbers BEFORE saving
        if case_col:
            df = df.drop_duplicates(subset=case_col)

        # Save to history
        if os.path.exists(HISTORY_FILE):
            history = pd.read_csv(HISTORY_FILE)
            history = pd.concat([history, df], ignore_index=True)
        else:
            history = df.copy()

        # Remove duplicates globally
        if case_col:
            history = history.drop_duplicates(subset=case_col)

        history.to_csv(HISTORY_FILE, index=False)

        st.success(f"{len(df)} new cases added.")

        st.dataframe(df, use_container_width=True)


# ----------------------------
# OVERVIEW TAB
# ----------------------------

with overview_tab:

    if os.path.exists(HISTORY_FILE):

        history = pd.read_csv(HISTORY_FILE)

        zone_col = find_column(history, ["fiberhood", "zone"])
        address_col = find_column(history, ["premises", "address"])
        case_col = find_column(history, ["case"])

        # Zone filter
        if zone_col:
            zones = ["All"] + sorted(history[zone_col].dropna().unique())
            selected_zone = st.selectbox("Filter Zone", zones)

            if selected_zone != "All":
                history = history[history[zone_col] == selected_zone]

        # Zone chart
        if zone_col:
            st.subheader("Cases per Zone")
            st.bar_chart(history[zone_col].value_counts())

        # TRUE repeat detection:
        # Same premises, DIFFERENT ticket numbers
        if address_col and case_col:

            st.subheader("Repeat Premises (New Tickets Same Address)")

            history["clean_address"] = normalize_address(history[address_col])

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
                    f"⚠️ Highest repeat premises: {worst['Premises']} "
                    f"({worst['Ticket Count']} different tickets)"
                )

    else:
        st.info("Upload data first.")


# ----------------------------
# HISTORY TAB
# ----------------------------

with history_tab:

    if os.path.exists(HISTORY_FILE):

        history = pd.read_csv(HISTORY_FILE)

        st.subheader("Accumulated Ticket History")

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
        st.info("No history yet.")
