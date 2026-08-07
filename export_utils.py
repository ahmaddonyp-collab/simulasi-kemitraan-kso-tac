# export_utils.py
import io
import pandas as pd
from fpdf import FPDF

def format_angka_export(angka):
    return f"{angka:,.0f}".replace(',', '.')

def generate_excel_report(spbu_name: str, product_summary: dict, manpower_ptpr: dict, kso_summary: dict, params: dict) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary_data = {
            "Komponen Perhitungan": [
                "Volume Sales Total (Liter)", "Total Omset Kotor (Rp)", "Gross Margin Normal / DODO (Rp)", 
                "Gross Margin Khusus PTPR (Rp)", "Porsi Sharing Margin Mitra (%)", 
                "Gross Share Mitra (Sebelum Losses/Gain) (Rp)", "Penyesuaian Losses/Gain BBM (Rp)", 
                "NET PAYOUT MITRA (Per Bulan)", "NET PAYOUT MITRA (Tahun Pertama)",
                "Beban Insentif Pertamina Way (Rp)", "Total OPEX SPBU Mitra (Per Bulan)", 
                "TRUE NET INCOME MITRA (Per Bulan)", "TRUE NET INCOME MITRA (Tahun Pertama)",
                "Total Beban OPEX PTPR (Bulan Rutin) (Rp)", "Total Beban Manpower PTPR (Rp)", "Beban PPh PTPR (Rp)",
                "NET MARGIN PTPR (Bulan Pertama) (Rp)", "NET MARGIN PTPR (Bulanan Rutin) (Rp)", "NET MARGIN PTPR (Tahun Pertama) (Rp)", "Status Proyeksi PTPR"
            ],
            "Nominal": [
                format_angka_export(product_summary["total_volume"]), product_summary["total_omset_gross"], 
                product_summary["total_margin_normal_gross"], product_summary["total_margin_khusus_gross"],
                f"{params['sharing_ratio_owner']*100:.1f}%", 
                kso_summary["owner_gross_share"], product_summary["total_loss_gain_rp"], 
                kso_summary["owner_net_standard_monthly"], kso_summary["owner_net_standard_yearly"],
                product_summary["total_insentif_pw_rp"], kso_summary["total_mitra_site_opex"], 
                kso_summary["owner_true_net_monthly"], kso_summary["owner_true_net_yearly"],
                kso_summary["total_opex_ptpr_rutin"], manpower_ptpr["total_manpower_ptpr"], product_summary["pph_tax"],
                kso_summary["ptpr_net_month_1"], kso_summary["ptpr_net_rutin_monthly"], kso_summary["ptpr_net_yearly"],
                "FEASIBLE" if kso_summary["is_feasible"] else "UNFEASIBLE"
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Ringkasan KSO", index=False)
        
        prod_rows = []
        for p_name, p_data in product_summary["products"].items():
            prod_rows.append({
                "Produk BBM": p_name, "Volume Bulanan (Liter)": format_angka_export(p_data["volume"]), "Harga Jual (Rp/Liter)": p_data["price"],
                "Kategori": p_data["category"], "Margin Normal (Rp)": p_data["margin_normal"], 
                "Margin Khusus (Rp)": p_data["margin_khusus"], "Estimasi Losses/Gain (%)": f"{p_data['loss_gain_rp']}",
                "Insentif PW (Rp/Liter)": p_data["insentif_pw_rate"], "Total Insentif PW (Rp)": p_data["insentif_pw_rp"]
            })
        pd.DataFrame(prod_rows).to_excel(writer, sheet_name="Breakdown Produk", index=False)
        
        if params.get('multi_year_mode'):
            df_my_raw = pd.DataFrame(kso_summary['yearly_projections'])
            df_my_raw = df_my_raw.rename(columns={
                "Gross Share Owner (Rp)": "Gross Share Mitra (Rp)",
                "Impact Loss/Gain (Rp)": "Penyesuaian Losses/Gain BBM (Rp)",
                "Standard Net Payout (Rp)": "Net Payout Mitra (Rp)",
                "True Net Income (Rp)": "True Net Income Mitra (Rp)",
                "Total OPEX Site Mitra (Rp)": "Total OPEX SPBU Mitra (Rp)"
            })
            tahun_mapping = {
                "Tahun Ke-1": "Tahun Pertama", "Tahun Ke-2": "Tahun Kedua",
                "Tahun Ke-3": "Tahun Ketiga", "Tahun Ke-4": "Tahun Keempat", "Tahun Ke-5": "Tahun Kelima"
            }
            df_my_raw["Tahun"] = df_my_raw["Tahun"].replace(tahun_mapping)
            pd.DataFrame(df_my_raw).to_excel(writer, sheet_name="Proyeksi Multi-Tahun", index=False)

    return output.getvalue()

def generate_pdf_standard_proposal(spbu_name: str, product_summary: dict, kso_summary: dict, params: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    
    pdf.cell(0, 10, f"PROPOSAL KEMITRAAN KSO TAC - {spbu_name.upper()}", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 8, f"Grading SPBU: {params['grading']} | Volume Total: {format_angka_export(product_summary['total_volume'])} Liter", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 8, "CONTRACT SUMMARY (ESTIMASI HAK PENERIMAAN MITRA):", ln=True)
    pdf.set_font("Helvetica", '', 11)
    
    pdf.cell(100, 8, "Gross Share Mitra (Sebelum Losses/Gain):", border=1)
    pdf.cell(60, 8, f"Rp {kso_summary['owner_gross_share']:,.0f}", border=1, ln=True)
    
    pdf.cell(100, 8, "Penyesuaian Losses/Gain BBM:", border=1)
    pdf.cell(60, 8, f"Rp {product_summary['total_loss_gain_rp']:,.0f}", border=1, ln=True)
    
    pdf.cell(100, 8, "Proyeksi Net Payout Bulanan Mitra:", border=1)
    pdf.cell(60, 8, f"Rp {kso_summary['owner_net_standard_monthly']:,.0f}", border=1, ln=True)
    
    pdf.cell(100, 8, "Proyeksi Net Payout Mitra (Tahun Pertama):", border=1)
    pdf.cell(60, 8, f"Rp {kso_summary['owner_net_standard_yearly']:,.0f}", border=1, ln=True)
    
    if params.get('multi_year_mode'):
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 8, f"PROYEKSI AKUMULASI {params['contract_years']} TAHUN (Asumsi Kenaikan Sales {params['sales_growth_pct']*100:.1f}% / Thn):", ln=True)
        pdf.set_font("Helvetica", '', 10)
        total_payout_acc = sum(y['Standard Net Payout (Rp)'] for y in kso_summary['yearly_projections'])
        pdf.cell(100, 8, f"Total Net Payout Mitra ({params['contract_years']} Tahun):", border=1)
        pdf.cell(60, 8, f"Rp {total_payout_acc:,.0f}", border=1, ln=True)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", 'I', 9)
    pdf.multi_cell(0, 5, "* Dokumen ini menerangkan proyeksi hak transfer bersih standar KSO TAC dari PT Pertamina Retail (PTPR) sebelum dikurangi biaya operasional dapur internal SPBU Mitra.")
    
    return bytes(pdf.output())

def generate_pdf_comprehensive_report(spbu_name: str, product_summary: dict, kso_summary: dict, params: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    
    pdf.cell(0, 10, f"COMPREHENSIVE SUMMARY - {spbu_name.upper()}", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 8, f"Grading SPBU: {params['grading']} | Volume Total: {format_angka_export(product_summary['total_volume'])} Liter", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 8, "PROYEKSI PENDAPATAN BERSIH RIIL (TRUE NET INCOME MITRA):", ln=True)
    pdf.set_font("Helvetica", '', 11)
    
    pdf.cell(105, 8, "Net Payout Mitra KSO TAC (PTPR):", border=1)
    pdf.cell(60, 8, f"Rp {kso_summary['owner_net_standard_monthly']:,.0f}", border=1, ln=True)
    
    pdf.cell(105, 8, "Dipotong Total OPEX SPBU Mitra:", border=1)
    pdf.cell(60, 8, f"- Rp {kso_summary['total_mitra_site_opex']:,.0f}", border=1, ln=True)

    pdf.cell(105, 8, "Dipotong Beban Insentif Pertamina Way:", border=1)
    pdf.cell(60, 8, f"- Rp {product_summary['total_insentif_pw_rp']:,.0f}", border=1, ln=True)
    
    pdf.cell(105, 8, "Proyeksi True Net Income Mitra (Per Bulan):", border=1)
    pdf.cell(60, 8, f"Rp {kso_summary['owner_true_net_monthly']:,.0f}", border=1, ln=True)
    
    pdf.cell(105, 8, "Proyeksi True Net Income Mitra (Tahun Pertama):", border=1)
    pdf.cell(60, 8, f"Rp {kso_summary['owner_true_net_yearly']:,.0f}", border=1, ln=True)
    
    if params.get('multi_year_mode'):
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 8, f"PROYEKSI AKUMULASI {params['contract_years']} TAHUN (Asumsi Kenaikan Sales {params['sales_growth_pct']*100:.1f}% / Thn):", ln=True)
        pdf.set_font("Helvetica", '', 10)
        total_true_net_acc = sum(y['True Net Income (Rp)'] for y in kso_summary['yearly_projections'])
        pdf.cell(105, 8, f"Total True Net Income Mitra ({params['contract_years']} Tahun):", border=1)
        pdf.cell(60, 8, f"Rp {total_true_net_acc:,.0f}", border=1, ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", 'I', 9)
    pdf.multi_cell(0, 5, "* Dokumen ini merupakan studi kelayakan lengkap yang memperhitungkan seluruh Beban Tenaga Kerja SPBU Mitra, Biaya Utilitas (Listrik & Air), Pemeliharaan & Perbaikan Sarfas, dan Beban Insentif Pertamina Way.")
    
    return bytes(pdf.output())