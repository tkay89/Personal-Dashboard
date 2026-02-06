import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Fiber Maintenance Dashboard", layout="wide")

st.title("📡 Fiber Maintenance Intelligence Dashboard")

# ---------------------------
# Helper Function
# ---------------------------
def parse_block_name(df):
    """
    Parses Block Name like:
    VR-PHX-25-AG1-B012
    Into Zone / AG / Block columns.
    """
    if "Block Name" in df.columns:
        parts = df["Block Name"].astype(str).str.split("-", expand=True)

        if parts.shape[1] >= 5:
            df["Zone"] = parts[1] + "-" + parts[2]
            df["AG"] = parts[3]
            df["Block"] = parts[4]

    return df


# ---------------------------
# Tabs Layout
# ---------------------------
tabs = st.tabs([
    "📊 Overview",
    "📁 Upload Data",
    "📈 Reports",
    "📝 Tasks"
])

# ---------------------------
# TAB 1: Upload
# ---------------------------
with tabs[1]:
    st.header("Upload Salesforce Export")

    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

    if file:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df = parse_block_name(df)

        st.session_state["data"] = df

        st.success("File loaded and parsed.")
        st.dataframe(df.head(20))


# ---------------------------
# TAB 0: Overview
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
# TAB 2: Reports
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

        # Excel export
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
# TAB 3: Tasks
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
