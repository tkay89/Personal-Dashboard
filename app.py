import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Fiber Maintenance Intelligence", layout="wide")

st.title("📡 Fiber Maintenance Intelligence Dashboard")


# ---------------------------
# FILE LOADER
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
        st.error("Header not found.")
        st.stop()

    if file.name.endswith(".csv"):
        df = pd.read_csv(file, skiprows=header_row)
    else:
        df = pd.read_excel(file, skiprows=header_row)

    if "Case Number" in df.columns:
        df = df[
            ~df["Case Number"]
            .astype(str)
            .str.contains("Total|Sum", case=False, na=False)
        ]

    return df.reset_index(drop=True)


# ---------------------------
# PARSE BLOCK NAME
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

        st.success(f"{len(df)} cases loaded.")
        st.dataframe(df.head(15))


# ---------------------------
# OVERVIEW TAB (DRILL DOWN)
# ---------------------------
with tabs[0]:

    st.header("Fault Location Hierarchy")

    if "data" not in st.session_state:
        st.info("Upload export first.")
    else:
        df = st.session_state["data"]

        # ---------- ZONE LEVEL ----------
        st.subheader("Zones")

        zone_counts = df["Zone"].value_counts()
        st.bar_chart(zone_counts)

        selected_zone = st.selectbox(
            "Select Zone",
            ["All"] + sorted(df["Zone"].dropna().unique().tolist())
        )

        # ---------- AG LEVEL ----------
        if selected_zone != "All":
            zone_df = df[df["Zone"] == selected_zone]
        else:
            zone_df = df

        st.subheader("AG Areas")

        ag_counts = zone_df["AG"].value_counts()
        st.bar_chart(ag_counts)

        selected_ag = st.selectbox(
            "Select AG",
            ["All"] + sorted(zone_df["AG"].dropna().unique().tolist())
        )

        # ---------- BLOCK LEVEL ----------
        if selected_ag != "All":
            ag_df = zone_df[zone_df["AG"] == selected_ag]
        else:
            ag_df = zone_df

        st.subheader("Blocks")

        block_counts = ag_df["Block"].value_counts()
        st.bar_chart(block_counts)

        st.divider()

        # Optional table view
        st.subheader("Filtered Cases")
        st.dataframe(ag_df)


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
            "Download Excel Report",
            buffer,
            f"report_{datetime.now().strftime('%Y%m%d')}.xlsx"
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
