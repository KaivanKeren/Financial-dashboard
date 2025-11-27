from datetime import datetime
from decimal import Decimal
from typing import Tuple, List, Optional
import pandas as pd

from database.repository import TransactionRepository
from models.entities.transaction import TransactionEntity
from models.dto.transaction_dto import TransactionDTO, CreateTransactionDTO
from models.dto.summary_dto import TransactionSummaryDTO, CategorySummaryDTO


class TransactionService:

    def __init__(self):
        self.repository = TransactionRepository()

    def add_transaction(self, dto: CreateTransactionDTO) -> Tuple[bool, str]:
        """
        Tambah transaksi baru menggunakan CreateTransactionDTO

        Args:
            dto: CreateTransactionDTO with validated data

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Hitung saldo
            saldo_awal = Decimal(str(self.repository.get_last_balance()))
            saldo_akhir = saldo_awal + dto.get_debit() - dto.get_kredit()

            # Convert DTO ke Entity
            entity = dto.to_entity(saldo=saldo_akhir)

            # Simpan ke database
            success = self.repository.insert(entity)

            if success:
                return True, "Transaksi berhasil ditambahkan"
            return False, "Gagal menyimpan transaksi"

        except ValueError as e:
            return False, f"Validasi error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def add_transaction_legacy(self, tanggal, deskripsi: str, kategori: str,
                               tipe: str, jumlah: float) -> Tuple[bool, str]:
        """
        Legacy method - untuk backward compatibility dengan UI lama
        Internally convert ke CreateTransactionDTO
        """
        try:
            # Konversi date ke datetime jika perlu
            if isinstance(tanggal, datetime):
                tanggal_datetime = tanggal
            else:
                tanggal_datetime = datetime.combine(tanggal, datetime.min.time())

            # Buat CreateTransactionDTO
            dto = CreateTransactionDTO(
                tanggal=tanggal_datetime,
                deskripsi=deskripsi,
                kategori=kategori,
                tipe=tipe,
                jumlah=Decimal(str(jumlah))
            )

            return self.add_transaction(dto)

        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_all_transactions_dto(self) -> List[TransactionDTO]:
        """Ambil semua transaksi sebagai list of DTOs"""
        entities = self.repository.get_all_entities()
        return [TransactionDTO.from_entity(entity) for entity in entities]

    def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionDTO]:
        """Ambil transaksi by ID sebagai DTO"""
        entity = self.repository.get_by_id(transaction_id)
        if entity:
            return TransactionDTO.from_entity(entity)
        return None

    def delete_transaction(self, index: int) -> bool:
        """Hapus transaksi dan recalculate"""
        try:
            success = self.repository.delete_by_index(index)
            if success:
                self.repository.recalculate_balances()
                return True
            return False
        except Exception as e:
            print(f"Error deleting transaction: {str(e)}")
            return False

    def get_all_transactions(self) -> pd.DataFrame:
        """Ambil semua transaksi sebagai DataFrame (backward compatibility)"""
        return self.repository.get_all_transactions()

    def get_summary_metrics(self, df: pd.DataFrame) -> TransactionSummaryDTO:
        """Hitung metrics summary dan return sebagai DTO"""
        if df.empty:
            return TransactionSummaryDTO()

        total_debit = Decimal(str(df["Debit"].sum()))
        total_kredit = Decimal(str(df["Kredit"].sum()))
        saldo_akhir = Decimal(str(self.repository.get_last_balance()))
        total_transaksi = len(df)

        # Hitung rata-rata
        debit_trans = df[df["Debit"] > 0]
        kredit_trans = df[df["Kredit"] > 0]

        avg_debit = total_debit / len(debit_trans) if len(debit_trans) > 0 else Decimal('0')
        avg_kredit = total_kredit / len(kredit_trans) if len(kredit_trans) > 0 else Decimal('0')

        return TransactionSummaryDTO(
            total_debit=total_debit,
            total_kredit=total_kredit,
            saldo_akhir=saldo_akhir,
            total_transaksi=total_transaksi,
            avg_debit=avg_debit,
            avg_kredit=avg_kredit
        )

    def get_category_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analisis per kategori"""
        if df.empty:
            return pd.DataFrame()

        summary = df.groupby("Kategori").agg({
            "Debit": "sum",
            "Kredit": "sum"
        }).round(0)
        summary["Net Balance"] = summary["Debit"] - summary["Kredit"]
        return summary

    def get_monthly_trend(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
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

    def export_to_csv(self, df: pd.DataFrame) -> bytes:
        """Export ke CSV"""
        return df.to_csv(index=False).encode('utf-8')

    def clear_all_data(self) -> bool:
        """Hapus semua data"""
        try:
            return self.repository.clear_all()
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
            return False