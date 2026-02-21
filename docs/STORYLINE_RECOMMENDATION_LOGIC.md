# Logic for Generating Storyline Recommendations

This document explains **how the system generates recommendations** for the final report.

The recommendation engine is split into two distinct parts:

1.  **Storyline 1 (Prioritization)**: Identifies _where_ to act (which Livelihoods).
2.  **Storyline 5 (Portfolio)**: Identifies _what_ to do (Interventions) and assigns a "Do Now / Do Next" tier.

---

## Part 1: Prioritization (Storyline 1)

**Goal:** Rank livelihoods (MdV) by urgency.

The system calculates an **Action Priority Index (IPA/API)** for every livelihood in every community.
Formula:

```python
IPA Score = (w1 * Priority) + (w2 * Risk) + (w3 * Capacity_Gap)
```

- **Priority (40%)**: How important is this livelihood to the community? (Source: Workshop voting)
- **Risk (40%)**: How threatened is it by climate/non-climate hazards? (Source: Threat Matrix)
- **Capacity Gap (20%)**: How unprepared is the community to adapt? (Source: Resilience Survey)

_Result:_ A ranked list of livelihoods. The Top 10 are passed to Storyline 5.

---

## Part 2: Portfolio Construction (Storyline 5)

**Goal:** Turn the prioritized livelihoods into a concrete action plan with specific interventions.

This is where the complex logic resides (`storyline5/portfolio.py`).

### Step A: The "Bundle" Construction

For each Priority Livelihood, the system builds a "bundle" of related data:

1.  **Ecosystem Services**: What services does this livelihood depend on? (e.g., Water provision)
2.  **Ecosystems**: Which ecosystems provide those services? (e.g., Cloud Forest)
3.  **Threats**: What is killing those ecosystems? (e.g., Deforestation, Drought)

### Step B: Scoring the Intervention

The system then scores the potential intervention based on 4 criteria:

1.  **Impact Potential**: (Inherited from Storyline 1 IPA Score).
2.  **Leverage (ELI)**: Does this ecosystem supports _many_ other livelihoods? (High leverage = better investment).
3.  **Equity (EVI)**: Does this intervention help vulnerable groups (women, youth, indigenous)?
4.  **Feasibility**: Is there high conflict or low governance in this area? (Acts as a penalty).

### Step C: The "Do Now / Do Next" Logic (Tier Assignment)

This is the core decision matrix used to assign the recommendation tier:

| Tier       | Name                       | Criteria Logic                                                                                           |
| :--------- | :------------------------- | :------------------------------------------------------------------------------------------------------- |
| **Tier 1** | **DO NOW (Inmediato)**     | High Urgency AND High Feasibility.<br>`(API > 0.7) AND (Feasibility > 0.6)`                              |
| **Tier 2** | **DO NEXT (Corto Plazo)**  | High Urgency BUT Low Feasibility (needs governance work first).<br>`(API > 0.7) AND (Feasibility < 0.6)` |
| **Tier 3** | **DO LATER (Largo Plazo)** | Lower Urgency, good for strategic planning.<br>`(API < 0.7)`                                             |

### Step D: The Conflict Gate

_Special Rule:_ If **Conflict Risk** is "Critical" (Score > 0.8), the recommendation is **automatically downgraded** or flagged with a "Go/No-Go" warning, regardless of its priority. This ensures "Do No Harm".

---

## 3. The Interactive Dashboard (Simplified Logic)

**Important Distinction:** The interactive HTML Dashboard uses a **simplified logic** compared to the full PDF report.

- **Report Logic**: Uses the full algorithm above (Tiers 1-3, Conflict Gates).
- **Dashboard Logic**:
  1.  Takes the **Top 6 Livelihoods** sorted by `i_total` (Importance).
  2.  For each, it looks up the **Primary Ecosystem Service**.
  3.  It identifies the **Top Threat** to that service.
  4.  It links this to a generic solution.

### Visual Representation in Dashboard

In the dashboard (`dashboard_template.html`), the cards are generated via JavaScript:

```javascript
// Simplified Dashboard Logic (pseudo-code)
const top_mdvs = livelihoods.sort((a, b) => b.i_total - a.i_total).slice(0, 6);

top_mdvs.forEach((mdv) => {
  DisplayCard({
    title: mdv.nombre,
    badge: "Prioridad Alta",
    icon: GetIcon(mdv.sector),
    // HARDCODED placeholder in current version:
    action: "SbN / Restauración",
  });
});
```

_Note: The dashboard is designed for rapid exploration, while the Storyline 5 Report is for detailed investment planning._

### Why was this hardcoded? (Technical Disconnect)

The Dashboard Generator (`dashboard_generator.py`) was designed as a lightweight, pre-computation viewer. It reads directly from the **Input Excel** (Pre-Analysis) to generate the visualization.

However, the specific recommendation logic (e.g., assigning "Restoration" vs "Agroforestry") happens in the **Storyline 5 Pipeline** (`storyline5/portfolio.py`), which generates the **Output Reports** (Post-Analysis).

Because the Dashboard Generator does not execute the Storyline 5 pipeline, it does not have access to the computed "Intervention Type" column. Therefore, `"SbN / Restauración"` was likely used as a **static placeholder** during development to demonstrate the UI layout without requiring the full heavy machinery of the analysis pipeline to be connected to the real-time dashboard.

## 7. Key Literature References

While the project does not contain a bibliography database or PDF files, the core logic is explicitly built upon three international frameworks (as documented in `docs/RESUMEN_EJECUTIVO.md`):

1.  **IUCN Global Standard for Nature-based Solutions (v2.0)**
    - _Usage:_ Guides the prioritization of co-benefits (biodiversity + human well-being) in Storylines 1 & 2.
    - _Source:_ [IUCN Global Standard](https://iucn.org/our-work/topic/iucn-global-standard-nature-based-solutions)

2.  **IPCC AR6 Working Group II (Impacts, Adaptation, and Vulnerability)**
    - _Usage:_ Defines the vulnerability framework (Exposure, Sensitivity, Adaptive Capacity) used in Storyline 1.
    - _Source:_ [IPCC AR6 WGII](https://www.ipcc.ch/report/ar6/wg2/)

3.  **UK Government Multi-Criteria Decision Analysis (MCDA)**
    - _Usage:_ Provides the mathematical basis for the "Action Priority Index" (IPA) and the sensitivity analysis (weighting scenarios).
    - _Source:_ [UK Gov MCDA Guide](https://analysisfunction.civilservice.gov.uk/policy-store/an-introductory-guide-to-mcda/)
