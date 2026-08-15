class EmbeddingService:
    """Placeholder boundary for embedding provider behavior.

    The current vector store owns sentence-transformer embedding. This service marks the dependency
    boundary so batching, provider swaps, and retries can be added without changing routes.
    """

