FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy App
COPY pares_converter ./pares_converter

# Copy Storylines Pipelines (Critical for analysis modules)
COPY storyline1_pipeline ./storyline1_pipeline
COPY storyline2_pipeline ./storyline2_pipeline
COPY storyline3_pipeline ./storyline3_pipeline
COPY storyline4_pipeline ./storyline4_pipeline
COPY storyline5_pipeline ./storyline5_pipeline

# Copy Docs and Scripts
COPY scripts ./scripts
COPY docs ./docs
COPY README.md .

EXPOSE 8000
CMD ["uvicorn", "pares_converter.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
