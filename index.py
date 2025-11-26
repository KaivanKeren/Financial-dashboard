import streamlit as st
from datetime import datetime

# Import layers
from config.settings import Config
from database.repository import TransactionRepository
from services.transaction_service import TransactionService
from ui.styles import get_custom_css
from ui.sidebar import Sidebar
from ui.dashboard import Dashboard

# Page config
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout=Config.PAGE_LAYOUT,
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize database
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = TransactionRepository.init_database()

# Initialize service
transaction_service = TransactionService()

# Load transactions
if 'transactions' not in st.session_state:
    st.session_state.transactions = transaction_service.get_all_transactions()

# Refresh data
st.session_state.transactions = transaction_service.get_all_transactions()

# Header
st.title(Config.APP_TITLE)
st.markdown('<p class="subtitle">Kelola keuangan Anda dengan mudah dan efisien</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    Sidebar.render(transaction_service, st.session_state.transactions)

# Main content
if st.session_state.transactions.empty:
    st.info("Belum ada transaksi. Silakan tambahkan transaksi baru di sidebar kiri.")
else:
    # Get metrics
    metrics = transaction_service.get_summary_metrics(st.session_state.transactions)

    # Render metrics
    Dashboard.render_metrics(metrics)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Transaksi", "📊 Visualisasi", "📈 Analisis", "⚙️ Management"])

    with tab1:
        Dashboard.render_transaction_list(st.session_state.transactions)

    with tab2:
        Dashboard.render_visualizations(st.session_state.transactions, metrics)

    with tab3:
        Dashboard.render_analysis(st.session_state.transactions, transaction_service, metrics)

    with tab4:
        Dashboard.render_management(st.session_state.transactions, transaction_service)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>"
    f"{Config.APP_TITLE} | Powered by Streamlit | © {datetime.now().year}"
    f"</div>",
    unsafe_allow_html=True
)