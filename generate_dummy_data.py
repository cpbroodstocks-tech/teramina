#!/usr/bin/env python3
"""
generate_dummy_data.py
======================
Generates a realistic 120-day Litopenaeus vannamei shrimp farming dataset
matching the Teramina Google Sheets template tab format exactly.

Outputs (sample_data/):
  DAILY_LOG.csv     — 120 rows, one per day of culture
  ABW_SAMPLING.csv  — 16 rows, every 7 days from DOC 14
  MORTALITY.csv     — ~35 rows, days when mortality was recorded
  COST.csv          — ~38 rows, operational cost ledger
  HARVEST.csv       — 2 rows (partial DOC 95 + final DOC 120)

Each CSV: Row 1 = headers, Row 2 = units, Row 3+ = data
(matches Google Sheets template structure — paste directly into each tab)

Usage:
  python generate_dummy_data.py
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

# ── Farm Configuration ────────────────────────────────────────────────────────

START_DATE        = datetime(2024, 3, 1)
CULTURE_DAYS      = 120
POND_AREA_M2      = 3_000        # 0.3 ha — common Indonesian small/medium farm
STOCKING_DENSITY  = 120          # PL/m²
INITIAL_POP       = POND_AREA_M2 * STOCKING_DENSITY  # 360,000 PL
PARTIAL_HARV_DOC  = 95           # partial harvest day
PARTIAL_HARV_PCT  = 0.30         # 30% of remaining population
OUTPUT_DIR        = Path(__file__).parent / "sample_data"

random.seed(42)   # reproducible

# ── Date helpers ──────────────────────────────────────────────────────────────

def date_str(doc: int) -> str:
    return (START_DATE + timedelta(days=doc - 1)).strftime("%Y-%m-%d")

def jitter(value: float, pct: float = 0.05) -> float:
    """Add symmetric random noise of ±pct fraction."""
    return value * (1 + random.uniform(-pct, pct))

# ── Growth model ──────────────────────────────────────────────────────────────
# Empirical ABW checkpoints (g) for L. vannamei, tropical grow-out.
# SGR ~10-12%/day early phase, declining to ~1%/day at close-out.

_ABW = {
     1: 0.02,   7: 0.10,  14: 0.40,  21: 1.00,  28: 2.00,
    35: 3.50,  42: 5.40,  49: 7.60,  56: 10.20,  63: 13.00,
    70: 15.80,  77: 18.40,  84: 20.90,  91: 23.20,  98: 25.30,
   105: 27.30, 112: 29.10, 119: 30.90, 120: 31.20,
}

def abw_g(doc: int) -> float:
    """Linearly interpolate ABW between empirical checkpoints."""
    keys = sorted(_ABW)
    if doc <= keys[0]:  return _ABW[keys[0]]
    if doc >= keys[-1]: return _ABW[keys[-1]]
    for i in range(len(keys) - 1):
        lo, hi = keys[i], keys[i + 1]
        if lo <= doc <= hi:
            t = (doc - lo) / (hi - lo)
            return _ABW[lo] + t * (_ABW[hi] - _ABW[lo])

# ── Population & survival ─────────────────────────────────────────────────────

def cumulative_sr(doc: int) -> float:
    """Cumulative survival rate fraction (0-1)."""
    if doc <=  7: return 0.980
    if doc <= 14: return 0.965
    if doc <= 30: return 0.940
    if doc <= 60: return 0.910
    if doc <= 90: return 0.885
    return 0.865

def _pop_factor(doc: int) -> float:
    """Reduce population by partial harvest after DOC 95."""
    return (1.0 - PARTIAL_HARV_PCT) if doc > PARTIAL_HARV_DOC else 1.0

def current_pop(doc: int) -> int:
    return int(INITIAL_POP * cumulative_sr(doc) * _pop_factor(doc))

def biomass_kg(doc: int) -> float:
    return abw_g(doc) * current_pop(doc) / 1_000.0

# ── Water quality ─────────────────────────────────────────────────────────────

def do_morning(doc: int) -> float:
    base = 5.0 + 0.8 * math.sin(doc * 0.04) + doc / 500
    return round(min(7.5, max(3.5, jitter(base, 0.06))), 1)

def do_afternoon(doc: int) -> float:
    return round(min(9.2, do_morning(doc) + random.uniform(1.3, 2.6)), 1)

def temp_morning(doc: int) -> float:
    base = 28.0 + 0.5 * math.sin(doc * 0.05)
    return round(max(26.0, min(30.5, jitter(base, 0.02))), 1)

def temp_afternoon(doc: int) -> float:
    return round(min(34.5, temp_morning(doc) + random.uniform(1.8, 3.2)), 1)

def ph_morning(doc: int) -> float:
    base = 7.72 + 0.10 * math.sin(doc * 0.06)
    return round(max(7.2, min(8.2, jitter(base, 0.02))), 2)

def ph_afternoon(doc: int) -> float:
    return round(min(8.8, ph_morning(doc) + random.uniform(0.15, 0.55)), 2)

def salinity(doc: int) -> float:
    base = 18.5 - doc * 0.012
    return round(max(12.0, min(25.0, jitter(base, 0.04))), 1)

def nh3(doc: int) -> float:
    if doc <= 30:   base = 0.07
    elif doc <= 60: base = 0.16
    elif doc <= 90: base = 0.26
    else:           base = 0.34
    return round(max(0.01, min(0.80, jitter(base, 0.28))), 3)

def turbidity_cm(doc: int) -> int:
    """Secchi disk depth (cm). Lower = more turbid / algae bloom."""
    if doc <= 20:   base = 46
    elif doc <= 60: base = 36
    else:           base = 28
    return max(15, min(60, int(jitter(base, 0.12))))

# ── Feeding ───────────────────────────────────────────────────────────────────

def feed_type(doc: int) -> str:
    if doc <=  7: return "CP Prima S-0 Starter (1.0mm)"
    if doc <= 21: return "CP Prima S-1 Starter (1.5mm)"
    if doc <= 45: return "Irawan G-1 Grower (2.0mm)"
    if doc <= 80: return "Irawan G-2 Grower (2.5mm)"
    if doc <= 105: return "Irawan G-3 Grower (3.0mm)"
    return "Charoen F-1 Finisher (3.5mm)"

def protein_pct(doc: int) -> int:
    if doc <=  7: return 42
    if doc <= 21: return 40
    if doc <= 45: return 38
    if doc <= 80: return 36
    return 35

def feeding_freq(doc: int) -> int:
    return 4 if doc <= 80 else 3

def feed_given_kg(doc: int) -> float:
    bm = biomass_kg(doc)
    if doc <=  7:  rate = 0.15
    elif doc <= 21: rate = 0.10
    elif doc <= 45: rate = 0.065
    elif doc <= 75: rate = 0.048
    elif doc <= 100: rate = 0.038
    else:           rate = 0.030
    raw = max(1.0, bm * rate)
    return round(jitter(raw, 0.07), 1)

def feed_leftover_kg(doc: int) -> float:
    fg = feed_given_kg(doc)
    pct = 0.04 if doc <= 30 else 0.015
    return round(random.uniform(0.0, pct) * fg, 1)

# ── Tab generators ────────────────────────────────────────────────────────────

def generate_daily_log() -> list:
    headers = [
        "Date", "DOC",
        "DO Morning", "DO Afternoon", "DO Average",
        "Temp Morning", "Temp Afternoon", "Temp Average",
        "pH Morning", "pH Afternoon",
        "Salinity", "NH3", "Turbidity",
        "Feed Given", "Feed Leftover",
        "Feed Type", "Protein %", "Feeding Freq",
        "Notes",
    ]
    units = [
        "YYYY-MM-DD", "(auto)",
        "mg/L", "mg/L", "mg/L",
        "°C", "°C", "°C",
        "-", "-",
        "ppt", "mg/L", "cm",
        "kg", "kg",
        "-", "%", "times/day",
        "-",
    ]

    special = {
        1:   "Benur tebar – hari pertama siklus",
        7:   "Penyesuaian pakan pertama",
        14:  "Sampling pertama – adaptasi selesai",
        15:  "Ganti air 20% – siang",
        21:  "Sampling kedua",
        30:  "Ganti air 30% + aplikasi probiotik",
        35:  "Sampling ketiga",
        45:  "Kontrol anco meningkat",
        56:  "Sampling kedelapan",
        60:  "Ganti air 25% – parameter membaik",
        70:  "Sampling kesepuluh",
        75:  "Perawatan kincir",
        84:  "Sampling keduabelas",
        90:  "Pre-harvest sampling",
        95:  "Panen sebagian 30% populasi",
        98:  "Sampling setelah panen sebagian",
        112: "Sampling pra-panen akhir",
        120: "Panen total – akhir siklus",
    }

    rows = [headers, units]
    for doc in range(1, CULTURE_DAYS + 1):
        dom = do_morning(doc)
        doa = do_afternoon(doc)
        tm  = temp_morning(doc)
        ta  = temp_afternoon(doc)
        rows.append([
            date_str(doc), doc,
            dom, doa, round((dom + doa) / 2, 1),
            tm, ta, round((tm + ta) / 2, 1),
            ph_morning(doc), ph_afternoon(doc),
            salinity(doc), nh3(doc), turbidity_cm(doc),
            feed_given_kg(doc), feed_leftover_kg(doc),
            feed_type(doc), protein_pct(doc), feeding_freq(doc),
            special.get(doc, ""),
        ])
    return rows


def generate_abw_sampling() -> list:
    headers = [
        "Date", "DOC",
        "Sample Count", "Total Weight (g)", "ABW (g)",
        "Min Weight", "Max Weight", "CV%",
        "Sampled By", "Notes",
    ]
    units = [
        "YYYY-MM-DD", "(auto)",
        "pcs", "g", "g", "g", "g", "%",
        "-", "-",
    ]

    samplers = ["Pak Budi", "Bu Sari", "Mas Ahmad", "Dek Dewi"]
    notes_map = {
        14:  "Sampling pertama post-tebar",
        21:  "Adaptasi selesai – growth normal",
        91:  "Pre-panen sebagian – cek size",
        105: "Persiapan panen akhir",
        119: "Final size check",
    }

    rows = [headers, units]
    for doc in range(14, CULTURE_DAYS + 1, 7):
        avg = round(abw_g(doc), 2)
        n   = 50
        cv  = round(random.uniform(14.0, 26.0), 1)
        std = avg * cv / 100.0
        min_w = round(max(0.01, avg - 2.2 * std), 2)
        max_w = round(avg + 2.2 * std, 2)
        total = round(avg * n, 1)
        rows.append([
            date_str(doc), doc,
            n, total, avg,
            min_w, max_w, cv,
            random.choice(samplers),
            notes_map.get(doc, ""),
        ])
    return rows


def generate_mortality() -> list:
    headers = ["Date", "DOC", "Dead Count", "Notes"]
    units   = ["YYYY-MM-DD", "(auto)", "pcs", "-"]

    early_notes = {
        1: "Stres pasca-tebar",
        2: "Stres pasca-tebar",
        3: "Stres pasca-tebar",
        4: "Adaptasi lingkungan",
        5: "Dugaan infeksi bakteri ringan",
        6: "Aplikasi probiotik preventif",
        7: "Tes Vibrio negatif",
        10: "Uji PCR WSSV negatif",
        12: "Mortalitas menurun",
        14: "Kanibalisme fase awal",
    }

    rows = [headers, units]
    for doc in range(1, CULTURE_DAYS + 1):
        if doc <= 7:
            p, lo, hi = 0.92, 0.0025, 0.0080
        elif doc <= 14:
            p, lo, hi = 0.75, 0.0010, 0.0040
        elif doc <= 30:
            p, lo, hi = 0.45, 0.0003, 0.0015
        elif doc <= 90:
            p, lo, hi = 0.18, 0.0001, 0.0006
        else:
            p, lo, hi = 0.09, 0.0001, 0.0002

        if random.random() < p:
            count = max(1, int(INITIAL_POP * random.uniform(lo, hi)))
            note  = early_notes.get(doc, "")
            rows.append([date_str(doc), doc, count, note])

    return rows


def generate_cost() -> list:
    headers = [
        "Date", "Category", "Description",
        "Quantity", "Unit", "Unit Price (IDR)", "Total (IDR)",
        "Vendor", "Notes",
    ]
    units = [
        "YYYY-MM-DD", "-", "-",
        "-", "-", "IDR", "IDR",
        "-", "-",
    ]

    # (doc, category, description, qty, unit, unit_price, vendor, notes)
    # Total is computed automatically (qty × unit_price) unless overridden
    _E = [
        # ── DOC 1 – Stocking & Pond Prep ──────────────────────────────────────
        (1,  "Benur",      "PL Vannamei SPF PL12 – Hatchery Bali",
              INITIAL_POP, "ekor",   80,       "Hatchery Bali Indo",   "Sertifikat SPF & PCR terlampir"),
        (1,  "Kimia",      "Kapur Pertanian CaCO3",
              600, "kg",  1_800,     "Toko Pertanian Sumber",  "pH normalisasi"),
        (1,  "Kimia",      "Dolomit",
              300, "kg",  1_600,     "Toko Pertanian Sumber",  "Alkalinitas"),
        (1,  "Kimia",      "TSP (Triple Superphosphate) – pupuk dasar",
              50,  "kg",  8_500,     "Toko Pupuk Makmur",      "Plankton seed"),
        (1,  "Probiotik",  "BioRemoval Probiotik Starter",
              10,  "kg",  225_000,   "PT Biosindo Nusantara",  "Aplikasi hari-1"),

        # ── DOC 3 – Feed Starter ──────────────────────────────────────────────
        (3,  "Pakan",      "CP Prima S-0 Starter 1mm (42% protein)",
              100, "kg",  38_000,    "PT Charoen Pokphand",    "Tas 25kg"),

        # ── DOC 7 ──────────────────────────────────────────────────────────────
        (7,  "Pakan",      "CP Prima S-1 Starter 1.5mm (40% protein)",
              300, "kg",  34_000,    "PT Charoen Pokphand",    ""),
        (7,  "Vitamin",    "Vitamin C 35% Ascorbic Acid",
               5,  "kg",  185_000,   "Agro Makmur Jaya",       ""),

        # ── DOC 10 – Labor & Utility Bulan 1 ─────────────────────────────────
        (10, "Tenaga Kerja", "Upah 3 teknisi – bulan 1",
               3,  "orang/bulan", 3_000_000, "-",              "Incl. lembur"),
        (10, "Utilitas",   "Listrik PLN – bulan 1",
               1,  "bulan", 6_800_000, "PLN",                  "Aerasi + pompa air"),

        # ── DOC 14 – Grower 1 ─────────────────────────────────────────────────
        (14, "Pakan",      "Irawan G-1 Grower 2mm (38% protein)",
              600, "kg",  24_500,    "PT Irawan Pakan",        ""),
        (14, "Probiotik",  "BioBalance rutin",
               5,  "kg",  225_000,   "PT Biosindo Nusantara",  ""),

        # ── DOC 21 ──────────────────────────────────────────────────────────────
        (21, "Kimia",      "EDTA 99% – chelate logam berat",
               5,  "kg",   88_000,   "Agro Makmur Jaya",       ""),
        (21, "Pakan",      "Irawan G-1 Grower 2mm",
             1_200, "kg",  24_500,   "PT Irawan Pakan",        ""),
        (21, "Vitamin",    "Premix Vitamin E + Selenium",
               5,  "kg",  168_000,   "Agro Makmur Jaya",       ""),

        # ── DOC 30 – Bulan 2 ─────────────────────────────────────────────────
        (30, "Pakan",      "Irawan G-1 Grower 2mm",
             2_500, "kg",  24_500,   "PT Irawan Pakan",        ""),
        (30, "Probiotik",  "Pond Detox Bacillus subtilis",
              10,  "kg",  188_000,   "PT Biosindo Nusantara",  "Pasca ganti air 30%"),
        (30, "Tenaga Kerja", "Upah 3 teknisi – bulan 2",
               3,  "orang/bulan", 3_000_000, "-",              ""),
        (30, "Utilitas",   "Listrik PLN – bulan 2",
               1,  "bulan", 7_200_000, "PLN",                  ""),

        # ── DOC 45 ──────────────────────────────────────────────────────────────
        (45, "Pakan",      "Irawan G-2 Grower 2.5mm (36% protein)",
             4_000, "kg",  22_000,   "PT Irawan Pakan",        ""),
        (45, "Kimia",      "Saponin – molluscicide",
              25,  "kg",   45_000,   "Toko Pertanian Sumber",  ""),
        (45, "Vitamin",    "Mineral Premix (Ca, Mg, Zn)",
               5,  "kg",  122_000,   "Agro Makmur Jaya",       ""),

        # ── DOC 60 – Bulan 3 ─────────────────────────────────────────────────
        (60, "Pakan",      "Irawan G-2 Grower 2.5mm",
             6_000, "kg",  22_000,   "PT Irawan Pakan",        ""),
        (60, "Probiotik",  "FertiZyme Probiotik + Enzim",
              10,  "kg",  198_000,   "PT Biosindo Nusantara",  ""),
        (60, "Tenaga Kerja", "Upah 3 teknisi – bulan 3",
               3,  "orang/bulan", 3_000_000, "-",              ""),
        (60, "Utilitas",   "Listrik PLN – bulan 3",
               1,  "bulan", 7_500_000, "PLN",                  ""),

        # ── DOC 75 ──────────────────────────────────────────────────────────────
        (75, "Pakan",      "Irawan G-3 Grower 3mm (36% protein)",
             7_000, "kg",  21_500,   "PT Irawan Pakan",        ""),
        (75, "Kimia",      "Zeolit – absorpsi NH3",
             300,  "kg",    3_800,   "Toko Pertanian Sumber",  ""),
        (75, "Lain-lain",  "Bensin genset backup",
              50,  "liter", 10_500,  "-",                      "Antisipasi pemadaman"),

        # ── DOC 90 – Bulan 4 ─────────────────────────────────────────────────
        (90, "Pakan",      "Charoen F-1 Finisher 3.5mm (35% protein)",
             7_000, "kg",  19_800,   "PT Charoen Pokphand",    ""),
        (90, "Probiotik",  "BioBalance rutin",
               5,  "kg",  225_000,   "PT Biosindo Nusantara",  ""),
        (90, "Tenaga Kerja", "Upah 3 teknisi – bulan 4",
               3,  "orang/bulan", 3_000_000, "-",              ""),
        (90, "Utilitas",   "Listrik PLN – bulan 4",
               1,  "bulan", 7_800_000, "PLN",                  ""),

        # ── DOC 95 – Partial Harvest ─────────────────────────────────────────
        (95, "Panen",      "Upah panen sebagian (6 orang)",
               6,  "orang",  300_000, "-",                     "Panen 30% populasi"),
        (95, "Lain-lain",  "Es balok",
              20,  "balok",  25_000,  "PT Berkah Es",          "Preservasi pasca-panen"),

        # ── DOC 105 – Top-up Feed ─────────────────────────────────────────────
        (105, "Pakan",     "Charoen F-1 Finisher 3.5mm",
             4_000, "kg",  19_800,   "PT Charoen Pokphand",    ""),

        # ── DOC 120 – Final Harvest ───────────────────────────────────────────
        (120, "Panen",     "Upah panen total (8 orang)",
               8,  "orang",  350_000, "-",                     "Hari panen akhir siklus"),
        (120, "Utilitas",  "Listrik PLN – bulan 5 (parsial)",
               1,  "bulan", 4_200_000, "PLN",                  ""),
        (120, "Lain-lain", "Es balok panen akhir",
              50,  "balok",  25_000,  "PT Berkah Es",          ""),
        (120, "Lain-lain", "Kantong plastik packing",
             500,  "lembar",  2_500,  "Toko Perlengkapan",     ""),
    ]

    rows = [headers, units]
    for doc, cat, desc, qty, unit, unit_price, vendor, note in _E:
        total = round(qty * unit_price)
        rows.append([date_str(doc), cat, desc, qty, unit, unit_price, total, vendor, note])
    return rows


def generate_harvest() -> list:
    headers = [
        "Date", "DOC", "Is Partial?",
        "Biomass (kg)", "ABW at Harvest (g)", "SR at Harvest (%)",
        "Bags", "Buyer", "Price/kg (IDR)", "Notes",
    ]
    units = [
        "YYYY-MM-DD", "(auto)", "Y/N",
        "kg", "g", "%",
        "bag", "-", "IDR", "-",
    ]

    rows = [headers, units]

    # ── Partial harvest DOC 95 ─────────────────────────────────────────────
    ph_doc = PARTIAL_HARV_DOC
    ph_abw = round(abw_g(ph_doc), 1)
    ph_sr  = round(cumulative_sr(ph_doc) * 100, 1)
    ph_pop = int(INITIAL_POP * cumulative_sr(ph_doc))          # before partial
    ph_harvested = int(ph_pop * PARTIAL_HARV_PCT)
    ph_biomass = round(ph_abw * ph_harvested / 1_000, 1)
    ph_bags = math.ceil(ph_biomass / 30)                       # ~30 kg/bag

    rows.append([
        date_str(ph_doc), ph_doc, "Y",
        ph_biomass, ph_abw, ph_sr,
        ph_bags, "UD Maju Jaya Seafood", 62_000,
        f"Panen sebagian 30% pop ({ph_harvested:,} ekor) – size 40/kg"
    ])

    # ── Final harvest DOC 120 ──────────────────────────────────────────────
    fh_doc = CULTURE_DAYS
    fh_abw = round(abw_g(fh_doc), 1)
    fh_sr  = round(cumulative_sr(fh_doc) * 100, 1)
    fh_pop = current_pop(fh_doc)                               # after partial harvest factor
    fh_biomass = round(fh_abw * fh_pop / 1_000, 1)
    fh_bags = math.ceil(fh_biomass / 30)

    rows.append([
        date_str(fh_doc), fh_doc, "N",
        fh_biomass, fh_abw, fh_sr,
        fh_bags, "PT Indo Segar Mandiri", 58_000,
        f"Panen total akhir siklus ({fh_pop:,} ekor) – size 32/kg"
    ])

    return rows


# ── Writer ────────────────────────────────────────────────────────────────────

def write_csv(filename: str, rows: list) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    data_rows = len(rows) - 2   # exclude header + units rows
    print(f"  ✓ {filename:<22} {data_rows:>4} data rows  →  {path}")


# ── Summary stats ─────────────────────────────────────────────────────────────

def print_summary() -> None:
    ph_pop = int(INITIAL_POP * cumulative_sr(PARTIAL_HARV_DOC))
    ph_harvested = int(ph_pop * PARTIAL_HARV_PCT)
    ph_biomass = round(abw_g(PARTIAL_HARV_DOC) * ph_harvested / 1_000, 1)

    fh_pop     = current_pop(CULTURE_DAYS)
    fh_biomass = round(abw_g(CULTURE_DAYS) * fh_pop / 1_000, 1)
    total_yield = ph_biomass + fh_biomass

    total_feed = sum(feed_given_kg(d) for d in range(1, CULTURE_DAYS + 1))
    fcr = round(total_feed / total_yield, 2)

    print(f"""
  ┌─────────────────────────────────────────────────────────────┐
  │              Simulated Cycle Summary                        │
  ├───────────────────────────────────────┬─────────────────────┤
  │ Pond area                             │ {POND_AREA_M2:>15,} m²  │
  │ Stocking density                      │ {STOCKING_DENSITY:>13} PL/m²  │
  │ Initial population                    │ {INITIAL_POP:>13,} PL  │
  │ Culture period                        │ {CULTURE_DAYS:>14} days  │
  │ Start date                            │ {START_DATE.strftime("%Y-%m-%d"):>16}  │
  ├───────────────────────────────────────┼─────────────────────┤
  │ DOC 95 partial harvest                │                     │
  │   ABW                                 │ {abw_g(PARTIAL_HARV_DOC):>14.1f} g  │
  │   Population harvested                │ {ph_harvested:>13,} ekor │
  │   Biomass                             │ {ph_biomass:>13.1f} kg  │
  │   Price/kg (est.)                     │ IDR {62_000:>11,}  │
  │   Revenue (est.)                      │ IDR {int(ph_biomass*62_000):>11,}  │
  ├───────────────────────────────────────┼─────────────────────┤
  │ DOC 120 final harvest                 │                     │
  │   ABW                                 │ {abw_g(CULTURE_DAYS):>14.1f} g  │
  │   Survival rate                       │ {cumulative_sr(CULTURE_DAYS)*100:>13.1f} %  │
  │   Remaining population                │ {fh_pop:>13,} ekor │
  │   Biomass                             │ {fh_biomass:>13.1f} kg  │
  │   Price/kg (est.)                     │ IDR {58_000:>11,}  │
  │   Revenue (est.)                      │ IDR {int(fh_biomass*58_000):>11,}  │
  ├───────────────────────────────────────┼─────────────────────┤
  │ Total yield                           │ {total_yield:>13.1f} kg  │
  │ Total feed consumed                   │ {total_feed:>13.1f} kg  │
  │ FCR                                   │ {fcr:>16.2f}  │
  │ Total revenue (est.)                  │ IDR {int(ph_biomass*62_000+fh_biomass*58_000):>11,}  │
  └───────────────────────────────────────┴─────────────────────┘""")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"\nGenerating 120-day vannamei dummy dataset...")
    print(f"  Pond: {POND_AREA_M2:,} m²  |  {INITIAL_POP:,} PL stocked  |  Start: {START_DATE.strftime('%Y-%m-%d')}\n")

    write_csv("DAILY_LOG.csv",     generate_daily_log())
    write_csv("ABW_SAMPLING.csv",  generate_abw_sampling())
    write_csv("MORTALITY.csv",     generate_mortality())
    write_csv("COST.csv",          generate_cost())
    write_csv("HARVEST.csv",       generate_harvest())

    print_summary()

    print("""
  How to use:
  1. Open your Google Sheets template (or create one via Teramina)
  2. For each tab, import the matching CSV:
       DAILY_LOG tab     ← DAILY_LOG.csv    (paste from row 3)
       ABW_SAMPLING tab  ← ABW_SAMPLING.csv (paste from row 3)
       MORTALITY tab     ← MORTALITY.csv    (paste from row 3)
       COST tab          ← COST.csv         (paste from row 3)
       HARVEST tab       ← HARVEST.csv      (paste from row 3)
  3. Trigger a manual sync from the Teramina cycle detail page.
     Rows 1-2 (headers + units) are already in the template — paste data only.
""")
