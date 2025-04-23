FROM python:3.10-slim

# Install dependencies for SQLite
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy Python requirements and install dependencies using uv
COPY requirements.txt .
RUN python -m pip install --upgrade pip uv && \
    uv pip install --system -r requirements.txt

# Copy all app files
COPY gatherings.py models.py services.py gatherings_mcp_server.py ./
# Copy test files
COPY test_example.py ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    GATHERINGS_DB_PATH=/data/gatherings.db \
    GATHERINGS_SCRIPT=/app/gatherings.py

# Create volume for data persistence
VOLUME /data

# Default command to run the MCP server
ENTRYPOINT ["python", "gatherings_mcp_server.py"]

# Add metadata labels
LABEL org.opencontainers.image.title="Gatherings MCP Server"
LABEL org.opencontainers.image.description="A Model Context Protocol server for managing gatherings and expense sharing"
LABEL org.opencontainers.image.licenses="Apache-2.0"