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
# Use the Python interpreter from the image
echo "Running tests..."
docker run --name $CONTAINER_NAME \
    --entrypoint python3 \
    --rm $IMAGE_NAME \
    /app/test_example.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Tests passed successfully!"
else
    echo "Tests failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
