import streamlit as st
import psycopg2
import pandas as pd

# Database connection parameters
DATABASE_URL = "postgresql://marriottspeechbot_user:OOsb5fB2mJd6n7cuo3kcptfglC3mseg6@dpg-d1ae2immcj7s73fegmng-a.virginia-postgres.render.com/marriottspeechbot"

# Function to fetch bookings table data
def fetch_bookings():
    connection = None
    cursor = None
    df = pd.DataFrame()

    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM bookings ORDER BY serial_number;")
        columns = [desc[0] for desc in cursor.description]
        records = cursor.fetchall()

        df = pd.DataFrame(records, columns=columns)

    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return df

# Streamlit UI
st.set_page_config(page_title="Bookings Table", layout="wide")
st.title("📋 Bookings Table Viewer")

# Load data
with st.spinner("Fetching data from database..."):
    data = fetch_bookings()

if not data.empty:
    st.success("Data loaded successfully!")
    st.dataframe(data, use_container_width=True)
else:
    st.warning("No data found in the bookings table.")
