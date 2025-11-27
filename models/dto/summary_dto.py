from dataclasses import dataclass
from decimal import Decimal
from typing import List


@dataclass
class TransactionSummaryDTO:
    """
    DTO untuk summary transaksi keseluruhan
    Digunakan untuk dashboard metrics
    """
    total_debit: Decimal = Decimal('0.00')
    total_kredit: Decimal = Decimal('0.00')
    saldo_akhir: Decimal = Decimal('0.00')
    total_transaksi: int = 0
    avg_debit: Decimal = Decimal('0.00')
    avg_kredit: Decimal = Decimal('0.00')

    def __post_init__(self):
        """Convert to Decimal if needed"""
        if not isinstance(self.total_debit, Decimal):
            self.total_debit = Decimal(str(self.total_debit))
        if not isinstance(self.total_kredit, Decimal):
            self.total_kredit = Decimal(str(self.total_kredit))
        if not isinstance(self.saldo_akhir, Decimal):
            self.saldo_akhir = Decimal(str(self.saldo_akhir))
        if not isinstance(self.avg_debit, Decimal):
            self.avg_debit = Decimal(str(self.avg_debit))
        if not isinstance(self.avg_kredit, Decimal):
            self.avg_kredit = Decimal(str(self.avg_kredit))

    def get_net_balance(self) -> Decimal:
        """Hitung net balance"""
        return self.total_debit - self.total_kredit

    def is_surplus(self) -> bool:
        """Check apakah surplus"""
        return self.saldo_akhir > 0

    def is_deficit(self) -> bool:
        """Check apakah defisit"""
        return self.saldo_akhir < 0

    def is_break_even(self) -> bool:
        """Check apakah break even"""
        return self.saldo_akhir == 0

    def get_status(self) -> str:
        """Return status keuangan"""
        if self.is_surplus():
            return "SURPLUS"
        elif self.is_deficit():
            return "DEFISIT"
        return "BREAK EVEN"

    def get_expense_ratio(self) -> float:
        """Return rasio pengeluaran terhadap pemasukan (%)"""
        if self.total_debit == 0:
            return 0.0
        return float((self.total_kredit / self.total_debit) * 100)

    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'total_debit': float(self.total_debit),
            'total_kredit': float(self.total_kredit),
            'saldo_akhir': float(self.saldo_akhir),
            'total_transaksi': self.total_transaksi,
            'avg_debit': float(self.avg_debit),
            'avg_kredit': float(self.avg_kredit),
            'net_balance': float(self.get_net_balance()),
            'status': self.get_status(),
            'expense_ratio': self.get_expense_ratio()
        }

@dataclass
class CategorySummaryDTO:
    """
    DTO untuk summary per kategori
    """
    kategori: str
    total_debit: Decimal = Decimal('0.00')
    total_kredit: Decimal = Decimal('0.00')
    net_balance: Decimal = Decimal('0.00')
    transaction_count: int = 0

    def __post_init__(self):
        """Convert to Decimal if needed"""
        if not isinstance(self.total_debit, Decimal):
            self.total_debit = Decimal(str(self.total_debit))
        if not isinstance(self.total_kredit, Decimal):
            self.total_kredit = Decimal(str(self.total_kredit))
        if not isinstance(self.net_balance, Decimal):
            self.net_balance = Decimal(str(self.net_balance))

    def get_percentage_of_total(self, total: Decimal) -> float:
        """Hitung persentase dari total"""
        if total == 0:
            return 0.0
        amount = self.total_kredit if self.total_kredit > 0 else self.total_debit
        return float((amount / total) * 100)

    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'kategori': self.kategori,
            'total_debit': float(self.total_debit),
            'total_kredit': float(self.total_kredit),
            'net_balance': float(self.net_balance),
            'transaction_count': self.transaction_count
        }


@dataclass
class MonthlyTrendDTO:
    """
    DTO untuk tren bulanan
    """
    bulan: str
    total_debit: Decimal = Decimal('0.00')
    total_kredit: Decimal = Decimal('0.00')
    saldo_akhir: Decimal = Decimal('0.00')
    transaction_count: int = 0

    def get_net(self) -> Decimal:
        """Net untuk bulan ini"""
        return self.total_debit - self.total_kredit

    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            'bulan': self.bulan,
            'total_debit': float(self.total_debit),
            'total_kredit': float(self.total_kredit),
            'saldo_akhir': float(self.saldo_akhir),
            'net': float(self.get_net()),
            'transaction_count': self.transaction_count
        }