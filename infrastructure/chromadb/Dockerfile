# ChromaDB Production Deployment Dockerfile
# Based on official chromadb/chroma image with production optimizations

FROM chromadb/chroma:0.4.15

# Set production environment variables
ENV CHROMA_HOST_PORT=8000
ENV CHROMA_HOST_ADDR=0.0.0.0
ENV CHROMA_WORKERS=1
ENV CHROMA_LOG_LEVEL=INFO

# Create data directory with proper permissions
RUN mkdir -p /chroma/chroma && \
    chown -R chroma:chroma /chroma

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/heartbeat || exit 1

# Use non-root user for security
USER chroma

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "chromadb.app:app", "--host", "0.0.0.0", "--port", "8000"]