# Teramina Platform — Algorithm & Functionality Deep Dive

> Generated: 2026-04-19
> Covers both `fe-teramina-main/` (React) and `core-be-teramina-main/` (Django Ninja + MongoDB)

---

## Table of Contents

1. [Authentication & Session](#1-authentication--session)
2. [Farm → Pond → Cycle Hierarchy](#2-farm--pond--cycle-hierarchy)
3. [Cycle Data (Population Logging)](#3-cycle-data-population-logging)
4. [Weight Growth Model](#4-weight-growth-model)
5. [Population Model](#5-population-model)
6. [Biomass Calculation](#6-biomass-calculation)
7. [SGR (Specific Growth Rate)](#7-sgr-specific-growth-rate)
8. [Feed Ration (FR) Formulas](#8-feed-ration-fr-formulas)
9. [Cost Model](#9-cost-model)
10. [Revenue Model](#10-revenue-model)
11. [Overview Dashboard](#11-overview-dashboard)
12. [Economics Widget](#12-economics-widget)
13. [Feeding Widget + Feeding Recommendation Service](#13-feeding-widget--feeding-recommendation-service)
14. [Forecast Widget](#14-forecast-widget)
15. [Harvest Widget](#15-harvest-widget)
16. [Harvest Optimization (Kalman + Scenario Engine)](#16-harvest-optimization-kalman--scenario-engine)
17. [Harvest Simulator Widget](#17-harvest-simulator-widget)
18. [Water Quality Dashboard](#18-water-quality-dashboard)
19. [Cycle Detail — AI Insights](#19-cycle-detail--ai-insights)
20. [Cycle Detail — Feeding Recommendation Tab](#20-cycle-detail--feeding-recommendation-tab)
21. [Cycle Detail — Benchmark](#21-cycle-detail--benchmark)
22. [Cycle Detail — Google Sheets Sync](#22-cycle-detail--google-sheets-sync)
23. [Cost Data Upload](#23-cost-data-upload)
24. [Agent (Conversational AI)](#24-agent-conversational-ai)
25. [Constants Reference](#25-constants-reference)

---

## 1. Authentication & Session

### Flow

```
User → Landing Page (/)
     → /signin or /signup
     → Firebase Auth (email/password or OAuth)
     → On success: POST /user/firebase-verify-user?token={idToken}
     → Backend verifies Firebase token, returns JWT + refresh token
     → Store in localStorage["authentication"]
     → Fetch user profile: GET /user/get-profile → Zustand useUserStore
     → Register FCM push token: POST /user/fcm-token?token={fcmToken}
     → Redirect to /dashboard
```

### Private Route Guard

```
PrivateRoute reads localStorage["authentication"]
  → if truthy: render children
  → else: <Navigate to="/signin" />
```

### Session Persistence

- Auth token stored in `localStorage["authentication"]`
- All API requests attach `Authorization: Bearer {token}` via Axios interceptor
- FCM token stored in `sessionStorage` to prevent duplicate registration per session

---

## 2. Farm → Pond → Cycle Hierarchy

### Data Models

**Farm**
```
Farm {
  id, name, location
  user_id (indexed)
  created_at, last_updated
}
```

**Pond**
```
Pond {
  id, name
  size: float (m²)
  depth: float (default 1.5 m)
  pond_construction: string
  pond_shape: string
  farm_id (indexed)
  is_active: bool
  active_cycle_id: string
  created_at, last_updated
}
```

**Cycle**
```
Cycle {
  id, name
  start_date: datetime
  pond_id (indexed)
  is_active: bool
  vector_list: list   ← Pinecone vector IDs for semantic retrieval
  last_updated
}
```

### CRUD APIs

| Entity | Endpoints |
|--------|-----------|
| Farm   | GET `/farm/list-farm`, POST `/farm/add-farm`, PUT `/farm/edit-farm`, DELETE `/farm/delete-farm` |
| Pond   | GET `/pond/list-pond?farm_id=`, POST `/pond/add-pond`, PUT, DELETE |
| Cycle  | GET `/cycle/list-cycles?pond_id=`, POST `/cycle/add-cycle`, PUT, DELETE |

### Navigation Drill-Down

```
/dashboard/farm
  → click farm → /dashboard/pond/:farm_id
    → click pond → /dashboard/cycle/:pond_id
      → click cycle → /dashboard/cycle/detail/:cycle_id
```

---

## 3. Cycle Data (Population Logging)

### Data Model

```
CycleData {
  cycle_id (indexed)
  result_data: [
    {
      doc: int              ← Day of Culture
      date: string
      temp_morning, temp_afternoon, temp_avg: float (°C)
      do_morning, do_afternoon, do_avg: float (mg/L)
      ph_morning, ph_afternoon: float
      salinity: float (ppt)
      nh3: float (mg/L)
      turbidity: float (NTU)
      abw: float (g)        ← Average Body Weight (from sampling)
      biomass: float (g)    ← Computed
      population: int       ← Computed
      survival_rate: float  ← Computed
      feed_given_kg: float  ← Sum of ration 1-4
      feed_ration: float    ← feed_given / biomass * 100
      ...
    }
  ]
  last_updated
}

ForecastData {
  cycle_id (indexed)
  result_data: [same shape, future DOC rows]
}

CycleModelParams {
  cycle_id (unique)
  alpha1, alpha2, alpha3, alpha4: float  ← calibrated growth params
  r_squared: float
  fitted_at_doc: int
  sample_count: int
  model_version: string ("adaptive_v1")
}
```

### Populate List UI (Cycle Detail → Data tab)

```
GET /cycle-data/list-cycle-data?cycle_id=
  → returns { columns: [...], data: [...] }
  → rendered as dynamic table
  → toolbar: Add Row button, Download Data button
```

---

## 4. Weight Growth Model

### Primary Formula (Bioenergetic Integration)

```
w(t) = [ wn³ - (wn³ - w0³) · exp( -Σ(αᵢ · ∫cond_i) ) ]^(1/3)

Where:
  w0  = initial weight (g)
  wn  = expected final weight (g)
  t0  = initial DOC

  α1  = 0.06383328  → temperature multiplier
  α2  = 0.00581553  → dissolved oxygen multiplier
  α3  = 0.00164433  → ammonia (NH3) multiplier
  α4  = 0.00019466  → time multiplier

  ∫Temp = cumulative trapezoidal integral of adjusted temperature
  ∫DO   = cumulative trapezoidal integral of adjusted DO
  ∫NH3  = cumulative trapezoidal integral of adjusted NH3
  ∫t    = cumulative time (DOC)
```

### Condition Adjustment Functions

**Temperature** — CubicSpline interpolation from `BASE_TEMPERATURE_DATA` lookup table (maps raw °C to adjusted score)

**DO** — Normal trapezoidal membership function:
```
normal_trapezoidal(do, suitable_min=3.0, suitable_max=10.0, optimal_min=5.0, optimal_max=7.0)

  do ≤ suitable_min:               0.0
  suitable_min < do < optimal_min: linear ramp 0 → 1
  optimal_min ≤ do ≤ optimal_max:  1.0
  optimal_max < do < suitable_max: linear ramp 1 → 0
  do ≥ suitable_max:               0.0
```

**NH3** — Left trapezoidal (lower is better):
```
left_trapezoidal(nh3, suitable_min=0.0, suitable_max=1.0, optimal_max=0.5)

  nh3 ≤ suitable_min:              1.0
  suitable_min < nh3 < optimal_max: 1.0
  optimal_max ≤ nh3 < suitable_max: linear ramp 1 → 0
  nh3 ≥ suitable_max:              0.0
```

### ABW Imputation

```
if ABW sample exists at DOC t:
  use as anchor point
else:
  linear interpolation between nearest samples
  if no future sample: use fitted growth curve
```

### Adaptive Alpha Calibration (CycleModelParams)

```
When ≥ 3 ABW samples collected:
  Fit alpha1..alpha4 via least-squares minimization
  Minimize: Σ(w_model(t) - w_observed(t))²
  Compute R² = 1 - SS_res / SS_tot
  Store in CycleModelParams
  Use calibrated alphas for all future projections
```

### Kalman Filter on Weight (WeightKalman)

Used for smoothing noisy weight observations:

```
State vector: x = [weight, α1, α2, α3, α4]

Prediction:
  x̂⁻ₜ = F(x̂ₜ₋₁)     ← apply growth formula with process noise w
  P⁻ₜ  = A·Pₜ₋₁·Aᵀ + Q

Update:
  K = P⁻ₜ·Hᵀ · (H·P⁻ₜ·Hᵀ + R)⁻¹   ← Kalman gain
  x̂ₜ = x̂⁻ₜ + K·(zₜ - H·x̂⁻ₜ)       ← measurement zₜ = observed ABW
  Pₜ  = (I - K·H)·P⁻ₜ

Noise params:
  v (measurement): 0.000001
  w (estimation):  0.0001
  r (parameter):   0.000001
  p_init:          0.01
```

### ADG-based Weight (fallback — WeightAdg)

```
Early DOC (< first sample):
  w(1) = w0
  w(2) = w(1) + 0.15
  w(i) = 2·w(i-1) - w(i-2)   ← linear extrapolation

After samples:
  adg = w(t) - w(t-1)           ← average daily gain
  w(t+i) = w(t) + i · adg
```

---

## 5. Population Model

### Formula

```
Survival Rate: SR(t) = CubicSpline(sampling_docs, sampling_sr_values)(t)

Total Population at t:
  P_total(t) = initial_stocking · SR(t)

After partial harvests:
  P(t) = P_total(t) - Σ(partial_harvest_amounts where doc ≤ t)

Mortality rate constant:
  λ = -ln(SR) / t
```

### Kalman Smoothing on Population

Same structure as weight Kalman — filters noisy survival rate observations.

```
Noise params:
  v: 0.000001
  w: 0.0001
  r: 0.000001
  p_init: 0.01
```

### Config Fields

```
population_config = {
  initial_stocking: int,
  partial_doc: [int, ...],   ← DOCs of partial harvests
  ph: [int, ...],            ← partial harvest amounts (shrimp count)
  doc_final: int
}
```

---

## 6. Biomass Calculation

```
biomass(t)         = population(t) · weight(t)              [grams]
harvest_biomass(t) = harvest_population(t) · weight(t)      [grams]
total_biomass(t)   = biomass(t) + cumsum(harvest_biomass)   [grams]

biomass_kg(t)      = biomass(t) / 1000
total_biomass_kg(t)= total_biomass(t) / 1000

carrying_capacity  = biomass_kg / (pond_area_m² · pond_depth_m)  [kg/m³]
```

---

## 7. SGR (Specific Growth Rate)

```
For each consecutive pair of ABW samples (t₀, t₁):
  sgr = (ABW(t₁) - ABW(t₀)) / (t₁ - t₀)   [g/day = ADG]

Returns None if ABW values are identical.
```

---

## 8. Feed Ration (FR) Formulas

Five complementary models, applied in layers or combined:

### 8a. FR by DPI (Digestible Protein Intake)

```
if 30% ≤ protein < 39%:
  dpi = 44.7 · ABW^(-0.714)
elif 39% ≤ protein ≤ 40%:
  dpi = 53.64 · ABW^(-0.714)

fr = (dpi / 1000) / (protein_content / 100)   [fraction of biomass/day]
```

### 8b. FR by Blind Feed (Early Stage, DOC ≤ 30)

```
current_feed = population / 100,000

DOC 0-10:   feed_per_day = current_feed · (1 + 0.2 · DOC)
DOC 10-20:  feed_per_day = current_feed · (1 + 2.0 + 0.4 · (DOC - 10))
DOC 20-30:  feed_per_day = current_feed · (1 + 6.0 + 0.6 · (DOC - 20))

fr = feed_per_day / biomass
```

### 8c. FR by Temperature

```
Lookup table: ABW → FR rate, indexed by temperature band:
  15-19°C, 19-21°C, 21-24°C, 24-28°C, 28-32°C, 32-33°C, 33-34°C

fr = CubicSpline(abw_values, fr_table[temp_band])(current_abw) / 100
```

### 8d. FR by DO Adjustment

```
adj_do = normal_trapezoidal(do_value, suitable_min, suitable_max, optimal_min, optimal_max)
fr_adjusted = adj_do · base_fr
```

### 8e. FR by NH3 Adjustment

```
adj_nh3 = left_trapezoidal(nh3_value, suitable_min, suitable_max, optimal_max)
fr_adjusted = adj_nh3 · base_fr
```

### 8f. FR by Tray (Leftover Feedback)

```
Per tray:
  excess_percent = (leftover / given) · 100

  excess == 0:      point = 3
  0 < excess ≤ 10:  point = -excess/5 + 3
  excess > 10:      point = -excess/90 + 10/9

Aggregate feed score:
  total_points = Σ(points_per_tray)

  ≥ 15:    adjusted_point = +10
  11-15:   adjusted_point = +5
  6-11:    adjusted_point =   0
  4-6:     adjusted_point = -5
  < 4:     adjusted_point = -10

Final FR: fr · (1 + adjusted_point / 100)
```

### 8g. Daily Ration Distribution (4 feedings)

```
Weights:  [0.30, 0.20, 0.10, 0.40]   (morning, mid-morning, afternoon, evening)

ration_per_feeding[i] = daily_feed_kg · weights[i]
```

---

## 9. Cost Model

### Daily Cost Components

```
harvest_cost   = harvest_biomass_kg · unit_harvest_cost
energy_cost    = mean(energy_cost_rates) · 820W · 24h
probiotics_cost= mean(probiotics_cost_rates)
feed_cost      = biomass_kg · fr · mean(feed_price)
labor_cost     = cost_items["labor_cost"]
bonus_cost     = cost_items["bonus"]
other_cost     = cost_items["other"]
seed_cost      = cost_items.get("seed_cost", 0)

daily_total = Σ(all components)
              → 0 after doc_final
```

### Cumulative Cost & Unit Economics

```
total_cost_cumsum(t) = cumsum(daily_total)[t]
cost_per_kg(t)       = total_cost_cumsum(t) / total_biomass_kg(t)
```

### Cost Data Upload (Excel → MongoDB)

```
POST /cost/add-single-cost-data (multipart)
  fields: farm_id, start_date, end_date, file (.xlsx)

Backend:
  1. Read Excel sheet "data"
  2. Upsert CostData { farm_id, start_date, end_date, data[] }
  3. data[] = [{ category, date, total, hp, ... }]
```

---

## 10. Revenue Model

### Price Curve

```
price_array = [[size₁, price₁], [size₂, price₂], ...]  ← IDR/kg by shrimp count/kg
f_price = CubicSpline(size_values, price_values)

size(t) = 1000 / weight(t)   ← shrimp per kg
```

### Realized Revenue (harvest events)

```
price = f_price(size) if 0 < size < 200, else 0
revenue = harvest_biomass_kg · price              [IDR]
```

### Potential Revenue (running estimate)

```
price = f_price(1000 / weight(t))
potential_revenue(t) = heaviside(price, 1) · biomass_kg(t) · price
```

### Profit

```
profit(t) = cumsum(revenue)(t) - total_cost_cumsum(t)
```

---

## 11. Overview Dashboard

**Route:** `/dashboard` (default child)
**API:** `GET /dashboard/overview` (filtered by farm/pond/cycle/date)

### Sections

| Section | Content |
|---------|---------|
| Pond Info | Pond metadata |
| Performance Metrics | ABW, SGR, Biomass — each with current value, change ratio, direction arrow |
| Performance Plots | ABW (scatter), SGR (line), Biomass (line) |
| Economics Cards | Total Cost, Total Revenue, Total Profit, Cost per Kilo |
| Report | Async PDF generation |

### PDF Report Generation

```
1. POST /dashboard/create-report → { task_id }
2. Poll GET /dashboard/get-report/{task_id} every 10s
3. On status == "done": download PDF blob
4. On status == "error": show error toast
5. Max wait: until success or error (no hard timeout)
```

### Filter System

```
useFilter("/dashboard/overview") hook:
  reads from localStorage: { farm_id, pond_id, cycle_id, date }
  sends as query params to API
  returns { data, isLoading, isError }
```

---

## 12. Economics Widget

**Route:** `/dashboard/economics`
**API:** `GET /dashboard/economics`

### Sections

| Section | Content |
|---------|---------|
| Profit & Loss | DOC, Total Cost, Total Revenue, Total Profit, Cost/kg — with icons |
| Cost Breakdown | DataGrid table (Item × Cost) + Pie chart by category |
| Production Status | 4 metric cards + line chart over time |

### Layout Adaptation

```
if production_status.data.length > 3:
  grid cols = 4
else:
  grid cols = production_status.data.length
```

---

## 13. Feeding Widget + Feeding Recommendation Service

**Route:** `/dashboard/feeding`
**API:** `GET /dashboard/feeding`

### Widget Sections

| Section | Content |
|---------|---------|
| Feed Status | 5 summary cards |
| Feed Adjustment | Original rate card, Adjusted rate card, Protein %, CHB:CP ratio, line chart over time |
| Daily Adjustment | Feed ration card, additional adjustment cards |
| Realization Table | Per ration: Feed Given, Realized amount, Leftover % — with Add button |

### FeedRealization Data Model

```
FeedRealization {
  cycle_id, doc
  ration_number: int (1-4)
  feed_ration: float       ← feed_given / biomass * 100
  feed_given: float (kg)
  feed_leftover: float (kg)
}
```

### Adding Feed Realization Record

```
POST /feeding/add-feeding-record
  1. Validate ration_number (1-4)
  2. DOC = (date - cycle.start_date).days + 1
  3. biomass_kg = current biomass from ResultData
  4. feed_ration = feed_given / biomass_kg * 100
  5. Save FeedRealization
  6. Update CycleData.result_data[doc].feed_given_kg
  7. Regenerate CombinedDataGenerator (historical + forecast pipeline)
```

### Feeding Recommendation Service (3-Layer)

```
Layer 1 — Blind Feed (DOC ≤ 30):
  Uses FrByBlindFeed formula (see §8b)
  model_layer = "blind_feed"

Layer 2 — Rule-based (DOC > 30):
  base_rate by ABW band:
    ABW < 5g:   10% of biomass/day
    5g - 15g:   6%  of biomass/day
    > 15g:      3%  of biomass/day

  Adjustments:
    leftover_ratio = Σ(leftover_last_3d) / Σ(given_last_3d)
    if leftover > 15%: fr *= 0.90   (reduce — oversupply)
    if leftover < 2%:  fr *= 1.05   (increase — underfeed)

    if DO_avg < DO_OPTIMAL_MIN:
      stress_factor = max(0.7, DO_avg / DO_OPTIMAL_MIN)
      fr *= stress_factor

  model_layer = "rule_v1"

Layer 3 — ML-based (DOC ≥ 60, confidence > 0.6):
  Integrates ML model predictions
  model_layer = "ml_v1"

Final output:
  recommended_ration_kg = fr · biomass_kg
  ration_per_feeding = recommended_ration_kg · [0.30, 0.20, 0.10, 0.40]
  confidence: float (0-1)
  adjustment_reason: string
```

---

## 14. Forecast Widget

**Route:** `/dashboard/forecast`
**APIs:**
- `GET /dashboard/forecast` — main forecast data
- `GET /dashboard/confidence-bands?cycle_id=` — bootstrap confidence bands
- `GET /dashboard/prophet-forecast?cycle_id=` — Prophet model (optional, fails gracefully)

### Sections

| Section | Content |
|---------|---------|
| Feeding Forecast | 4 cards: DOC, forecasted metrics |
| Production Forecast | 4 metric cards + Forecast Biomass chart + Forecast ABW chart |
| ABW Confidence Bands | Line chart with Lower 80% / Upper 80% bounds |
| Prophet Forecast | Line chart (Forecast + CI) + R² chip (loaded async) |
| Economic Forecast | 4 cards + Revenue chart + Profit chart |

### Confidence Bands Algorithm (Bootstrap)

```
For n=1000 bootstrap resamples:
  1. Resample alpha parameters from fitted distribution
  2. Project weight curve w(t) using sampled alphas
  3. Compute biomass trajectory

Lower 80% band = 10th percentile across resamples
Upper 80% band = 90th percentile across resamples
```

### Prophet Forecast

```
Input: historical ABW time series
Model: Facebook Prophet
  trend: linear
  seasonality: disabled (daily farming data)
Output: forecast + yhat_lower / yhat_upper (80% CI)
R² displayed as model quality indicator
Failure: gracefully hidden if insufficient data points
```

---

## 15. Harvest Widget

**Route:** `/dashboard/harvest`
**APIs:**
- `GET /harvest/harvest-record-data` — existing records
- `GET /harvest/harvest-recommendation` — recommended harvest plan
- `POST /harvest/add-harvest-record?cycle_id=` — add/edit record
- `POST /harvest/create-harvest-simulation?cycle_id=` — simulate plan

### Sub-components

**HarvestRecommendationTable**
```
Displays recommended partial1, partial2, partial3, final harvest schedule
Columns: dynamic from data.fields
Source: Optimization engine output (§16)
```

**HarvestRecord**
```
Max 4 records: partial1, partial2, partial3, final
Add button disabled if: 4 records exist OR final harvest recorded
Edit button: per record row

ModalAddHarvestRecord fields:
  type: Radio (Partial / Final)
  doc: int
  biomass_kg: float
  revenue: float (IDR)

Validation:
  DOC ≤ current_doc
  biomass ≤ remaining biomass
  doc values must be ascending
  no duplicate DOC entries
```

**HarvestSimulation**
```
Max 2 simulation plans allowed
ModalAddHarvestSimulationPlan fields:
  partial1_doc, partial2_doc, partial3_doc, final_doc (int)
  partial1_biomass, ... (float)

Already-recorded harvests: fields disabled (pre-filled from records)

TableHarvestSimulation:
  DOC, ABW, Biomass, Revenue, Cost, Profit, Margin %
```

---

## 16. Harvest Optimization (Kalman + Scenario Engine)

**Class:** `Optimization`
**Location:** `formulas/harvest_optimization_formula.py`

### Scenario Generation

```
docfinal = population_config["doc_final"]
total_observation = max_doc - docfinal
remaining_harvests = MAX_PARTIAL_HARVEST - len(existing_partial_harvests)

if total_observation > 60:
  t_harvest = combinations(range(60), remaining_harvests)
  prepend zeros for (total_observation - 60) gap days
else:
  t_harvest = combinations(range(total_observation), remaining_harvests)
```

### Matrix Projection (vectorized over all scenarios)

```
matrix_wt         = tile(projected_weight_vector, n_scenarios)
matrix_population = [historical_population | forecast_population - cumsum(partial_harvests)]
matrix_biomass    = (matrix_wt · matrix_population) / 1000              [kg]
matrix_ph         = partial_harvest_amounts_matrix
matrix_harvested  = (matrix_ph · matrix_wt) / 1000                     [kg]
```

### Revenue Matrix

```
matrix_size    = 1000 / matrix_wt
matrix_price   = f_price(matrix_size)                     ← CubicSpline
matrix_revenue = matrix_harvested · matrix_price          [IDR]
```

### Cost Matrix

```
matrix_energy      = mean(energy_cost) · 820W · 24h · scenario_length
matrix_probiotics  = mean(probiotics_cost) · scenario_length
matrix_labor       = mean(labor_cost) · scenario_length
matrix_bonus       = matrix_harvested · mean(bonus)
matrix_harvest_cost= matrix_harvested · mean(harvest_cost)
matrix_feed        = matrix_fr · matrix_biomass · mean(feed_price)
matrix_other       = mean(other_cost) · scenario_length

daily_cost_matrix = energy + probiotics + labor + bonus + harvest + feed + other
```

### Optimization

```
profit_matrix = matrix_revenue - daily_cost_matrix
total_profit  = sum(profit_matrix, axis=1)              ← per scenario
optimal_idx   = argmax(total_profit)
optimal_plan  = matrix_ph[optimal_idx]                  ← selected harvest schedule
```

---

## 17. Harvest Simulator Widget

**Route:** `/dashboard/harvest-simulator/:cycle_id`
**APIs:**
- `GET /harvest/simulate/presets?cycle_id=` — preset scenario library
- `GET /harvest/simulate/saved?cycle_id=` — user-saved scenarios
- `POST /harvest/simulate?cycle_id=` — run simulation
- `POST /harvest/simulate/save?cycle_id=` — save scenario

### Scenario Types

**date_range**
```
Input: { doc_start: int, doc_end: int, step_days: int }
Generates: harvest date at every step from doc_start to doc_end
```

**partial**
```
Input: { partial_doc: int, partial_pct: float (10-90) }
Generates: partial harvest at doc, taking partial_pct% of biomass
```

**price_sensitivity**
```
Input: { target_doc: int }
Generates: harvest at target_doc across price curve variations
```

### Results Display

```
Line chart: Profit (IDR) vs Biomass (kg)   ← dual Y-axes
Table: Label | DOC | ABW | Biomass | Revenue | Cost | Profit | Margin %
Saved Scenarios: accordion list with result count + date
```

---

## 18. Water Quality Dashboard

**Route:** `/dashboard/water-quality`
**API:** `GET /water_quality/get-water-quality-dashboard`

### Water Quality Index (WQI) Algorithm

```
For each parameter p (Temp, DO, pH, NH3, Salinity, Turbidity, ...):

  if p.type == "left":
    score_p = left_trapezoidal(value, lb, ub, opt_max)
  else:
    score_p = normal_trapezoidal(value, lb, ub, opt_min, opt_max)

  score_weight_p = p.weight · score_p

wqi_1 = Σ(score_weight_p)                        ← absolute weighted sum
wqi_2 = Σ(score_weight_p) / Σ(weight_p)          ← normalized (0-1)

If any score < 0: use min-weighted aggregation instead
```

### WQ Variable Defaults

| Parameter | Type | Optimal Range |
|-----------|------|---------------|
| DO | normal | 5.0 – 7.0 mg/L |
| NH3 | left | ≤ 0.5 mg/L |
| Temperature | normal | 26 – 30 °C |

### Widget Tabs

| Tab | Content |
|-----|---------|
| Line Chart | All `data.line_plot` objects → LineEcharts |
| Scatter Chart | All `data.scatter_plot` objects → ScatterCharts |
| Table | `data.data` → dynamic table, keys as headers |

---

## 19. Cycle Detail — AI Insights

**API:**
- `GET /summarize/insight?cycle_id=&type=` — standard fetch
- `GET /summarize/insight/cached?cycle_id=&type=` — cached
- `GET /summarize/insight/stream?cycle_id=&type=` — Server-Sent Events

### Insight Types

`performance`, `water_quality`, `feeding`, `harvest`, `economics`, `weekly`

### Insight Data Model

```
CycleInsightCache {
  cycle_id (indexed)
  insight_type: string
  doc_at_generation: int
  insight_data: {
    summary: string
    performance_score: int (0-100)
    metrics: [
      { name, current_value, target_value, unit, status, trend, insight }
    ]
    anomalies: [
      { type, severity, description, first_detected_doc, recommendation }
    ]
    recommendations: [
      { priority, action, reason, expected_impact }
    ]
    forecast_outlook: string (optional)
  }
  generated_at, model_used
}
```

### Streaming Algorithm (SSE)

```
1. Open EventSource to /summarize/insight/stream?...
   OR fallback to fetch() with ReadableStream

2. Parse each line:
   "data: {json}"

   event.type == "tool_call":   display "Fetching {tool_name}…"
   event.type == "chunk":       accumulate text buffer
   event.type == "done":        parse accumulated JSON, render UI
   event.type == "error":       show toast

3. Backend (InsightService):
   a. Build cycle context (metrics, water quality, forecast, costs)
   b. Build type-specific prompt → send to Claude (Anthropic SDK)
   c. Claude calls tool functions (get_cycle_metrics, get_forecast, etc.)
   d. Stream tool_call events → chunk events → done event
   e. Cache result in CycleInsightCache
```

---

## 20. Cycle Detail — Feeding Recommendation Tab

**APIs:**
- `GET /feeding/recommendation?cycle_id=` — today's recommendation
- `POST /feeding/recommendation/override?cycle_id=&doc=` — record override

### UI Flow

```
Show:
  recommended_ration_kg (large number)
  adjustment_reason
  model_layer (e.g., "rule_v1")

Buttons:
  [Accept] → toast "Recommendation accepted" (no backend write)
  [Override] → toggle override form

Override form:
  actual_kg: float input
  reason: text input
  [Submit] → POST override → toast success
  [Cancel] → hide form
```

---

## 21. Cycle Detail — Benchmark

**APIs:**
- `GET /benchmark/my-performance?cycle_id=` — benchmark comparison
- `POST /benchmark/opt-in?cycle_id=` — join benchmark pool
- `POST /benchmark/opt-out?cycle_id=` — leave benchmark pool

### Cohort Construction

```
CohortKey = MD5( species | doc_bucket | density_bucket | region | pond_size_bucket )

doc_bucket:         "1-60" | "61-90" | "91-120" | "121+"
density_bucket:     "<50" | "50-100" | "100-200" | ">200"   (ekor/m²)
pond_size_bucket:   "<500" | "500-2000" | ">2000"            (m²)
```

### Cohort Metrics (Nightly Celery Aggregation)

```
Metrics per cohort: FCR, SR, ADG, Biomass Yield, Cost/kg, Revenue/m²

_extract_cycle_metrics(cycle_id):
  adg               = (last_abw - first_abw) / (last_doc - first_doc)
  fcr               = total_feed_kg / last_biomass_kg
  sr_final          = last survival_rate
  cost_per_kg       = total_cost / last_biomass_kg
  biomass_yield     = (biomass_kg / 1000) / (pond_size_m2 / 10000)   [ton/ha]
  stocking_density  = initial_population / pond_size_m2

_percentile_dict(values):
  → { p10, p25, p50, p75, p90, mean, n }

Suppression: cohort.suppressed = True if sample_count < 5
```

### Benchmark UI

```
Not opted in:
  Checkbox: "I agree to share anonymized farm metrics..."
  Enable button (disabled until checked)
  Disclaimer: "minimum 5 farms required"

Opted in:
  Per metric card:
    metric_name
    my_value
    chip: "Above Average" (green) if my_value > p50, else "Below Average" (yellow)
    MetricBar: visual showing p25 / p50 / p75 markers + my_value pointer
    cohort_size

  "Insufficient data (need 5+ farms)" shown if cohort_size < 5
```

---

## 22. Cycle Detail — Google Sheets Sync

**APIs:**
- `GET /sheets/status?cycle_id=`
- `POST /sheets/connect?cycle_id=` — connect existing sheet
- `POST /sheets/create-template?cycle_id=` — create new sheet from template
- `POST /sheets/manual-sync?cycle_id=` — trigger sync
- `DELETE /sheets/disconnect?cycle_id=`

### Sheet Layout (Tabs)

| Tab | Columns |
|-----|---------|
| DAILY_LOG | date, doc, do_morning, do_afternoon, do_avg, temp_morning, temp_afternoon, temp_avg, ph_morning, ph_afternoon, salinity, nh3, turbidity, feed_given_kg, feed_leftover, feed_type, protein_pct, feeding_freq, notes |
| ABW_SAMPLING | date, doc, abw_sample |
| MORTALITY | date, doc, dead_count, survival_rate |
| COST | date, category, item, quantity, unit_price, total |
| HARVEST | date, doc, type, biomass_kg, size, revenue, profit |
| SYNC_LOG | timestamp, tab, rows_processed, inserted, updated, skipped, rejected, status, error |

### Sync Algorithm

```
SheetService.sync_cycle(cycle_id):
  1. Read all tabs via Google Sheets API
  2. For each row in DAILY_LOG:
     a. _normalize_date(val) → YYYY-MM-DD
        Handles: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY
     b. auto_fill_doc = (date - cycle.start_date).days + 1 if doc missing
     c. Validate required fields, skip malformed rows
  3. Upsert into CycleData.result_data (avoid overwriting existing values with None)
  4. Process ABW_SAMPLING → update abw values
  5. Process MORTALITY → update survival_rate values
  6. Process COST → upsert CostData records
  7. Process HARVEST → upsert HarvestRecord
  8. Append summary row to SYNC_LOG tab
  9. Update SheetIntegration.last_status, last_synced, rows_synced

Polling (frontend):
  After manual sync trigger: poll GET /sheets/status every 3s
  Stop when last_status != "syncing" OR after 20 attempts (60s timeout)
```

### Spreadsheet ID Extraction

```javascript
match(/\/d\/([a-zA-Z0-9_-]+)/)   ← from URL or direct ID input
```

---

## 23. Cost Data Upload

**Route:** `/dashboard/cost-data/:farm_id`
**API:** `POST /cost/add-single-cost-data` (multipart/form-data)

### Algorithm

```
Input fields:
  farm_id (from URL params)
  start_date, end_date (date inputs)
  file (.xlsx, via TeraminaDropzone)

Backend:
  1. Read Excel file, sheet "data"
  2. Upsert CostData { farm_id, start_date, end_date, data[] }
  3. data[] = [{ category, date, total, hp, ... }]

Download:
  GET /cost/download → generate_pl_report() → P&L Excel export
```

---

## 24. Agent (Conversational AI)

**Location:** `teramina/agent/`

### Data Models

```
AgentConversation {
  session_id (unique, indexed)
  user_id, farm_id, cycle_id
  messages: [{ role, content, timestamp }]
  created_at, last_active
}

FarmAlert {
  user_id, farm_id, cycle_id
  alert_type: "water_quality" | "growth" | "harvest_window" | "feeding"
  severity: "info" | "warning" | "critical"
  message: string
  data: dict
  is_read: bool
  created_at, expires_at
}
```

### Agent Chat Loop

```
AgentService.chat(user_id, message, session_id, farm_id, cycle_id):
  1. Get or create AgentConversation
  2. Build Claude messages from last 20 turns (MAX_HISTORY_TURNS)
  3. Agentic loop (max 5 rounds):
     a. Call Claude API with TOOL_DEFINITIONS
     b. If stop_reason == "tool_use":
          Execute tool(s) via TOOL_REGISTRY
          Append tool_result to messages
          Continue loop
     c. If stop_reason == "end_turn":
          Extract final text response
          Break loop
  4. Persist full conversation to MongoDB
  5. Return { response, session_id, context }
```

### Available Tools (Claude Function Calling)

| Tool | Description | Inputs |
|------|-------------|--------|
| `get_farm_overview` | All ponds + active cycles for a farm | farm_id |
| `get_cycle_metrics` | Current ABW, DO, Temp, NH3, feed totals | cycle_id |
| `get_water_quality_trend` | WQ readings for last N days | cycle_id, days (default 7) |
| `get_forecast` | Production forecast + optimal harvest window | cycle_id |
| `get_cost_breakdown` | Cost by category | cycle_id |

### get_cycle_metrics Implementation

```python
current_doc    = max(r.doc for r in cd.result_data if r.doc)
latest_abw     = sorted(r.abw for r in cd.result_data if r.abw)[-1]
do_avg_7d      = mean(r.do_avg for r in last_7_days)
temp_avg_7d    = mean(r.temp_avg for r in last_7_days)
nh3_avg_7d     = mean(r.nh3 for r in last_7_days)
total_feed_kg  = sum(r.feed_given_kg for r in cd.result_data)

do_status  = "optimal" if do_avg ≥ DO_OPTIMAL_MIN else "below_optimal"
nh3_status = "optimal" if nh3_avg ≤ NH3_OPTIMAL_MAX else "elevated"
```

### System Prompt Guidelines

```
- Be specific and data-driven; cite actual numbers
- Detect user language from input, respond in same language
- Flag low DO or high NH3 as urgent
- Keep responses mobile-friendly (concise)
- Never invent or fabricate data
```

### Alert Management

```
GET  /agent/alerts          → unread FarmAlerts, ordered by created_at
POST /agent/alerts/{id}/read   → mark is_read = True
POST /agent/alerts/{id}/dismiss → delete alert
```

---

## 25. Constants Reference

```python
# DOC Thresholds
EARLY_STAGE_DOC_THRESHOLD = 30
MAX_DOC                   = 120
ML_LAYER_DOC_THRESHOLD    = 60

# Feeding
MAX_FEED_TIME             = 4
FEEDING_TIME_WEIGHTS      = [0.30, 0.20, 0.10, 0.40]
AERATOR_WATTS             = 820
HOURS_PER_DAY             = 24

# Water Quality Optimal Ranges
DO_OPTIMAL_MIN            = 5.0   # mg/L
DO_OPTIMAL_MAX            = 7.0   # mg/L
DO_SUITABLE_MIN           = 3.0   # mg/L
DO_SUITABLE_MAX           = 10.0  # mg/L
NH3_OPTIMAL_MAX           = 0.5   # mg/L
NH3_SUITABLE_MIN          = 0.0   # mg/L
NH3_SUITABLE_MAX          = 1.0   # mg/L

# Feeding Adjustment
LEFTOVER_HIGH_THRESHOLD   = 0.15  # 15% → reduce feed
LEFTOVER_LOW_THRESHOLD    = 0.02  # 2%  → increase feed
LEFTOVER_REDUCTION_FACTOR = 0.90
LEFTOVER_INCREASE_FACTOR  = 1.05

# Benchmark
MIN_COHORT_SIZE           = 5     # farms required before data shown
MAX_PARTIAL_HARVEST       = 3     # max partial harvests before final

# Harvest Simulator
MAX_HISTORY_TURNS         = 20    # agent conversation window
```

---

## Summary Formula Table

| Feature | Core Formula | Output |
|---------|-------------|--------|
| Weight | `[wn³ - (wn³-w0³)·e^(-Σαᵢ∫condᵢ)]^⅓` | g |
| Population | `P₀·SR(t) - Σ(partial_harvests)` | count |
| Biomass | `population × weight` | g → kg |
| SGR/ADG | `(ABW_t - ABW_t₀) / ΔDOC` | g/day |
| FR (DPI) | `dpi / (protein%) where dpi=44.7·ABW^-0.714` | % biomass |
| FR (Blind) | `population/100k × (1 + rate×DOC) / biomass` | % biomass |
| FR (Temp) | `CubicSpline(ABW→FR)[temp_band]` | % biomass |
| FR (WQ adj) | `trap_fn(condition) × base_fr` | % biomass |
| FR (Tray) | `base_fr × (1 + point_adj/100)` | % biomass |
| Cost/day | `Σ(harvest+energy+probiotics+feed+labor+bonus+other)` | IDR |
| Cost/kg | `cumsum(cost) / total_biomass_kg` | IDR/kg |
| Revenue | `harvest_kg × CubicSpline(size→price)(size)` | IDR |
| Profit | `cumsum(revenue) - cumsum(cost)` | IDR |
| WQI | `Σ(weight·trap_score) / Σ(weight)` | 0–1 |
| Harvest opt | `argmax Σ(revenue - cost) over all harvest schedules` | schedule |
| Benchmark | `percentile_rank(my_value, cohort_distribution)` | p0–p100 |
| Feed rec | `base_rate × leftover_adj × wq_stress × biomass` | kg/day |
