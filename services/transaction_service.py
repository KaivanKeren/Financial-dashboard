from datetime import datetime
import pandas as pd
from database.repository import TransactionRepository


class TransactionService:

    def __init__(self):
        self.repository = TransactionRepository()

    def add_transaction(self, tanggal, deskripsi, kategori, tipe, jumlah):
        """
        Tambah transaksi baru dengan validasi

        Args:
            tanggal: datetime object
            deskripsi: string
            kategori: string
            tipe: 'Pemasukan' atau 'Pengeluaran'
            jumlah: float

        Returns:
            bool: True jika berhasil, False jika gagal
        """
        if not deskripsi or jumlah <= 0:
            return False, "Deskripsi dan jumlah harus diisi dengan benar"

        # Konversi date ke datetime jika perlu
        if isinstance(tanggal, datetime):
            tanggal_datetime = tanggal
        else:
            tanggal_datetime = datetime.combine(tanggal, datetime.min.time())

        # Tentukan debit/kredit
        debit = jumlah if tipe == "Pemasukan" else 0
        kredit = jumlah if tipe == "Pengeluaran" else 0

        # Hitung saldo
        saldo_awal = self.repository.get_last_balance()
        saldo_akhir = saldo_awal + debit - kredit

        # Simpan ke database
        success = self.repository.insert_transaction(
            tanggal_datetime, deskripsi, kategori, debit, kredit, saldo_akhir
        )

        if success:
            return True, "Transaksi berhasil ditambahkan"
        return False, "Gagal menyimpan transaksi"

    def delete_transaction(self, index):
        """Hapus transaksi dan recalculate"""
        success = self.repository.delete_transaction_by_index(index)
        if success:
            self.repository.recalculate_balances()
            return True
        return False

    def get_all_transactions(self):
        """Ambil semua transaksi"""
        return self.repository.get_all_transactions()

    def get_summary_metrics(self, df):
        """Hitung metrics summary"""
        if df.empty:
            return {
                "total_debit": 0,
                "total_kredit": 0,
                "saldo_akhir": 0,
                "total_transaksi": 0
            }

        return {
            "total_debit": df["Debit"].sum(),
            "total_kredit": df["Kredit"].sum(),
            "saldo_akhir": self.repository.get_last_balance(),
            "total_transaksi": len(df)
        }

    def get_category_summary(self, df):
        """Analisis per kategori"""
        if df.empty:
            return pd.DataFrame()

        summary = df.groupby("Kategori").agg({
            "Debit": "sum",
            "Kredit": "sum"
        }).round(0)
        summary["Net Balance"] = summary["Debit"] - summary["Kredit"]
        return summary

    def get_monthly_trend(self, df):
        """Analisis tren bulanan"""
        if df.empty or len(df) <= 5:
            return None

        df_trend = df.copy()
        df_trend["Tanggal"] = pd.to_datetime(df_trend["Tanggal"])
        df_trend["Bulan"] = df_trend["Tanggal"].dt.to_period("M").astype(str)

        monthly = df_trend.groupby("Bulan").agg({
            "Debit": "sum",
            "Kredit": "sum"
        }).reset_index()

        return monthly

    def export_to_csv(self, df):
        """Export ke CSV"""
        return df.to_csv(index=False).encode('utf-8')

    def clear_all_data(self):
        """Hapus semua data"""
        return self.repository.clear_all()