#!/bin/bash
# docker-test.sh: Build and test the Gatherings app in Docker
set -e

IMAGE_NAME=gatherings-mcp-test
CONTAINER_NAME=gatherings-mcp-test-container

# Build the Docker image
echo "Building Docker image..."
DOCKER_BUILDKIT=1 docker build -t $IMAGE_NAME .

# Remove any previous container with the same name
if docker ps -a --format '{{.Names}}' | grep -Eq "^$CONTAINER_NAME$"; then
    docker rm -f $CONTAINER_NAME
fi

# Run the test in a new container
echo "Running tests..."
docker run --name $CONTAINER_NAME \
    --rm $IMAGE_NAME \
    python /app/test_example.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Tests passed successfully!"
else
    echo "Tests failed with exit code $EXIT_CODE"
fi

# Optional: Run a quick test to ensure the MCP server starts correctly
echo "Testing MCP server startup..."
docker run --rm $IMAGE_NAME --version || {
    echo "MCP server failed to start properly!"
    exit 1
}

echo "All tests completed successfully!"
exit $EXIT_CODE
