import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import os

# Database configuration
DATABASE_URL = "postgresql://marriottspeechbot_user:OOsb5fB2mJd6n7cuo3kcptfglC3mseg6@dpg-d1ae2immcj7s73fegmng-a.virginia-postgres.render.com/marriottspeechbot"

@st.cache_resource
def init_connection():
    """Initialize database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def get_tables(conn):
    """Get all table names from the database"""
    try:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        cursor = conn.cursor()
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []

def get_table_columns(conn, table_name):
    """Get column information for a specific table"""
    try:
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
        """
        cursor = conn.cursor()
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        st.error(f"Error fetching columns: {e}")
        return []

def fetch_data(conn, table_name):
    """Fetch all data from a specific table"""
    try:
        query = f"SELECT * FROM {table_name} ORDER BY 1;"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame()

def insert_record(conn, table_name, data):
    """Insert a new record into the table"""
    try:
        columns = list(data.keys())
        values = list(data.values())
        
        # Create placeholders for the query
        placeholders = ', '.join(['%s'] * len(values))
        columns_str = ', '.join(columns)
        
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"Error inserting record: {e}")
        conn.rollback()
        return False

def delete_record(conn, table_name, condition_column, condition_value):
    """Delete a record from the table"""
    try:
        query = f"DELETE FROM {table_name} WHERE {condition_column} = %s"
        cursor = conn.cursor()
        cursor.execute(query, (condition_value,))
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        return rows_affected
    except Exception as e:
        st.error(f"Error deleting record: {e}")
        conn.rollback()
        return 0

def main():
    st.set_page_config(page_title="Database Manager", layout="wide")
    st.title("🗄️ Database Manager")
    st.markdown("---")
    
    # Initialize database connection
    conn = init_connection()
    if not conn:
        st.stop()
    
    # Get all tables
    tables = get_tables(conn)
    if not tables:
        st.warning("No tables found in the database.")
        st.stop()
    
    # Sidebar for table selection
    st.sidebar.header("Table Selection")
    selected_table = st.sidebar.selectbox("Choose a table:", tables)
    
    if selected_table:
        # Get table columns
        columns_info = get_table_columns(conn, selected_table)
        column_names = [col[0] for col in columns_info]
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["📊 View Data", "➕ Add Record", "🗑️ Delete Record"])
        
        with tab1:
            st.header(f"Data from: {selected_table}")
            
            # Fetch and display data
            df = fetch_data(conn, selected_table)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.info(f"Total records: {len(df)}")
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data found in this table.")
        
        with tab2:
            st.header(f"Add New Record to: {selected_table}")
            
            # Check if reference_number column exists
            has_reference_number = 'reference_number' in column_names
            
            with st.form("add_record_form"):
                st.subheader("Enter Record Details")
                
                form_data = {}
                
                # Create custom form based on your schema
                # Reference Number (Mandatory - 6 digits)
                form_data['reference_number'] = st.text_input(
                    "Reference Number *", 
                    placeholder="Enter 6-digit number (e.g., 123456)",
                    help="Required: Must be exactly 6 digits",
                    max_chars=6
                )
                
                # Name
                form_data['name'] = st.text_input(
                    "Name", 
                    placeholder="Enter name (optional)",
                    max_chars=100
                )
                
                # Phone Number
                form_data['phone_number'] = st.text_input(
                    "Phone Number", 
                    placeholder="Enter phone number (optional)",
                    max_chars=15
                )
                
                # Event Start Date
                form_data['event_start'] = st.date_input(
                    "Event Start Date", 
                    value=None,
                    help="Select event start date"
                )
                
                # Event End Date
                form_data['event_end'] = st.date_input(
                    "Event End Date", 
                    value=None,
                    help="Select event end date"
                )
                
                # Event Type
                form_data['event_type'] = st.text_input(
                    "Event Type", 
                    placeholder="e.g., Wedding, Conference, Birthday (optional)",
                    max_chars=100
                )
                
                # Is Flexible
                form_data['is_flexible'] = st.selectbox(
                    "Is Flexible", 
                    options=["", "Yes", "No"],
                    help="Select if event timing is flexible"
                )
                
                # Meal
                form_data['meal'] = st.text_input(
                    "Meal", 
                    placeholder="e.g., Lunch, Dinner, Breakfast (optional)",
                    max_chars=100
                )
                
                # With Rooms
                form_data['with_rooms'] = st.selectbox(
                    "With Rooms", 
                    options=["", "Yes", "No"],
                    help="Select if rooms are required"
                )
                
                # Budget
                form_data['budget'] = st.number_input(
                    "Budget", 
                    min_value=0,
                    value=None,
                    help="Enter budget amount (optional)"
                )
                
                # Guest Count
                form_data['guest_count'] = st.number_input(
                    "Guest Count", 
                    min_value=0,
                    value=None,
                    help="Enter number of guests (optional)"
                )
                
                # Timings Start
                form_data['timings_start'] = st.time_input(
                    "Start Time", 
                    value=None,
                    help="Select event start time"
                )
                
                # Timings End
                form_data['timings_end'] = st.time_input(
                    "End Time", 
                    value=None,
                    help="Select event end time"
                )
                
                submitted = st.form_submit_button("Add Record", type="primary")
                
                if submitted:
                    # Validate reference_number (must be exactly 6 digits)
                    reference_number = form_data.get('reference_number', '').strip()
                    
                    if not reference_number:
                        st.error("❌ Reference number is required!")
                    elif not reference_number.isdigit() or len(reference_number) != 6:
                        st.error("❌ Reference number must be exactly 6 digits!")
                    else:
                        # Validate date logic
                        event_start = form_data.get('event_start')
                        event_end = form_data.get('event_end')
                        
                        if event_start and event_end and event_start > event_end:
                            st.error("❌ Event start date cannot be after event end date!")
                        else:
                            # Validate time logic
                            timings_start = form_data.get('timings_start')
                            timings_end = form_data.get('timings_end')
                            
                            if timings_start and timings_end and timings_start >= timings_end:
                                st.error("❌ Start time must be before end time!")
                            else:
                                # Clean data - remove empty strings and None values
                                cleaned_data = {}
                                for key, value in form_data.items():
                                    if value is not None and value != "":
                                        cleaned_data[key] = value
                                
                                # Check if reference number already exists
                                try:
                                    check_query = f"SELECT COUNT(*) FROM {selected_table} WHERE reference_number = %s"
                                    cursor = conn.cursor()
                                    cursor.execute(check_query, (reference_number,))
                                    count = cursor.fetchone()[0]
                                    cursor.close()
                                    
                                    if count > 0:
                                        st.error("❌ Reference number already exists! Please use a different number.")
                                    else:
                                        if insert_record(conn, selected_table, cleaned_data):
                                            st.success("✅ Record added successfully!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Failed to add record.")
                                except Exception as e:
                                    st.error(f"❌ Error checking reference number: {e}")
        
        with tab3:
            st.header(f"Delete Records from: {selected_table}")
            
            # Fetch current data for selection
            df = fetch_data(conn, selected_table)
            if not df.empty:
                st.subheader("Select Record to Delete")
                
                # Choose column for deletion criteria
                delete_column = st.selectbox(
                    "Select column to filter by:",
                    column_names,
                    help="Choose which column to use for identifying the record to delete"
                )
                
                if delete_column:
                    # Get unique values for the selected column
                    unique_values = df[delete_column].dropna().unique()
                    
                    if len(unique_values) > 0:
                        selected_value = st.selectbox(
                            f"Select {delete_column} value:",
                            unique_values
                        )
                        
                        # Show preview of records that will be deleted
                        preview_df = df[df[delete_column] == selected_value]
                        
                        if not preview_df.empty:
                            st.subheader("Records to be deleted:")
                            st.dataframe(preview_df, use_container_width=True)
                            
                            # Confirmation
                            confirm_delete = st.checkbox("I confirm I want to delete these records")
                            
                            if st.button("🗑️ Delete Records", type="secondary", disabled=not confirm_delete):
                                rows_deleted = delete_record(conn, selected_table, delete_column, selected_value)
                                if rows_deleted > 0:
                                    st.success(f"Successfully deleted {rows_deleted} record(s)!")
                                    st.rerun()
                                else:
                                    st.warning("No records were deleted.")
                        else:
                            st.info("No records found with the selected criteria.")
                    else:
                        st.warning(f"No values found in column '{delete_column}'")
            else:
                st.warning("No data available to delete.")
        
        # Table information sidebar
        st.sidebar.header("Table Information")
        st.sidebar.write(f"**Table:** {selected_table}")
        st.sidebar.write(f"**Columns:** {len(column_names)}")
        
        with st.sidebar.expander("Column Details"):
            for col_name, data_type, is_nullable, default_value in columns_info:
                st.write(f"**{col_name}**")
                st.write(f"Type: {data_type}")
                st.write(f"Nullable: {is_nullable}")
                if default_value:
                    st.write(f"Default: {default_value}")
                st.write("---")

if __name__ == "__main__":
    main()
