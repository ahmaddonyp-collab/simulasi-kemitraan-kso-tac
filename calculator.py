# calculator.py
from config import (
    MARGIN_DODO, MARGIN_KHUSUS, HO_OVERHEAD_PER_LITER, 
    MDR_NON_CASH_RATE, PPH_RATE, PERTAMINA_WAY_INSENTIF_RATE,
    INSENTIF_PW_RATES
)

def calculate_manpower_cost_ptpr(umk: float, bur_base_salary: float, num_admin: int, num_bur: int) -> dict:
    salary_admin = umk * (14.0 / 12.0) * 1.10 * num_admin
    salary_bur = bur_base_salary * (14.0 / 12.0) * 1.10 * num_bur
    insentif_pw_ptpr = (salary_admin + salary_bur) * PERTAMINA_WAY_INSENTIF_RATE
    total_manpower_ptpr = salary_admin + salary_bur + insentif_pw_ptpr
    
    return {
        "salary_admin": salary_admin,
        "salary_bur": salary_bur,
        "insentif_pw_ptpr": insentif_pw_ptpr,
        "total_manpower_ptpr": total_manpower_ptpr
    }

def calculate_manpower_cost_mitra(base_salary: float, num_karyawan: int) -> dict:
    salary_karyawan_total = base_salary * (14.0 / 12.0) * 1.10 * num_karyawan
    return {
        "num_karyawan": num_karyawan,
        "base_salary": base_salary,
        "total_karyawan_mitra": salary_karyawan_total
    }

def calculate_product_details(grading: str, sales_volume: dict, selling_prices: dict, loss_percentages: dict) -> dict:
    details = {}
    total_volume = 0
    total_omset_gross = 0
    total_basic_price_omset = 0
    total_margin_normal_gross = 0
    total_margin_khusus_gross = 0
    total_loss_gain_rp = 0
    total_insentif_pw_rp = 0

    for prod, vol in sales_volume.items():
        if vol <= 0:
            continue
            
        price = selling_prices.get(prod, 0)
        loss_pct = loss_percentages.get(prod, 0.0) / 100.0 
        
        category = MARGIN_DODO[prod]["Category"]
        margin_normal = MARGIN_DODO[prod][grading]
        margin_khusus = MARGIN_KHUSUS[category]
        
        if prod == "Pertalite":
            pw_rate = INSENTIF_PW_RATES[grading]["Pertalite"]
        elif prod == "Bio Solar":
            pw_rate = INSENTIF_PW_RATES[grading]["Bio Solar"]
        else:
            pw_rate = INSENTIF_PW_RATES[grading]["NPSO"]
            
        insentif_pw_prod_rp = vol * pw_rate
        
        basic_price = price - margin_normal
        omset_prod = vol * price
        basic_omset_prod = vol * basic_price
        
        margin_normal_prod = vol * margin_normal
        margin_khusus_prod = vol * margin_khusus
        loss_gain_prod_rp = vol * loss_pct * price
        
        details[prod] = {
            "volume": vol, "price": price, "category": category,
            "margin_normal": margin_normal, "margin_khusus": margin_khusus,
            "basic_price": basic_price, "omset": omset_prod,
            "margin_normal_gross": margin_normal_prod,
            "margin_khusus_gross": margin_khusus_prod, 
            "loss_gain_rp": loss_gain_prod_rp,
            "insentif_pw_rate": pw_rate,
            "insentif_pw_rp": insentif_pw_prod_rp
        }
        
        total_volume += vol
        total_omset_gross += omset_prod
        total_basic_price_omset += basic_omset_prod
        total_margin_normal_gross += margin_normal_prod
        total_margin_khusus_gross += margin_khusus_prod  # TYPO DIPERBAIKI DI SINI
        total_loss_gain_rp += loss_gain_prod_rp
        total_insentif_pw_rp += insentif_pw_prod_rp

    pph_tax = total_basic_price_omset * PPH_RATE

    return {
        "products": details, "total_volume": total_volume,
        "total_omset_gross": total_omset_gross, "total_margin_normal_gross": total_margin_normal_gross,
        "total_margin_khusus_gross": total_margin_khusus_gross,
        "total_loss_gain_rp": total_loss_gain_rp, 
        "total_insentif_pw_rp": total_insentif_pw_rp,
        "pph_tax": pph_tax
    }

def calculate_kso_tac(
    product_summary: dict, manpower_ptpr: dict, non_cash_pct: float,
    petty_cash: float, cit_pickup: float, ict_cost: float, startup_cost: float, 
    sharing_ratio_owner: float, include_mitra_opex: bool,
    manpower_mitra: dict = None, utilitas_mitra: float = 0, maintenance_mitra: float = 0,
    multi_year_mode: bool = False, contract_years: int = 1, sales_growth_pct: float = 0.0
) -> dict:
    
    total_vol = product_summary["total_volume"]
    total_omset = product_summary["total_omset_gross"]
    margin_normal_gross = product_summary["total_margin_normal_gross"]
    margin_khusus_gross = product_summary["total_margin_khusus_gross"]
    loss_gain_rp = product_summary["total_loss_gain_rp"]
    insentif_pw_rp = product_summary["total_insentif_pw_rp"]
    pph_tax = product_summary["pph_tax"]
    
    mdr_fee = (total_omset * (non_cash_pct / 100.0)) * MDR_NON_CASH_RATE
    ho_overhead = total_vol * HO_OVERHEAD_PER_LITER
    total_manpower_ptpr = manpower_ptpr["total_manpower_ptpr"]
    
    # OPEX PTPR Base
    total_opex_ptpr_rutin = petty_cash + cit_pickup + ict_cost + mdr_fee + ho_overhead
    total_opex_ptpr_month_1 = total_opex_ptpr_rutin + startup_cost
    
    # Sharing Matrix Base
    owner_gross_share = margin_normal_gross * sharing_ratio_owner
    ptpr_gross_realization = margin_khusus_gross - owner_gross_share

    # Standard Net Owner Base
    owner_net_standard_monthly = owner_gross_share + loss_gain_rp
    owner_net_standard_yearly = owner_net_standard_monthly * 12
    
    # Mitra OPEX Base
    mitra_manpower_cost = manpower_mitra["total_karyawan_mitra"] if (include_mitra_opex and manpower_mitra) else 0
    total_mitra_site_opex = (mitra_manpower_cost + utilitas_mitra + maintenance_mitra) if include_mitra_opex else 0
    
    # True Net Owner Base
    owner_true_net_monthly = owner_net_standard_monthly - total_mitra_site_opex - insentif_pw_rp
    owner_true_net_yearly = owner_true_net_monthly * 12
    
    # PTPR Net Base
    ptpr_net_month_1 = ptpr_gross_realization - total_opex_ptpr_month_1 - total_manpower_ptpr - pph_tax
    ptpr_net_rutin_monthly = ptpr_gross_realization - total_opex_ptpr_rutin - total_manpower_ptpr - pph_tax
    ptpr_net_yearly = ptpr_net_month_1 + (ptpr_net_rutin_monthly * 11)

    # --- MULTI-YEAR CALCULATION ENGINE ---
    yearly_projections = []
    if multi_year_mode:
        for y in range(1, contract_years + 1):
            # Growth Factor per Tahun (Misal Tahun 1: 1.0, Tahun 2: 1.05, Tahun 3: 1.1025)
            growth_factor = (1 + sales_growth_pct) ** (y - 1)
            
            # 1. Variabel yang berskala proporsional dengan peningkatan Volume/Sales
            y_margin_normal_gross = margin_normal_gross * growth_factor
            y_margin_khusus_gross = margin_khusus_gross * growth_factor
            y_loss_gain_rp = loss_gain_rp * growth_factor
            y_insentif_pw_rp = insentif_pw_rp * growth_factor
            y_total_omset = total_omset * growth_factor
            y_total_vol = total_vol * growth_factor
            y_pph_tax = pph_tax * growth_factor
            
            y_mdr_fee = (y_total_omset * (non_cash_pct / 100.0)) * MDR_NON_CASH_RATE
            y_ho_overhead = y_total_vol * HO_OVERHEAD_PER_LITER
            
            # --- LOGIKA BARU OPEX MITRA (SPLIT VARIABLE & FIXED) ---
            # Biaya Utilitas & Maintenance naik sesuai proporsi pertumbuhan Sales
            y_utilitas_mitra = utilitas_mitra * growth_factor
            y_maintenance_mitra = maintenance_mitra * growth_factor
            
            # Biaya Tenaga Kerja (Manpower) di-lock konstan / flat
            y_total_mitra_site_opex = (mitra_manpower_cost + y_utilitas_mitra + y_maintenance_mitra) if include_mitra_opex else 0
            
            # Kalkulasi P&L OPEX PTPR
            y_opex_ptpr_rutin = petty_cash + cit_pickup + ict_cost + y_mdr_fee + y_ho_overhead
            y_owner_gross_share = y_margin_normal_gross * sharing_ratio_owner
            y_ptpr_gross_realization = y_margin_khusus_gross - y_owner_gross_share
            
            # Yearly Accumulations
            y_owner_net_standard_yearly_acc = (y_owner_gross_share + y_loss_gain_rp) * 12
            y_owner_true_net_yearly_acc = y_owner_net_standard_yearly_acc - (y_total_mitra_site_opex * 12) - (y_insentif_pw_rp * 12)
            
            if y == 1:
                y_ptpr_net_yearly_acc = ptpr_net_yearly 
            else:
                y_ptpr_net_monthly = y_ptpr_gross_realization - y_opex_ptpr_rutin - total_manpower_ptpr - y_pph_tax
                y_ptpr_net_yearly_acc = y_ptpr_net_monthly * 12
                
            # Menyimpan detail rincian untuk kebutuhan tabel simetris
            yearly_projections.append({
                "Tahun": f"Tahun Ke-{y}",
                "Gross Share Owner (Rp)": y_owner_gross_share * 12,
                "Impact Loss/Gain (Rp)": y_loss_gain_rp * 12,
                "Standard Net Payout (Rp)": y_owner_net_standard_yearly_acc,
                "Total OPEX Site Mitra (Rp)": y_total_mitra_site_opex * 12,
                "Beban Insentif PW (Rp)": y_insentif_pw_rp * 12,
                "True Net Income (Rp)": y_owner_true_net_yearly_acc,
                "Net Margin PTPR (Rp)": y_ptpr_net_yearly_acc
            })
    
    return {
        "mdr_fee": mdr_fee, "ho_overhead": ho_overhead, 
        "total_opex_ptpr_month_1": total_opex_ptpr_month_1, "total_opex_ptpr_rutin": total_opex_ptpr_rutin,
        "owner_gross_share": owner_gross_share, 
        "owner_net_standard_monthly": owner_net_standard_monthly, "owner_net_standard_yearly": owner_net_standard_yearly,
        "total_mitra_site_opex": total_mitra_site_opex, "mitra_manpower_cost": mitra_manpower_cost,
        "owner_true_net_monthly": owner_true_net_monthly, "owner_true_net_yearly": owner_true_net_yearly,
        "ptpr_gross_realization": ptpr_gross_realization,
        "ptpr_net_month_1": ptpr_net_month_1, "ptpr_net_rutin_monthly": ptpr_net_rutin_monthly, "ptpr_net_yearly": ptpr_net_yearly,
        "is_feasible": ptpr_net_rutin_monthly > 0,
        "yearly_projections": yearly_projections
    }