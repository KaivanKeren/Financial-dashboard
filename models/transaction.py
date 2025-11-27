from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class Transaction:
    """Model untuk transaksi keuangan"""
    id: Optional[int] = None
    tanggal: datetime = None
    deskripsi: str = ""
    kategori: str = ""
    debit: Decimal = Decimal('0.00')
    kredit: Decimal = Decimal('0.00')
    saldo: Decimal = Decimal('0.00')
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validasi setelah inisialisasi"""
        if self.tanggal is None:
            self.tanggal = datetime.now()

        # Convert to Decimal if needed
        if not isinstance(self.debit, Decimal):
            self.debit = Decimal(str(self.debit))
        if not isinstance(self.kredit, Decimal):
            self.kredit = Decimal(str(self.kredit))
        if not isinstance(self.saldo, Decimal):
            self.saldo = Decimal(str(self.saldo))

    def is_income(self) -> bool:
        """Check apakah transaksi adalah pemasukan"""
        return self.debit > 0

    def is_expense(self) -> bool:
        """Check apakah transaksi adalah pengeluaran"""
        return self.kredit > 0

    def get_amount(self) -> Decimal:
        """Ambil jumlah transaksi (debit atau kredit)"""
        return self.debit if self.is_income() else self.kredit

    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'id': self.id,
            'tanggal': self.tanggal,
            'deskripsi': self.deskripsi,
            'kategori': self.kategori,
            'debit': float(self.debit),
            'kredit': float(self.kredit),
            'saldo': float(self.saldo),
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create instance dari dictionary"""
        return cls(
            id=data.get('id'),
            tanggal=data.get('tanggal'),
            deskripsi=data.get('deskripsi', ''),
            kategori=data.get('kategori', ''),
            debit=Decimal(str(data.get('debit', 0))),
            kredit=Decimal(str(data.get('kredit', 0))),
            saldo=Decimal(str(data.get('saldo', 0))),
            created_at=data.get('created_at')
        )

    @classmethod
    def from_tuple(cls, data: tuple) -> 'Transaction':
        """Create instance dari tuple (database result)"""
        return cls(
            id=data[0] if len(data) > 7 else None,
            tanggal=data[1] if len(data) > 7 else data[0],
            deskripsi=data[2] if len(data) > 7 else data[1],
            kategori=data[3] if len(data) > 7 else data[2],
            debit=Decimal(str(data[4] if len(data) > 7 else data[3])),
            kredit=Decimal(str(data[5] if len(data) > 7 else data[4])),
            saldo=Decimal(str(data[6] if len(data) > 7 else data[5])),
            created_at=data[7] if len(data) > 7 else None
        )


@dataclass
class TransactionSummary:
    """Model untuk summary transaksi"""
    total_debit: Decimal = Decimal('0.00')
    total_kredit: Decimal = Decimal('0.00')
    saldo_akhir: Decimal = Decimal('0.00')
    total_transaksi: int = 0
    avg_debit: Decimal = Decimal('0.00')
    avg_kredit: Decimal = Decimal('0.00')

    def get_net_balance(self) -> Decimal:
        """Hitung net balance"""
        return self.total_debit - self.total_kredit

    def is_surplus(self) -> bool:
        """Check apakah surplus"""
        return self.saldo_akhir > 0

    def is_deficit(self) -> bool:
        """Check apakah defisit"""
        return self.saldo_akhir < 0

    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'total_debit': float(self.total_debit),
            'total_kredit': float(self.total_kredit),
            'saldo_akhir': float(self.saldo_akhir),
            'total_transaksi': self.total_transaksi,
            'avg_debit': float(self.avg_debit),
            'avg_kredit': float(self.avg_kredit)
        }


@dataclass
class CategorySummary:
    """Model untuk summary per kategori"""
    kategori: str
    total_debit: Decimal = Decimal('0.00')
    total_kredit: Decimal = Decimal('0.00')
    net_balance: Decimal = Decimal('0.00')
    transaction_count: int = 0

    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'kategori': self.kategori,
            'total_debit': float(self.total_debit),
            'total_kredit': float(self.total_kredit),
            'net_balance': float(self.net_balance),
            'transaction_count': self.transaction_count
        }