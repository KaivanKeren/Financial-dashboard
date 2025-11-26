import psycopg2
from contextlib import contextmanager
import streamlit as st

class DatabaseConnection:
    @staticmethod
    @contextmanager
    def get_connection():
        """Context manager untuk koneksi database"""
        conn = None
        try:
            # Gunakan st.secrets untuk production
            conn = psycopg2.connect(
                host=st.secrets["postgres"]["host"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"],
                port=st.secrets["postgres"]["port"]
            )
            yield conn
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            yield None
        finally:
            if conn:
                conn.close()
