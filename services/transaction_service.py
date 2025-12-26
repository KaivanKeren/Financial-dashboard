from datetime import datetime
from decimal import Decimal
from typing import Tuple, List, Optional

import pandas as pd

from database.repository import TransactionRepository
from models.dto.transaction_dto import TransactionDTO, CreateTransactionDTO
from models.dto.summary_dto import TransactionSummaryDTO


class TransactionService:

    def __init__(self):
        self.repository = TransactionRepository()

    # ======================================================
    # CREATE TRANSACTION
    # ======================================================
    def add_transaction(self, dto: CreateTransactionDTO) -> Tuple[bool, str]:
        """
        Tambah transaksi baru menggunakan CreateTransactionDTO
        """
        try:
            saldo_awal = Decimal(str(self.repository.get_last_balance()))
            saldo_akhir = saldo_awal + dto.get_debit() - dto.get_kredit()

            entity = dto.to_entity(saldo=saldo_akhir)
            success = self.repository.insert(entity)

            if success:
                return True, "Transaksi berhasil ditambahkan"
            return False, "Gagal menyimpan transaksi"

        except ValueError as e:
            return False, f"Validasi error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def add_transaction_legacy(
        self,
        tanggal,
        deskripsi: str,
        kategori: str,
        tipe: str,
        jumlah: float
    ) -> Tuple[bool, str]:
        """
        Legacy method - backward compatibility UI lama
        """
        try:
            if isinstance(tanggal, datetime):
                tanggal_datetime = tanggal
            else:
                tanggal_datetime = datetime.combine(
                    tanggal, datetime.min.time()
                )

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

    # ======================================================
    # READ
    # ======================================================
    def get_all_transactions_dto(self) -> List[TransactionDTO]:
        entities = self.repository.get_all_entities()
        return [TransactionDTO.from_entity(e) for e in entities]

    def get_transaction_by_id(
        self, transaction_id: int
    ) -> Optional[TransactionDTO]:
        entity = self.repository.get_by_id(transaction_id)
        return TransactionDTO.from_entity(entity) if entity else None

    def get_all_transactions(self) -> pd.DataFrame:
        """Backward compatibility (DataFrame)"""
        return self.repository.get_all_transactions()

    # ======================================================
    # DELETE
    # ======================================================
    def delete_transaction(self, index: int) -> bool:
        try:
            success = self.repository.delete_by_index(index)
            if success:
                self.repository.recalculate_balances()
            return success
        except Exception as e:
            print(f"Error deleting transaction: {str(e)}")
            return False

    # ======================================================
    # SUMMARY & ANALYTICS
    # ======================================================
    def get_summary_metrics(
        self, df: pd.DataFrame
    ) -> TransactionSummaryDTO:
        if df.empty:
            return TransactionSummaryDTO()

        total_debit = Decimal(str(df["Debit"].sum()))
        total_kredit = Decimal(str(df["Kredit"].sum()))
        saldo_akhir = Decimal(str(self.repository.get_last_balance()))

        debit_trans = df[df["Debit"] > 0]
        kredit_trans = df[df["Kredit"] > 0]

        avg_debit = (
            total_debit / len(debit_trans)
            if len(debit_trans) > 0 else Decimal("0")
        )
        avg_kredit = (
            total_kredit / len(kredit_trans)
            if len(kredit_trans) > 0 else Decimal("0")
        )

        return TransactionSummaryDTO(
            total_debit=total_debit,
            total_kredit=total_kredit,
            saldo_akhir=saldo_akhir,
            total_transaksi=len(df),
            avg_debit=avg_debit,
            avg_kredit=avg_kredit
        )

    def get_category_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        summary = (
            df.groupby("Kategori")[["Debit", "Kredit"]]
            .sum()
            .round(0)
        )
        summary["Net Balance"] = summary["Debit"] - summary["Kredit"]
        return summary

    def get_monthly_trend(
        self, df: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        if df.empty or len(df) <= 5:
            return None

        df_trend = df.copy()
        df_trend["Tanggal"] = pd.to_datetime(df_trend["Tanggal"])
        df_trend["Bulan"] = (
            df_trend["Tanggal"].dt.to_period("M").astype(str)
        )

        return (
            df_trend.groupby("Bulan")[["Debit", "Kredit"]]
            .sum()
            .reset_index()
        )

    # ======================================================
    # EXPORT
    # ======================================================
    def export_to_csv(self, df: pd.DataFrame) -> bytes:
        """
        Export CSV rapi & Excel (Indonesia) friendly
        """
        if df.empty:
            return b""

        export_df = df.copy()

        # Format tanggal
        if "Tanggal" in export_df.columns:
            export_df["Tanggal"] = (
                pd.to_datetime(export_df["Tanggal"], errors="coerce")
                .dt.strftime("%d-%m-%Y")
            )

        # Format angka
        for col in ["Debit", "Kredit", "Saldo"]:
            if col in export_df.columns:
                export_df[col] = export_df[col].apply(
                    lambda x: f"{Decimal(str(x)):.2f}"
                )

        # Rename kolom
        export_df.rename(columns={
            "Debit": "Debit (Rp)",
            "Kredit": "Kredit (Rp)",
            "Saldo": "Saldo (Rp)"
        }, inplace=True)

        return export_df.to_csv(
            index=False,
            sep=";",
            encoding="utf-8-sig"
        ).encode("utf-8-sig")

    # ======================================================
    # CLEAR DATA
    # ======================================================
    def clear_all_data(self) -> bool:
        try:
            return self.repository.clear_all()
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
            return False
