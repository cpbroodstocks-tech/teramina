import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.integrate import quad

from teramina.formulas.weight.weight_formula import Growth


class WeightKalman(Growth):
    """Weight Kalman"""

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
            df (pd.DataFrame): _description_
            t (int): _description_
            conditions (list): data conditions. It's contains
                    temperature, do, and nh3 condition
            required_columns (list, optional): list of requiered columns.
                    Defaults to None.
            kwargs : keyword arguments
                t0 (int): initial t
                w0 (float): initial weight
                wn (float): expected weight
        """

        t0 = kwargs.get("t0", 1)
        w0 = kwargs.get("w0", df[required_columns[3]].iloc[0])
        wn = kwargs.get("wn", 45)

        super().__init__(
            df=df,
            t=t,
            conditions=conditions,
            required_columns=required_columns,
            t0=t0,
            w0=w0,
            wn=wn,
        )

    # joint estimation using kalman filter
    def calculate_weight(self, alpha: np.ndarray, t: int, **kwargs):
        """weight function for combining with kalman filter

        Args:
            alpha (np.ndarray): array of parameters
            t (int): time t
            kwargs: keyword arguments
                t0 (int): initial t (could be t-1)
                w0 (float): initial weight
                wn (float): expected weight in time n

        Returns:
            float: estimated weight at time t
        """

        t0 = kwargs.get("t0", 1)
        w0 = kwargs.get("w0", 0.05)
        wn = kwargs.get("wn", 45)

        base_data = self.base_data
        x = np.arange(self.t0, self.t) + 1

        if len(x) == 1:
            x = np.append(x, x[0] + 1)
            base_data = np.array([base_data[0], base_data[0]])

        temp_f = CubicSpline(x, base_data[:, 0])
        do_f = CubicSpline(x, base_data[:, 1])
        nh3_f = CubicSpline(x, base_data[:, 2])

        integrate = (
            alpha[0] * quad(temp_f, t0, t, limit=100)[0]
            + alpha[1] * quad(do_f, t0, t, limit=100)[0]
            + alpha[2] * quad(nh3_f, t0, t, limit=100)[0]
            + alpha[3] * quad(lambda x: 1, t0, t, limit=100)[0]
        )

        return (np.cbrt(wn) - (np.cbrt(wn) - np.cbrt(w0)) * np.exp(-1 * integrate)) ** 3

    def generate_teta(self, alpha, r):
        """function to find teta or the estimated parameter"""
        return alpha + np.random.normal(loc=0.1, scale=np.sqrt(r), size=alpha.shape)

    def generate_estimation_values(self, alpha: np.ndarray, t: int, **kwargs):
        """estimation function

        Args:
            alpha (np.ndarray): parameters
            t (int): last time t that estimated
            kwargs: Keyword arguments
                t0 (int): initial t (could be t-1) for estimate
                w0 (float): initial weight
                wn (float): w_infinite or w_n
                w (float): variance of estimation for the base function
                r (float): variance of estimation for the parameters

        Returns:
            list: list of estimated weight and parameter values
        """
        t0 = kwargs.get("t0", 1)
        w0 = kwargs.get("w0", 0.05)
        wn = kwargs.get("wn", 45)
        w = kwargs.get("w", 0.1)
        r = kwargs.get("r", 0.01)

        wt = self.calculate_weight(alpha=alpha, t=t, t0=t0, w0=w0, wn=wn)
        w = np.random.normal(scale=np.sqrt(w))
        alpha = np.array(alpha)

        F = [wt + w, self.generate_teta(alpha, r)]

        return F

    def generate_measurement_values(self, x, alpha, v):
        """measurement function"""
        alpha = np.array(alpha)
        x = np.array(x)
        alpha = alpha + np.random.normal(scale=np.sqrt(v), size=alpha.shape)
        x = x + np.random.normal(scale=np.sqrt(v), size=x.shape)
        H = [x, alpha]
        return H

    def _calculate_differentiation(self, alpha: np.ndarray, t: int, **kwargs):
        """this function is a helper to find the deriffative of function F

        Args:
            alpha (np.ndarray): parameters
            t (int): last time t that estimated
            kwargs: Keyword arguments
                t0 (int): initial t (could be t-1) for estimate
                w0 (float): initial weight
                wn (float): w_infinite or w_n

        Returns:
            list: list of estimated weight and parameter values
        """

        t0 = kwargs.get("t0", 1)
        w0 = kwargs.get("w0", 0.05)
        wn = kwargs.get("wn", 45)

        base_data = self.base_data
        x = np.arange(self.t0, self.t) + 1
        if len(x) == 1:
            x = np.append(x, x[0] + 1)
            base_data = np.array([base_data[0], base_data[0]])

        temp_f = CubicSpline(x, base_data[:, 0])
        do_f = CubicSpline(x, base_data[:, 1])
        nh3_f = CubicSpline(x, base_data[:, 2])
        integrate = (
            alpha[0] * quad(temp_f, t0, t, limit=100)[0]
            + alpha[1] * quad(do_f, t0, t, limit=100)[0]
            + alpha[2] * quad(nh3_f, t0, t, limit=100)[0]
            + alpha[3] * quad(lambda x: 1, t0, t, limit=100)[0]
        )

        res = (
            3
            * np.exp(-1 * integrate)
            * (np.cbrt(wn) - (np.cbrt(wn) - np.cbrt(w0)) * np.exp(-1 * integrate)) ** 2
        )
        res = res * np.exp(-1 * integrate)
        return res

    def generate_matrix_a(self, alpha: np.ndarray, t: int, **kwargs):
        """transition matrix

        Args:
            alpha (np.ndarray): parameters
            t (int): last time t that estimated
            kwargs: Keyword arguments
                t0 (int): initial t (could be t-1) for estimate
                w0 (float): initial weight
                wn (float): w_infinite or w_n

        Returns:
            list: list of transition function and parameter
        """
        t0 = kwargs.get("t0", 1)
        w0 = kwargs.get("w0", 0.05)
        wn = kwargs.get("wn", 45)
        l = self._calculate_differentiation(alpha=alpha, t=t, t0=t0, w0=w0, wn=wn)
        a = [1 / (3 * w0 ** (2 / 3)) * l, np.eye(4)]
        return a

    def generate_matrix_b(self):
        """transition matrix control"""
        b = [1, np.eye(4)]
        return b

    def generate_matrix_c(self):
        """transition matrix of measurement"""
        c = [1, np.eye(4)]
        return c

    def generate_matrix_d(self):
        """transition matrix control of measurement"""
        d = [1, np.eye(4)]
        return d

    def _kf_update_step(self, x_pred, p_pred, measurement, v):
        # initialize the matrix transition of measurement
        c = self.generate_matrix_c()
        # initialize the matrix control of measurement
        d = self.generate_matrix_d()
        # initialize the error covariance matrix
        cov_v = [v, np.eye(4) * v]

        # define the kalman gain
        k_x = (
            p_pred[0]
            * c[0]
            * (c[0] * p_pred[0] * c[0] + d[0] * cov_v[0] * d[0]) ** (-1)
        )
        k_alpha = (p_pred[1] @ c[1].T) * np.linalg.inv(
            (c[1] @ p_pred[1] @ c[1].T) + (d[1] @ cov_v[1] @ d[1].T)
        )

        # Update step
        h_pred = self.generate_measurement_values(x_pred[0], x_pred[1], v)
        x_update = x_pred[0] + k_x * (measurement[0] - h_pred[0])
        alpha = x_pred[1] + k_alpha @ (measurement[1] - h_pred[1])

        p = [
            (1 - k_x * c[0]) * p_pred[0],
            (np.eye(4) - k_alpha @ c[1]) @ p_pred[1],
        ]

        return x_update, alpha, p

    def _kf_predict_step(self, alpha, w0, t, **kwargs):
        t0 = kwargs.get("t0")
        w = kwargs.get("w")
        r = kwargs.get("r")
        p = kwargs.get("p")

        # initialize error covariance w
        cov_w = [w, np.eye(4) * w]

        # generate the control matrix
        b = self.generate_matrix_b()

        # calculate the estimation
        x_pred = self.generate_estimation_values(
            alpha=alpha,
            t=t,
            t0=t0,
            w0=w0,
            wn=self.wn,
            w=w,
            r=r,
        )

        # generate the transition matrix
        a = self.generate_matrix_a(
            alpha=alpha,
            t=t,
            t0=t0,
            w0=w0,
            wn=self.wn,
        )

        p_pred_x = (a[0] * p[0] * a[0]) + (b[0] * cov_w[0] * b[0])
        p_pred_alpha = (a[1] @ p[1] @ a[1].T) + (b[1] @ cov_w[1] * b[1].T)

        return x_pred, [p_pred_x, p_pred_alpha]

    def joint_estimation_wt(self, measurement: np.ndarray, alpha: np.ndarray, **kwargs):
        """joint estimation functions

        Args:
            measurement (np.ndarray): array of measurement values
            alpha (np.ndarray): array of initial parameters
            kwargs: keyword arguments
                t0 (int): initial t
                t (int): time t
                v (float): variance of noise in measurement function
                w (float): variance of noise in estimation function
                r (float): variance of noise in parameter estimation
                p_init (list): initial error of covariance

        Returns:
            tuple: tuple of array estimation and parameter values
        """

        v = kwargs.get("v")
        w = kwargs.get("w")
        r = kwargs.get("r")
        p = kwargs.get("p_init")

        x_est = np.zeros(measurement.shape)
        alpha_estimates = []

        # get the measurement
        z = self.generate_measurement_values(measurement, alpha, v)

        for val in enumerate(range(kwargs.get("t0"), kwargs.get("t"))):
            # prediction step
            if val[0] == 0:
                x_pred, p_pred = self._kf_predict_step(
                    alpha=alpha,
                    w0=measurement[0],
                    t=val[1] + 1,
                    t0=val[1] + 1,
                    w=w,
                    r=r,
                    p=p,
                )
            else:
                x_pred, p_pred = self._kf_predict_step(
                    alpha=alpha,
                    w0=x_est[val[0] - 1],
                    t=val[1] + 2,
                    t0=val[1] + 1,
                    w=w,
                    r=r,
                    p=p,
                )

            # update step
            x_update, alpha, p = self._kf_update_step(
                x_pred=x_pred, p_pred=p_pred, measurement=[z[0][val[0]], z[1]], v=v
            )

            x_est[val[0]] = x_update
            alpha_estimates.append(alpha)

        return x_est, alpha_estimates
