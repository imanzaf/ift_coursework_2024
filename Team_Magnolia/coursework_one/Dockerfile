# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy project files
COPY . .

# Ensure dependencies are installed
RUN pip install --no-cache-dir -r requirements.txt

# Expose necessary ports
EXPOSE 8000  # FastAPI
EXPOSE 8501  # Streamlit

# Default command: Run FastAPI + Streamlit
CMD ["uvicorn", "modules.api.fastapi_api:app", "--host", "0.0.0.0", "--port", "8000"]

WORKDIR /app
COPY Magnolia/coursework_one/modules/scraper /app/