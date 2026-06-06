# pylint: disable=too-few-public-methods, E0401, C0115, E0402, W0707, R1705
import io
from datetime import datetime
from ninja import Schema
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .variable_management import VariableManagement, canonical_wq_variable_name
from ...schemas.general_schema import DataSuccessSchema, DataErrorSchema
from ...cycle_data.models.cycle_data_model import CycleData
from ...cycle.models.cycle_model import Cycle
from ...helpers.plot import Line, BasicScatter
from ...helpers.utils import left_trapezoidal, normal_trapezoidal


matplotlib.use("Agg")


class AddVariableSchema(Schema):
    variables: list


class WaterQuality:
    """water quality"""

    def get_result_data(self, cycles: list):
        """get result data"""
        data = []
        for cycle_id in cycles:
            cycle = Cycle.objects(id=cycle_id).only("name").first()
            result_data = (
                CycleData.objects(cycle_id=cycle_id).only("result_data").first()
            )
            if result_data:
                ndf = pd.DataFrame(result_data.result_data)
                ndf["date"] = pd.to_datetime(ndf["date"], errors="raise")
                ndf = self.generate_water_quality_index(ndf)
                ndf["cycle"] = cycle.name
                data.append(ndf)

        return data

    def date_data_mapping(self, start_date, end_date):
        """date mapping"""
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if (end_date - start_date).days < 0:
            raise ValueError("The range of date should be incremented")

        return start_date, end_date

    def get_first_wqi(self, df):
        """generate first wqi"""
        columns = [i for i in df.columns if i.endswith("_score_weight")]
        data = df[columns].values
        return data.sum(axis=1)

    def get_second_wqi(self, df):
        """generate second wqi"""
        columns = [i for i in df.columns if i.endswith("_score_weight")]
        weight_columns = [i for i in df.columns if i.endswith("_scale")]
        score_columns = [i for i in df.columns if i.endswith("_score")]

        values = (df[columns].sum(axis=1) / df[weight_columns].sum(axis=1)).values
        has_negative = np.any(df[score_columns].values < 0)
        if has_negative:
            minimum_values = np.min(df[score_columns].values, axis=1)
            values = minimum_values * values

        return values

    def get_parameter(self, var_name):
        """get parameter"""
        data = VariableManagement().is_variable_exist(var_name)
        return (
            data.weight,
            data.type,
            data.lower_bound,
            data.optimal_min,
            data.optimal_max,
            data.upper_bound,
        )

    def generate_water_quality_index(self, df):
        """add wqi into df"""
        wq_variables = df.columns
        for i in wq_variables:
            var = canonical_wq_variable_name(i)
            if var in VariableManagement().get_variable_names():
                try:
                    (
                        param_weight,
                        param_type,
                        lb,
                        opt_min,
                        opt_max,
                        ub,
                    ) = self.get_parameter(var)

                    if param_type == "left":
                        df[f"{i}_score"] = [
                            left_trapezoidal(x, lb, ub, opt_max) for x in df[i].values
                        ]
                    else:
                        df[f"{i}_score"] = [
                            normal_trapezoidal(x, lb, ub, opt_min, opt_max)
                            for x in df[i].values
                        ]

                    df[f"{i}_score_weight"] = param_weight * df[f"{i}_score"]
                    df[f"{i}_scale"] = param_weight
                except TypeError as err:
                    raise TypeError(f"please check your type of data. {err}")

        df["wqi_1"] = self.get_first_wqi(df)
        df["wqi_2"] = self.get_second_wqi(df)

        return df

    def get_data(
        self,
        cycles: str,
        start_date: str = None,
        end_date: str = None,
    ):
        """get all data"""
        if not cycles:
            raise ValueError("No one cycle selected")

        cycles = cycles.split(",")

        start_date, end_date = self.date_data_mapping(start_date, end_date)

        list_df = self.get_result_data(cycles)
        new_list_df = []
        for df in list_df:
            new_list_df.append(
                df[(df["date"] >= start_date) & (df["date"] <= end_date)]
            )

        return new_list_df

    def get_table(
        self,
        cycles: str,
        start_date: str = None,
        end_date: str = None,
        variables: str = None,
    ):
        """get table"""
        if not cycles:
            raise ValueError("No one cycle selected")

        data = self.get_data(cycles, start_date, end_date)
        df = pd.concat(data, axis=0)
        variables = variables.split(",")
        df = df[["cycle", "date", "doc"] + variables]
        df["date"] = df["date"].dt.date
        # Replace NaN with None
        df = df.replace({np.nan: None})
        return df

    # Define a custom aggregation function
    def custom_sum(self, series):
        """custom sum"""
        if series.isna().all():
            return np.nan
        else:
            return series.sum()

    def restructuring_variables_length(self, df: pd.DataFrame, cycles: list):
        """resturcturing variable"""
        columns = []
        data = []
        for cycle in cycles:
            data.append(df.groupby(["cycle", "doc"]).agg(self.custom_sum).loc[cycle])
            columns.append(cycle)

        ndf = pd.concat(data, axis=1)
        ndf = ndf.replace(np.nan, None)
        return ndf

    def get_plot(self, df: pd.DataFrame, variables: str, plot_type: str) -> list:
        """generate line plot"""
        variables = variables.split(",")
        plot = []
        for var in variables:
            ndf = df[["cycle", "doc", var]]
            ndf = self.restructuring_variables_length(
                ndf, ndf["cycle"].unique().tolist()
            )

            is_any_null_values = any(ndf[var].isna())
            index = ndf.index.astype(str).tolist()
            if plot_type == "line":
                plot_data = Line(
                    title=var,
                    x=index,
                    y=ndf.values.transpose().tolist(),
                    labels=ndf.columns.tolist(),
                    legend=True,
                ).plot()
                if is_any_null_values:
                    plot_data["series"][0]["symbol"] = "circle"
            else:
                plot_data = BasicScatter(
                    title=var,
                    x=index,
                    y=ndf.values.transpose().tolist(),
                    labels=ndf.columns.tolist(),
                    legend=True,
                ).plot()

            if var == "temperature":
                plot_data["yAxis"]["min"] = 15
                plot_data["yAxis"]["max"] = 35

            if var == "ph":
                plot_data["yAxis"]["min"] = 4
                plot_data["yAxis"]["max"] = 9

            plot_data["color"] = [
                "#57D0CB",
                "#2CC1BA",
                "#00B1A9",
                "#008E87",
                "#80c7c3",
                "#c0e3e1",
                "#e0f1f0",
            ]
            plot.append(plot_data)

        return plot

    def get_plot_document(self, df: pd.DataFrame, variables: str):
        """generate plot document"""
        variables = variables.split(",")
        pallete = [
            "#57D0CB",
            "#2CC1BA",
            "#00B1A9",
            "#008E87",
            "#80c7c3",
            "#c0e3e1",
            "#e0f1f0",
        ]

        _, axes = plt.subplots(nrows=len(variables), figsize=(40, 6 * len(variables)))
        for idx, var in enumerate(variables):
            ndf = df[["cycle", "doc", var]]
            ndf = self.restructuring_variables_length(
                ndf, ndf["cycle"].unique().tolist()
            )
            index = ndf.index.astype(str).tolist()
            for i, col in enumerate(ndf.columns):
                axes[idx].plot(
                    index, ndf[col].values, color=pallete[i % len(pallete)], label=col
                )

            axes[idx].set_xlabel("doc")
            axes[idx].set_title(var)
            axes[idx].grid(axis="y")

        # Save the plot to a BytesIO object as a PDF
        buffer = io.BytesIO()
        plt.savefig(buffer, format="pdf")
        buffer.seek(0)
        plt.close()

        return buffer

    def get_water_quality_data(
        self,
        cycles: str,
        start_date: str = None,
        end_date: str = None,
        variables: str = None,
    ):
        """water quality data"""
        try:
            data = self.get_table(cycles, start_date, end_date, variables)
            line_plot = self.get_plot(data, variables, plot_type="line")
            scatter_plot = self.get_plot(data, variables, plot_type="scatter")
        except (KeyError, TypeError, ValueError) as e:
            return 400, DataErrorSchema(code=400, message=str(e))

        return 200, DataSuccessSchema(
            code=200,
            message="Variable successfully registered.",
            payload={
                "data": data.to_dict("records"),
                "line_plot": line_plot,
                "scatter_plot": scatter_plot,
            },
        )
