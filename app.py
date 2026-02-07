import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Personal Command Center", layout="wide")

st.title("📊 Personal Command Center Dashboard")

HISTORY_FILE = "case_history.csv"


# ----------------------------
# COLUMN DETECTION
# ----------------------------
def find_column(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None


# ----------------------------
# SALESFORCE CLEANING
# ----------------------------
def clean_salesforce_export(df):

    # Remove totally empty rows
    df = df.dropna(how="all")

    # Remove Salesforce header junk rows
    bad_words = ["open cases", "filtered by", "units:"]
    df = df[
        ~df.astype(str).apply(
            lambda row: any(word in str(row).lower() for word in bad_words),
            axis=1
        )
    ]

    df = df.reset_index(drop=True)
    return df


# ----------------------------
# NORMALIZE ADDRESS FUNCTION
# ----------------------------
def normalize_address(series):

    return (
        series.astype(str)
        .str.lower()
        .str.replace(",", " ")
        .str.replace("  ", " ")
        .str.strip()
    )


# ----------------------------
# FILE UPLOAD
# ----------------------------
uploaded_file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df = clean_salesforce_export(df)

    zone_col = find_column(df, ["fiberhood", "zone"])
    address_col = find_column(df, ["premises", "address"])
    date_col = find_column(df, ["date"])

    # Sort latest first
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col, ascending=False)

    # Save history
    if os.path.exists(HISTORY_FILE):
        history = pd.read_csv(HISTORY_FILE)
        history = pd.concat([history, df], ignore_index=True)
    else:
        history = df.copy()

    history.to_csv(HISTORY_FILE, index=False)

    st.success(f"{len(df)} cases loaded successfully.")

    st.subheader("Preview")
    st.dataframe(df, use_container_width=True)


# ----------------------------
# OPERATIONS OVERVIEW
# ----------------------------
if os.path.exists(HISTORY_FILE):

    st.divider()
    st.header("📈 Operations Overview")

    history = pd.read_csv(HISTORY_FILE)

    zone_col = find_column(history, ["fiberhood", "zone"])
    address_col = find_column(history, ["premises", "address"])

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

    # Repeat premises detection
    if address_col:

        st.subheader("Repeat Fault Locations")

        cleaned_addresses = normalize_address(history[address_col])

        repeat_df = (
            cleaned_addresses.value_counts()
            .reset_index()
        )

        repeat_df.columns = ["Premises", "Tickets"]

        repeat_df = repeat_df[repeat_df["Tickets"] > 1]

        st.dataframe(repeat_df, use_container_width=True)

        if not repeat_df.empty:
            worst = repeat_df.iloc[0]
            st.info(
                f"⚠️ Most repeated premises: {worst['Premises']} "
                f"({worst['Tickets']} tickets logged)"
            )

    # Download cleaned report
    buffer = io.BytesIO()
    history.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "⬇ Download Full Clean Report",
        data=buffer,
        file_name="network_history.xlsx"
    )
