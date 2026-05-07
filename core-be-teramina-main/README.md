# Teramina

A digital shrimp farming platform.

## Install

```
pip install -r requirements.txt
```

## Usage

without https:

```
python manage.py runserver
```

with https: (in local)

```
python3 manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```

see this [link](https://timonweb.com/django/https-django-development-server-ssl-certificate/) to know more.

## API Documentation

- https://teramina-3gfipztgma-as.a.run.app/api/docs

## Sample Data Generator

- https://colab.research.google.com/drive/1Nx2IJpVWJnA0E7PujxhL-COY1d8Wvdub?usp=sharing

## Metadata

| Variable         | Description                                                                                                             |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------- |
| date             | The date on which the data was recorded.                                                                                |
| doc              | The number of days since the shrimp were stocked in the pond.                                                           |
| temperature      | The water temperature in degrees Celsius.                                                                               |
| do               | The concentration of oxygen dissolved in the water, usually measured in mg/L.                                           |
| nh3              | The concentration of ammonia in the water, typically measured in mg/L. High levels of ammonia can be harmful to shrimp. |
| abw              | The average weight of the shrimp in the pond, often measured in grams.                                                  |
| fr               | The ratio of the feed consumed by the shrimp to the weight gained by the shrimp.                                        |
| sr               | The percentage of shrimp that have survived up to the recorded date.                                                    |
| w0               | The initial number of shrimp stocked in the pond.                                                                       |
| initial_stocking | The number of shrimp initially stocked in the pond.                                                                     |
| labor_cost       | The cost associated with labor, including wages and salaries, for managing the shrimp farm.                             |
| bonus_cost       | Additional monetary incentives or bonuses provided to farm workers.                                                     |
| energy_cost      | The cost of energy usage on the shrimp farm, including electricity and fuel costs.                                      |
| probiotic_cost   | The cost of probiotics or beneficial microorganisms used to enhance shrimp health and growth.                           |
| other_cost       | Miscellaneous costs related to shrimp farming that don't fall into the categories listed above.                         |
| harvest_cost     | The cost associated with harvesting and processing the shrimp for sale.                                                 |
| feeding_cost     | The cost of shrimp feed used during the farming period.                                                                 |

## Data Flow

![Alt text](image.png)

## Deployment

![Alt text](image-1.png)

## Formula Documentation

### Weight

$w_t = (w_n^{\frac{1}{3}} - (w_n^{\frac{1}{3}} - w_{t_0}^{\frac{1}{3}})e^{-\int_{t_0}^{t} \sum f_i(r) dr })^3$

where:

- $f_i$ : the extrapolation function for the dependent variable such as temperature, do, etc
- $w_n$ : weight at time n
- $w_{t_0}$ : weight at the initial time
- $w_{t}$ : weight at time t

### Population

$N(t) = N({t_0}) e^{-\int M(t) dt} - \gamma \sum_t (n(t)-k) - \sum_i p(i) $

where

- $M(t)$: mortality rate at time t
- $N_{t_0}$: population at time $t_0$
- n(t): nh3 value at t
- k: $NH_{3_{limit}}$ value
- $\gamma$ : mortality rate due to $NH_3$ value
- $-\int M(t) dt$ : integral of M(t) from t0 to t
- p(i): partial harvest i-th

### Kalman Filter

Two main steps of kalman filter (discrete):

1. Predict the present state value based on all past available data. For example, a linear Kalman filter computes

   $\hat{x}_k^- = \hat{A} x_{k-1}^{+} + Bu_{k-1}$

2. Estimate the present state value, by updating the prediction based on all presently available data.

   $\hat{x}_k^+ = \hat{x}_k^- + L(z_k - (\hat{x}_k^- + Du_k))$

where:

- $\hat{x}_k^-$ is the prediction of $x_k$
- $\hat{x}_k^+$ is the estimated value of $x_k$

Fundamental form for deterministic, time-invariant, continuous-time
linear state-space model:

$\dot{x}(t) = Ax(t) + Bu(t)$

$z(t) = Cx(t) + Du(t)$

where u(t) is input, x(t) is the state, A, B, C, D are constant matrices.

### Nonlinear Kalman Filter

Nonlinear state-space model:

$x_k = f(x_{k-1},u_{k-1}, w_{k-1})$

$z_k = h(x_k, u_k, v_k)$

Definition:

$\hat{A}_k = \frac{df_k(x_k, u_k, w_k)}{dx_k} |_{x_k = \hat{x}_k^+}$

$\hat{B}_k = \frac{df_k(x_k, u_k, w_k)}{dx_k} |_{w_k = \hat{w}_k^+}$

$\hat{C}_k = \frac{dh_k(x_k, u_k, v_k)}{dx_k} |_{x_k = \bar{x}_k^-}$

$\hat{D}_k = \frac{dh_k(x_k, u_k, v_k)}{dx_k} |_{v_k = \bar{x}_k^+}$

Initialization:

$\hat{x}_0^+ = E[x_0]$

$\sum^+_{\tilde{x}, 0} = E[(x_0 - \hat{x}_0^+)(x_0 - \hat{x}_0^+)^T]$

Computation, for each k:

1. state estimate time update

   $\hat{x}^-_k = f_{k-1}(\hat{x}^+_{k-1},u_{k-1}, \bar{w}_{k-1})$

2. Error covariance time update

   $\sum^-_{\tilde{x}, k} = \hat{A}_{k-1} \sum^+_{\tilde{x}, k-1} \hat{A}_{k-1}^T + \hat{B}_{k-1} \sum_{\tilde{w}} \hat{B}_{k-1}^T$

3. Output estimate

   $\hat{z}_k = h_k (\hat{x}_k^-, u_k, \bar{v}_k)$

4. Estimator gain matrix

   $L_k = \sum^-_{\tilde{x}, k} \hat{C}_k^T [\hat{C}_k \sum^-_{\tilde{x}, k} \hat{C}_k^T + \hat{D}_k \sum_{\tilde{v}} \hat{D}_k]^{-1}$

5. State estimate measurement update

   $\hat{x}_k^+ = \hat{x}_k^- + L_k(z_k - \hat{z}_k)$

6. Error covariance measurement update

   $\sum_{\tilde{x}, k}^+ = (I - L_k \hat{C}_k)\sum_{\tilde{x}, k}^-$

### Joint Estimation (Kalman filter for parameter estimation)

state space model:

$ \begin{matrix} x*k = f*{k-1} (x*{k-1}, u*{k-1}, w*{k-1}, \theta*{k-1})\\ z_k = h_k(x_k, u_k, v_k, \theta_k)\end{matrix}$

and

$\begin{matrix} \theta_{k} = \theta_{k-1} + r_{k-1} \\ d_k = h_k(f_{k-1}(x_{k-1}, u_k, \bar{v}_k, \theta_{k-1})) \end{matrix}$


### SGR (specific growth rate)

$s(t) = w(t) - w(t-1), \forall t>=1 $

where:

- s: spesific growth rate
- w: abw
- t: time t or doc t
