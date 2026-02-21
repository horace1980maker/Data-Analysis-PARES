# PARES Data Analysis System — Executive Overview

## What Is This System?

The **PARES System** is a data-processing platform that takes **raw field-survey data** collected across vulnerable landscapes in Central America and transforms it into **clear, evidence-based strategic recommendations** for investments in **Nature-based Solutions (NbS)** and **Ecosystem-based Adaptation (EbA)**.

In practical terms: field teams fill out standardised Excel workbooks during workshops and interviews. This system ingests those workbooks, cleans and structures the data, and then runs five analytical pipelines ("Storylines") that answer the critical questions decision-makers need answered before committing resources.

---

## How It Works (High-Level Flow)

```
  Raw field data (Excel)
        │
        ▼
  ┌──────────────────────┐
  │  1. DATA CONVERSION  │  Cleans, validates, and restructures
  │     (Converter)       │  raw spreadsheets into a standardised
  └──────────┬───────────┘  analytical database (LOOKUP + TIDY tables)
             │
             ▼
  ┌──────────────────────┐
  │  2. ANALYSIS ENGINE  │  Five thematic pipelines (Storylines)
  │   (5 Storylines)     │  compute indices, rankings, and flags
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │   3. DELIVERABLES    │  Interactive HTML reports, Excel summaries,
  │   (Reports & Data)   │  visualisations, and downloadable ZIP packages
  └──────────────────────┘
```

---

## The Five Storylines at a Glance

| #   | Storyline                  | Key Questions Answered                                                                                                                                                | Main Output                                                                                                  |
| --- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | **Prioritisation**         | **Where should we act first?**<br>_Also:_ Which livelihoods are at highest risk of collapse?<br>Where are the biggest gaps in adaptive capacity?                      | Ranked list of livelihoods and geographic zones by urgency, threat severity, and adaptive-capacity gaps.     |
| 2   | **Ecosystem Lifelines**    | **Which ecosystem services are most critical?**<br>_Also:_ Which specific threats are breaking these lifelines?<br>Which ecosystems act as "critical infrastructure"? | Dependency map (Ecosystem → Service → Livelihood) highlighting leverage points for maximum impact.           |
| 3   | **Equity & Vulnerability** | **Who must not be left behind?**<br>_Also:_ Are there access barriers for women or youth?<br>Which groups will suffer disproportionately if we do not act?            | "Do-No-Harm" alerts identifying differentially affected groups (gender, ethnicity, age) and access barriers. |
| 4   | **Governance & Conflict**  | **Is intervention feasible?**<br>_Also:_ Who are the key actors (champions) to lead change?<br>What current conflicts could block implementation?                     | Stakeholder network analysis, dialogue-space coverage, and conflict-risk mapping.                            |
| 5   | **NbS Portfolio & MEAL**   | **What should we fund, and how do we track it?**<br>_Also:_ Which actions are "do now" vs "do later"?<br>What minimum indicators will tell us if we are succeeding?   | Integrated action portfolio ("Do Now / Do Next / Do Later") with an auto-generated monitoring plan.          |

> **Storyline 5** synthesises the outputs of the previous four into a single investment-ready recommendation.

---

## Why It Matters for Coordinators & Managers

| Benefit             | Description                                                                                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Reproducibility** | Every recommendation is traceable back to field data; results can be regenerated with one click.                                                                         |
| **Comparability**   | Standardised data structure allows cross-landscape and cross-country comparisons.                                                                                        |
| **Speed**           | What previously required weeks of manual spreadsheet analysis now runs in minutes.                                                                                       |
| **Transparency**    | Built-in quality-assurance reports flag data issues (duplicates, missing IDs), and sensitivity analysis tests whether rankings hold under different weighting scenarios. |
| **Do-No-Harm**      | Equity and conflict dimensions are embedded in the analysis, not added as afterthoughts.                                                                                 |

---

## What Goes In / What Comes Out

| Input                                                                                      | Output                                                                     |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| Raw Excel workbooks from PARES field data collection (workshops, surveys, actor mappings). | **Interactive HTML reports** with charts and tables per Storyline.         |
|                                                                                            | **Analysis-ready Excel** workbooks with structured LOOKUP and TIDY tables. |
|                                                                                            | **Visualisations** (PNG charts: quadrant plots, heatmaps, network graphs). |
|                                                                                            | **Downloadable ZIP** packages containing all generated assets.             |

---

## Technical Deployment (summary)

- **Technology**: Python (Pandas, NumPy, Matplotlib), served via a **FastAPI** web application.
- **Interface**: Users interact through a modern **web UI** (upload file → choose analysis → download results).
- **Containerised**: Ships with Docker for consistent deployment anywhere.
- **API-ready**: All functionality is also available through REST endpoints for integration with other systems.

---

## Alignment with International Standards

The analytical framework is grounded in three key international references:

### 1. IUCN Global Standard for Nature-based Solutions (v2.0)

The [International Union for Conservation of Nature (IUCN)](https://iucn.org/our-work/topic/iucn-global-standard-nature-based-solutions) defines eight criteria for designing and verifying NbS. The PARES system incorporates them as follows:

- **Prioritisation criteria**: Storylines 1 and 2 evaluate the ecosystem → service → livelihood chain to identify leverage points, aligning with the IUCN criterion that NbS must generate simultaneous benefits for biodiversity and human well-being.
- **Social and environmental safeguards**: Storyline 3 (Equity) and Storyline 4 (Governance & Conflict) function as integrated "Do-No-Harm" safeguards, verifying the inclusion of vulnerable groups and governance feasibility before recommending interventions.
- **Monitoring indicators**: Storyline 5 draws from a library of 12 standard indicator templates based on IUCN and EbA guidelines to auto-generate MEAL plans.

### 2. IPCC AR6 Working Group II — Impacts, Adaptation and Vulnerability

The [IPCC Sixth Assessment Report, Working Group II](https://www.ipcc.ch/report/ar6/wg2/) provides the conceptual foundation for assessing climate vulnerability and adaptation options. Its influence on PARES includes:

- **Vulnerability framework**: Storyline 1's analytical structure (threats → impacts → adaptive-capacity gap) mirrors the IPCC framework that defines vulnerability as a function of exposure, sensitivity, and adaptive capacity.
- **Impact dimensions**: The eight impact dimensions assessed (economic, social, health, education, environmental, political, conflict, and migration) align with the risk categories identified by the IPCC for Central America.
- **Adaptation evidence**: The NbS portfolio recommendations (Storyline 5) are framed within the ecosystem-based adaptation options validated by the IPCC.

### 3. Multi-Criteria Decision Analysis (MCDA)

Following best practices established by the [UK Government Analytical Function](https://analysisfunction.civilservice.gov.uk/policy-store/an-introductory-guide-to-mcda/), the system implements MCDA as a transparent and reproducible prioritisation mechanism:

- **Action Priority Index (API)**: Combines three normalised metrics (community priority, impact risk, and capacity gap) via additive weighting: `API = w₁·Priority + w₂·Risk + w₃·Gap`.
- **Sensitivity analysis**: Three weighting scenarios ("Balanced", "Livelihood-first", and "Risk-first") are run to verify ranking stability, ensuring recommendations are not dependent on a single weight configuration.
- **Traceability**: Every input to the composite index is traceable back to raw field data, satisfying the MCDA principle of transparency.

---

_For technical implementation details, refer to `README.md` and the `docs/` folder within the repository._
