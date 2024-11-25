import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import time

# Streamlit App
st.title("Division II Disclosure Tracker")

# Database setup
conn = sqlite3.connect("disclosure_tracker_v3.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        offence TEXT,
        analyst TEXT,
        supervisor TEXT,
        status TEXT,
        file_location TEXT,
        date_received DATE,
        work_file TEXT,
        "case" TEXT,
        remarks TEXT
    )
''')
conn.commit()

# Tabs for app functionality
tab1, tab2, tab3 = st.tabs(["Add Task", "View Tasks", "Edit Task"])

# 1. Add Task
# 1. Add Task
with tab1:
    st.header("Add New Task")

    # Task type selection
    task_type = st.selectbox("Type", ["Pro", "RFI", "MLA", "CV", "Others"])
    type_reason = ""
    if task_type == "Others":
        type_reason = st.text_input("Specify Task Reason", placeholder="Enter details for 'Others'")

    # Combine type and reason for the final type value
    final_task_type = f"{task_type} - {type_reason}" if task_type == "Others" else task_type

    # Additional inputs
    offence = st.text_input("Offence")
    analyst = st.text_input("Analyst")
    supervisor = st.selectbox("Supervisor", ["LHH", "MHS", "MSS", "LWL", "ALAK"])
    status = st.selectbox("Status", ["Pending Analyst", "Pending Supervisor", "Pending DD", "Completed"])
    file_location = st.text_input("File Location")

    # Date Received with "N/A" option
    na_date_received = st.checkbox("Mark 'Date Received' as N/A")
    if na_date_received:
        date_received = None  # Store as NULL in the database
    else:
        date_received = st.date_input("Date Received", value=datetime.now())

    work_file = st.text_input("Work File")
    case = st.text_input("Case")  # Enclosed in quotes in the table schema
    remarks = st.text_area("Remarks")

    if st.button("Add Task"):
        cursor.execute('''
            INSERT INTO tasks (type, offence, analyst, supervisor, status, file_location, date_received, work_file, "case", remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (final_task_type, offence, analyst, supervisor, status, file_location, date_received, work_file, case, remarks))
        conn.commit()
        st.success("Task added successfully!")


# 2. View Tasks
with tab2:
    st.header("View Tasks")

    # Load data into pandas DataFrame
    df = pd.read_sql_query("SELECT * FROM tasks", conn)

    # Filters
    filter_analyst = st.text_input("Filter by Analyst")
    filter_supervisor = st.selectbox("Filter by Supervisor", ["All"] + ["LHH", "MHS", "MSS", "LWL", "ALAK"])
    filter_status = st.selectbox("Filter by Status", ["All", "Pending Analyst", "Pending Supervisor", "Pending DD", "Completed"])

    # Apply filters
    filtered_df = df.copy()
    if filter_analyst:
        filtered_df = filtered_df[filtered_df["analyst"].str.contains(filter_analyst, case=False, na=False)]
    if filter_supervisor != "All":
        filtered_df = filtered_df[filtered_df["supervisor"] == filter_supervisor]
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == filter_status]

    # Set ID as index for clean display
    filtered_df.set_index("id", inplace=True)

    # Display the filtered DataFrame
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("No tasks match the selected filters.")

# 3. Edit Task
with tab3:
    st.header("Edit Task")

    # Input Task ID for search
    task_id_to_edit = st.text_input("Enter Task ID to Search")

    if task_id_to_edit:
        try:
            # Convert input to integer and fetch the task details
            selected_id = int(task_id_to_edit)
            task_to_edit = pd.read_sql_query(f"SELECT * FROM tasks WHERE id = {selected_id}", conn)

            if not task_to_edit.empty:
                # Pre-fill fields with current data
                task_row = task_to_edit.iloc[0]  # Get the first (and only) row

                # Extract task type and reason for editing
                task_type, type_reason = (task_row["type"].split(" - ", 1) + [""])[:2] if " - " in task_row["type"] else (task_row["type"], "")

                # Unique keys for each form element based on task ID to prevent duplicate IDs
                edit_task_type = st.selectbox(
                    "Type",
                    ["Pro", "RFI", "MLA", "CV", "Others"],
                    index=["Pro", "RFI", "MLA", "CV", "Others"].index(task_type),
                    key=f"edit_type_{selected_id}"
                )
                edit_type_reason = ""
                if edit_task_type == "Others":
                    edit_type_reason = st.text_input("Specify Task Reason", value=type_reason, key=f"edit_type_reason_{selected_id}")

                final_edit_task_type = f"{edit_task_type} - {edit_type_reason}" if edit_task_type == "Others" else edit_task_type

                # Other fields
                edit_offence = st.text_input("Offence", value=task_row["offence"], key=f"edit_offence_{selected_id}")
                edit_analyst = st.text_input("Analyst", value=task_row["analyst"], key=f"edit_analyst_{selected_id}")
                edit_supervisor = st.selectbox(
                    "Supervisor",
                    ["LHH", "MHS", "MSS", "LWL", "ALAK"],
                    index=["LHH", "MHS", "MSS", "LWL", "ALAK"].index(task_row["supervisor"]),
                    key=f"edit_supervisor_{selected_id}"
                )
                edit_status = st.selectbox(
                    "Status",
                    ["Pending Analyst", "Pending Supervisor", "Pending DD", "Completed"],
                    index=["Pending Analyst", "Pending Supervisor", "Pending DD", "Completed"].index(task_row["status"]),
                    key=f"edit_status_{selected_id}"
                )
                edit_file_location = st.text_input("File Location", value=task_row["file_location"], key=f"edit_file_location_{selected_id}")

                # Handle "Date Received" with None (N/A) values
                if task_row["date_received"] is not None:
                    edit_date_received = st.date_input(
                        "Date Received",
                        value=datetime.strptime(task_row["date_received"], '%Y-%m-%d').date(),
                        key=f"edit_date_received_{selected_id}"
                    )
                else:
                    edit_date_received = None
                    na_date_received = st.checkbox("Mark 'Date Received' as N/A", value=True)
                    if not na_date_received:
                        edit_date_received = st.date_input("Date Received", value=datetime.now(), key=f"edit_date_received_{selected_id}")

                edit_work_file = st.text_input("Work File", value=task_row["work_file"], key=f"edit_work_file_{selected_id}")
                edit_case = st.text_input("Case", value=task_row["case"], key=f"edit_case_{selected_id}")
                edit_remarks = st.text_area("Remarks", value=task_row["remarks"], key=f"edit_remarks_{selected_id}")

                # Update Task
                if st.button("Update Task"):
                    cursor.execute('''
                        UPDATE tasks
                        SET type = ?, offence = ?, analyst = ?, supervisor = ?, status = ?, 
                            file_location = ?, date_received = ?, work_file = ?, "case" = ?, remarks = ?
                        WHERE id = ?
                    ''', (
                        final_edit_task_type, edit_offence, edit_analyst, edit_supervisor, edit_status,
                        edit_file_location, edit_date_received, edit_work_file, edit_case, edit_remarks, selected_id
                    ))
                    conn.commit()
                    st.success("Task updated successfully!")
                    time.sleep(3)
                    st.rerun()
            else:
                st.warning(f"No task found with ID {selected_id}!")

        except ValueError:
            st.error("Please enter a valid numeric Task ID!")


# Close the database connection
conn.close()
