# Data Connections & Lineage Map

This document details the data "plumbing" for the **PARES Analysis Pipelines**. It maps how raw Excel sheets are transformed into analysis-ready tables and how those tables are joined to calculate key metrics.

## Storyline 1: Where to Act First? (Prioritization)

**Goal:** Identify which Livelihoods (Medios de Vida) are most critical, most at risk, and have the least adaptive capacity.
**Key Metric:** Action Priority Index (API) = Weighted Index of (Priority + Risk + Capacity Gap).

### 1. Data Source Traceability (Raw inputs)

| Raw Sheet (User Input) | Key Columns Extracted | Conversion Logic (Tidy) | Output Table (Analysis Ready) |
| :--- | :--- | :--- | :--- |
| **3.2. Priorización** | `País`, `Grupo`, `Medio de vida`, `Total` | Normalizes columns, links to Context & MdV IDs. | `TIDY_3_2_PRIORIZACION` |
| **4.1. Amenazas** | `País`, `Grupo`, `Amenaza`, `Suma` (Severity) | Extracts threat severity scores. | `TIDY_4_1_AMENAZAS` |
| **4.2.1. Amenazas_MdV** | `País`, `Grupo`, `Medio de vida`, `Amenaza`, Impact scores (`Pérdida`, etc.) | Links specific threats to specific MdVs. | `TIDY_4_2_1_AMENAZA_MDV` |
| **7.1. Encuesta CA** | `m_d_v` (or `Medio de vida`), Questions (Aggregated or Raw) | Processes survey responses into numeric scores (0-1). | `TIDY_7_1_RESPONSES`<br>`TIDY_7_1_RESPONDENTS` |
| **1.1. Contexto** | `País`, `Grupo`, `Paisaje` | Builds the Global ID spine. | `LOOKUP_CONTEXT`<br>`LOOKUP_GEO` |

### 2. Analysis Logic & Joins (The "Plumbing")

The analysis pipeline joins these tables to compute the final **API Score**.

#### Step A: Calculate Importance (Priority)
*   **Source:** `TIDY_3_2_PRIORIZACION`
*   **Logic:** Aggregates the `i_total` (Importance Total) by Livelihood (`mdv_id`).
*   **Metric:** `mean_i_total` -> Normalized to `priority_norm` (0-1).

#### Step B: Calculate Threat Severity
*   **Source:** `TIDY_4_1_AMENAZAS`
*   **Logic:** Aggregates `suma` (Severity Score) by Threat (`amenaza_id`).
*   **Metric:** `mean_suma` -> Normalized to `suma_norm` (0-1).

#### Step C: Calculate Risk (Impact * Severity)
*   **Source:** `TIDY_4_2_1_AMENAZA_MDV` **JOIN** `Step B (Threat Severity)`
*   **Join Key:** `amenaza_id`
*   **Logic:** 
    1.  Sum the Impact Dimensions (Loss, Quality, Access...) -> `impact_total`.
    2.  Multiply `impact_total` * `suma_norm` (Threat Severity) = `weighted_impact`.
    3.  Sum `weighted_impact` for all threats affecting a Livelihood.
*   **Metric:** `sum_weighted_impact` -> Normalized to `risk_norm` (0-1).

#### Step D: Calculate Adaptive Capacity
*   **Source:** `TIDY_7_1_RESPONSES` **JOIN** `TIDY_7_1_RESPONDENTS`
*   **Join Key:** `respondent_id`
*   **Logic:** 
    1.  Average the normalized response scores (0-1) per Livelihood (`mdv_id`).
    2.  `Capacity Gap` = 1 - `Average Capacity`.
*   **Metric:** `capacity_gap` -> Normalized to `cap_gap_norm` (0-1).

#### Step E: Final API Calculation
*   **Inputs:** `priority_norm`, `risk_norm`, `cap_gap_norm`
*   **Formula:** 
    ```python
    API = (w_priority * priority) + (w_risk * risk) + (w_capacity * capacity_gap)
    ```
    *(Weights vary by scenario, e.g., Balanced, Risk-First)*
*   **Output:** Ranked list of Livelihoods requiring intervention.

### 3. Visual Connection Map (Mermaid)

```mermaid
graph TD
    %% RAW INPUTS
    subgraph Raw_Inputs ["Excel / Raw Data"]
        S32["3.2. Priorización"]
        S41["4.1. Amenazas"]
        S421["4.2.1. Amenazas_MdV"]
        S71["7.1. Encuesta CA"]
    end

    %% TIDY INTERMEDIATES
    subgraph Converter ["Converter / Tidy Tables"]
        T_PRI["TIDY_3_2_PRIORIZACION"]
        T_AMEN["TIDY_4_1_AMENAZAS"]
        T_AMEN_MDV["TIDY_4_2_1_AMENAZA_MDV"]
        T_RESP["TIDY_7_1_RESPONSES"]
    end

    %% ANALYSIS METRICS
    subgraph Metrics ["Analysis Pipeline / Metrics"]
        M_PRI["Priority Score"]
        M_SEV["Threat Severity"]
        M_RISK["Risk Score"]
        M_CAP["Capacity Gap"]
        M_API["API Index"]
    end

    %% FLOW
    S32 --> T_PRI
    S41 --> T_AMEN
    S421 --> T_AMEN_MDV
    S71 --> T_RESP

    T_PRI -->|"mean(i_total)"| M_PRI
    T_AMEN -->|"mean(suma)"| M_SEV
    
    T_AMEN_MDV -->|"joins"| M_RISK
    M_SEV -->|"weighted by"| M_RISK
    
    T_RESP -->|"mean(response)"| M_CAP
    
    M_PRI --> M_API
    M_RISK --> M_API
    M_CAP --> M_API
    
    classDef raw fill:#ffecd2,stroke:#333,stroke-width:1px,color:black;
    classDef tidy fill:#d4e6f1,stroke:#333,stroke-width:1px,color:black;
    classDef metric fill:#d5f5e3,stroke:#333,stroke-width:1px,color:black;
    
    class S32,S41,S421,S71 raw;
    class T_PRI,T_AMEN,T_AMEN_MDV,T_RESP tidy;
    class M_PRI,M_SEV,M_RISK,M_CAP,M_API metric;
```

## Storyline 2: Ecosystem-Service Lifelines

**Goal:** Understand the "Lifelines" connecting Ecosystems -> Services -> Livelihoods.
**Key Metrics:** 
*   **SCI (Service Criticality Index):** How vital a service is to the community.
*   **ELI (Ecosystem Leverage Index):** How strategically important an ecosystem is (supporting critical services).
*   **TPS (Threat Pressure on Services):** Vulnerability of services to threats.

### 1. Data Source Traceability

| Raw Sheet | Key Columns | Conversion Logic | Output Table |
| :--- | :--- | :--- | :--- |
| **3.4. Ecosistemas** | `Ecosistema`, `Causas degradación` | Normalizes ecosystem names/IDs. | `TIDY_3_4_ECOSISTEMAS` |
| **3.4. Eco_SE** | `Ecosistema`, `Servicio Ecosistémico` | Maps ecosystems to the services they provide. | `TIDY_3_4_ECO_SE` |
| **3.5. SE_MdV** | `Servicio`, `MdV`, `Usuarios`, `Mes falta` | Maps services to livelihood dependence + seasonality. | `TIDY_3_5_SE_MDV` |
| **3.2. Priorización** | `MdV`, `Total` (Importance) | Used to weight the importance of livelihoods dependent on services. | `TIDY_3_2_PRIORIZACION` |
| **4.2.2. Amenazas_SE** | `Amenaza`, `Servicio`, `Impacto` | Maps threats impacting specific services. | `TIDY_4_2_2_AMENAZA_SE` |
| **4.1. Amenazas** | `Amenaza`, `Suma` | Threat severity weights. | `TIDY_4_1_AMENAZAS` |

### 2. Analysis Logic & Joins

#### Step A: Ecosystem Connectivity
*   **Sources:** `TIDY_3_4_ECOSISTEMAS` **LEFT JOIN** `TIDY_3_4_ECO_SE` **LEFT JOIN** `TIDY_3_4_ECO_MDV`
*   **Logic:** Count unique Services and Livelihoods supported by each Ecosystem.
*   **Metric:** `connectivity_raw` = Count(Services) + Count(MdVs).

#### Step B: Service Criticality Index (SCI)
*   **Source:** `TIDY_3_5_SE_MDV`
*   **Logic:**
    1.  **Users:** Sum of `nr_usuarios` receiving the service.
    2.  **Breadth:** Count of unique Livelihoods (`mdv_id`) using the service.
    3.  **Seasonality:** Derived from `mes_falta` (scarcity).
    4.  **Priority Weight:** Average Importance (`priority_norm` from Story 1) of the Livelihoods using this service.
*   **Metric:** `SCI` = Weighted sum of (Users, Breadth, Seasonality, MdV Priority).

#### Step C: Ecosystem Leverage Index (ELI)
*   **Source:** `Step A (Connectivity)` **JOIN** `Step B (SCI)`
*   **Logic:** An ecosystem is strategic if it supports *many* services (Connectivity) AND those services are *critical* (SCI).
*   **Metric:** `ELI` = w1 * `Connectivity` + w2 * Avg(`SCI` of supported services).

#### Step D: Threat Pressure on Services (TPS)
*   **Source:** `TIDY_4_2_2_AMENAZA_SE` **JOIN** `TIDY_4_1_AMENAZAS`
*   **Logic:** Sum of Impact Scores on a service, weighted by the Severity of the Threat.
*   **Metric:** `pressure` = Impact * Threat_Severity.

### 3. Visual Connection Map (Mermaid)

```mermaid
graph TD
    %% RAW INPUTS
    subgraph Raw_2 ["Raw Sources"]
        S34["3.4. Ecosistemas"]
        S35["3.5. SE_MdV"]
        S422["4.2.2. Amenazas_SE"]
        S32["3.2. Priorización"]
        S41["4.1. Amenazas"]
    end

    %% TIDY
    subgraph Tidy_2 ["Tidy Tables"]
        T_ECO["TIDY_3_4_ECOSISTEMAS"]
        T_SE_MDV["TIDY_3_5_SE_MDV"]
        T_AMEN_SE["TIDY_4_2_2_AMENAZA_SE"]
        T_PRI["TIDY_3_2_PRIORIZACION"]
        T_AMEN["TIDY_4_1_AMENAZAS"]
        T_ECO_SE["TIDY_3_4_ECO_SE"]
    end

    %% METRICS
    subgraph Metric_2 ["Metrics"]
        M_CONN["Connectivity"]
        M_SCI["SCI: Service Criticality"]
        M_ELI["ELI: Eco Leverage"]
        M_TPS["TPS: Threat Pressure"]
    end

    S34 --> T_ECO
    S34 --> T_ECO_SE
    S35 --> T_SE_MDV
    S422 --> T_AMEN_SE
    S32 --> T_PRI
    S41 --> T_AMEN

    T_ECO -->|"supports"| T_ECO_SE
    
    T_ECO_SE -->|"count links"| M_CONN
    
    T_SE_MDV -->|"users, seasonality"| M_SCI
    T_PRI -->|"weights"| M_SCI
    
    M_SCI -->|"avg per eco"| M_ELI
    M_CONN --> M_ELI
    
    T_AMEN_SE -->|"impacts"| M_TPS
    T_AMEN -->|"severity"| M_TPS
    
    classDef raw fill:#ffecd2,stroke:#333,stroke-width:1px,color:black;
    classDef tidy fill:#d4e6f1,stroke:#333,stroke-width:1px,color:black;
    classDef metric fill:#d5f5e3,stroke:#333,stroke-width:1px,color:black;
    
    class T_ECO,T_SE_MDV,T_AMEN_SE,T_PRI,T_AMEN,T_ECO_SE tidy;
    class M_CONN,M_SCI,M_ELI,M_TPS metric;
```

## Storyline 3: Equity & Differentiated Vulnerability

**Goal:** Analyze how vulnerability affects different groups (women, youth, indigenous peoples) differently.
**Key Metric:** **EVI (Equity Vulnerability Index)**.

### 1. Data Source Traceability

| Raw Sheet | Key Columns | Conversion Logic | Output Table |
| :--- | :--- | :--- | :--- |
| **4.2.1. Amenazas_MdV** | `Amenaza`, `MdV`, `Grupo Impactado` (e.g., Mujeres) | Identifies impacts specific to vulnerable groups. | `TIDY_4_2_1_DIFERENCIADO` |
| **4.2.2. Amenazas_SE** | `Amenaza`, `Servicio`, `Grupo Impactado` | Identifies service-related impacts on groups. | `TIDY_4_2_2_DIFERENCIADO` |
| **3.5. SE_MdV** | `Barreras acceso`, `Inclusión` | Qualitative text on access barriers and inclusion. | `TIDY_3_5_SE_MDV` |
| **7.1. Encuesta CA** | `Grupo`, Questions | Capacity gaps aggregated by demographic group. | `TIDY_7_1_RESPONSES` |

### 2. Analysis Logic & Joins

#### Step A: Differentiated Impact Intensity (DIF)
*   **Sources:** `TIDY_4_2_1_DIFERENCIADO` **UNION** `TIDY_4_2_2_DIFERENCIADO`
*   **Logic:** Count frequency of mentions for each vulnerable group (e.g., "How many times are 'Women' cited as uniquely impacted?").
*   **Metric:** `DIF Intensity` = normalized count of citations.

#### Step B: Access Barriers & Inclusion
*   **Source:** `TIDY_3_5_SE_MDV`
*   **Logic:** 
    1.  Parse text columns (`barreras`, `inclusión`) for keywords.
    2.  Calculate `Barrier Rate` (proportion of records citing barriers).
    3.  Calculate `Inclusion Rate` (proportion of records citing active inclusion).
*   **Metrics:** `bar_norm`, `inc_norm`.

#### Step C: Capacity Gap (by Group)
*   **Source:** `TIDY_7_1_RESPONSES`
*   **Logic:** Filter survey responses by demographic `Grupo`.
*   **Metric:** `cap_gap` = 1 - Avg(Capacity Score) for that specific group.

#### Step D: Equity Vulnerability Index (EVI)
*   **Inputs:** `DIF Intensity`, `Barrier Rate`, `Inclusion Rate`, `Capacity Gap`
*   **Formula:** 
    ```python
    EVI = w1*DIF + w2*Barriers - w3*Inclusion + w4*CapacityGap
    ```
    *(Note: Inclusion reduces vulnerability, others increase it)*

### 3. Visual Connection Map (Mermaid)

```mermaid
graph TD
    %% RAW
    subgraph Raw_3 ["Raw Sources"]
        S421["4.2.1. Impacts"]
        S422["4.2.2. Impacts"]
        S35["3.5. SE_MdV"]
        S71["7.1. Encuesta"]
    end

    %% TIDY
    subgraph Tidy_3 ["Tidy Tables"]
        T_DIF_1["TIDY_4_2_1_DIFERENCIADO"]
        T_DIF_2["TIDY_4_2_2_DIFERENCIADO"]
        T_SE_MDV["TIDY_3_5_SE_MDV"]
        T_RESP["TIDY_7_1_RESPONSES"]
    end

    %% METRICS
    subgraph Metric_3 ["Metrics"]
        M_DIF["DIF Intensity"]
        M_BAR["Barrier Rate"]
        M_INC["Inclusion Rate"]
        M_CAP["Group Capacity Gap"]
        M_EVI["EVI Index"]
    end

    S421 --> T_DIF_1
    S422 --> T_DIF_2
    S35 --> T_SE_MDV
    S71 --> T_RESP

    T_DIF_1 -->|"union"| M_DIF
    T_DIF_2 -->|"union"| M_DIF
    
    T_SE_MDV -->|"text analysis"| M_BAR
    T_SE_MDV -->|"text analysis"| M_INC
    
    T_RESP -->|"filter by group"| M_CAP
    
    M_DIF --> M_EVI
    M_BAR --> M_EVI
    M_INC --> M_EVI
    M_CAP --> M_EVI
    
    classDef raw fill:#ffecd2,stroke:#333,stroke-width:1px,color:black;
    classDef tidy fill:#d4e6f1,stroke:#333,stroke-width:1px,color:black;
    classDef metric fill:#d5f5e3,stroke:#333,stroke-width:1px,color:black;
    
    class S421,S422,S35,S71 raw;
    class T_DIF_1,T_DIF_2,T_SE_MDV,T_RESP tidy;
    class M_DIF,M_BAR,M_INC,M_CAP,M_EVI metric;
```

## Storyline 4: Feasibility, Governance & Conflict Risk

**Goal:** Assess the social feasibility of interventions by analyzing governance strength and conflict risks.
**Key Metric:** **Feasibility Index** = (Actor Strength + Dialogue) - Conflict Risk.

### 1. Data Source Traceability

| Raw Sheet | Key Columns | Conversion Logic | Output Table |
| :--- | :--- | :--- | :--- |
| **5.1. Actores** | `Actor`, `Tipo`, `Poder`, `Interés` | Census of key actors. | `TIDY_5_1_ACTORES` |
| **5.1. Relaciones** | `Actor 1`, `Actor 2`, `Relación` (Colabora/Conflicto) | Network edges (graph). | `TIDY_5_1_RELACIONES` |
| **5.2. Espacios Diálogo** | `Espacio`, `Tipo`, `Alcance` | Inventory of governance tables. | `TIDY_5_2_DIALOGO` |
| **6.1. Eventos Conflicto** | `Conflicto`, `Año`, `Incidencia` | Time-series of conflict events. | `TIDY_6_1_CONFLICT_EVENTS` |

### 2. Analysis Logic & Joins

#### Step A: Actor Network Strength
*   **Source:** `TIDY_5_1_RELACIONES`
*   **Logic:** Build a network graph. Calculate `Out-Degree` (number of collaboration links per actor).
*   **Metric:** `actor_network_strength` = Mean collaboration degree of all actors.

#### Step B: Dialogue Coverage
*   **Source:** `TIDY_5_2_DIALOGO` **JOIN** `TIDY_5_2_DIALOGO_ACTOR`
*   **Logic:** Count unique actors participating in dialogue spaces.
*   **Metric:** `dialogue_coverage` = Avg number of actors per dialogue space.

#### Step C: Conflict Risk
*   **Source:** `TIDY_6_1_CONFLICT_EVENTS`
*   **Logic:** Sum of conflict events (frequency) and incidence (severity) over time.
*   **Metric:** `conflict_risk` = Normalized event count.

#### Step D: Feasibility Index
*   **Inputs:** `Actor Strength`, `Dialogue Coverage`, `Conflict Risk`
*   **Formula:** 
    ```python
    Feasibility = w1*ActorStrength + w2*Dialogue - w3*ConflictRisk
    ```
    *(Higher strength + dialogue increases feasibility; conflict decreases it)*

### 3. Visual Connection Map (Mermaid)

```mermaid
graph TD
    %% RAW
    subgraph Raw_4 ["Raw Sources"]
        S51a["5.1. Actores"]
        S51b["5.1. Relaciones"]
        S52["5.2. Dialogo"]
        S61["6.1. Conflictos"]
    end

    %% TIDY
    subgraph Tidy_4 ["Tidy Tables"]
        T_ACT["TIDY_5_1_ACTORES"]
        T_REL["TIDY_5_1_RELACIONES"]
        T_DIA["TIDY_5_2_DIALOGO"]
        T_EVT["TIDY_6_1_CONFLICT_EVENTS"]
    end

    %% METRICS
    subgraph Metric_4 ["Metrics"]
        M_NET["Actor Network Strength"]
        M_DIA["Dialogue Coverage"]
        M_CON["Conflict Risk"]
        M_FEAS["Feasibility Index"]
    end

    S51a --> T_ACT
    S51b --> T_REL
    S52 --> T_DIA
    S61 --> T_EVT

    T_REL -->|"graph degree"| M_NET
    
    T_DIA -->|"participation count"| M_DIA
    
    T_EVT -->|"event frequency"| M_CON
    
    M_NET --> M_FEAS
    M_DIA --> M_FEAS
    M_CON --> M_FEAS
    
    classDef raw fill:#ffecd2,stroke:#333,stroke-width:1px,color:black;
    classDef tidy fill:#d4e6f1,stroke:#333,stroke-width:1px,color:black;
    classDef metric fill:#d5f5e3,stroke:#333,stroke-width:1px,color:black;
    
    class T_ACT,T_REL,T_DIA,T_EVT tidy;
    class M_NET,M_DIA,M_CON,M_FEAS metric;
```

## Storyline 5: SbN Portfolio Design

**Goal:** Synthesize all previous insights to recommend "Bundles" of Nature-based Solutions (SbN).
**Key Output:** **Ranked Portfolio** (Do Now / Do Next / Do Later).

### 1. Data Source Traceability

| Raw Sheet | Key Columns | Conversion Logic | Output Table |
| :--- | :--- | :--- | :--- |
| **All Previous Tables** | N/A | Aggregates all previous metrics. | `METRICS_ALL` |
| **Parameters (YAML)** | `weights`, `thresholds` | Configuration for portfolio weights. | `params.yaml` |

### 2. Analysis Logic & Joins (The "Bundle" Builder)

Storyline 5 does not create new raw metrics; it **assembles** existing ones into an investment case.

#### Step A: Select Candidates
*   **Input:** `Storyline 1 (Impact Potential)`
*   **Logic:** Select top N Livelihoods (`MdV`) with the highest `API` scores.

#### Step B: Build "Bundles" (Enrichment)
For each candidate MdV, attach its "support system":
1.  **Services:** Top services supporting this MdV (ranked by `SCI`).
2.  **Ecosystems:** Ecosystems providing those services (ranked by `ELI`).
3.  **Threats:** Top threats driving risk.
4.  **Equity:** Vulnerability score (`EVI`) for the affected groups.
5.  **Feasibility:** Social feasibility score (`Feasibility Index`).

#### Step C: Score & Rank Portfolio
*   **Formula:**
    ```python
    PortfolioScore = w1*Impact + w2*Leverage(SCI+ELI) + w3*Equity(EVI) + w4*Feasibility
    ```

#### Step D: Assign Tiers (The "Traffic Light")
*   **Logic:**
    *   **Do Now:** Top 33% of scores AND Conflict Risk < Threshold.
    *   **Do Next:** Middle 33% OR High Score but High Conflict Risk.
    *   **Do Later:** Bottom 33%.

### 3. Visual Connection Map (Mermaid)

```mermaid
graph TD
    %% INPUTS
    subgraph Inputs ["Previous Storylines"]
        S1[S1: Impact Potential]
        S2[S2: SCI & ELI]
        S3[S3: Equity EVI]
        S4[S4: Feasibility]
    end

    %% LOGIC
    subgraph Engine ["Portfolio Engine"]
        F_SEL[Select Candidates]
        F_BUN[Build Bundles]
        F_SCO[Score Portfolio]
        F_TIE[Assign Tiers]
    end

    %% OUTPUT
    subgraph Output ["Final Product"]
        P_NOW[Tier: Do Now]
        P_NXT[Tier: Do Next]
        P_LAT[Tier: Do Later]
    end

    S1 -->|"rank MdVs"| F_SEL
    
    F_SEL -->|"candidate MdVs"| F_BUN
    S2 -->|"enrich services/eco"| F_BUN
    S3 -->|"enrich equity"| F_BUN
    S4 -->|"enrich feasibility"| F_BUN
    
    F_BUN -->|"bundle objects"| F_SCO
    
    F_SCO -->|"portfolio score"| F_TIE
    
    F_TIE --> P_NOW
    F_TIE --> P_NXT
    F_TIE --> P_LAT
    
    classDef input fill:#e8daef,stroke:#333,stroke-width:1px,color:black;
    classDef engine fill:#fcf3cf,stroke:#333,stroke-width:1px,color:black;
    classDef output fill:#d6dbdf,stroke:#333,stroke-width:1px,color:black;
    
    class S1,S2,S3,S4 input;
    class F_SEL,F_BUN,F_SCO,F_TIE engine;
    class P_NOW,P_NXT,P_LAT output;
```
