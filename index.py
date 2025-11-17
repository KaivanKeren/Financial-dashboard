import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2 import sql
from contextlib import contextmanager

# Konfigurasi halaman
st.set_page_config(
    page_title="Financial Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan lebih professional
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #f8f9fa;
    }
    h1 {
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    h2, h3 {
        color: #334155;
        font-weight: 600;
    }
    .subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)


# Database Configuration
@contextmanager
def get_db_connection():
    """Context manager untuk koneksi database"""
    conn = None
    try:
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


def init_database():
    """Inisialisasi tabel database"""
    with get_db_connection() as conn:
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


def load_transactions_from_db():
    """Load semua transaksi dari database"""
    with get_db_connection() as conn:
        if conn:
            try:
                query = """
                        SELECT tanggal, deskripsi, kategori, debit, kredit, saldo
                        FROM transactions
                        ORDER BY id ASC
                        """
                df = pd.read_sql_query(query, conn)
                df.columns = ["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"]
                return df
            except Exception as e:
                st.error(f"Error loading transactions: {str(e)}")
                return pd.DataFrame(columns=["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"])
    return pd.DataFrame(columns=["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"])


def save_transaction_to_db(tanggal, deskripsi, kategori, debit, kredit, saldo):
    """Simpan transaksi ke database"""
    with get_db_connection() as conn:
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


def delete_transaction_from_db(index):
    """Hapus transaksi dari database berdasarkan index"""
    with get_db_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                # Get transaction id at index
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

                    # Recalculate all balances
                    recalculate_all_balances()
                    cursor.close()
                    return True
            except Exception as e:
                st.error(f"Error deleting transaction: {str(e)}")
                return False
    return False


def recalculate_all_balances():
    """Recalculate semua saldo setelah penghapusan"""
    with get_db_connection() as conn:
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


def clear_all_transactions():
    """Hapus semua transaksi dari database"""
    with get_db_connection() as conn:
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


# Initialize database
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = init_database()

# Inisialisasi session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = load_transactions_from_db()


def get_last_balance():
    """Mendapatkan saldo terakhir dari database"""
    with get_db_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                               SELECT saldo
                               FROM transactions
                               ORDER BY id DESC LIMIT 1
                               """)
                result = cursor.fetchone()
                cursor.close()

                if result:
                    return float(result[0])
                return 0
            except Exception as e:
                st.error(f"Error getting last balance: {str(e)}")
                return 0
    return 0


def add_transaction(tanggal, deskripsi, kategori, debit=0, kredit=0):
    """Menambah transaksi baru"""
    # Ambil saldo terakhir langsung dari database
    saldo_awal = get_last_balance()
    saldo_akhir = saldo_awal + debit - kredit

    # Simpan ke database
    if save_transaction_to_db(tanggal, deskripsi, kategori, debit, kredit, saldo_akhir):
        # Reload data dari database
        st.session_state.transactions = load_transactions_from_db()
        return True
    return False


def delete_transaction(index):
    """Menghapus transaksi dan recalculate saldo"""
    if delete_transaction_from_db(index):
        # Reload data dari database
        st.session_state.transactions = load_transactions_from_db()
        return True
    return False


def export_to_csv():
    """Export data ke CSV"""
    return st.session_state.transactions.to_csv(index=False).encode('utf-8')


# Header
st.title("Financial Dashboard")
st.markdown('<p class="subtitle">Kelola keuangan Anda dengan mudah dan efisien</p>', unsafe_allow_html=True)

# Sidebar untuk input transaksi
with st.sidebar:
    st.header("Transaksi Baru")
    st.markdown("---")

    with st.form("transaction_form"):
        tanggal_transaksi = st.date_input(
            "Tanggal Transaksi",
            value=datetime.now(),
            help="Pilih tanggal transaksi"
        )

        deskripsi = st.text_input("Deskripsi", placeholder="Contoh: Gaji Bulanan")

        kategori = st.selectbox(
            "Kategori",
            ["Pendapatan", "Pengeluaran", "Investasi", "Operasional", "Lainnya"]
        )

        tipe_transaksi = st.radio("Tipe", ["Pemasukan", "Pengeluaran"])

        jumlah = st.number_input("Jumlah (Rp)", min_value=0.0, step=1000.0, format="%.2f")

        submit = st.form_submit_button("Simpan Transaksi", use_container_width=True)

        if submit:
            if deskripsi and jumlah > 0:
                # Konversi date ke datetime
                tanggal_datetime = datetime.combine(tanggal_transaksi, datetime.min.time())

                if tipe_transaksi == "Pemasukan":
                    add_transaction(tanggal_datetime, deskripsi, kategori, debit=jumlah, kredit=0)
                    st.success("Transaksi berhasil ditambahkan")
                else:
                    add_transaction(tanggal_datetime, deskripsi, kategori, debit=0, kredit=jumlah)
                    st.success("Transaksi berhasil ditambahkan")
                st.rerun()
            else:
                st.error("Mohon isi semua field dengan benar")

    st.markdown("---")
    st.subheader("Export & Pengaturan")

    if not st.session_state.transactions.empty:
        csv = export_to_csv()
        st.download_button(
            label="Download Laporan CSV",
            data=csv,
            file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Hapus Semua Data", use_container_width=True, type="secondary"):
            if clear_all_transactions():
                st.session_state.transactions = pd.DataFrame(
                    columns=["Tanggal", "Deskripsi", "Kategori", "Debit", "Kredit", "Saldo"]
                )
                st.success("Semua data berhasil dihapus")
                st.rerun()

# Main content
if st.session_state.transactions.empty:
    st.info("Belum ada transaksi. Silakan tambahkan transaksi baru di sidebar kiri.")
else:
    # Metrics Dashboard
    col1, col2, col3, col4 = st.columns(4)

    total_debit = st.session_state.transactions["Debit"].sum()
    total_kredit = st.session_state.transactions["Kredit"].sum()
    saldo_akhir = get_last_balance()
    total_transaksi = len(st.session_state.transactions)

    with col1:
        st.metric(
            label="Total Pemasukan",
            value=f"Rp {total_debit:,.0f}",
            delta="Income"
        )
    with col2:
        st.metric(
            label="Total Pengeluaran",
            value=f"Rp {total_kredit:,.0f}",
            delta="Expense",
            delta_color="inverse"
        )
    with col3:
        status = "positive" if saldo_akhir >= 0 else "negative"
        st.metric(
            label="Saldo Akhir",
            value=f"Rp {saldo_akhir:,.0f}",
            delta=f"{'+' if saldo_akhir >= 0 else ''}{saldo_akhir:,.0f}",
            delta_color="normal" if saldo_akhir >= 0 else "inverse"
        )
    with col4:
        st.metric(
            label="Total Transaksi",
            value=f"{total_transaksi}",
            delta="Records"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs untuk berbagai view
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Transaksi", "📊 Visualisasi", "📈 Analisis", "⚙️ Management"])

    with tab1:
        st.subheader("Daftar Transaksi")

        # Filter
        col1, col2 = st.columns([2, 2])
        with col1:
            filter_kategori = st.multiselect(
                "Filter berdasarkan Kategori",
                options=st.session_state.transactions["Kategori"].unique(),
                default=st.session_state.transactions["Kategori"].unique()
            )

        # Apply filter
        filtered_df = st.session_state.transactions[
            st.session_state.transactions["Kategori"].isin(filter_kategori)
        ]

        # Format untuk tampilan
        display_df = filtered_df.copy()
        display_df["Debit"] = display_df["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
        display_df["Kredit"] = display_df["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
        display_df["Saldo"] = display_df["Saldo"].apply(lambda x: f"Rp {x:,.0f}")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

    with tab2:
        st.subheader("Visualisasi Keuangan")

        # Row 1: Pie and Bar charts
        col1, col2 = st.columns(2)

        with col1:
            # Pie chart kategori pengeluaran
            kredit_by_kategori = st.session_state.transactions[
                st.session_state.transactions["Kredit"] > 0
                ].groupby("Kategori")["Kredit"].sum()

            if not kredit_by_kategori.empty:
                fig_pie = px.pie(
                    values=kredit_by_kategori.values,
                    names=kredit_by_kategori.index,
                    title="Distribusi Pengeluaran per Kategori",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(
                    showlegend=True,
                    height=400,
                    margin=dict(t=50, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Bar chart debit vs kredit
            summary = pd.DataFrame({
                "Kategori": ["Pemasukan", "Pengeluaran"],
                "Jumlah": [total_debit, total_kredit]
            })

            fig_bar = px.bar(
                summary,
                x="Kategori",
                y="Jumlah",
                title="Perbandingan Pemasukan vs Pengeluaran",
                color="Kategori",
                color_discrete_map={"Pemasukan": "#10b981", "Pengeluaran": "#ef4444"},
                text="Jumlah"
            )
            fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
            fig_bar.update_layout(
                showlegend=False,
                height=400,
                margin=dict(t=50, b=20, l=20, r=20),
                yaxis_title="Jumlah (Rp)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Row 2: Line chart saldo
        st.markdown("<br>", unsafe_allow_html=True)

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=st.session_state.transactions["Tanggal"],
            y=st.session_state.transactions["Saldo"],
            mode='lines+markers',
            name='Saldo',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        fig_line.update_layout(
            title="Perkembangan Saldo dari Waktu ke Waktu",
            xaxis_title="Tanggal",
            yaxis_title="Saldo (Rp)",
            hovermode='x unified',
            height=400,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with tab3:
        st.subheader("Analisis Mendalam")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Ringkasan per Kategori")
            kategori_summary = st.session_state.transactions.groupby("Kategori").agg({
                "Debit": "sum",
                "Kredit": "sum"
            }).round(0)
            kategori_summary["Net Balance"] = kategori_summary["Debit"] - kategori_summary["Kredit"]
            kategori_summary = kategori_summary.style.format({
                "Debit": "Rp {:,.0f}",
                "Kredit": "Rp {:,.0f}",
                "Net Balance": "Rp {:,.0f}"
            })
            st.dataframe(kategori_summary, use_container_width=True)

        with col2:
            st.markdown("#### Key Insights")

            # Rata-rata transaksi
            avg_debit = total_debit / len(
                st.session_state.transactions[st.session_state.transactions["Debit"] > 0]
            ) if len(st.session_state.transactions[st.session_state.transactions["Debit"] > 0]) > 0 else 0

            avg_kredit = total_kredit / len(
                st.session_state.transactions[st.session_state.transactions["Kredit"] > 0]
            ) if len(st.session_state.transactions[st.session_state.transactions["Kredit"] > 0]) > 0 else 0

            st.metric("Rata-rata Pemasukan", f"Rp {avg_debit:,.0f}")
            st.metric("Rata-rata Pengeluaran", f"Rp {avg_kredit:,.0f}")

            # Status keuangan
            st.markdown("<br>", unsafe_allow_html=True)
            if saldo_akhir > 0:
                st.success(f"Status: SURPLUS Rp {saldo_akhir:,.0f}")
            elif saldo_akhir < 0:
                st.error(f"Status: DEFISIT Rp {abs(saldo_akhir):,.0f}")
            else:
                st.info("Status: BREAK EVEN")

            # Kategori terbesar
            kredit_by_kategori = st.session_state.transactions[
                st.session_state.transactions["Kredit"] > 0
                ].groupby("Kategori")["Kredit"].sum()

            if not kredit_by_kategori.empty:
                max_kategori = kredit_by_kategori.idxmax()
                max_nilai = kredit_by_kategori.max()
                st.info(f"Pengeluaran Terbesar: {max_kategori} (Rp {max_nilai:,.0f})")

        # Grafik tren bulanan jika ada data cukup
        st.markdown("<br>", unsafe_allow_html=True)
        if len(st.session_state.transactions) > 5:
            st.markdown("#### Tren Transaksi")

            df_trend = st.session_state.transactions.copy()
            df_trend["Tanggal"] = pd.to_datetime(df_trend["Tanggal"])
            df_trend["Bulan"] = df_trend["Tanggal"].dt.to_period("M").astype(str)

            monthly = df_trend.groupby("Bulan").agg({
                "Debit": "sum",
                "Kredit": "sum"
            }).reset_index()

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=monthly["Bulan"],
                y=monthly["Debit"],
                name="Pemasukan",
                marker_color="#10b981"
            ))
            fig_trend.add_trace(go.Bar(
                x=monthly["Bulan"],
                y=monthly["Kredit"],
                name="Pengeluaran",
                marker_color="#ef4444"
            ))

            fig_trend.update_layout(
                barmode='group',
                xaxis_title="Periode",
                yaxis_title="Jumlah (Rp)",
                height=350,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with tab4:
        st.subheader("Management Transaksi")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### Hapus Transaksi")
            st.write("Pilih nomor baris transaksi yang ingin dihapus dari tabel di bawah ini.")

            # Tampilkan tabel dengan index
            display_manage = st.session_state.transactions.copy()
            display_manage["Debit"] = display_manage["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            display_manage["Kredit"] = display_manage["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            display_manage["Saldo"] = display_manage["Saldo"].apply(lambda x: f"Rp {x:,.0f}")

            st.dataframe(display_manage, use_container_width=True, height=300)

        with col2:
            st.markdown("#### Aksi")
            index_to_delete = st.number_input(
                "Nomor Baris",
                min_value=0,
                max_value=len(st.session_state.transactions) - 1,
                step=1,
                help="Nomor baris dimulai dari 0"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Hapus Transaksi", use_container_width=True, type="primary"):
                delete_transaction(index_to_delete)
                st.success("Transaksi berhasil dihapus")
                st.rerun()

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>"
    f"Financial Dashboard Pro | Powered by Streamlit | © {datetime.now().year}"
    f"</div>",
    unsafe_allow_html=True
)