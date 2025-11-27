from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass
class TransactionEntity:
    """
    Entity yang merepresentasikan tabel transactions di database
    Mapping 1:1 dengan struktur tabel
    """
    id: Optional[int] = None
    tanggal: Optional[datetime] = None
    deskripsi: str = ""
    kategori: str = ""
    debit: Decimal = Decimal('0.00')
    kredit: Decimal = Decimal('0.00')
    saldo: Decimal = Decimal('0.00')
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Konversi otomatis ke Decimal untuk konsistensi"""
        if not isinstance(self.debit, Decimal):
            self.debit = Decimal(str(self.debit))
        if not isinstance(self.kredit, Decimal):
            self.kredit = Decimal(str(self.kredit))
        if not isinstance(self.saldo, Decimal):
            self.saldo = Decimal(str(self.saldo))

    @classmethod
    def from_db_row(cls, row: tuple) -> 'TransactionEntity':
        """
        Create entity dari database row

        Args:
            row: tuple dari cursor.fetchone() atau cursor.fetchall()
            Expected format: (id, tanggal, deskripsi, kategori, debit, kredit, saldo, created_at)
        """
        if len(row) >= 8:
            return cls(
                id=row[0],
                tanggal=row[1],
                deskripsi=row[2],
                kategori=row[3],
                debit=Decimal(str(row[4])),
                kredit=Decimal(str(row[5])),
                saldo=Decimal(str(row[6])),
                created_at=row[7]
            )
        # Fallback untuk query tanpa id dan created_at
        return cls(
            tanggal=row[0],
            deskripsi=row[1],
            kategori=row[2],
            debit=Decimal(str(row[3])),
            kredit=Decimal(str(row[4])),
            saldo=Decimal(str(row[5]))
        )