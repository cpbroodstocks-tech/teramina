# pylint: disable=consider-using-f-string, C0121, R0903, E0401, R0914
import asyncio
import pandas as pd
import numpy as np
from mongoengine.errors import InvalidQueryError

from teramina.pond.models.pond_model import Pond
from teramina.cycle.models.cycle_model import Cycle
from teramina.helpers.constant_value import Constant
from teramina.schemas.general_schema import DataSuccessSchema, DataErrorSchema
from teramina.helpers.plot import Line, PieReport, BasicScatter, LineMultiScatter#, Scatter
from teramina.helpers.unit import Unit
from teramina.summarize.summarize_service import SingleChat

from teramina.dashboard.services.historical.utils import (
    get_list_pond_id,
    get_list_cycle_id,
    get_selected_data,
    extract_json
)

from teramina.dashboard.services.historical.economic import DashboardEconomic
from teramina.water_quality_dashboard.services.variable_management import (
    VariableManagement,
)


class DashboardOverview:
    """Dashboard service that leads to provide data for dashboard view"""

    def __init__(self, farm_id, pond_id=None, cycle_id=None, date=None) -> None:
        self.farm_id = farm_id
        self.pond_id = pond_id
        self.cycle_id = cycle_id
        self.date = date

        # get the list of data
        self.pond_list = get_list_pond_id(farm_id) if farm_id else []
        self.cycle_list = get_list_cycle_id(pond_id) if pond_id else []

    def __get_performance_metric(
        self,
        series_data: pd.Series = None,
        dataframe_data: pd.DataFrame = None,
        column_name: str = None,
        is_agregate=True,
    ):
        try:
            if is_agregate:
                if not series_data:
                    raise ValueError("srs couldn't be None for agregate is True")

                data = series_data[-2:].astype(float)
            else:
                if dataframe_data is None:
                    raise ValueError("df couldn't be None for agregate is False")

                if not column_name:
                    raise ValueError(
                        "column_name couldn't be None for agregate is False"
                    )

                data = dataframe_data[column_name].tail(2).astype(float)

            len_data = data.shape[0]
            current_value = None if np.isnan(data.iloc[-1]) else data.iloc[-1]

            if (len_data == 1) or (current_value == None):
                change_ratio = 0
            else:
                change_ratio = (
                    round(100 * (current_value - data.iloc[0]) / data.iloc[0], 2)
                    if data.iloc[0] != 0
                    else 0
                )

            status = "equal"
            if change_ratio > 0:
                status = "increase"
            elif change_ratio < 0:
                status = "decrease"

        except ValueError as exc:
            raise ValueError(f"error:{exc}") from exc

        return current_value, change_ratio, status

    def __get_pond_info(self, cycle_id):
        cycle = Cycle.objects(id=cycle_id).only("pond_id").first()
        pond = (
            Pond.objects(id=cycle.pond_id).only("name", "name", "size", "depth").first()
        )
        return {
            "id": cycle.pond_id,
            "name": pond.name,
            "area": pond.size,
            "depth": pond.depth,
        }

    def __get_economic_overview_data(self, df: pd.DataFrame):
        economic_obj = DashboardEconomic(
            farm_id=self.farm_id,
            pond_id=self.pond_id,
            cycle_id=self.cycle_id,
            date=self.date,
        )
        profit_lost = economic_obj.get_profit_lost_metric(df, df["doc"].max())
        economics = {
            "title": Constant.TITLE_ECONOMIC,
            "data": profit_lost["data"][1:],
        }

        return economics

    def __get_detail_area(self, is_agregate=True):
        if is_agregate:
            list_area = []
            for pond in self.pond_list:
                cycles = get_list_cycle_id(pond)
                for cycle in cycles:
                    list_area.append(self.__get_pond_info(cycle)["area"])

            area = sum(list_area)
        else:
            pond_description = self.__get_pond_info(self.cycle_id)
            area = pond_description["area"]

        return area

    def __get_abw_plot(self, df: pd.DataFrame):
        """get the size variation"""
        doc = df["doc"].tolist()
        sampling_df = df.filter(like="sampling_")
        if sampling_df.empty:
            abw_plot = Line(
                title="",
                x=doc,
                y=[df["adj_abw"].round(2).tolist()],
                labels=["Average Body Weight (Gr) "],
                legend=False,
                smooth=True,
            ).plot()
            return abw_plot

        labels = sampling_df.columns.tolist()
        # Replace NaN with None so the JSON serializer emits null, not the invalid NaN token
        y_raw = sampling_df.round(2).values.T.tolist()
        y_clean = [[None if (v != v) else v for v in row] for row in y_raw]
        abw_plot = LineMultiScatter(title="",
            x=doc,
            y=y_clean,
            labels=labels,
            legend=True
        ).get_combined_plot("Average Body Weight (Gr) ", df["abw"].tolist())
        return abw_plot

    def __get_pond_overview_data(self, df: pd.DataFrame, last_doc: int, is_agregate=True):
        area = self.__get_detail_area(is_agregate)
        pond_info = {
            "title": Constant.TITLE_POND_INFO,
            "data": [
                {
                    "title": Constant.TITLE_POND_AREA,
                    "value": area,
                    "unit": "m2",
                },
                {
                    "title": "Density",
                    "value": round(df["initial_stocking"].iloc[0] / area, 2),
                    "unit": Unit.pl_m2,
                },
                {
                    "title": "Yield",
                    "value": round(
                        (df["harvest_biomass_kg"].sum() / 1000) / (area / 10000),
                        2,
                    ),
                    "unit": Unit.mt_ha,
                },
                {
                    "title": "DOC",
                    "value": int(last_doc),
                    "unit": Unit.days,
                },
            ],
        }

        return pond_info

    def __get_performance_overview_data(self, df: pd.DataFrame, doc: list, is_agregate=True):
        # set the performance column data
        performance_columns = [
            "biomass_kg",
            "",
            "cum_feed",
            "realized_fcr",
        ]
        performance_data = [
            {
                "title": "Biomass",
                "value": 0,
                "unit": Unit.kg,
                "current_status": "",
                "change_ratio": 0,
                "description": Constant.BIOMASS_DESCRIPTION,
            },
            {
                "title": "Survival Rate",
                "value": (
                    round(df["sr"].iloc[-1] * 100, 2) if df["sr"].iloc[-1] else None
                ),
                "unit": Unit.percent,
                "current_status": "equal",
                "change_ratio": 0,
                "description": Constant.SURVIVAL_RATE_DESCRIPTION,
            },
            {
                "title": Constant.TITLE_TOTAL_FEED,
                "value": 0,
                "unit": Unit.kg,
                "current_status": "",
                "change_ratio": 0,
                "description": Constant.TOTAL_FEED_DESCRIPTION,
            },
            {
                "title": "FCR",
                "value": 0,
                "unit": "",
                "current_status": "",
                "change_ratio": 0,
                "description": Constant.FEED_CONVERTION_RATION_DESCRIPTION,
            },
        ]
        # generating plot
        plot = []
        if not is_agregate:
            # update value of data
            df.eval("adg = adj_abw.iloc[-1] - adj_abw.iloc[-2]", inplace=True)
            performance_columns.insert(1, "adj_abw")
            performance_columns.insert(3, "adg")
            abw_plot = self.__get_abw_plot(df)
            plot.append({"title": "ABW Plot", "echart_option": abw_plot})
            performance_data.insert(
                1,
                {
                    "title": "Average Body Weight",
                    "value": 0,
                    "unit": Unit.gr,
                    "current_status": "",
                    "change_ratio": 0,
                    "description": Constant.AVERAGE_BODY_WEIGHT_DESCRIPTION,
                },
            )
            performance_data.insert(
                3,
                {
                    "title": "ADG",
                    "value": 0,
                    "unit": Unit.gr,
                    "current_status": "",
                    "change_ratio": 0,
                    "description": Constant.AVERAGE_DAILY_GROWTH_DESCRIPTION,
                },
            )

            # sgr plot
            if "sgr" in df.columns:
                df["sgr"] = df["sgr"].round(2)
                sgr_data = df[df["sgr"].notna()]
                # df["sgr"] = df["sgr"].replace({np.nan: None})
                # sgr_value = df["doc"]
                plot.append(
                    {
                        "title": "SGR Plot",
                        "echart_option": Line(
                            title="",
                            x=sgr_data["doc"].tolist(),
                            y=[sgr_data["sgr"].tolist()],
                            labels=["sgr"],
                            legend=False,
                        ).plot()
                    }
                )

        biomass_plot = Line(
            title="",
            x=doc,
            y=[df["biomass_kg"].round(2).tolist()],
            labels=["Biomass (Kg)"],
            legend=False,
        ).plot()
        plot.append({"title": "Biomass Plot", "echart_option": biomass_plot})

        # set the result
        performance = {
            "title": Constant.TITLE_PERFORMANCE,
            "data": performance_data,
            "plot": plot,
        }

        # update the value
        for idx, column in enumerate(performance_columns):
            if column != "":
                current_value, change_ratio, status = self.__get_performance_metric(
                    dataframe_data=df, column_name=column, is_agregate=False
                )

                if column in ["adg", "realized_fcr"]:
                    current_value = round(current_value, 3)
                else:
                    current_value = round(current_value)

                performance["data"][idx]["value"] = current_value
                performance["data"][idx]["current_status"] = status
                performance["data"][idx]["change_ratio"] = change_ratio

        return performance

    def __get_summarize_prompt(self, df):
        """summarize with AI"""

        unused_variables = [
            "cost_bonuss",
            "bonus_cost",
            "protein_content",
            "alpha4",
            "cost_seed",
            "adj_fr",
            "other_cost",
            "alpha2",
            "feed_ration_3",
            "feed_ration_2",
            "potential_revenue",
            "profit",
            "w0",
            "harvest_cost",
            "initial_fr",
            "feed_ration_4",
            "initial_stocking",
            "alpha1",
            "cost_harvest",
            "chb",
            "category",
            "harvest_population",
            "feed_ration_1",
            "adj_abw",
            "alpha3",
            "biomass_kg",
            "harvest_biomass_kg",
            "total_biomass"
        ]
        used_variables = list(set(df.columns) - set(unused_variables))
        df["realized_fcr"] = df["realized_fcr"].round(2)
        if "adg" in df.columns:
            df["adg"] = df["adg"].round(2)
        data = str(df[used_variables].iloc[-1].to_dict())

        prompt = f"""
        Think step by step\
        You are a professional expert in shrimp farming. Your task is to make precise analyses and actionable recommendations for shrimp farmers\
        Here are the guidance for analysis:\
        1. Load this pond's data from the shrimp farm\
        {data}
        2. Identify if there is any problem in the farm\
        3. Make an analysis on how the farm performing, choose the reliable metrics\
        4. Give recommendations on which area the farmer should pay attention to\
        5. Summarize those into 150 words maximum\
        6. Make it very concise, complete and structured\
        7. Avoid output mentioning 'nan' or value is not provided.\
        8. Make your report engaging, informative, and well-structured\
        Here are some example important metrics:
        \
        FCR (Feed Conversion Ratio),
        FCR is ideal when less than 1.2,
        FCR is suitable between 1.2-1.4,
        FCR is not good when more than 1.4,
        \
        dissolve oxygen (DO),
        DO Optimal Range 5-8 ppm,	
        DO Suitable Range 4-5 and 8-9 ppm,
        DO Dangerous less than 4 ppm and greater than 9 ppm,
        \
        Growth Rate (SGR),
        SGR should monotonous increasing function,
        If the Growth Rate is decreasing, then there are some potential problem causing shrimp's growth.
        Find water quality that is not in optimal range,
        Address that probelm using your knowldge,
        \
        survival rate (SR), 
        SR baseline is 70%, less than that mean is not ideal, and less than 60% is a bad performance
        \
        carrying capacity maximum is 3kg/m3, suitable  when it is less than 2kg/m3
        \
        cost per kg:
        cost per kg ideal is less than Rp. 40,000,
        cost per kg is good between Rp. 40,000 - Rp. 45,000,
        cost per kg is acceptable Rp. 45,000 - Rp. 50,000,
        cost per kg is inefficient when more than Rp. 50,000,
        \
        Yield
        Yield above 30Ton/Ha is excellent,
        Yield in the range of 20-30Ton/Ha is good,
        Yield between 15-20Ton/Ha is acceptable,
        Yield below 15Ton/Ha is low,
        \
        Here are the guidance to identify problem:\
        Farm in trouble  
          ├── Low yield, biomass
          │     └── Low survival rate (SR)
          │           └── Mortality
          │                 ├── Disease
          │                 │     └── Various diseases
          │                 ├── Stress
          │                 │      ├── Water quality variable outside optimal range
          │                 │      │     ├── Daily swing from natural process
          │                 │      │     ├── Daily swing from chemico/phytotics treatment
          │                 │      │     ├── Daily swing from operational
          │                 │      │     │     ├── by water exchange
          │                 │      │     │     ├── by partial harvest
          │                 │      │     │     └── by shipping
          │                 │      └── Anaerobic conditions
          │                 │      │     ├── Overfeeding
          │                 │      │     ├── High biomass
          │                 │      │     ├── Inadequate aeration
          │                 │      │     ├── Phyto-plankton bloom
          │                 │      │     ├── Poor Feed Delivery and Maintenance
          │                 │      │     ├── Algal Blooms
          │                 │      │     ├── Decomposition of Organic Matter
          │                 │      │     ├── Climatic Conditions
          │                 │      │     └── Pond water depth/stratification
          │  		        │	   ├── Biomass exceeds pond's carrying capacity
          │                 │
          │                 ├── Genetic traits
          │                 ├── Cannibalism
          │                 ├── Molting
          │                 ├── Toxic substances
          │                 │     ├── NO3
          │                 │     ├── NO2
          │                 │     └── NH4
          │                 └── Oxygen Depletion
          │                       ├── Anaerobic conditions
          │                       ├── In-optimal aeration
          │                       ├── Algal bloom
          │                       └── Handling and Transport
          ├── Low shrimp price
          ├── In-efficiency in operational cost (OPEx)
          │     └── High FCR
          │           ├── Slow growth/average daily growth (adg)
          │           │     ├── Disease
          │           │     ├── Stress
          │           │     ├── Under-feeding
          │           │     └── Bad feed quality
          └── Bad budgeting/planning
                ├── No cost control/cost accounting
                ├── No proper budgeting/planning
                ├── Bad decision making on harvesting
                │     └── There are no visibility on important factors affecting decision
                └── Bias
        """
        return prompt

    def __get_report_prompt(self, data: dict):
        """prompt for report"""

        prompt = f"""
            make intepretation if my data has values:
            {data}
            make the interpretation in JSON format.\
            Make an in-depth analysis and recommendation of the pond's financial performance based on the given data in 'summary_finance'.\
            Make an in-depth analysis and recommendation of the pond's cost spending based on the given data in 'summary_cost_counting'.\
            Make an in-depth analysis and recommendation of the pond's water quality states based on the given data in 'summary_water_quality' and 'intepretation_water_quality'.\
        """
        return prompt

    def overview(self):
        """overview data"""
        try:
            df, group_df = get_selected_data(
                self.farm_id, self.pond_id, self.cycle_id, self.date
            )
            if self.cycle_id:
                pond_info = self.__get_pond_overview_data(
                    df, last_doc=df["doc"].max(), is_agregate=False
                )
                performance = self.__get_performance_overview_data(
                    df, doc=group_df[0]["doc"].tolist(), is_agregate=False
                )
            else:
                pond_info = self.__get_pond_overview_data(df, last_doc=df["doc"].max())
                performance = self.__get_performance_overview_data(
                    df, doc=group_df[0]["doc"].tolist()
                )

            economics = self.__get_economic_overview_data(df)
            prompt = self.__get_summarize_prompt(df)

        except (
            KeyError,
            ValueError,
            TypeError,
            AttributeError,
            InvalidQueryError,
            LookupError,
        ) as err:
            return 400, DataErrorSchema(code=400, message=str(err))

        return 200, DataSuccessSchema(
            code=200,
            message="OK",
            payload={
                "prompt_summary": prompt,
                "pond_info": pond_info,
                "performance": performance,
                "economics": economics,
            },
        )

    async def download_report_pdf(self):
        """pdf report downloader"""
        df, _ = get_selected_data(self.farm_id, self.pond_id, self.cycle_id, self.date)
        area = self.__get_detail_area(False)
        last_data = df[["adj_abw", "realized_revenue", "total_cost", "profit"]].iloc[-1].tolist()
        # water quality
        var_names = VariableManagement().get_variable_names()
        current_cols = [i for i in df.columns if i in var_names]
        wq_data = df[current_cols].round(2)
        wq_data = wq_data.iloc[-1].to_dict()

        # economic
        economic_obj = DashboardEconomic(
            farm_id=self.farm_id,
            pond_id=self.pond_id,
            cycle_id=self.cycle_id,
            date=self.date,
        )
        economic_table, _ = economic_obj.get_cost_breakdown_data(df)
        colors = ["#104C9C","#E71D7A","#EE7859","#FAB72D","#F0E419","#4CAF46","#D0D0D0"]
        if len(economic_table["name"]) == 8:
            colors.append("#C4B0FF")
        # pie plot
        PieReport(
            economic_table["value"].str.replace(',', '').astype(float),
            label=economic_table["name"], color=colors
        ).plot("pie_plot.png")

        # data preparation
        data_to_interprete = {
            "adg": last_data[0] - df["adj_abw"].iloc[-2],
            "abw": last_data[0],
            "yield": round((df["harvest_biomass_kg"].sum() / 1000) / (area / 10000),2),
            "revenue": last_data[1],
            "total_cost": last_data[2],
            "profit": last_data[3],
        }

        data_to_interprete.update(zip(economic_table["name"], economic_table["value"]))
        data_to_interprete.update(wq_data)

        result = await asyncio.wait_for(
            SingleChat('openai').stream_ask(self.__get_report_prompt(data_to_interprete)),
            timeout=90
        )

        result = extract_json(result)

        report_contents = {
            "content": [
                {
                    "title": "A. Farm Summary",
                    "type": "text",
                    "interpretation": None,
                    "content": [
                        {
                            "title": "1. Productivity",
                            "type": "text",
                            "interpretation": None,
                            "content": [
                                {
                                    "title": "Yield",
                                    "type": "text",
                                    "interpretation": result["yield"],
                                    "content": [],
                                },
                                {
                                    "title": "MBW",
                                    "type": "text",
                                    "interpretation": result["abw"],
                                    "content": [],
                                },
                                {
                                    "title": "ADG",
                                    "type": "text",
                                    "interpretation": result["adg"],
                                    "content": [],
                                },
                            ],
                        },
                        {
                            "title": "2. Finance",
                            "type": "text",
                            "interpretation": result["summary_finance"],
                            "content": [],
                        },
                        {
                            "title": "3. Water Quality",
                            "type": "text",
                            "interpretation": result["summary_water_quality"],
                            "content": [],
                        },
                    ],
                },
                {
                    "title": "B. Cost Counting",
                    "type": "text",
                    "interpretation": None,
                    "content": [
                        {
                            "title": None,
                            "type": "image",
                            "interpretation": None,
                            "content": [],
                            "url": "pie_plot.png",
                            "config": {"width": 100, "location_x": 15},
                        },
                        {
                            "title": None,
                            "type": "text",
                            "interpretation": result["summary_cost_counting"],
                            "content": [],
                        },
                    ],
                },
                {
                    "title": "C. Water Quality",
                    "type": "text",
                    "interpretation": None,
                    "content": [
                        {
                            "title": None,
                            "type": "table",
                            "interpretation": None,
                            "content": [],
                            "table_data": df[current_cols]
                            .round(2)
                            .iloc[-1]
                            .reset_index()
                            .values.tolist(),
                            "table_column_widths": [40, 30],
                        },
                        {
                            "title": None,
                            "type": "text",
                            "interpretation": result["intepretation_water_quality"],
                            "content": [],
                        },
                    ],
                },
            ]
        }

        return report_contents
