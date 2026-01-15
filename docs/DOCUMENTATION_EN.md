# PARES Excel Converter

## Documentation (English)

### What is this converter?
The **PARES Excel Converter** is a specialized tool designed to bridge the gap between raw data collection and structured analysis in the context of the PARES SES (Social-Ecological Systems) framework. It automates the transformation of Excel workbooks from a source format (specifically those structured like the **TIERRAVIVA** database) into a standardized, analysis-ready template (**FINAL_SES**).

### Why do we need it?
1.  **Standardization**: Raw field data is often collected in formats that are user-friendly for data entry but difficult for automated analysis engines or visualization tools to process. This tool ensures that every dataset follows a rigorous, uniform structure.
2.  **Complex Data Mapping**: The converter handles complex translation rules, such as:
    *   **One-to-Many Relationships**: Expanding a single row of survey data into multiple tidy records based on specific categories like "Medios de Vida" (Livelihoods).
    *   **Deterministic ID Generation**: Creating unique, stable identifiers (UIDs) for ecosystems, actors, and threats to ensure consistency across different versions of the data.
    *   **Cross-Module Linking**: Automatically relating actors to specific livelihoods or threats based on keyword matching and predefined logic.
3.  **Efficiency and Accuracy**: Manual conversion of these workbooks is time-consuming and prone to human error. Automation ensures that data integrity is maintained, and Quality Assurance (QA) issues are flagged immediately (e.g., missing sheets or inconsistent references).
4.  **Premium Workflow**: By providing both a modern web interface and a robust API, the tool integrates seamlessly into the broader SES analysis suite, allowing researchers to quickly prepare their data for high-fidelity dashboards and reports.

### Key Features
*   **Module Transformation**: Supports conversion for Livelihoods (MdV), Ecosystems (SE), Threats, Actors, and Dialogue spaces.
*   **Tidy Table Generation**: Produces "tidy" datasets that are optimized for statistical analysis and visualization.
*   **QA Logging**: Includes metadata in the output (GeoId, QA issue count) to track the health of the converted data.
