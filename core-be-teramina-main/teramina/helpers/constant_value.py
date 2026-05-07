# pylint: disable=missing-class-docstring, too-few-public-methods, line-too-long


class Constant:
    DO_SUITABLE_MIN = 2
    DO_OPTIMAL_MIN = 3.5
    DO_OPTIMAL_MAX = 9
    DO_SUITABLE_MAX = 10

    NH3_SUITABLE_MIN = 0
    NH3_OPTIMAL_MIN = 0
    NH3_OPTIMAL_MAX = 0.25
    NH3_SUITABLE_MAX = 2.09

    WN = 45
    NH3_LIM = 1
    GAMMA = 0.001

    MAX_DOC = 130
    # DOC threshold below which early-stage feeding rate table is applied
    EARLY_STAGE_DOC_THRESHOLD = 30
    # Aerator/pump rated power (Watts) used to estimate daily energy consumption.
    # energy_cost_per_day = energy_cost_per_kwh * AERATOR_WATTS * HOURS_PER_DAY
    AERATOR_WATTS = 820
    HOURS_PER_DAY = 24

    FR_TEMPERATURE_DATA_PATH = "teramina/helpers/data_example/feed_table_temp.csv"
    FR_TEMPERATURE_ARRAY_PATH = "teramina/helpers/data_example/feed_temp_array.csv"

    SHRIMP_PRICE_DATA_PATH = "teramina/helpers/data_example/shrimp_price.csv"
    SHRIMP_PRICE_ARRAY_PATH = (
        "teramina/helpers/data_example/shrimp_price_preprocessed.csv"
    )

    BIOMASS_DESCRIPTION = "The total weight of shrimp in pond."
    SURVIVAL_RATE_DESCRIPTION = "The proportion of shrimp that are able to survive, usually measured as a percentage."
    AVERAGE_DAILY_GROWTH_DESCRIPTION = "The rate at which shrimp grow on a daily basis."
    AVERAGE_BODY_WEIGHT_DESCRIPTION = "The average weight of shrimp in a population."
    FEED_CONVERTION_RATION_DESCRIPTION = (
        "A measure of how efficiently shrimp convert feed into body weight."
    )
    TOTAL_FEED_DESCRIPTION = "Total amount of feed given at current DOC."
    HARVESTED_BIOMASS_DESCRIPTION = (
        "The total weight of shrimp that are harvested at current DOC."
    )
    TOTAL_BIOMASS_DESCRIPTION = "The total weight of all shrimp that are currently in the pond and have been harvested at current DOC."
    POND_BIOMASS_DESCRIPTION = (
        "The total weight of shrimp that are currently in the pond."
    )
    ORIGINAL_FEEDING_RATE_DESCRIPTION = (
        "The original the amount of feed given to shrimp in one DOC."
    )
    ADJUSTED_FEEDING_RATE_DESCRIPTION = "The suggested amount of feed given to shrimp in one DOC calculated using Teramina’s algorithm."
    PROTEIN_CONTENT_DESCRIPTION = (
        "The amount of protein present in the feed given to shrimp"
    )
    CHB_CP_DESCRIPTION = (
        "The ratio of Crude Protein (CP) to Crude Hydrolysable Carbohydrates (CHB)."
    )
    FEEDING_RATION_DESCRIPTION = "The amount of feed given to shrimp per day."
    CURRENT_REVENUE_DESCRIPTION = "The amount of money that the farm earns from the sale of shrimp in the current DOC."
    FORECASTED_REVENUE_DESCRIPTION = "The amount of money that the farm earns from the sale of shrimp in the forecasted DOC."
    CURRENT_PROFIT_DESCRIPTION = "The amount of money that a shrimp farm earns after deducting all of its expenses in the current DOC."
    FORECASTED_PROFIT_DESCRIPTION = "The amount of money that a shrimp farm earns after deducting all of its expenses in the forecasted DOC."
    CURRENT_BIOMASS_DESCRIPTION = (
        "The current weight of shrimp that are currently in the pond."
    )
    FORECASTED_BIOMASS_DESCRIPTION = (
        "The forecasted weight of shrimp that are currently in the pond."
    )
    CURRENT_FCR_DESCRIPTION = (
        "The current ratio of how efficiently shrimp convert feed into body weight."
    )
    FORECASTED_FCR_DESCRIPTION = "The estimated ratio of how efficiently shrimp convert feed into body weight at forecasted DOC."
    CURRENT_FEED_GIVEN_DESCRIPTION = (
        "The total amount of feed given at the current DOC."
    )
    FORECASTED_FEED_GIVEN_DESCRIPTION = (
        "The estimated amount of feed given at the forecasted DOC."
    )
    CURRENT_ABW_DESCRIPTION = (
        "The average weight of shrimp in a population at current DOC."
    )
    FORECASTED_ABW_DESCRIPTION = (
        "The estimated average weight of shrimp in a population at forecasted DOC"
    )

    ## Indonesian
    # BIOMASS_DESCRIPTION = "Total berat udang di kolam."
    # SURVIVAL_RATE_DESCRIPTION = "Proporsi udang yang mampu bertahan hidup, biasanya diukur dalam persentase."
    # AVERAGE_DAILY_GROWTH_DESCRIPTION = "Laju pertumbuhan udang secara harian."
    # AVERAGE_BODY_WEIGHT_DESCRIPTION = "Rata-rata berat udang dalam sebuah populasi."
    # FEED_CONVERTION_RATION_DESCRIPTION = "Ukuran seberapa efisien udang mengubah pakan menjadi berat badan."
    # TOTAL_FEED_DESCRIPTION = "Jumlah total pakan yang diberikan pada saat ini DOC."
    # HARVESTED_BIOMASS_DESCRIPTION = "Total berat udang yang dipanen pada saat ini DOC."
    # TOTAL_BIOMASS_DESCRIPTION = "Total berat semua udang yang saat ini ada di kolam dan telah dipanen pada saat ini DOC."
    # POND_BIOMASS_DESCRIPTION = "Total berat udang yang saat ini ada di kolam."
    # ORIGINAL_FEEDING_RATE_DESCRIPTION = "Jumlah pakan awal yang diberikan pada udang dalam satu DOC."
    # ADJUSTED_FEEDING_RATE_DESCRIPTION = "Jumlah pakan yang disarankan yang diberikan pada udang dalam satu DOC yang dihitung menggunakan algoritma Teramina."
    # PROTEIN_CONTENT_DESCRIPTION = "Jumlah protein yang terkandung dalam pakan yang diberikan pada udang."
    # CHB_CP_DESCRIPTION = "Rasio Protein Kasar (CP) ke Karbohidrat Kasar yang Terhidrolisis (CHB)."
    # FEEDING_RATION_DESCRIPTION = "Jumlah pakan yang diberikan pada udang per hari."
    # CURRENT_REVENUE_DESCRIPTION = "Jumlah uang yang diperoleh peternakan dari penjualan udang pada DOC saat ini."
    # FORECASTED_REVENUE_DESCRIPTION = "Jumlah uang yang diperoleh peternakan dari penjualan udang pada DOC yang diproyeksikan."
    # CURRENT_PROFIT_DESCRIPTION = "Jumlah uang yang diperoleh peternakan udang setelah dikurangi semua biaya pada DOC saat ini."
    # FORECASTED_PROFIT_DESCRIPTION = "Jumlah uang yang diperoleh peternakan udang setelah dikurangi semua biaya pada DOC yang diproyeksikan."
    # CURRENT_BIOMASS_DESCRIPTION = "Berat udang saat ini yang ada di kolam."
    # FORECASTED_BIOMASS_DESCRIPTION = "Perkiraan berat udang saat ini yang ada di kolam pada DOC yang diproyeksikan."
    # CURRENT_FCR_DESCRIPTION = "Rasio saat ini seberapa efisien udang mengubah pakan menjadi berat badan."
    # FORECASTED_FCR_DESCRIPTION = "Perkiraan rasio seberapa efisien udang mengubah pakan menjadi berat badan pada DOC yang diproyeksikan."
    # CURRENT_FEED_GIVEN_DESCRIPTION = "Jumlah total pakan yang diberikan pada saat ini DOC."
    # FORECASTED_FEED_GIVEN_DESCRIPTION = "Perkiraan jumlah pakan yang diberikan pada DOC yang diproyeksikan."
    # CURRENT_ABW_DESCRIPTION = "Rata-rata berat udang dalam sebuah populasi pada saat ini DOC."
    # FORECASTED_ABW_DESCRIPTION = "Perkiraan rata-rata berat udang dalam sebuah populasi pada DOC yang diproyeksikan."

    # english
    TITLE_POND_INFO = "Pond Info"
    TITLE_POND_AREA = "Pond Area"
    TITLE_DENSITY = "Density"
    TITLE_YIELD = "Yield"
    TITLE_PERFORMANCE = "Performance"
    TITLE_BIOMASS = "Biomass"
    TITLE_AVERAGE_BODY_WEIGHT = "Average Body Weight"
    TITLE_SURVIVAL_RATE = "Survival Rate"
    TITLE_ADG = "ADG"
    TITLE_TOTAL_FEED = "Total Feed"
    TITLE_FCR = "FCR"
    TITLE_ECONOMIC = "Economics"
    TITLE_TOTAL_COST = "Total Cost"
    TITLE_TOTAL_REVENUE = "Total Revenue"
    TITLE_TOTAL_PROFIT = "Total Profit"
    TITLE_COST_PER_KILO = "Cost per Kilo"
    TITLE_PROFIT_AND_LOST = "P&L"
    TITLE_COST_BREAKDOWN = "Cost Breakdown"
    TITLE_PRODUCTION_STATUS = "Production Status"
    TITLE_HARVESTED_BIOMASS = "Harvested Biomass"
    TITLE_TOTAL_BIOMASS = "Total Biomass"
    TITLE_POND_BIOMASS = "Pond Biomass"
    TITLE_ABW = "ABW"
    TITLE_FEEDING_STATUS = "Feeding Status"
    TITLE_FEED_GIVEN = "Feed Given"
    TITLE_FEED_COST = "Feed Cost"
    TITLE_FEED_CONVERTION_RATE = "Feed Convertion Rate"
    TITLE_FEED_RATE = "Feed Rate"
    TITLE_ORIGINAL_FEEDING_RATE = "Original Feeding Rate"
    TITLE_ADJUSTMENT_FEEDING_RATE = "Adjustment Feeding Rate"
    TITLE_PROTEIN_CONTENT = "Protein Content"
    TITLE_CHB_CP = "CHB:CP"
    TITLE_DAILY_FEED_ADJUSTMENT = "Daily Feeding Adjustment"
    TITLE_PRODUCTION_FORECAST = "Production Forecast"
    TITLE_CURRENT_BIOMASS = "Current Biomass"
    TITLE_FORECASTED_BIOMASS = "Forecasted Biomass"
    TITLE_CURRENT_ABW = "Current ABW"
    TITLE_FORECASTED_ABW = "Forecasted ABW"
    TITLE_ECONOMIC_FORECAST = "Economic Forecast"
    TITLE_CURRENT_REVENUE = "Current Revenue"
    TITLE_FORECASTED_REVENUE = "Forecasted Revenue"
    TITLE_CURRENT_PROFIT = "Current Profit"
    TITLE_FORECASTED_PROFIT = "Forecasted Profit"
    TITLE_FEEDING_FORECAST = "Feeding Forecast"
    TITLE_CURRENT_FCR = "Current FCR"
    TITLE_FORECASTED_FCR = "Forecasted FCR"
    TITLE_FEED_GIVEN_CURRENT = "Feed Given (C)"
    TITLE_FEED_GIVEN_FORECASTED = "Feed Given (F)"

    ## Indonesian
    # TITLE_POND_INFO="Info Kolam"
    # TITLE_POND_AREA="Luas Kolam"
    # TITLE_DENSITY="Density"
    # TITLE_YIELD="Yield"
    # TITLE_PERFORMANCE="Performa"
    # TITLE_BIOMASS="Biomassa"
    # TITLE_AVERAGE_BODY_WEIGHT="Average Body Weight"
    # TITLE_SURVIVAL_RATE="Survival Rate"
    # TITLE_ADG="ADG"
    # TITLE_TOTAL_FEED="Pakan Diberikan"
    # TITLE_FCR="FCR"

    # TITLE_ECONOMIC="Keuangan"
    # TITLE_TOTAL_COST="Total Biaya"
    # TITLE_TOTAL_REVENUE="Total Omzet"
    # TITLE_TOTAL_PROFIT="Total Profit"
    # TITLE_COST_PER_KILO="Biaya per Kilo"
    # TITLE_PROFIT_AND_LOST="Profit & Loss"
    # TITLE_COST_BREAKDOWN="Rincian Biaya"
    # TITLE_PRODUCTION_STATUS="Status Produksi"
    # TITLE_HARVESTED_BIOMASS="Biomassa Terpanen"
    # TITLE_TOTAL_BIOMASS="Biomassa Keseluruhan"
    # TITLE_POND_BIOMASS="Biomass Di Kolam"
    # TITLE_ABW="ABW"
    # TITLE_FEEDING_STATUS="Status Pakan"
    # TITLE_FEED_GIVEN="Pakan Diberikan"
    # TITLE_FEED_COST="Biaya Pakan"
    # TITLE_FEED_CONVERTION_RATE="Feed Convertion Ratio"
    # TITLE_FEED_RATE="Feed Rate"
    # TITLE_ORIGINAL_FEEDING_RATE="Feeding Rate Awal"
    # TITLE_ADJUSTMENT_FEEDING_RATE="Feeding Rate Disesuaikan"
    # TITLE_PROTEIN_CONTENT="Protein Content"
    # TITLE_CHB_CP="CHB:CP"
    # TITLE_DAILY_FEED_ADJUSTMENT="Penyesuaian Pemberian Pakan"

    # TITLE_PRODUCTION_FORECAST="Prediksi Produksi"
    # TITLE_CURRENT_BIOMASS="Biomassa Sekarang"
    # TITLE_FORECASTED_BIOMASS="Biomassa Diprediksi"
    # TITLE_CURRENT_ABW="ABW Sekarang"
    # TITLE_FORECASTED_ABW="ABW Diprediksi"
    # TITLE_ECONOMIC_FORECAST="Prediksi Keuangan"
    # TITLE_CURRENT_REVENUE="Omzet Sekarang"
    # TITLE_FORECASTED_REVENUE="Omzet Diprediksi"
    # TITLE_CURRENT_PROFIT="Profit Sekarang"
    # TITLE_FORECASTED_PROFIT="Profit Diprediksi"
    # TITLE_FEEDING_FORECAST="Feeding Forecast"
    # TITLE_CURRENT_FCR="FCR Sekarang"
    # TITLE_FORECASTED_FCR="FCR Diprediksi"
    # TITLE_FEED_GIVEN_CURRENT="Pakan Diberikan Sekarang"
    # TITLE_FEED_GIVEN_FORECASTED="Pakan Diberikan Diperdiksi"

    MAX_PARTIAL_HARVEST = 4
    MAX_FEED_TIME = 10              # maximum ration slots per day (was 4)

    # ── Asymmetric feeding penalty ────────────────────────────────────────────
    # Overfeeding: convex (exponential) — each extra kg beyond threshold is
    #              riskier than the previous; never fully safe to overfeed.
    # Underfeeding: linear — growth loss proportional to deficit.
    OVERFEEDING_CONVEXITY = 5.0         # k in: reduction = 1 - exp(-k * excess)
    MAX_OVERFEEDING_REDUCTION = 0.50    # cap: never reduce more than 50%
    MAX_UNDERFEEDING_BOOST = 1.20       # cap: never increase more than 20%

    # ── Sigmoid risk function (DO / NH3 / feed-load interaction) ─────────────
    # P(stress) = σ(α·FR + β/DO + γ·NH3 − intercept)
    # Same FR at low DO generates far higher risk than at optimal DO.
    RISK_ALPHA = 3.0        # feed-rate contribution
    RISK_BETA = 1.5         # DO inverse contribution (higher = more DO-sensitive)
    RISK_GAMMA = 2.0        # NH3 contribution
    RISK_INTERCEPT = 2.0    # shifts sigmoid zero-crossing (baseline risk offset)
    MAX_RISK_REDUCTION = 0.30  # cap: risk function reduces ration by at most 30%

    HARVEST_FIELDS = [
        {"column": "harvest_no", "column_title": "Harvest No."},
        {"column": "harvest_type", "column_title": "Harvest Type"},
        {"column": "doc", "column_title": "DOC"},
        {"column": "biomass_kg", "column_title": "Biomass (Kg)"},
        {"column": "size", "column_title": "Size"},
        {"column": "revenue", "column_title": "Revenue"},
        {"column": "profit", "column_title": "Profit"},
    ]
