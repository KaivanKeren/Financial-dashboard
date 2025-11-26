import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


class Dashboard:

    @staticmethod
    def render_metrics(metrics):
        """Render metrics cards"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Pemasukan",
                value=f"Rp {metrics['total_debit']:,.0f}",
                delta="Income"
            )
        with col2:
            st.metric(
                label="Total Pengeluaran",
                value=f"Rp {metrics['total_kredit']:,.0f}",
                delta="Expense",
                delta_color="inverse"
            )
        with col3:
            saldo = metrics['saldo_akhir']
            st.metric(
                label="Saldo Akhir",
                value=f"Rp {saldo:,.0f}",
                delta=f"{'+' if saldo >= 0 else ''}{saldo:,.0f}",
                delta_color="normal" if saldo >= 0 else "inverse"
            )
        with col4:
            st.metric(
                label="Total Transaksi",
                value=f"{metrics['total_transaksi']}",
                delta="Records"
            )

    @staticmethod
    def render_transaction_list(df):
        """Render daftar transaksi dengan filter"""
        st.subheader("Daftar Transaksi")

        # Filter
        col1, col2 = st.columns([2, 2])
        with col1:
            filter_kategori = st.multiselect(
                "Filter berdasarkan Kategori",
                options=df["Kategori"].unique(),
                default=df["Kategori"].unique()
            )

        # Apply filter
        filtered_df = df[df["Kategori"].isin(filter_kategori)]

        # Format display
        display_df = filtered_df.copy()
        display_df["Debit"] = display_df["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
        display_df["Kredit"] = display_df["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
        display_df["Saldo"] = display_df["Saldo"].apply(lambda x: f"Rp {x:,.0f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

    @staticmethod
    def render_visualizations(df, metrics):
        """Render visualisasi grafik"""
        st.subheader("Visualisasi Keuangan")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            kredit_by_kategori = df[df["Kredit"] > 0].groupby("Kategori")["Kredit"].sum()

            if not kredit_by_kategori.empty:
                fig_pie = px.pie(
                    values=kredit_by_kategori.values,
                    names=kredit_by_kategori.index,
                    title="Distribusi Pengeluaran per Kategori",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=True, height=400, margin=dict(t=50, b=20, l=20, r=20))
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Bar chart
            summary = pd.DataFrame({
                "Kategori": ["Pemasukan", "Pengeluaran"],
                "Jumlah": [metrics['total_debit'], metrics['total_kredit']]
            })

            fig_bar = px.bar(
                summary, x="Kategori", y="Jumlah",
                title="Perbandingan Pemasukan vs Pengeluaran",
                color="Kategori",
                color_discrete_map={"Pemasukan": "#10b981", "Pengeluaran": "#ef4444"},
                text="Jumlah"
            )
            fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
            fig_bar.update_layout(showlegend=False, height=400, margin=dict(t=50, b=20, l=20, r=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        # Line chart saldo
        st.markdown("<br>", unsafe_allow_html=True)
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df["Tanggal"], y=df["Saldo"],
            mode='lines+markers', name='Saldo',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6'),
            fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        fig_line.update_layout(
            title="Perkembangan Saldo dari Waktu ke Waktu",
            xaxis_title="Tanggal", yaxis_title="Saldo (Rp)",
            hovermode='x unified', height=400,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    @staticmethod
    def render_analysis(df, transaction_service, metrics):
        """Render analisis mendalam"""
        st.subheader("Analisis Mendalam")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Ringkasan per Kategori")
            kategori_summary = transaction_service.get_category_summary(df)
            if not kategori_summary.empty:
                styled_summary = kategori_summary.style.format({
                    "Debit": "Rp {:,.0f}",
                    "Kredit": "Rp {:,.0f}",
                    "Net Balance": "Rp {:,.0f}"
                })
                st.dataframe(styled_summary, use_container_width=True)

        with col2:
            st.markdown("#### Key Insights")

            # Rata-rata
            debit_trans = df[df["Debit"] > 0]
            kredit_trans = df[df["Kredit"] > 0]

            avg_debit = metrics['total_debit'] / len(debit_trans) if len(debit_trans) > 0 else 0
            avg_kredit = metrics['total_kredit'] / len(kredit_trans) if len(kredit_trans) > 0 else 0

            st.metric("Rata-rata Pemasukan", f"Rp {avg_debit:,.0f}")
            st.metric("Rata-rata Pengeluaran", f"Rp {avg_kredit:,.0f}")

            # Status
            st.markdown("<br>", unsafe_allow_html=True)
            saldo = metrics['saldo_akhir']
            if saldo > 0:
                st.success(f"Status: SURPLUS Rp {saldo:,.0f}")
            elif saldo < 0:
                st.error(f"Status: DEFISIT Rp {abs(saldo):,.0f}")
            else:
                st.info("Status: BREAK EVEN")

        # Tren bulanan
        monthly = transaction_service.get_monthly_trend(df)
        if monthly is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Tren Transaksi")

            fig_trend = go.Figure()
            fig_trend.add_trace(
                go.Bar(x=monthly["Bulan"], y=monthly["Debit"], name="Pemasukan", marker_color="#10b981"))
            fig_trend.add_trace(
                go.Bar(x=monthly["Bulan"], y=monthly["Kredit"], name="Pengeluaran", marker_color="#ef4444"))
            fig_trend.update_layout(barmode='group', height=350)
            st.plotly_chart(fig_trend, use_container_width=True)

    @staticmethod
    def render_management(df, transaction_service):
        """Render management transaksi"""
        st.subheader("Management Transaksi")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### Hapus Transaksi")
            display_manage = df.copy()
            display_manage["Debit"] = display_manage["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            display_manage["Kredit"] = display_manage["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            display_manage["Saldo"] = display_manage["Saldo"].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(display_manage, use_container_width=True, height=300)

        with col2:
            st.markdown("#### Aksi")
            index_to_delete = st.number_input(
                "Nomor Baris", min_value=0,
                max_value=len(df) - 1, step=1,
                help="Nomor baris dimulai dari 0"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Hapus Transaksi", use_container_width=True, type="primary"):
                if transaction_service.delete_transaction(index_to_delete):
                    st.success("Transaksi berhasil dihapus")
                    st.rerun()
