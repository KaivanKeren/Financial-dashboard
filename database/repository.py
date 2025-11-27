import pandas as pd
import streamlit as st
from typing import List, Optional
from database.connection import DatabaseConnection
from models.entities.transaction import TransactionEntity


class TransactionRepository:

    @staticmethod
    def init_database() -> bool:
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
    def get_all_transactions() -> pd.DataFrame:
        """Ambil semua transaksi sebagai DataFrame (untuk backward compatibility)"""
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
    def get_all_entities() -> List[TransactionEntity]:
        """Ambil semua transaksi sebagai list of Entities"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                                   SELECT id,
                                          tanggal,
                                          deskripsi,
                                          kategori,
                                          debit,
                                          kredit,
                                          saldo,
                                          created_at
                                   FROM transactions
                                   ORDER BY id ASC
                                   """)
                    results = cursor.fetchall()
                    cursor.close()
                    return [TransactionEntity.from_db_row(row) for row in results]
                except Exception as e:
                    st.error(f"Error loading transactions: {str(e)}")
                    return []
        return []

    @staticmethod
    def get_by_id(transaction_id: int) -> Optional[TransactionEntity]:
        """Ambil transaksi by ID"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                                   SELECT id,
                                          tanggal,
                                          deskripsi,
                                          kategori,
                                          debit,
                                          kredit,
                                          saldo,
                                          created_at
                                   FROM transactions
                                   WHERE id = %s
                                   """, (transaction_id,))
                    result = cursor.fetchone()
                    cursor.close()

                    if result:
                        return TransactionEntity.from_db_row(result)
                except Exception as e:
                    st.error(f"Error getting transaction: {str(e)}")
        return None

    @staticmethod
    def get_last_balance() -> float:
        """Ambil saldo terakhir"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT saldo FROM transactions ORDER BY id DESC LIMIT 1")
                    result = cursor.fetchone()
                    cursor.close()
                    return float(result[0]) if result else 0.0
                except Exception as e:
                    st.error(f"Error getting last balance: {str(e)}")
                    return 0.0
        return 0.0

    @staticmethod
    def insert(entity: TransactionEntity) -> bool:
        """Simpan transaksi baru menggunakan Entity"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                                   INSERT INTO transactions (tanggal, deskripsi, kategori, debit, kredit, saldo)
                                   VALUES (%s, %s, %s, %s, %s, %s)
                                   """, (
                                       entity.tanggal,
                                       entity.deskripsi,
                                       entity.kategori,
                                       float(entity.debit),
                                       float(entity.kredit),
                                       float(entity.saldo)
                                   ))
                    conn.commit()
                    cursor.close()
                    return True
                except Exception as e:
                    st.error(f"Error saving transaction: {str(e)}")
                    return False
        return False

    @staticmethod
    def delete_by_index(index: int) -> bool:
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
    def recalculate_balances() -> bool:
        """Recalculate semua saldo"""
        with DatabaseConnection.get_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, debit, kredit FROM transactions ORDER BY id ASC")
                    transactions = cursor.fetchall()

                    saldo = 0.0
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
    def clear_all() -> bool:
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