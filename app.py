import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Fiber Maintenance Dashboard", layout="wide")

st.title("📡 Fiber Maintenance Intelligence Dashboard")

# ---------------------------
# AUTO HEADER DETECTION
# ---------------------------
def load_salesforce_file(file):

    # Load raw without assuming headers
    if file.name.endswith(".csv"):
        raw = pd.read_csv(file, header=None)
    else:
        raw = pd.read_excel(file, header=None)

    header_row = None

    # Detect header row by known Salesforce column names
    keywords = ["Case Number", "Block Name", "Case Status", "Date/Time Opened"]

    for i, row in raw.iterrows():
        if any(k in str(cell) for cell in row for k in keywords):
            header_row = i
            break

    if header_row is None:
        st.error("Could not detect header row.")
        st.stop()

    # Reload properly with detected header
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, skiprows=header_row)
    else:
        df = pd.read_excel(file, skiprows=header_row)

    return df


# ---------------------------
# BLOCK NAME PARSING
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
    "📁 Upload Data",
    "📈 Reports",
    "📝 Tasks"
])


# ---------------------------
# UPLOAD TAB
# ---------------------------
with tabs[1]:

    st.header("Upload Salesforce Export")

    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

    if file:

        df = load_salesforce_file(file)
        df = parse_block_name(df)

        st.session_state["data"] = df

        st.success("File loaded, cleaned and parsed.")
        st.dataframe(df.head(20))


# ---------------------------
# OVERVIEW TAB
# ---------------------------
with tabs[0]:

    st.header("Network Overview")

    if "data" not in st.session_state:
        st.info("Upload data first.")
    else:
        df = st.session_state["data"]

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Tickets", len(df))

        if "Zone" in df.columns:
            col2.metric("Zones Impacted", df["Zone"].nunique())

        if "AG" in df.columns:
            col3.metric("AGs Impacted", df["AG"].nunique())

        st.divider()

        if "Zone" in df.columns:
            st.subheader("Tickets per Zone")
            st.bar_chart(df["Zone"].value_counts())

        if "AG" in df.columns:
            st.subheader("Top AG Hotspots")
            st.bar_chart(df["AG"].value_counts().head(10))

        if "Block" in df.columns:
            st.subheader("Top Blocks")
            st.bar_chart(df["Block"].value_counts().head(10))


# ---------------------------
# REPORTS TAB
# ---------------------------
with tabs[2]:

    st.header("Custom Reports")

    if "data" not in st.session_state:
        st.warning("Upload data first.")
    else:
        df = st.session_state["data"]

        cols = st.multiselect(
            "Select columns",
            df.columns.tolist(),
            default=df.columns.tolist()
        )

        filtered_df = df[cols]
        st.dataframe(filtered_df)

        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="📥 Download Excel Report",
            data=buffer,
            file_name=f"report_{datetime.now().strftime('%Y%m%d')}.xlsx",
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
