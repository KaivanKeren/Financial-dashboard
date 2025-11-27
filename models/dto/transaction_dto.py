from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass
class TransactionDTO:
    """
    DTO untuk response/read operations
    Digunakan untuk mengirim data dari service ke UI
    """
    id: Optional[int]
    tanggal: datetime
    deskripsi: str
    kategori: str
    debit: Decimal
    kredit: Decimal
    saldo: Decimal
    created_at: Optional[datetime] = None

    def is_income(self) -> bool:
        """Check apakah transaksi adalah pemasukan"""
        return self.debit > 0

    def is_expense(self) -> bool:
        """Check apakah transaksi adalah pengeluaran"""
        return self.kredit > 0

    def get_amount(self) -> Decimal:
        """Ambil jumlah transaksi (debit atau kredit)"""
        return self.debit if self.is_income() else self.kredit

    def get_type(self) -> str:
        """Return tipe transaksi"""
        return "Pemasukan" if self.is_income() else "Pengeluaran"

    def to_dict(self) -> dict:
        """Convert ke dictionary untuk serialization"""
        return {
            'id': self.id,
            'tanggal': self.tanggal.isoformat() if self.tanggal else None,
            'deskripsi': self.deskripsi,
            'kategori': self.kategori,
            'debit': float(self.debit),
            'kredit': float(self.kredit),
            'saldo': float(self.saldo),
            'tipe': self.get_type(),
            'jumlah': float(self.get_amount()),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_entity(cls, entity) -> 'TransactionDTO':
        """Create DTO dari Entity"""
        return cls(
            id=entity.id,
            tanggal=entity.tanggal,
            deskripsi=entity.deskripsi,
            kategori=entity.kategori,
            debit=entity.debit,
            kredit=entity.kredit,
            saldo=entity.saldo,
            created_at=entity.created_at
        )


@dataclass
class CreateTransactionDTO:
    """
    DTO untuk membuat transaksi baru
    Hanya field yang diperlukan untuk input
    """
    tanggal: datetime
    deskripsi: str
    kategori: str
    tipe: str  # "Pemasukan" atau "Pengeluaran"
    jumlah: Decimal

    def __post_init__(self):
        """Validasi input"""
        if not self.deskripsi:
            raise ValueError("Deskripsi tidak boleh kosong")

        if self.jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0")

        if self.tipe not in ["Pemasukan", "Pengeluaran"]:
            raise ValueError("Tipe harus 'Pemasukan' atau 'Pengeluaran'")

        # Convert to Decimal
        if not isinstance(self.jumlah, Decimal):
            self.jumlah = Decimal(str(self.jumlah))

    def get_debit(self) -> Decimal:
        """Return debit amount"""
        return self.jumlah if self.tipe == "Pemasukan" else Decimal('0')

    def get_kredit(self) -> Decimal:
        """Return kredit amount"""
        return self.jumlah if self.tipe == "Pengeluaran" else Decimal('0')

    def to_entity(self, saldo: Decimal) -> 'TransactionEntity':
        """
        Convert DTO ke Entity untuk disimpan ke database

        Args:
            saldo: Saldo akhir setelah transaksi ini
        """
        from models.entities.transaction import TransactionEntity

        return TransactionEntity(
            tanggal=self.tanggal,
            deskripsi=self.deskripsi,
            kategori=self.kategori,
            debit=self.get_debit(),
            kredit=self.get_kredit(),
            saldo=saldo
        )


@dataclass
class UpdateTransactionDTO:
    """
    DTO untuk update transaksi
    Semua field optional kecuali id
    """
    id: int
    tanggal: Optional[datetime] = None
    deskripsi: Optional[str] = None
    kategori: Optional[str] = None
    tipe: Optional[str] = None
    jumlah: Optional[Decimal] = None

    def __post_init__(self):
        """Validasi input"""
        if self.jumlah is not None and self.jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0")

        if self.tipe is not None and self.tipe not in ["Pemasukan", "Pengeluaran"]:
            raise ValueError("Tipe harus 'Pemasukan' atau 'Pengeluaran'")