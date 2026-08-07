# config.py

MARGIN_DODO = {
    "Pertalite": {"Basic": 320, "Good": 355, "Excellent": 380, "Category": "PSO"},
    "Pertamax": {"Basic": 445, "Good": 635, "Excellent": 685, "Category": "NPSO"},
    "Pertamax Green": {"Basic": 485, "Good": 685, "Excellent": 730, "Category": "NPSO"},
    "Pertamax Turbo": {"Basic": 525, "Good": 725, "Excellent": 775, "Category": "NPSO"},
    "Bio Solar": {"Basic": 210, "Good": 257, "Excellent": 275, "Category": "PSO"},
    "Dexlite": {"Basic": 485, "Good": 610, "Excellent": 660, "Category": "NPSO"},
    "Pertamina Dex": {"Basic": 525, "Good": 700, "Excellent": 750, "Category": "NPSO"},
    "Pertamina Dex (Small)": {"Basic": 495, "Good": 650, "Excellent": 700, "Category": "NPSO"},
}

MARGIN_KHUSUS = {
    "PSO": 375,
    "NPSO": 740
}

DEFAULT_PRICES = {
    "Pertalite": 10000,
    "Pertamax": 15950,
    "Pertamax Green": 16600,
    "Pertamax Turbo": 18300,
    "Bio Solar": 6800,
    "Dexlite": 19700,
    "Pertamina Dex": 21150,
    "Pertamina Dex (Small)": 21150,
}

# TARIF INSENTIF PERTAMINA WAY (Rp / Liter)
INSENTIF_PW_RATES = {
    "Basic": {"Pertalite": 0, "Bio Solar": 0, "NPSO": 0},
    "Good": {"Pertalite": 4, "Bio Solar": 2, "NPSO": 30},
    "Excellent": {"Pertalite": 8, "Bio Solar": 5, "NPSO": 40}
}

# Biaya Operasional Tetap Standar PTPR
DEFAULT_PETTY_CASH = 2500000
DEFAULT_CIT_PICKUP = 10000000
DEFAULT_ICT_COST = 5000000
DEFAULT_STARTUP_COST = 1300000

# Variabel Pengali
HO_OVERHEAD_PER_LITER = 15.0
MDR_NON_CASH_RATE = 0.005
PPH_RATE = 0.0025
PERTAMINA_WAY_INSENTIF_RATE = 0.15
