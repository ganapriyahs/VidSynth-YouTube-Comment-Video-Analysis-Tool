FROM python:3.12-slim

WORKDIR /app

# Copy and install dependencies 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src directory
COPY src/ ./src/

# Setting working directory to src 
WORKDIR /app/src

# Creating output directory for persisted files
RUN mkdir /output

# Run all three scripts sequentially, then copy output to mounted volume (output)
CMD ["sh", "-c", "python initialize_validation_set.py && python generate_summaries_all_test.py && python validate_summaries.py && cp videoList.json log.txt /output/"]