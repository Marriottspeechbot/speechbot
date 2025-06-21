import streamlit as st
import psycopg2
import pandas as pd

# Database connection parameters
DATABASE_URL = "postgresql://marriottspeechbot_user:OOsb5fB2mJd6n7cuo3kcptfglC3mseg6@dpg-d1ae2immcj7s73fegmng-a.virginia-postgres.render.com/marriottspeechbot"

# Function to fetch bookings table data
def fetch_bookings():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM bookings ORDER BY serial_number;")
                columns = [desc[0] for desc in cursor.description]
                records = cursor.fetchall()
                return pd.DataFrame(records, columns=columns)
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Function to delete a row by serial_number
def delete_booking(serial_number):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM bookings WHERE serial_number = %s;", (serial_number,))
                conn.commit()
                st.success(f"Deleted booking with serial_number = {serial_number}")
    except psycopg2.Error as e:
        st.error(f"Error deleting record: {e}")

# Streamlit UI
st.set_page_config(page_title="Bookings Table", layout="wide")
st.title("📋 Bookings Table Viewer")

# Load data
with st.spinner("Fetching data from database..."):
    data = fetch_bookings()

if not data.empty:
    st.success("Data loaded successfully!")
    
    # Show table with selectable rows
    selected_index = st.selectbox("Select a row to delete (by serial_number):", data["serial_number"])
    
    # Show the full row details
    st.write("Selected Row Details:")
    st.dataframe(data[data["serial_number"] == selected_index])

    # Delete button
    if st.button("❌ Delete Selected Row"):
        delete_booking(selected_index)
        # Refresh data
        data = fetch_bookings()

    st.divider()
    st.dataframe(data, use_container_width=True)

else:
    st.warning("No data found in the bookings table.")
