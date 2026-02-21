
import os
import json
import logging
from pares_converter.app.dashboard_generator import generate_dashboard

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_generation():
    # Input file (assuming it exists from previous context)
    input_file = "FINAL_ADEL_analysis_ready.xlsx"
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    output_dir = "test_output_v2"
    
    logger.info(f"Generating dashboard from {input_file}...")
    try:
        html_path, bundle_path, qa_path = generate_dashboard(input_file, output_dir)
        logger.info(f"Dashboard generated at: {html_path}")
        logger.info(f"Bundle generated at: {bundle_path}")
        
        # Verify Bundle Content
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
            
        contexts = bundle.get("contexts", [])
        logger.info(f"Number of contexts: {len(contexts)}")
        if len(contexts) == 1 and contexts[0]["context_id"] == "CTX_GLOBAL":
            logger.info("SUCCESS: Single global context found.")
            for k in contexts[0]:
                logger.info(f"Context {k}: {contexts[0][k]}")
        else:
            logger.error(f"FAILURE: Expected 1 context 'CTX_GLOBAL', found {len(contexts)}: {[c.get('context_id') for c in contexts]}")

        # Check KPIs
        kpis = bundle.get("kpis", {})
        if "CTX_GLOBAL" in kpis:
            logger.info(f"KPIs for CTX_GLOBAL: {kpis['CTX_GLOBAL']}")
        else:
            logger.error("FAILURE: Missing KPIs for CTX_GLOBAL")

    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)

if __name__ == "__main__":
    test_generation()
