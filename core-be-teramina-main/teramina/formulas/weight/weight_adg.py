# pylint: disable=too-many-arguments, E0401, R0801
"""Growth function that refer to the average daily growth"""

import numpy as np
import pandas as pd

from teramina.formulas.weight.abw_data_preprocessing import abw_data_prep

####
# the order of data base
# 0: adjusted temperature
# 1: DO
# 2: NH3
# 3: init ABW
# 4: origin temperature
# 5: adjusted ABW
# 6: fr
# 7: doc
####


class Growth:
    """Individual growth service"""

    def __init__(
        self,
        df: pd.DataFrame,
        t: int,
        conditions: list,
        required_columns=None,
        **kwargs,
    ) -> None:
        """Growth service

        Args:
            df (pd.DataFrame): dataframe of farming data
            t (int): max doc
            conditions (list): data conditions. It's contains
                    temperature, do, and nh3 condition
            required_columns (list, optional): list of requiered columns.
                    Defaults to None.
            kwargs : keyword arguments
                t0 (int): initial t
                w0 (float): initial weight
                wn (float): expected weight
        """
        if required_columns is None:
            required_columns = ["Temp", "DO", "NH3", "ABW"]

        self.t0 = kwargs.get("t0", 1)
        self.w0 = kwargs.get("w0", df[required_columns[3]].iloc[0])
        self.wn = kwargs.get("wn", 45)
        self.t = t

        # set conditions instances with conditions contains
        # temp_condition, do_condition, nh3_condition
        self.conditions = conditions
        self.base_data = abw_data_prep(self.t0, t, required_columns, df, conditions)

    def wt(self) -> np.ndarray:
        """basic weight function based on adg

        adg = w(t) - w(t-1)
        w(t+i) = w(t) + i * adg

        in this case we set the i=1
        """
        wt = []

        # check, wether simulation or not
        if self.t == len(self.base_data[:, 3]):
            return self.base_data[:, 3]

        doc = list(range(self.t0, self.t))
        for i, _ in enumerate(doc):
            if i == 0:
                wt.append(self.w0)
            elif i == 1:
                # wt.append(2 * wt[-1])
                wt.append(wt[-1] + 0.15)
            else:
                wt.append(2 * wt[-1] - wt[-2])
        return np.array(wt)

    def single_wt(self, i: int, wt: float, adg: float) -> list:
        """basic weight function based on adg

            adg = w(t) - w(t-1)
            w(t+i) = w(t) + i * adg

            in this case we set the i=1
        Args:
            i (int): interval
            wt (float): before wt
            adg (float): average daily growth
        """
        estimated_wt = wt + i * adg
        return estimated_wt
