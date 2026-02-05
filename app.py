import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Personal Command Center", layout="wide")

st.title("📊 Personal Command Center Dashboard")

# Tabs
tabs = st.tabs([
    "📊 Overview",
    "📁 Upload & Preview",
    "📈 Reports",
    "📝 Tasks"
])

# -------------------------
# TAB 0: Overview
# -------------------------
with tabs[0]:
    st.header("Overview Dashboard")
    st.write("Stats and graphs will appear here soon.")

    if "data" in st.session_state:
        df = st.session_state["data"]

        st.subheader("Quick Stats")
        col1, col2 = st.columns(2)
        col1.metric("Total Tickets", len(df))

        if "Status" in df.columns:
            open_cases = df[df["Status"].str.contains("open", case=False, na=False)].shape[0]
            col2.metric("Open Cases", open_cases)

# -------------------------
# TAB 1: Upload & Preview
# -------------------------
with tabs[1]:
    st.header("Upload CSV or Excel")

    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["csv", "xlsx"]
    )

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File loaded successfully")
        st.dataframe(df.head(50))

        st.session_state["data"] = df


# -------------------------
# TAB 2: Reports
# -------------------------
with tabs[2]:
    st.header("Reports & Filters")

    if "data" not in st.session_state:
        st.warning("Upload data first.")
    else:
        df = st.session_state["data"]

        cols = st.multiselect(
            "Select columns for report",
            options=df.columns.tolist(),
            default=df.columns.tolist()
        )

        filtered_df = df[cols]
        st.dataframe(filtered_df)

        # Excel download fix
        buffer = io.BytesIO()
        filtered_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="📥 Download Excel Report",
            data=buffer,
            file_name=f"report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-offexmlformats-officedocument.spreadsheetml.sheet"
        )


# -------------------------
# TAB 3: Tasks
# -------------------------
with tabs[3]:
    st.header("Tasks & Reminders")

    if "tasks" not in st.session_state:
        st.session_state["tasks"] = []

    with st.form("task_form"):
        title = st.text_input("Task title")
        due = st.date_input("Due date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submitted = st.form_submit_button("Add Task")

        if submitted and title:
            st.session_state["tasks"].append({
                "Title": title,
                "Due": due,
                "Priority": priority,
                "Status": "Open"
            })

    if st.session_state["tasks"]:
        tasks_df = pd.DataFrame(st.session_state["tasks"])
        st.dataframe(tasks_df)
