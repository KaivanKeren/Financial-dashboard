import streamlit as st
from datetime import datetime
from config.settings import Config


class Sidebar:

    @staticmethod
    def render(transaction_service, transactions_df):
        """Render sidebar berisi form transaksi, export CSV, dan settings."""

        st.header("Transaksi Baru")
        st.markdown("---")

        # Form transaksi
        with st.form("transaction_form"):
            tanggal_transaksi = st.date_input(
                "Tanggal Transaksi",
                value=datetime.now(),
                help="Pilih tanggal transaksi"
            )

            deskripsi = st.text_input(
                "Deskripsi",
                placeholder="Contoh: Gaji Bulanan"
            )

            kategori = st.selectbox("Kategori", Config.CATEGORIES)

            tipe_transaksi = st.radio(
                "Tipe",
                ["Pemasukan", "Pengeluaran"]
            )

            jumlah = st.number_input(
                "Jumlah (Rp)",
                min_value=0.0,
                step=1000.0,
                format="%.2f"
            )

            submit = st.form_submit_button(
                "Simpan Transaksi",
                use_container_width=True
            )

            if submit:
                success, message = transaction_service.add_transaction_legacy(
                    tanggal_transaksi, deskripsi, kategori, tipe_transaksi, jumlah
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        st.markdown("---")
        st.subheader("Export & Pengaturan")

        # Export CSV
        if not transactions_df.empty:
            csv_data = transaction_service.export_to_csv(transactions_df)

            st.download_button(
                label="Download Laporan CSV",
                data=csv_data,
                file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Clear all data
            if st.button("Hapus Semua Data", use_container_width=True, type="secondary"):
                if transaction_service.clear_all_data():
                    st.success("Semua data berhasil dihapus")
                    st.rerun()