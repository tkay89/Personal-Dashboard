import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Fiber Maintenance Intelligence", layout="wide")

st.title("📡 Fiber Maintenance Intelligence Dashboard")

# ---------------------------
# SMART SALESFORCE FILE LOADER
# ---------------------------
def load_salesforce_file(file):

    # Load raw first (no headers)
    if file.name.endswith(".csv"):
        raw = pd.read_csv(file, header=None)
    else:
        raw = pd.read_excel(file, header=None)

    # Detect header row reliably
    keywords = ["Case Number", "Block Name", "Case Status", "Total Days Open"]

    header_row = None
    for i, row in raw.iterrows():
        if sum(any(k in str(cell) for k in keywords) for cell in row) >= 2:
            header_row = i
            break

    if header_row is None:
        st.error("Could not detect header row.")
        st.stop()

    # Reload clean dataframe
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, skiprows=header_row)
    else:
        df = pd.read_excel(file, skiprows=header_row)

    return df


# ---------------------------
# PARSE BLOCK NAME → Zone/AG/Block
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
# TABS
# ---------------------------
tabs = st.tabs([
    "📊 Overview",
    "📁 Upload",
    "📈 Reports",
    "📝 Tasks"
])


# ---------------------------
# UPLOAD TAB
# ---------------------------
with tabs[1]:

    st.header("Upload Salesforce Export")

    file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

    if file:
        df = load_salesforce_file(file)
        df = parse_block_name(df)

        st.session_state["data"] = df

        st.success("File loaded and cleaned.")
        st.dataframe(df.head(15))


# ---------------------------
# OVERVIEW TAB (MAIN INTELLIGENCE)
# ---------------------------
with tabs[0]:

    st.header("Network Health Overview")

    if "data" not in st.session_state:
        st.info("Upload a Salesforce export first.")
    else:
        df = st.session_state["data"]

        # --- Snapshot KPIs ---
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Tickets", len(df))

        if "Zone" in df.columns:
            col2.metric("Zones Impacted", df["Zone"].nunique())

        if "AG" in df.columns:
            col3.metric("AGs Impacted", df["AG"].nunique())

        if "Total Days Open" in df.columns:
            aging = df[df["Total Days Open"] > 3]
            col4.metric("Aging Tickets (>3 days)", len(aging))

        st.divider()

        # --- CLUSTER DETECTION ---
        if "Zone" in df.columns:
            st.subheader("🚨 Zone Hotspots")
            zone_counts = df["Zone"].value_counts()
            st.bar_chart(zone_counts)

        if "AG" in df.columns:
            st.subheader("🚨 AG Hotspots")
            ag_counts = df["AG"].value_counts()
            st.bar_chart(ag_counts.head(10))

        if "Block" in df.columns:
            st.subheader("🚨 Block Concentration")
            block_counts = df["Block"].value_counts()
            st.bar_chart(block_counts.head(10))

        # --- AUTO RISK FLAGS ---
        st.subheader("⚠️ High Risk Indicators")

        risk_notes = []

        if "Total Days Open" in df.columns:
            if (df["Total Days Open"] > 5).any():
                risk_notes.append("Aging tickets detected (>5 days).")

        if "AG" in df.columns:
            if df["AG"].value_counts().max() > 5:
                risk_notes.append("High AG concentration detected.")

        if "Zone" in df.columns:
            if df["Zone"].value_counts().max() > 8:
                risk_notes.append("Zone experiencing heavy ticket volume.")

        if risk_notes:
            for note in risk_notes:
                st.warning(note)
        else:
            st.success("Network appears stable.")


# ---------------------------
# REPORTS TAB
# ---------------------------
with tabs[2]:

    st.header("Custom Reports")

    if "data" not in st.session_state:
        st.warning("Upload data first.")
    else:
        df = st.session_state["data"]

        # Select important columns first
        default_cols = [
            c for c in df.columns
            if c in ["Case Number", "Zone", "AG", "Block", "Case Status", "Total Days Open"]
        ]

        cols = st.multiselect(
            "Select columns to view",
            df.columns.tolist(),
            default=default_cols
        )

        filtered_df = df[cols]
        st.dataframe(filtered_df)

        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "📥 Download Excel Report",
            buffer,
            f"report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ---------------------------
# TASKS TAB
# ---------------------------
with tabs[3]:

    st.header("Tasks / Reminders")

    if "tasks" not in st.session_state:
        st.session_state["tasks"] = []

    with st.form("task_form"):
        task = st.text_input("Task")
        due = st.date_input("Due Date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        submit = st.form_submit_button("Add Task")

        if submit and task:
            st.session_state["tasks"].append({
                "Task": task,
                "Due": due,
                "Priority": priority
            })

    if st.session_state["tasks"]:
        st.dataframe(pd.DataFrame(st.session_state["tasks"]))
