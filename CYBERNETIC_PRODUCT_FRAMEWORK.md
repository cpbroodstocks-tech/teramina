# Teramina Cybernetic Product Framework

## Purpose

This document translates the cybernetic shrimp-farm thesis into product requirements for Teramina.

Teramina should not be treated as a collection of dashboards. Its product direction is to become a cybernetic control system for shrimp farming: a system that helps farmers observe pond state, infer hidden risk, choose interventions, monitor response, and learn across crops.

## Product Thesis

A shrimp pond is a cybernetic economic-biological reactor.

It is:

- biological, because shrimp, microbes, water chemistry, sludge, pathogens, feed, and oxygen interact continuously;
- economic, because each biological state eventually becomes cost, revenue, margin, risk, or loss;
- cybernetic, because management quality depends on the feedback loop: observe, interpret, act, observe response, and learn.

Teramina succeeds if it helps farmers regulate biological complexity before risk destroys economic value.

## Product North Star

Help farmers keep each pond inside a viable operating region long enough to convert biological potential into risk-adjusted profit.

This means the product must answer:

- What is the current pond state?
- What is changing?
- What is hidden or uncertain?
- Which margin is narrowing?
- What action improves risk-adjusted profit?
- What should be measured next?
- Did the last intervention work?
- What did this farm learn from prior crops?

## Product Principles

### State Before Screens

Every major surface should make pond state legible, not just display module data.

A good pond state summary includes:

- DOC and crop stage;
- biomass, ABW, survival estimate, and FCR;
- DO, pH, temperature, NH3/TAN, nitrite, salinity, and alkalinity where available;
- feed pressure and leftover trend;
- current alert/task status;
- uncertainty and missing data.

### Trajectory Before Snapshot

Current values are not enough. Teramina must elevate trajectory, speed, and recovery.

Important dynamic indicators:

- nighttime DO decline rate;
- morning DO recovery time;
- daily pH amplitude;
- feed response trend;
- TAN/NH3 trend;
- nitrite trend;
- FCR drift;
- growth deviation from expected curve;
- mortality acceleration;
- intervention frequency;
- recovery time after rain, feed reduction, water exchange, or aeration change.

### Margin Before Maximum

The product should discourage pure growth maximization. It should show whether current biomass, feed input, waste load, and weather exposure are consuming control margin.

Useful margin concepts:

- oxygen reserve;
- nitrogen processing pressure;
- biomass versus estimated dynamic carrying capacity;
- sludge and organic-load proxy;
- late-cycle fragility;
- harvest optionality.

### Uncertainty Before False Precision

Teramina should distinguish observed data from inferred state.

Every recommendation should clarify:

- what was measured;
- what was inferred;
- confidence level;
- missing data;
- what evidence would change the recommendation.

### Control Loop Before Advice

Advice is incomplete unless it closes the loop.

Recommendations should include:

- recommended action;
- reason;
- expected benefit;
- expected tradeoff;
- confidence;
- next observation needed;
- when to recheck;
- success/failure signal.

## Core Product Objects

### Pond State

The estimated current condition of a pond/cycle.

Minimum fields:

- identifiers: farm_id, pond_id, cycle_id;
- crop stage: DOC, start date, active/final status;
- production: ABW, biomass, population, survival estimate, growth rate;
- water: DO, temperature, pH, salinity, NH3/TAN, nitrite, alkalinity if available;
- feeding: ration, feed given, feed leftover, FCR;
- economics: cost/kg, current projected revenue, current projected profit;
- risk: severity, drivers, confidence, missing data.

Current implementation sources:

- `CycleData`, `ForecastData`, `FeedRealization`, `HarvestRecord`, `CostData`;
- dashboard and formula services;
- Mnemon memory and alert models.

### Dynamic Indicator

A trend, rate, recovery measurement, or deviation that describes whether the pond is becoming easier or harder to control.

Examples:

- DO recovery slowed from 1 day after rain to 3 days;
- pH amplitude widened above normal;
- feed leftover rose above 20 percent;
- ABW deviated below expected curve after DOC 45;
- interventions increased over the last week.

### Control Margin

An estimate of remaining safety before the pond leaves the viable operating region.

Control margin is not one metric. It combines oxygen, nitrogen, sludge proxy, feeding pressure, biomass, weather, biosecurity, and farm control capacity.

Early implementation can use a transparent score instead of a hidden model:

- oxygen margin;
- nitrogen margin;
- feeding margin;
- growth/biomass margin;
- economic/harvest margin;
- data confidence.

### Intervention

Any action that changes pond state.

Examples:

- reduce/increase feed;
- increase aeration;
- siphon sludge;
- water exchange;
- apply lime/carbon/probiotics;
- partial harvest;
- final harvest;
- lab test;
- recheck after disturbance.

Interventions should be logged when possible, because response monitoring is impossible without action history.

### Response

The observed effect after an intervention or disturbance.

Examples:

- DO recovered within 24 hours;
- feeding normalized after 2 days;
- nitrite did not improve after feed reduction;
- growth remained below curve;
- mortality accelerated.

Response data is the foundation of farm-specific learning.

## AI Recommendation Contract

Every farmer-facing AI recommendation should follow this structure:

```text
State:
What the pond appears to be doing now.

Risk:
Main risk level and drivers.

Confidence:
High / medium / low, with missing data called out.

Recommendation:
Specific action.

Tradeoff:
What the farmer gains and what they may sacrifice.

Next check:
What to observe next and when.

Source:
Relevant pond data, trend, memory, alert, or report reference.
```

The assistant should avoid generic advice. If required data is missing, it should say so and recommend the next observation instead of pretending certainty.

## Feature Requirements

### Today View

Current role:

- Show urgent alerts, active alerts, tasks, and pond status.

Cybernetic target:

- Show which ponds are losing control margin.
- Rank urgent actions by risk-adjusted importance.
- Show next observation needed for each risky pond.
- Let farmer open chat with context already attached.

### Pond Timeline

Current role:

- Show observations, alerts, and memory events.

Cybernetic target:

- Show control loop history: disturbance -> action -> response -> learned memory.
- Make recovery time visible.
- Mark unresolved loops where no response was recorded.

### Memory Page

Current role:

- Review, verify, correct, create, and delete memories.

Cybernetic target:

- Separate facts, preferences, events, advice outcomes, pond patterns, and response history.
- Highlight memories that affect current risk interpretation.
- Surface stale assumptions and low-confidence memories for review.

### Dashboard Widgets

Current role:

- Show overview, feeding, economics, forecast, harvest, and water-quality data.

Cybernetic target:

- Add state, trend, margin, and confidence to each widget.
- Avoid presenting metrics as isolated numbers.
- Show whether the pond is becoming more stable or more fragile.

### Harvest Simulator

Current role:

- Compare harvest scenarios.

Cybernetic target:

- Compare harvest now versus wait using risk-adjusted value.
- Include biological fragility, forecast confidence, market price, and accumulated value at risk.
- Make partial harvest a control action, not only an economics scenario.

### Feeding Recommendation

Current role:

- Recommend ration and allow override.

Cybernetic target:

- Treat feed as both production input and pond disturbance.
- Explain whether feed pressure is consistent with oxygen, nitrogen, biomass, and leftover signals.
- Require response monitoring after override.

### AI Chat

Current role:

- Context-aware assistant with memory and tools.

Cybernetic target:

- Act as a probabilistic control assistant.
- Ask for missing measurements when confidence is low.
- Cite live data over stale memory.
- Close recommendations with next observation timing.

## Data Implications

### Data Needed Soon

The current system should prioritize capturing:

- event/disturbance logs: rain, water exchange, power issue, algal crash, disease suspicion;
- intervention logs: feed reduction, aeration increase, siphoning, treatment, harvest decision;
- response logs: time to feeding recovery, DO recovery, nitrite recovery, pH stabilization;
- confidence metadata: source, timestamp, unit, measurement method.

### Derived Metrics To Add

Near-term derived metrics:

- DO trend and recovery proxy;
- pH amplitude;
- NH3/nitrite trend;
- feed leftover percentage;
- growth deviation from expected curve;
- FCR drift;
- intervention frequency;
- open-loop count: recommendations without recorded follow-up;
- risk-adjusted harvest value.

Later derived metrics:

- dynamic carrying-capacity estimate;
- pond fragility score;
- resilience/recovery score;
- hidden biomass uncertainty;
- disease-risk belief state.

## Roadmap Alignment

### Current Beta

Keep the current MongoEngine Mnemon beta narrow:

- validate chat context;
- validate memory create/correct/verify/delete;
- validate alerts and tasks;
- validate Today view and pond timeline;
- validate pattern jobs;
- run authenticated smoke tests with seeded farmer data.

### Next Product Layer

After beta validation, add cybernetic product features without requiring a database migration:

- Pond State Card;
- Dynamic Indicator Panel;
- Control Margin summary;
- AI Recommendation Contract enforcement;
- intervention and response logging;
- recovery-time calculations from existing observations.

### Future Platform Track

Only after the migration gate is met:

- move canonical farm events and observations to Postgres/TimescaleDB;
- use pgvector for memory and observation retrieval;
- add stronger audit trail and formula versioning;
- evaluate Temporal for long-running follow-up workflows.

## Evaluation Questions

Use these questions to judge any new feature:

- Does it help the farmer see state, trend, margin, or uncertainty?
- Does it reduce generic advice?
- Does it close the control loop after an intervention?
- Does it protect accumulated crop value?
- Does it distinguish biological maximum from economic optimum?
- Does it preserve farmer judgment instead of encouraging automation bias?
- Does it make the next observation clearer?

## One-Sentence Product Definition

Teramina is a cybernetic shrimp-farm operating system that helps farmers regulate pond state, biological risk, and economic decisions through feedback, memory, forecasting, and action tracking.
