# pylint: disable=missing-class-docstring, too-few-public-methods, line-too-long


class Column:
    required_columns = [
        "date",
        "doc",
        "temperature",
        "do",
        "nh3",
        "abw",
        "fr",
        "sr",
        "w0",
        "initial_stocking",
        "labor_cost",
        "bonus_cost",
        "energy_cost",
        "probiotic_cost",
        "other_cost",
        "harvest_cost",
        "feeding_cost",
        "protein_content",
        "chb",
    ]

    required_columns_simple = [
        "date",
        "doc",
        "temperature",
        "do",
        "nh3",
        "abw",
        "fr",
        "sr",
        "initial_stocking",
    ]

    single_data_columns = [
        "sr",
        "w0",
        "initial_stocking",
        "labor_cost",
        "bonus_cost",
        "energy_cost",
        "probiotic_cost",
        "other_cost",
        "harvest_cost",
        "feeding_cost",
        "protein_content",
        "chb",
    ]

    dependent_columns = ["temperature", "do", "nh3", "abw"]

    cost_columns = [
        "labor_cost",
        "bonus_cost",
        "energy_cost",
        "probiotic_cost",
        "other_cost",
        "harvest_cost",
        "feeding_cost",
    ]

    day_cost_columns = [
        "cost_feed",
        "cost_probiotics",
        "cost_energy",
        "cost_labor",
        "cost_bonuss",
        "cost_harvest",
        "cost_other",
    ]

    partial_columns = ["partial1_doc", "partial2_doc", "partial3_doc", "final_doc"]
