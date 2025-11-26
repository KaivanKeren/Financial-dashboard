import pandas as pd
from datetime import datetime
from database.connection import DatabaseConnection


class TransactionRepository:

    @staticmethod
    def init_database():
        """Inisialisasi tabel database"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                                   CREATE TABLE IF NOT EXISTS transactions
                                   (
                                       id
                                       SERIAL
                                       PRIMARY
                                       KEY,
                                       tanggal
                                       TIMESTAMP
                                       NOT
                                       NULL,
                                       deskripsi
                                       TEXT
                                       NOT
                                       NULL,
                                       kategori
                                       VARCHAR
                                   (
                                       50
                                   ) NOT NULL,
                                       debit DECIMAL
                                   (
                                       15,
                                       2
                                   ) DEFAULT 0,
                                       kredit DECIMAL
                                   (
                                       15,
                                       2
                                   ) DEFAULT 0,
                                       saldo DECIMAL
                                   (
                                       15,
                                       2
                                   ) DEFAULT 0,
                                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                       )
                                   """)
                    conn.commit()
                    cursor.close()
                    return True
                except Exception as e:
                    st.error(f"Error creating table: {str(e)}")
                    return False
        return False

    @staticmethod
    def get_all_transactions():
        """Ambil semua transaksi dari database"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    query = """
                            SELECT tanggal, deskripsi, kategori, debit, kredit, saldo
                            FROM transactions
                            ORDER BY id ASC \
                            """
                    df = pd.read_sql_query(query, conn)
                    df.columns = ["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"]
                    return df
                except Exception as e:
                    st.error(f"Error loading transactions: {str(e)}")
                    return pd.DataFrame(columns=["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"])
        return pd.DataFrame(columns=["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"])

    @staticmethod
    def get_last_balance():
        """Ambil saldo terakhir"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT saldo FROM transactions ORDER BY id DESC LIMIT 1")
                    result = cursor.fetchone()
                    cursor.close()
                    return float(result[0]) if result else 0
                except Exception as e:
                    st.error(f"Error getting last balance: {str(e)}")
                    return 0
        return 0

    @staticmethod
    def insert_transaction(tanggal, deskripsi, kategori, debit, kredit, saldo):
        """Simpan transaksi baru"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                                   INSERT INTO transactions (tanggal, deskripsi, kategori, debit, kredit, saldo)
                                   VALUES (%s, %s, %s, %s, %s, %s)
                                   """, (tanggal, deskripsi, kategori, debit, kredit, saldo))
                    conn.commit()
                    cursor.close()
                    return True
                except Exception as e:
                    st.error(f"Error saving transaction: {str(e)}")
                    return False
        return False

    @staticmethod
    def delete_transaction_by_index(index):
        """Hapus transaksi berdasarkan index"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                                   SELECT id
                                   FROM transactions
                                   ORDER BY id ASC LIMIT 1
                                   OFFSET %s
                                   """, (index,))
                    result = cursor.fetchone()

                    if result:
                        transaction_id = result[0]
                        cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
                        conn.commit()
                        cursor.close()
                        return True
                except Exception as e:
                    st.error(f"Error deleting transaction: {str(e)}")
                    return False
        return False

    @staticmethod
    def recalculate_balances():
        """Recalculate semua saldo"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, debit, kredit FROM transactions ORDER BY id ASC")
                    transactions = cursor.fetchall()

                    saldo = 0
                    for trans_id, debit, kredit in transactions:
                        saldo += float(debit) - float(kredit)
                        cursor.execute(
                            "UPDATE transactions SET saldo = %s WHERE id = %s",
                            (saldo, trans_id)
                        )

                    conn.commit()
                    cursor.close()
                    return True
                except Exception as e:
                    st.error(f"Error recalculating balances: {str(e)}")
                    return False
        return False

    @staticmethod
    def clear_all():
        """Hapus semua transaksi"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("TRUNCATE TABLE transactions RESTART IDENTITY")
                    conn.commit()
                    cursor.close()
                    return True
                except Exception as e:
                    st.error(f"Error clearing transactions: {str(e)}")
                    return False
        return False

