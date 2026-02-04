import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Personal Command Center", layout="wide")

st.title("📊 Personal Command Center Dashboard")

tabs = st.tabs(["📁 Upload & Preview", "📈 Reports", "📝 Tasks"])

# -------------------------
# TAB 1: Upload & Preview
# -------------------------
with tabs[0]:
    st.header("Upload CSV or Excel")
    uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx"])

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
with tabs[1]:
    st.header("Reports & Filters")

    if "data" not in st.session_state:
        st.warning("Upload data first")
    else:
        df = st.session_state["data"]

        cols = st.multiselect(
            "Select columns to include in report",
            options=df.columns.tolist(),
            default=df.columns.tolist()
        )

        filtered_df = df[cols]

        st.dataframe(filtered_df)

        st.download_button(
            "📥 Download Excel Report",
            data=filtered_df.to_excel(index=False),
            file_name=f"report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )

# -------------------------
# TAB 3: Tasks
# -------------------------
with tabs[2]:
    st.header("Tasks & Reminders")

    if "tasks" not in st.session_state:
        st.session_state["tasks"] = []

    with st.form("task_form"):
        title = st.text_input("Task title")
        due = st.date_input("Due date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        submitted = st.form_submit_button("Add task")

        if submitted and title:
            st.session_state["tasks"].append({
                "title": title,
                "due": due,
                "priority": priority,
                "status": "Open"
            })

    if st.session_state["tasks"]:
        tasks_df = pd.DataFrame(st.session_state["tasks"])
        st.dataframe(tasks_df)
