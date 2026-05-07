# pylint: disable=too-few-public-methods, too-many-arguments, too-many-instance-attributes, too-many-positional-arguments

import numpy as np
import matplotlib.pyplot as plt


class Line:
    """Echart line plot generator"""

    def __init__(
        self, title: str, x: list, y: list, labels: list, legend: bool = False, smooth: bool = False
    ):
        """Line Plot

        Args:
            title (str): title of plot
            x (list): x axis data
            y (list): y axis data
            labels (list): labels of data
            legend (bool, optional): wether using legend or not. Defaults to False.
            smooth (bool, optional): smooth bezier curve. Defaults to False.
        """
        self.title = title
        self.x = x
        self.y = y
        self.labels = labels
        self.legend = legend
        self.smooth = smooth

    def plot(self):
        """generate plot"""
        legend = {"data": self.labels, "show": self.legend, "top": "10%"}
        series = [
            {"name": i[1], "data": self.y[i[0]], "type": "line", "symbol": "none", "smooth": self.smooth}
            for i in enumerate(self.labels)
        ]

        option = {
            "title": {"text": self.title},
            "legend": legend,
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": self.x},
            "yAxis": {"type": "value"},
            "series": series,
        }

        return option


class BasicScatter:
    """Echart Scatter plot generator"""

    def __init__(
        self, title: str, x: list, y: list, labels: list, legend: bool = False
    ):
        """Line Plot

        Args:
            title (str): title of plot
            x (list): x axis data
            y (list): y axis data
            labels (list): labels of data
            legend (bool, optional): wether using legend or not. Defaults to False.
        """
        self.title = title
        self.x = x
        self.y = y
        self.labels = labels
        self.legend = legend

    def plot(self):
        """generate plot"""
        legend = {"data": self.labels, "show": self.legend, "top": "10%"}
        series = [
            {"name": i[1], "data": self.y[i[0]], "type": "scatter"}
            for i in enumerate(self.labels)
        ]

        option = {
            "title": {"text": self.title},
            "legend": legend,
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": self.x},
            "yAxis": {"type": "value"},
            "series": series,
        }

        return option

class LineMultiScatter(BasicScatter):
    """Echart line plot with multiple scatter"""
    def get_combined_plot(self, line_label, line_data):
        """generate plot"""
        option = self.plot()
        series = option["series"]
        legend_data = option["legend"]["data"]

        # Make sampling-tray scatter dots prominent
        for s in series:
            s["symbolSize"] = 10
            s["itemStyle"] = {"borderWidth": 2, "borderColor": "white"}

        # Smooth continuous line for the Kalman-estimated ABW
        series.append({
            "name": line_label,
            "data": line_data,
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2.5},
            "z": 1,
        })
        legend_data.append(line_label)
        option["legend"]["data"] = legend_data
        option["series"] = series
        return option

class Bar:
    """Echart line plot generator"""

    def __init__(
        self, title: str, x: list, y: list, labels: list, legend: bool = False
    ):
        """Bar Plot

        Args:
            title (str): title of plot
            x (list): x axis data
            y (list): y axis data
            labels (list): labels of data
            legend (bool, optional): wether using legend or not. Defaults to False.
        """
        self.title = title
        self.x = x
        self.y = y
        self.labels = labels
        self.legend = legend

    def plot(self):
        """generate plot"""
        legend = {"data": self.labels, "show": self.legend, "top": "10%"}
        series = [
            {"name": i[1], "data": self.y[i[0]], "type": "bar", "symbol": "none"}
            for i in enumerate(self.labels)
        ]

        option = {
            "title": {"text": self.title},
            "legend": legend,
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": self.x},
            "yAxis": {"type": "value"},
            "series": series,
        }

        return option


class LineForecast:
    """Echart line plot generator for forecast"""

    def __init__(
        self,
        title: str,
        x: list,
        y: list,
        betweenes_index: int,
        labels: list,
        legend: bool = False,
        base_color="blue",
        forecast_color="red",
    ):
        """Line Plot for Forecasted

        Args:
            title (str): _description_
            x (list): _description_
            y (list): _description_
            betweenes_index (int): _description_
            labels (list): _description_
            legend (bool, optional): _description_. Defaults to False.
            base_color (str, optional): _description_. Defaults to "blue".
            forecast_color (str, optional): _description_. Defaults to "red".
        """
        self.title = title
        self.x = x
        self.y = y
        self.labels = labels
        self.legend = legend
        self.base_col = base_color
        self.forecast_col = forecast_color
        self.betweenes_index = betweenes_index  # based on index of DOC

    def __get_visual_map(self):
        pieces = [
            {"lte": self.betweenes_index, "color": self.base_col},
            {
                "gt": self.betweenes_index,
                "lte": len(self.y[0]),
                "color": self.forecast_col,
            },
        ]

        return {"show": False, "dimension": 0, "pieces": pieces}

    def plot(self):
        """generate plot"""
        legend = {"data": self.labels, "show": self.legend, "top": "10%"}
        series = [
            {
                "name": i[1],
                "data": self.y[i[0]],
                "type": "line",
                "symbol": "none",
                "markArea": {
                    "itemStyle": {"color": "#f4f5fb"},
                    "data": [
                        [
                            {"name": "forecast", "xAxis": self.betweenes_index},
                            {"xAxis": self.x[-1]},
                        ]
                    ],
                },
            }
            for i in enumerate(self.labels)
        ]

        option = {
            "title": {"text": self.title, "left": "center"},
            "legend": legend,
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": self.x},
            "yAxis": {"type": "value"},
            "visualMap": self.__get_visual_map(),
            "series": series,
        }

        return option


class Pie:
    """Echart Pie Plot"""

    def __init__(
        self, title, data, doughnut: bool = False, legend: bool = False
    ) -> None:
        """Pie Plot

        Args:
            title (str): title of plot
            data (dict): _description_
            doughnut (bool, optional): condition for doughnut type. Defaults to False.
            legend (bool, optional): condition for legend. Defaults to False.
        """
        self.title = title
        self.data = data
        self.doughnut = doughnut
        self.legend = legend

    def plot(self):
        """generate plot"""
        radius = ["40%", "70%"] if self.doughnut else "50%"
        option = {
            "title": {"text": self.title},
            "legend": {"show": self.legend},
            "tooltip": {"trigger": "item"},
            "series": [
                {
                    "name": "Costing",
                    "type": "pie",
                    "radius": radius,
                    "data": self.data,
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)",
                        }
                    },
                }
            ],
        }
        return option


class LineScatter:
    """Line Plot with Scatter"""

    def __init__(
        self,
        title: str,
        x: list,
        y: list,
        absis: list,
        ordinat: list,
        labels=None,
    ):
        """Line Plot with scatter

        Args:
            title (str): title of plot
            x (list): x axis data
            y (list): y axis data
            absis (list): x data for scatter
            ordinat (list): y data for scatter
            labels (list, optional): labels of data. Defaults to None.
        """
        if not labels:
            labels = ["line", "scatter"]

        self.title = title
        self.absis_scatter = np.array(absis)
        self.ordinat_scatter = np.array(ordinat)
        self.x = x
        self.y = y
        self.labels = labels

    def plot(self):
        """generate plot"""
        series = [
            {"name": self.labels[0], "data": self.y, "type": "line", "symbol": "none"},
            {
                "name": self.labels[1],
                "data": np.append(
                    np.array(list(range(len(self.x)))).reshape(len(self.x), 1),
                    self.ordinat_scatter.reshape(self.ordinat_scatter.size, 1),
                    axis=1,
                ).tolist(),
                "type": "scatter",
            },
        ]

        option = {
            "title": {"text": self.title},
            "tooltip": {"trigger": "axis"},
            "legend": {},
            "yAxis": {"type": "value"},
            "xAxis": {"type": "category", "data": self.x},
            "series": series,
        }

        return option


class Scatter:
    """Echart scatter plot"""

    def __init__(self, title: str, absis: list, ordinat: list, label: str=None):
        """Scatter Plot

        Args:
            title (str): title of plot
            absis (list): x axis data
            ordinat (list): y axis data
        """
        self.title = title
        self.absis_scatter = np.array(absis)
        self.ordinat_scatter = np.array(ordinat)
        self.label = label if label else "scatter"

    def plot(self):
        """generate plot"""
        series = [
            {
                "name": self.label,
                "symbolSize": 10,
                "data": np.append(
                    self.absis_scatter.reshape(self.absis_scatter.size, 1),
                    self.ordinat_scatter.reshape(self.ordinat_scatter.size, 1),
                    axis=1,
                ).tolist(),
                "type": "scatter",
            }
        ]

        option = {
            "title": {"text": self.title},
            "tooltip": {"trigger": "axis"},
            "xAxis": {},
            "yAxis": {},
            "series": series,
        }

        return option


class PieReport:
    """pie plot for report"""

    def __init__(self, data, label, color=None, title=None) -> None:
        """Pie Plot

        Args:
            title (str): title of plot
            data (list): list of data
        """
        self.title = title
        self.data = data
        self.label = label
        self.color = color

    def plot(self, filename="plot.png"):
        """plot"""
        _, ax = plt.subplots(figsize=(6, 3), subplot_kw={"aspect": "equal"})

        wedges, _, _ = ax.pie(
            self.data,
            autopct="%1.1f%%",
            wedgeprops={"width": 0.3},
            startangle=-40,
            colors=self.color,
        )
        bbox_props = {"boxstyle": "square,pad=0.3", "fc": "w", "ec": "k", "lw": 0.72}
        kw = {
            "arrowprops": {"arrowstyle": "-"},
            "bbox": bbox_props,
            "zorder": 0,
            "va": "center",
        }

        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate(
                self.label[i],
                xy=(x, y),
                xytext=(1.35 * np.sign(x), 1.4 * y),
                horizontalalignment=horizontalalignment,
                **kw,
            )

        if self.title:
            ax.set_title(self.title)

        plt.savefig(filename)
