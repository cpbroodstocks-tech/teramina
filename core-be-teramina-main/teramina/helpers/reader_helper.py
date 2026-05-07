# pylint: disable=too-few-public-methods

import io
import pandas as pd
import numpy as np


class Reader:
    """Reader class"""

    def csv(self, file):
        """reader for csv

        Args:
            file (input): stringIo

        Returns:
            pd.DataFrame: dataframe of readed file
        """
        try:
            df = pd.read_csv(io.StringIO(file.read().decode("utf-8")), delimiter=",")
            columns = df.columns

            if not self.__column_validation(columns):
                raise ValueError("One or more primary columns not found")

            if not self.__shape_validation(df):
                raise ValueError("Data is empty")

            df.columns = df.columns.str.lower()

            df = df.where(pd.notnull(df), None)
            df = df.replace({np.nan: None})
            return df
        except pd.errors.ParserError as e:
            raise ValueError("Cannot read the data") from e

    def __column_validation(self, columns):
        """column validation for the uploaded data"""
        base_columns = ["temperature", "do", "nh3", "abw", "fr"]

        columns = [i.casefold() for i in columns]
        columns = [i for i in columns if i in base_columns]

        if len(columns) != len(base_columns):
            return False

        return True

    def __shape_validation(self, df: pd.DataFrame):
        """shape validation for the uploaded data"""
        shape, _ = df.shape
        if shape == 0:
            return False

        return True
