# app.py
import streamlit as st
import pandas as pd
import altair as alt
from config import MARGIN_DODO, DEFAULT_PRICES, DEFAULT_PETTY_CASH, DEFAULT_CIT_PICKUP, DEFAULT_ICT_COST, DEFAULT_STARTUP_COST
from calculator import calculate_manpower_cost_ptpr, calculate_manpower_cost_mitra, calculate_product_details, calculate_kso_tac
from export_utils import generate_excel_report, generate_pdf_standard_proposal, generate_pdf_comprehensive_report

st.set_page_config(page_title="Kalkulator KSO TAC", layout="wide")

# ==========================================
# INJEKSI CUSTOM CSS (UI/UX BRANDING PTPR)
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Futura', 'Plus Jakarta Sans', 'Montserrat', sans-serif !important;
}

/* Custom Cards */
.metric-card-blue {
    background-color: #FFFFFF; border-radius: 8px; padding: 16px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #0055A6; margin-bottom: 16px;
}
.metric-card-red {
    background-color: #FFFFFF; border-radius: 8px; padding: 16px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #ED1C24; margin-bottom: 16px;
}
.metric-card-gray {
    background-color: #FFFFFF; border-radius: 8px; padding: 16px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #808080; margin-bottom: 16px;
}
.hero-card-blue {
    background-color: #FFFFFF; border-radius: 8px; padding: 24px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.1); border-top: 6px solid #0055A6; margin-bottom: 24px; text-align: center;
}
.hero-card-green {
    background-color: #FFFFFF; border-radius: 8px; padding: 24px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.1); border-top: 6px solid #58B932; margin-bottom: 24px; text-align: center;
}

/* Typography for Cards */
.metric-value { font-size: 28px; font-weight: 700; color: #082313; margin: 4px 0; }
.hero-value { font-size: 36px; font-weight: 800; color: #082313; margin: 8px 0; }
.metric-label { font-size: 14px; color: #555555; font-weight: 600; }
.metric-caption { font-size: 12px; color: #888888; margin-top: 4px; }

/* Callouts & Banners */
.callout-blue {
    background-color: rgba(0, 85, 166, 0.08); border-left: 4px solid #0055A6;
    padding: 14px 16px; border-radius: 4px; margin-bottom: 16px; color: #082313;
}
.banner-feasible {
    background-color: #58B932; color: white; padding: 16px; border-radius: 8px; font-weight: 700; text-align: center; margin-bottom: 20px; font-size: 16px;
}
.banner-unfeasible {
    background-color: #ED1C24; color: white; padding: 16px; border-radius: 8px; font-weight: 700; text-align: center; margin-bottom: 20px; font-size: 16px;
}
.banner-info {
    background-color: rgba(0, 85, 166, 0.1); border: 1px solid #0055A6; color: #0055A6; padding: 16px; border-radius: 8px; font-weight: 600; text-align: center; margin-bottom: 20px;
}

/* Internal Dashboard Container */
.internal-dash {
    background-color: #E9ECEF; padding: 24px; border-radius: 12px; margin-top: 16px; margin-bottom: 24px;
}

/* Custom Table Header */
.table-header-dark {
    background-color: #082313; color: white; padding: 12px; border-radius: 4px; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Helper Functions (Didefinisikan paling atas agar selalu siap dipanggil)
def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(',', '.')

def format_angka(angka):
    return f"{angka:,.0f}".replace(',', '.')

def style_df(df):
    return df.style.set_table_styles([
        dict(selector='th', props=[('background-color', '#082313'), ('color', 'white'), ('font-weight', 'bold')])
    ])

# Header Utama
st.title("Simulasi Kemitraan KSO TAC")
st.caption("PT Pertamina Retail - Financial Feasibility & Revenue Calculator for KSO TAC")

# Sidebar
with st.sidebar:
    st.header("Parameter Utama SPBU")
    spbu_name = st.text_input("Identitas / Nomor SPBU", value="SPBU 44.xxx.xx")
    grading = st.selectbox("Grading Pertamina Way", ["Basic", "Good", "Excellent"], index=1)
    umk = st.number_input("UMK Wilayah SPBU (Rp)", value=3200000, step=100000)
    bur_salary = st.number_input("Payroll BUR (Rp)", value=5500000, step=250000)
    
    st.divider()
    sharing_ratio_owner = st.slider("Porsi Sharing Margin Mitra (%)", min_value=10.0, max_value=90.0, value=60.0, step=0.5) / 100.0

    st.divider()
    include_mitra_opex = st.toggle("Sertakan OPEX SPBU Mitra", value=False)
    
    multi_year_mode = st.toggle("Proyeksi Multi-Tahun (1-5 Thn)", value=False)
    if multi_year_mode:
        contract_years = st.slider("Durasi Kontrak (Tahun)", 1, 5, 3)
        sales_growth_pct = st.number_input("Kenaikan Sales/Tahun (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.5) / 100.0
    else:
        contract_years = 1
        sales_growth_pct = 0.0

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Sales & Losses", 
    "2. Manpower", 
    "3. OPEX & Taxes", 
    "4. Contract Summary", 
    "5. Comprehensive Summary",
    "6. Visual Analytics"
])

# === TAB 1: SALES & LOSSES ===
with tab1:
    st.subheader("Data Sales & Losses BBM")
    col_nc, _ = st.columns([1, 3])
    non_cash_pct = col_nc.number_input("Porsi Transaksi Non-Tunai (%)", value=30.0, max_value=100.0, step=1.0)
    
    sales_volume = {}
    selling_prices = {}
    loss_percentages = {}
    
    cols = st.columns([1.5, 2, 2, 2])
    cols[0].markdown('<div class="table-header-dark">Produk BBM</div>', unsafe_allow_html=True)
    cols[1].markdown('<div class="table-header-dark">Harga Jual (Rp/Liter)</div>', unsafe_allow_html=True)
    cols[2].markdown('<div class="table-header-dark">Volume Bulanan (Liter)</div>', unsafe_allow_html=True)
    cols[3].markdown('<div class="table-header-dark">Estimasi Losses/Gain (%)</div>', unsafe_allow_html=True)
    st.write("") 
    
    for prod in MARGIN_DODO.keys():
        c1, c2, c3, c4 = st.columns([1.5, 2, 2, 2])
        c1.write(f"**{prod}**")
        price = c2.number_input(f"Harga {prod}", value=DEFAULT_PRICES[prod], step=100, key=f"price_{prod}", label_visibility="collapsed")
        vol = c3.number_input(f"Vol {prod}", value=30000 if "Pertalite" in prod or "Pertamax" in prod else 0, step=1000, key=f"vol_{prod}", label_visibility="collapsed")
        loss = c4.number_input(f"Loss {prod}", value=-0.1, step=0.01, format="%.2f", key=f"loss_{prod}", label_visibility="collapsed")
        
        selling_prices[prod] = price
        sales_volume[prod] = vol
        loss_percentages[prod] = loss
    
    st.divider()
    st.subheader("Ringkasan Estimasi Penjualan Bulanan")
    summary_table_data = []
    for prod, vol in sales_volume.items():
        if vol > 0:
            summary_table_data.append({
                "Produk BBM": prod,
                "Harga Jual": format_rupiah(selling_prices[prod]),
                "Volume Bulanan": f"{format_angka(vol)} Liter",
                "Estimasi Losses/Gain (%)": f"{loss_percentages[prod]:.2f}%",
                "Proyeksi Omset Kotor": format_rupiah(vol * selling_prices[prod])
            })
    if summary_table_data:
        df_summary = pd.DataFrame(summary_table_data)
        st.dataframe(style_df(df_summary), use_container_width=True, hide_index=True)
    st.caption(f"**Total Volume Penjualan BBM:** {format_angka(sum(sales_volume.values()))} Liter / Bulan")

# === TAB 2: MANPOWER ===
with tab2:
    st.subheader("Alokasi & Beban Tenaga Kerja")
    
    with st.container(border=True):
        st.markdown("##### **Bagian A: Perwakilan PTPR (BUR & Admin)**")
        c_m1, c_m2 = st.columns(2)
        num_admin = c_m1.number_input("Jumlah Admin PTPR", min_value=0, value=1, step=1)
        num_bur = c_m2.number_input("Jumlah BUR PTPR", min_value=0, value=1, step=1)
        manpower_ptpr = calculate_manpower_cost_ptpr(umk, bur_salary, num_admin, num_bur)
        st.markdown(f'<div class="callout-blue"><b>Total Beban Tenaga Kerja PTPR ({format_angka(num_admin + num_bur)} Orang):</b> {format_rupiah(manpower_ptpr["total_manpower_ptpr"])}</div>', unsafe_allow_html=True)

    manpower_mitra = None
    if include_mitra_opex:
        with st.container(border=True):
            st.markdown("##### **Bagian B: Karyawan SPBU Mitra (Operator, Security, CS)**")
            salary_type = st.radio("Skema Gaji Karyawan:", ["Berbasis UMK Wilayah", "Nominal Custom"], horizontal=True)
            c_k1, c_k2 = st.columns(2)
            num_karyawan_mitra = c_k1.number_input("Jumlah Total Karyawan SPBU", min_value=0, value=8, step=1)
            
            if salary_type == "Berbasis UMK Wilayah":
                base_salary_mitra = umk
                # PENYESUAIAN OPSI B (Biru Callout & Sejajar Presisi)
                c_k2.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                c_k2.markdown(f'<div class="callout-blue"><b>Acuan UMK Wilayah:</b> {format_rupiah(umk)}</div>', unsafe_allow_html=True)
            else:
                base_salary_mitra = c_k2.number_input("Nominal Gaji Dasar Per Orang (Rp)", value=2800000, step=100000)
                
            manpower_mitra = calculate_manpower_cost_mitra(base_salary_mitra, num_karyawan_mitra)
            st.markdown(f'<div class="callout-blue"><b>Total Beban Tenaga Kerja SPBU Mitra ({format_angka(num_karyawan_mitra)} Orang):</b> {format_rupiah(manpower_mitra["total_karyawan_mitra"])}</div>', unsafe_allow_html=True)

product_summary = calculate_product_details(grading, sales_volume, selling_prices, loss_percentages)

# === TAB 3: OPEX & TAXES ===
with tab3:
    st.subheader("OPEX & Taxes")
    
    with st.container(border=True):
        st.markdown("##### **Bagian A: OPEX & Taxes PTPR**")
        o_col1, o_col2 = st.columns(2)
        with o_col1:
            petty_cash = st.number_input("Petty Cash BUR & Admin (Rp/Bulan)", value=DEFAULT_PETTY_CASH, step=100000)
            cit_pickup = st.number_input("Layanan Pick-Up / CIT (Rp/Bulan)", value=DEFAULT_CIT_PICKUP, step=500000)
            ict_cost = st.number_input("Sewa & Maintenance ICT (Rp/Bulan)", value=DEFAULT_ICT_COST, step=100000)
        with o_col2:
            startup_cost = st.number_input("Biaya Start-Up (Rp - Khusus Bulan Pertama)", value=DEFAULT_STARTUP_COST, step=100000)
            st.markdown(f'<div class="callout-blue"><b>Overhead HO PTPR (Rp15/Liter):</b> {format_rupiah(product_summary["total_volume"]*15)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="callout-blue"><b>PPh PTPR (0,25% x Basic Price):</b> {format_rupiah(product_summary["pph_tax"])}</div>', unsafe_allow_html=True)

    utilitas_mitra = 0
    maintenance_mitra = 0
    if include_mitra_opex:
        with st.container(border=True):
            st.markdown("##### **Bagian B: OPEX SPBU Mitra**")
            m_col1, m_col2 = st.columns(2)
            utilitas_mitra = m_col1.number_input("Biaya Utilitas (Listrik & Air) (Rp/Bulan)", value=7500000, step=500000)
            maintenance_mitra = m_col2.number_input("Pemeliharaan & Perbaikan Sarfas (Rp/Bulan)", value=3000000, step=500000)

kso_summary = calculate_kso_tac(
    product_summary, manpower_ptpr, non_cash_pct,
    petty_cash, cit_pickup, ict_cost, startup_cost, sharing_ratio_owner,
    include_mitra_opex, manpower_mitra, utilitas_mitra, maintenance_mitra,
    multi_year_mode, contract_years, sales_growth_pct
)

tahun_mapping = {
    "Tahun Ke-1": "Tahun Pertama", "Tahun Ke-2": "Tahun Kedua",
    "Tahun Ke-3": "Tahun Ketiga", "Tahun Ke-4": "Tahun Keempat", "Tahun Ke-5": "Tahun Kelima"
}

if multi_year_mode:
    df_my = pd.DataFrame(kso_summary['yearly_projections'])
    df_my["Tahun"] = df_my["Tahun"].replace(tahun_mapping)
    df_my = df_my.rename(columns={
        "Gross Share Owner (Rp)": "Gross Share Mitra (Rp)",
        "Impact Loss/Gain (Rp)": "Penyesuaian Losses/Gain (Rp)",
        "Standard Net Payout (Rp)": "Net Payout Mitra (Rp)",
        "True Net Income (Rp)": "True Net Income Mitra (Rp)",
        "Total OPEX Site Mitra (Rp)": "Total OPEX SPBU Mitra (Rp)"
    })

# === TAB 4: CONTRACT SUMMARY ===
with tab4:
    st.subheader("Contract Summary")
    st.write("**Rincian Nilai Sharing Margin Mitra:**")
    
    st.markdown(f"""
    <div style="display: flex; gap: 16px; flex-wrap: wrap;">
        <div class="metric-card-blue" style="flex: 1; min-width: 250px;">
            <div class="metric-label">Gross Share Mitra (Sebelum Losses/Gain)</div>
            <div class="metric-value">{format_rupiah(kso_summary['owner_gross_share'])}</div>
        </div>
        <div class="metric-card-blue" style="flex: 1; min-width: 250px;">
            <div class="metric-label">Penyesuaian Losses/Gain BBM</div>
            <div class="metric-value">{format_rupiah(product_summary['total_loss_gain_rp'])}</div>
        </div>
        <div class="metric-card-blue" style="flex: 1; min-width: 250px;">
            <div class="metric-label">Proyeksi Net Payout Bulanan Mitra</div>
            <div class="metric-value">{format_rupiah(kso_summary['owner_net_standard_monthly'])}</div>
        </div>
    </div>
    <div class="hero-card-blue">
        <div class="metric-label">Proyeksi Net Payout Mitra (Tahun Pertama)</div>
        <div class="hero-value">{format_rupiah(kso_summary['owner_net_standard_yearly'])}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if multi_year_mode:
        st.write(f"#### Proyeksi Multi-Tahun Mitra ({contract_years} Tahun)")
        st.markdown(f"<p style='font-size:13px; color:#555555; margin-top:-10px; margin-bottom:12px;'>Dihitung berdasarkan asumsi kenaikan volume penjualan sebesar {sales_growth_pct*100:.1f}%/tahun</p>", unsafe_allow_html=True)
        df_owner = df_my[["Tahun", "Gross Share Mitra (Rp)", "Penyesuaian Losses/Gain (Rp)", "Net Payout Mitra (Rp)"]].copy()
        for col in df_owner.columns[1:]:
            df_owner[col] = df_owner[col].apply(format_rupiah)
        st.dataframe(style_df(df_owner), use_container_width=True, hide_index=True)
        
        total_payout_acc = df_my["Net Payout Mitra (Rp)"].sum()
        st.info(f"**Total Akumulasi Net Payout Mitra ({contract_years} Tahun): {format_rupiah(total_payout_acc)}**")

    # Internal Dashboard PTPR
    st.markdown('<div class="internal-dash">', unsafe_allow_html=True)
    st.write("### Internal Dashboard PTPR")
    
    if kso_summary["is_feasible"]:
        st.markdown('<div class="banner-feasible">Feasible Scenario — Net Margin PTPR Positif</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner-unfeasible">Unfeasible Scenario — Net Margin PTPR Negatif</div>', unsafe_allow_html=True)
        
    st.markdown(f"""
    <div style="display: flex; gap: 16px; flex-wrap: wrap;">
        <div class="metric-card-red" style="flex: 1; min-width: 250px;">
            <div class="metric-label">Net Margin PTPR (Bulan Pertama)</div>
            <div class="metric-value">{format_rupiah(kso_summary['ptpr_net_month_1'])}</div>
            <div class="metric-caption">Termasuk Biaya Start-Up</div>
        </div>
        <div class="metric-card-red" style="flex: 1; min-width: 250px;">
            <div class="metric-label">Net Margin PTPR (Bulanan Rutin)</div>
            <div class="metric-value">{format_rupiah(kso_summary['ptpr_net_rutin_monthly'])}</div>
            <div class="metric-caption">Operasional Rutin (Tanpa Biaya Start-Up)</div>
        </div>
        <div class="metric-card-red" style="flex: 1; min-width: 250px;">
            <div class="metric-label">Net Margin PTPR (Tahun Pertama)</div>
            <div class="metric-value">{format_rupiah(kso_summary['ptpr_net_yearly'])}</div>
            <div class="metric-caption">(Bulan 1 + [Rutin x 11])</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if multi_year_mode:
        st.write(f"#### Proyeksi Multi-Tahun PTPR ({contract_years} Tahun)")
        st.markdown(f"<p style='font-size:13px; color:#555555; margin-top:-10px; margin-bottom:12px;'>Dihitung berdasarkan asumsi kenaikan volume penjualan sebesar {sales_growth_pct*100:.1f}%/tahun</p>", unsafe_allow_html=True)
        df_ptpr = df_my[["Tahun", "Net Margin PTPR (Rp)"]].copy()
        for col in df_ptpr.columns[1:]:
            df_ptpr[col] = df_ptpr[col].apply(format_rupiah)
        st.dataframe(style_df(df_ptpr), use_container_width=True, hide_index=True)
        total_ptpr_acc = df_my["Net Margin PTPR (Rp)"].sum()
        st.info(f"**Total Akumulasi Net Margin PTPR ({contract_years} Tahun): {format_rupiah(total_ptpr_acc)}**")
        
    st.markdown('</div>', unsafe_allow_html=True) 
    
    st.subheader("Export Contract Documentation")
    params_export = {"grading": grading, "umk": umk, "sharing_ratio_owner": sharing_ratio_owner, "multi_year_mode": multi_year_mode, "contract_years": contract_years, "sales_growth_pct": sales_growth_pct}
    
    col_ex1, col_ex2 = st.columns(2)
    excel_data = generate_excel_report(spbu_name, product_summary, manpower_ptpr, kso_summary, params_export)
    col_ex1.download_button("Download Detail Recap (Excel)", data=excel_data, file_name=f"KSO_TAC_{spbu_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="secondary", use_container_width=True)
    
    pdf_standard = generate_pdf_standard_proposal(spbu_name, product_summary, kso_summary, params_export)
    col_ex2.download_button("Download Contract Proposal (PDF)", data=pdf_standard, file_name=f"Proposal_Standard_{spbu_name}.pdf", mime="application/pdf", type="primary", use_container_width=True)

# === TAB 5: COMPREHENSIVE SUMMARY ===
with tab5:
    st.subheader("Comprehensive Summary")
    
    if not include_mitra_opex:
        st.markdown('<div class="banner-info">Simulasi OPEX SPBU Mitra sedang Non-Aktif. Aktifkan toggle di Sidebar untuk melihat Full Feasibility Analysis.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <div class="hero-card-green" style="flex: 1; min-width: 250px;">
                <div class="metric-label">Proyeksi True Net Income Mitra (Per Bulan)</div>
                <div class="hero-value" style="font-size:30px;">{format_rupiah(kso_summary['owner_true_net_monthly'])}</div>
            </div>
            <div class="hero-card-green" style="flex: 1; min-width: 250px;">
                <div class="metric-label">Proyeksi True Net Income Mitra (Tahun Pertama)</div>
                <div class="hero-value" style="font-size:30px;">{format_rupiah(kso_summary['owner_true_net_yearly'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("**Rincian OPEX SPBU Mitra (Per Bulan):**")
        st.markdown(f"""
        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <div class="metric-card-gray" style="flex: 1; min-width: 200px;">
                <div class="metric-label">Beban Tenaga Kerja SPBU ({format_angka(num_karyawan_mitra)} Orang)</div>
                <div class="metric-value">{format_rupiah(kso_summary['mitra_manpower_cost'])}</div>
            </div>
            <div class="metric-card-gray" style="flex: 1; min-width: 200px;">
                <div class="metric-label">Biaya Utilitas (Listrik & Air)</div>
                <div class="metric-value">{format_rupiah(utilitas_mitra)}</div>
            </div>
            <div class="metric-card-gray" style="flex: 1; min-width: 200px;">
                <div class="metric-label">Pemeliharaan & Perbaikan Sarfas</div>
                <div class="metric-value">{format_rupiah(maintenance_mitra)}</div>
            </div>
            <div class="metric-card-gray" style="flex: 1; min-width: 200px;">
                <div class="metric-label">Beban Insentif Pertamina Way</div>
                <div class="metric-value">{format_rupiah(product_summary['total_insentif_pw_rp'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if multi_year_mode:
            st.write(f"#### Proyeksi Multi-Tahun Feasibility Mitra ({contract_years} Tahun)")
            st.markdown(f"<p style='font-size:13px; color:#555555; margin-top:-10px; margin-bottom:12px;'>Dihitung berdasarkan asumsi kenaikan volume penjualan sebesar {sales_growth_pct*100:.1f}%/tahun</p>", unsafe_allow_html=True)
            df_owner_true = df_my[["Tahun", "Net Payout Mitra (Rp)", "Total OPEX SPBU Mitra (Rp)", "Beban Insentif PW (Rp)", "True Net Income Mitra (Rp)"]].copy()
            for col in df_owner_true.columns[1:]:
                df_owner_true[col] = df_owner_true[col].apply(format_rupiah)
            st.dataframe(style_df(df_owner_true), use_container_width=True, hide_index=True)

            total_true_acc = df_my["True Net Income Mitra (Rp)"].sum()
            st.info(f"**Total Akumulasi True Net Income Mitra ({contract_years} Tahun): {format_rupiah(total_true_acc)}**")

        # Mirroring Internal Dashboard PTPR
        st.markdown('<div class="internal-dash">', unsafe_allow_html=True)
        st.write("### Internal Dashboard PTPR")
        if kso_summary["is_feasible"]:
            st.markdown('<div class="banner-feasible">Feasible Scenario — Net Margin PTPR Positif</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="banner-unfeasible">Unfeasible Scenario — Net Margin PTPR Negatif</div>', unsafe_allow_html=True)
            
        st.markdown(f"""
        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <div class="metric-card-red" style="flex: 1; min-width: 250px;">
                <div class="metric-label">Net Margin PTPR (Bulan Pertama)</div>
                <div class="metric-value">{format_rupiah(kso_summary['ptpr_net_month_1'])}</div>
                <div class="metric-caption">Termasuk Biaya Start-Up</div>
            </div>
            <div class="metric-card-red" style="flex: 1; min-width: 250px;">
                <div class="metric-label">Net Margin PTPR (Bulanan Rutin)</div>
                <div class="metric-value">{format_rupiah(kso_summary['ptpr_net_rutin_monthly'])}</div>
                <div class="metric-caption">Operasional Rutin (Tanpa Biaya Start-Up)</div>
            </div>
            <div class="metric-card-red" style="flex: 1; min-width: 250px;">
                <div class="metric-label">Net Margin PTPR (Tahun Pertama)</div>
                <div class="metric-value">{format_rupiah(kso_summary['ptpr_net_yearly'])}</div>
                <div class="metric-caption">(Bulan 1 + [Rutin x 11])</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if multi_year_mode:
            st.write(f"#### Proyeksi Multi-Tahun PTPR ({contract_years} Tahun)")
            st.markdown(f"<p style='font-size:13px; color:#555555; margin-top:-10px; margin-bottom:12px;'>Dihitung berdasarkan asumsi kenaikan volume penjualan sebesar {sales_growth_pct*100:.1f}%/tahun</p>", unsafe_allow_html=True)
            st.dataframe(style_df(df_ptpr), use_container_width=True, hide_index=True)
            st.info(f"**Total Akumulasi Net Margin PTPR ({contract_years} Tahun): {format_rupiah(total_ptpr_acc)}**")
        st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("Export Feasibility Report")
        pdf_comprehensive = generate_pdf_comprehensive_report(spbu_name, product_summary, kso_summary, params_export)
        st.download_button("Download Full Feasibility Report (PDF)", data=pdf_comprehensive, file_name=f"Feasibility_Report_{spbu_name}.pdf", mime="application/pdf", type="primary", use_container_width=True)

# === TAB 6: VISUAL ANALYTICS ===
with tab6:
    st.subheader("Visual Analytics")
    st.caption("Proyeksi tren pertumbuhan kinerja keuangan Mitra dan PTPR selama durasi kontrak.")
    
    if not multi_year_mode:
        st.markdown('<div class="banner-info">Fitur ini membutuhkan data Multi-Tahun. Silakan aktifkan toggle <b>"Proyeksi Multi-Tahun (1-5 Thn)"</b> di Sidebar untuk melihat grafik tren dan analitik pendapatan.</div>', unsafe_allow_html=True)
    else:
        df_chart = df_my.copy()
        base_props = dict(height=350)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            with st.container(border=True):
                st.markdown("##### Tren Net Payout Mitra")
                # Urutan Sumbu X dikunci kronologis (sort=None)
                c1 = alt.Chart(df_chart).mark_bar(color="#0055A6", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X('Tahun:N', sort=None, axis=alt.Axis(grid=False, title="", labelAngle=0)),
                    y=alt.Y('Net Payout Mitra (Rp):Q', axis=alt.Axis(grid=True, gridColor="#E0E0E0", title="", format="~s")),
                    tooltip=[alt.Tooltip('Tahun:N'), alt.Tooltip('Net Payout Mitra (Rp):Q', format=",.0f")]
                ).properties(**base_props).configure_view(strokeWidth=0)
                st.altair_chart(c1, use_container_width=True)
            
        with col_g2:
            with st.container(border=True):
                st.markdown("##### Tren Net Margin PTPR")
                # Urutan Sumbu X dikunci kronologis (sort=None)
                c2 = alt.Chart(df_chart).mark_bar(color="#ED1C24", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X('Tahun:N', sort=None, axis=alt.Axis(grid=False, title="", labelAngle=0)),
                    y=alt.Y('Net Margin PTPR (Rp):Q', axis=alt.Axis(grid=True, gridColor="#E0E0E0", title="", format="~s")),
                    tooltip=[alt.Tooltip('Tahun:N'), alt.Tooltip('Net Margin PTPR (Rp):Q', format=",.0f")]
                ).properties(**base_props).configure_view(strokeWidth=0)
                st.altair_chart(c2, use_container_width=True)
            
        if include_mitra_opex:
            with st.container(border=True):
                st.markdown("##### Tren True Net Income Mitra")
                st.caption("Proyeksi pendapatan bersih riil setelah dikurangi OPEX SPBU Mitra")
                # Urutan Sumbu X dikunci kronologis (sort=None)
                c3 = alt.Chart(df_chart).mark_bar(color="#58B932", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X('Tahun:N', sort=None, axis=alt.Axis(grid=False, title="", labelAngle=0)),
                    y=alt.Y('True Net Income Mitra (Rp):Q', axis=alt.Axis(grid=True, gridColor="#E0E0E0", title="", format="~s")),
                    tooltip=[alt.Tooltip('Tahun:N'), alt.Tooltip('True Net Income Mitra (Rp):Q', format=",.0f")]
                ).properties(height=400).configure_view(strokeWidth=0)
                st.altair_chart(c3, use_container_width=True)