import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Personal Command Center", layout="wide")

st.title("📊 Personal Command Center Dashboard")

HISTORY_FILE = "case_history.csv"


# -----------------------------
# SMART FILE CLEANING FUNCTION
# -----------------------------
def clean_salesforce_export(df):
    # Drop completely empty rows
    df = df.dropna(how="all")

    # Remove Salesforce header junk rows automatically
    df = df[df.astype(str).apply(
        lambda row: row.str.contains("Open Cases|Filtered By|Units:", case=False).any(),
        axis=1
    ) == False]

    # Reset index
    df = df.reset_index(drop=True)

    return df


# -----------------------------
# COLUMN DETECTION FUNCTION
# -----------------------------
def find_column(df, keywords):
    for col in df.columns:
        for word in keywords:
            if word.lower() in col.lower():
                return col
    return None


# -----------------------------
# UPLOAD SECTION
# -----------------------------
uploaded_file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df = clean_salesforce_export(df)

    # Detect important columns dynamically
    zone_col = find_column(df, ["fiberhood", "zone"])
    block_col = find_column(df, ["block"])
    address_col = find_column(df, ["premises", "address"])
    status_col = find_column(df, ["status"])
    date_col = find_column(df, ["date"])

    # Sort latest first if date exists
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


# -----------------------------
# LOAD HISTORY FOR ANALYTICS
# -----------------------------
if os.path.exists(HISTORY_FILE):

    st.divider()
    st.header("📈 Operations Overview")

    history = pd.read_csv(HISTORY_FILE)

    zone_col = find_column(history, ["fiberhood", "zone"])
    block_col = find_column(history, ["block"])
    address_col = find_column(history, ["premises", "address"])

    # Zone filter
    if zone_col:
        zones = ["All"] + sorted(history[zone_col].dropna().unique())
        selected_zone = st.selectbox("Filter by Zone", zones)

        if selected_zone != "All":
            history = history[history[zone_col] == selected_zone]

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        if zone_col:
            st.subheader("Cases per Zone")
            st.bar_chart(history[zone_col].value_counts())

    with col2:
        if block_col:
            st.subheader("Cases per Block")
            st.bar_chart(history[block_col].value_counts().head(15))

    # Repeat address detection
    if address_col:
        st.subheader("Repeat Fault Locations")

        repeat_df = (
            history[address_col]
            .value_counts()
            .reset_index()
        )
        repeat_df.columns = ["Address", "Tickets"]

        repeat_df = repeat_df[repeat_df["Tickets"] > 1]

        st.dataframe(repeat_df, use_container_width=True)

        if not repeat_df.empty:
            worst = repeat_df.iloc[0]
            st.info(
                f"⚠️ Most repeated fault area: {worst['Address']} "
                f"({worst['Tickets']} tickets logged)"
            )

    # Export cleaned report
    buffer = io.BytesIO()
    history.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "⬇ Download Full Clean Report",
        data=buffer,
        file_name="network_history.xlsx"
    )
