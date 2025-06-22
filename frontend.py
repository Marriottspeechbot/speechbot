import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime, date

# Database connection string
DATABASE_URL = "postgresql://marriott_cq2r_user:tmynVDjwCktaZL6KCzWXdDr2EuI3hTK8@dpg-d1btqleuk2gs73a4897g-a.oregon-postgres.render.com/marriott_cq2r"

# Streamlit page configuration for a polished look
st.set_page_config(page_title="Marriott Event Management Admin", layout="wide")

# Helper function to establish database connection
def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# Helper function to execute SQL queries with error handling
def execute_sql(query, values=None):
    try:
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# Helper function to fetch table schema
def get_columns():
    conn = get_connection()
    if not conn:
        return []
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name='events'
    """)
    columns = cur.fetchall()
    cur.close()
    conn.close()
    return columns

# Helper function to fetch all data (no caching to ensure fresh data)
def fetch_data():
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM events ORDER BY reference_number DESC", conn)
    conn.close()
    return df

# Helper function to generate 6-digit reference number
def generate_reference_number():
    import random
    return f"{random.randint(100000, 999999)}"

# Enhanced sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Commands", [
    "📋 View Events",
    "➕ Add Event",
    "✏️ Update Event",
    "🗑️ Delete Event",
    "🧱 Schema Management"
])

# --- PAGE: VIEW EVENTS ---
if page == "📋 View Events":
    st.title("📋 Event Records")
    st.markdown("View all event records in the database below.")
    if st.button("🔄 Refresh Data"):
        st.rerun()
    df = fetch_data()
    if df.empty:
        st.warning("No events found in the table.")
    else:
        st.dataframe(df, use_container_width=True)

# --- PAGE: ADD EVENT ---
elif page == "➕ Add Event":
    st.title("➕ Add New Event")
    st.markdown("Fill out the form below to add a new event record.")
    
    with st.form("add_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            reference_number = st.text_input("Reference Number (6 digits)", value=generate_reference_number(), max_chars=6)
            event_type = st.selectbox("Event Type", [
                "", "Wedding", "Corporate Meeting", "Conference", "Birthday Party", 
                "Anniversary", "Graduation", "Holiday Party", "Other"
            ])
            is_flexible = st.checkbox("Is Flexible")
            with_rooms = st.checkbox("With Rooms")
            budget = st.number_input("Budget ($)", min_value=0, value=0)
        
        with col2:
            event_start = st.date_input("Event Start Date", value=None)
            event_end = st.date_input("Event End Date", value=None)
            meal = st.selectbox("Meal Type", [
                "", "Breakfast", "Lunch", "Dinner", "Cocktail Reception", 
                "Coffee Break", "Full Catering", "No Meal"
            ])
            guest_count = st.number_input("Guest Count", min_value=0, value=0)
            phone_number = st.text_input("Phone Number (10-15 digits)", max_chars=15)
        
        submitted = st.form_submit_button("Add Event")
        
        if submitted:
            # Validation
            errors = []
            if not reference_number or len(reference_number) != 6 or not reference_number.isdigit():
                errors.append("Reference number must be exactly 6 digits")
            if not phone_number or len(phone_number) < 10 or len(phone_number) > 15 or not phone_number.isdigit():
                errors.append("Phone number must be 10-15 digits")
            if event_end and event_start and event_end < event_start:
                errors.append("Event end date cannot be before start date")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Prepare data
                form_data = {
                    'reference_number': reference_number,
                    'event_start': event_start.strftime("%Y-%m-%d") if event_start else None,
                    'event_end': event_end.strftime("%Y-%m-%d") if event_end else None,
                    'event_type': event_type if event_type else None,
                    'is_flexible': is_flexible,
                    'meal': meal if meal else None,
                    'with_rooms': with_rooms,
                    'budget': budget,
                    'guest_count': guest_count,
                    'phone_number': phone_number
                }
                
                keys = list(form_data.keys())
                values = list(form_data.values())
                query = f"INSERT INTO events ({', '.join(keys)}) VALUES ({', '.join(['%s']*len(keys))})"
                
                success = execute_sql(query, values)
                if success:
                    st.success("✅ Event added successfully!")
                    st.rerun()

# --- PAGE: UPDATE EVENT ---
elif page == "✏️ Update Event":
    st.title("✏️ Update Event")
    st.markdown("Select an event by reference number and update a specific field.")
    
    df = fetch_data()
    if df.empty:
        st.info("No events available to update.")
    else:
        with st.form("update_event_form"):
            selected_ref = st.selectbox("Select Reference Number", df['reference_number'], key="update_ref")
            field = st.selectbox("Field to Update", [
                'event_start', 'event_end', 'event_type', 'is_flexible', 
                'meal', 'with_rooms', 'budget', 'guest_count', 'phone_number'
            ], key="update_field")
            
            # Dynamic input based on field type
            if field in ['event_start', 'event_end']:
                new_value = st.date_input("New Value", key="update_value")
                new_value = new_value.strftime("%Y-%m-%d") if new_value else None
            elif field in ['is_flexible', 'with_rooms']:
                new_value = st.checkbox("New Value", key="update_value")
            elif field in ['budget', 'guest_count']:
                new_value = st.number_input("New Value", min_value=0, key="update_value")
            elif field == 'event_type':
                new_value = st.selectbox("New Value", [
                    "", "Wedding", "Corporate Meeting", "Conference", "Birthday Party", 
                    "Anniversary", "Graduation", "Holiday Party", "Other"
                ], key="update_value")
            elif field == 'meal':
                new_value = st.selectbox("New Value", [
                    "", "Breakfast", "Lunch", "Dinner", "Cocktail Reception", 
                    "Coffee Break", "Full Catering", "No Meal"
                ], key="update_value")
            elif field == 'phone_number':
                new_value = st.text_input("New Value (10-15 digits)", max_chars=15, key="update_value")
            else:
                new_value = st.text_input("New Value", key="update_value")
            
            update_btn = st.form_submit_button("Update Event")
            
            if update_btn:
                # Validation
                valid = True
                if field == 'phone_number':
                    if not new_value or len(new_value) < 10 or len(new_value) > 15 or not new_value.isdigit():
                        st.error("Phone number must be 10-15 digits")
                        valid = False
                
                if valid and new_value is not None:
                    query = f"UPDATE events SET {field} = %s WHERE reference_number = %s"
                    success = execute_sql(query, (new_value, selected_ref))
                    if success:
                        st.success(f"✅ Updated {field} for reference {selected_ref}")
                        st.rerun()
                elif not valid:
                    pass  # Error already shown
                else:
                    st.warning("Please provide a new value.")

# --- PAGE: DELETE EVENT ---
elif page == "🗑️ Delete Event":
    st.title("🗑️ Delete Event")
    st.markdown("Select an event by reference number to delete.")
    
    df = fetch_data()
    if df.empty:
        st.info("No events available to delete.")
    else:
        with st.form("delete_event_form"):
            selected_ref = st.selectbox("Select Reference Number", df['reference_number'], key="delete_ref")
            
            # Show event details for confirmation
            event_details = df[df['reference_number'] == selected_ref].iloc[0]
            st.write("**Event Details:**")
            st.write(f"- Event Type: {event_details['event_type']}")
            st.write(f"- Start Date: {event_details['event_start']}")
            st.write(f"- End Date: {event_details['event_end']}")
            st.write(f"- Guest Count: {event_details['guest_count']}")
            st.write(f"- Budget: ${event_details['budget']}")
            
            confirm_delete = st.checkbox("I confirm I want to delete this event", key="delete_confirm")
            delete_btn = st.form_submit_button("Delete Event")
            
            if delete_btn:
                if confirm_delete:
                    success = execute_sql("DELETE FROM events WHERE reference_number = %s", (selected_ref,))
                    if success:
                        st.success(f"✅ Deleted event with reference number {selected_ref}")
                        st.rerun()
                else:
                    st.warning("Please confirm deletion by checking the checkbox.")

# --- PAGE: SCHEMA MANAGEMENT ---
elif page == "🧱 Schema Management":
    st.title("🧱 Schema Management")
    st.markdown("Manage the structure of the `events` table.")

    # List Schema
    with st.expander("📜 View Table Schema", expanded=True):
        cols = get_columns()
        if cols:
            schema_df = pd.DataFrame(cols, columns=["Column", "Type", "Max Length", "Nullable", "Default"])
            st.dataframe(schema_df, use_container_width=True)
        else:
            st.warning("Unable to fetch schema.")

    # Add Column
    with st.expander("➕ Add New Column"):
        with st.form("add_column_form"):
            col_name = st.text_input("Column Name", key="add_col_name")
            col_type = st.selectbox("Data Type", [
                "VARCHAR(255)", "TEXT", "INTEGER", "BOOLEAN", "DATE", 
                "TIMESTAMP", "DECIMAL(10,2)", "BIGINT"
            ], key="add_col_type")
            add_btn = st.form_submit_button("Add Column")
            
            if add_btn:
                if col_name:
                    query = f"ALTER TABLE events ADD COLUMN {col_name} {col_type}"
                    success = execute_sql(query)
                    if success:
                        st.success(f"✅ Column `{col_name}` added!")
                        st.rerun()
                else:
                    st.warning("Please provide a column name.")

    # Delete Column
    with st.expander("🗑️ Delete Column"):
        if cols:
            col_to_drop = st.selectbox("Select Column", [c[0] for c in cols if c[0] != "reference_number"], key="delete_col")
            confirm = st.text_input("Type 'DELETE' to confirm", key="delete_confirm")
            if st.button("Delete Column"):
                if confirm == "DELETE":
                    query = f"ALTER TABLE events DROP COLUMN {col_to_drop}"
                    success = execute_sql(query)
                    if success:
                        st.success(f"✅ Column `{col_to_drop}` deleted!")
                        st.rerun()
                else:
                    st.warning("Please type 'DELETE' to confirm.")
        else:
            st.info("No columns available to delete.")

    # Update Column
    with st.expander("✏️ Update Column"):
        if cols:
            col_to_update = st.selectbox("Select Column", [c[0] for c in cols], key="update_col")
            action = st.radio("Action", ["Rename", "Change Type"], key="update_action")
            
            if action == "Rename":
                with st.form("rename_column_form"):
                    new_name = st.text_input("New Name", key="rename_value")
                    rename_btn = st.form_submit_button("Rename Column")
                    
                    if rename_btn:
                        if new_name and new_name != col_to_update:
                            query = f"ALTER TABLE events RENAME COLUMN {col_to_update} TO {new_name}"
                            success = execute_sql(query)
                            if success:
                                st.success(f"✅ Renamed `{col_to_update}` to `{new_name}`")
                                st.rerun()
                        else:
                            st.warning("Please provide a different new name.")
            else:  # Change Type
                with st.form("change_type_form"):
                    new_type = st.selectbox("New Type", [
                        "VARCHAR(255)", "TEXT", "INTEGER", "BOOLEAN", "DATE", 
                        "TIMESTAMP", "DECIMAL(10,2)", "BIGINT"
                    ], key="type_value")
                    st.warning("⚠️ Changing type may fail if data is incompatible.")
                    type_btn = st.form_submit_button("Change Type")
                    
                    if type_btn:
                        query = f"ALTER TABLE events ALTER COLUMN {col_to_update} TYPE {new_type}"
                        success = execute_sql(query)
                        if success:
                            st.success(f"✅ Changed type of `{col_to_update}` to {new_type}")
                            st.rerun()
        else:
            st.info("No columns available to update.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Marriott Event Management System**")
st.sidebar.markdown("Admin Interface v1.0")
