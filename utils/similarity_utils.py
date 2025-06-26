import numpy as np
from app.config import settings


EMBEDDING_MODEL = settings.EMBEDDING_MODEL
SIMILARITY_THRESHOLD = settings.SIMILARITY_THRESHOLD


def fetch_embedding(text, provider='openai', model=EMBEDDING_MODEL):
    """
    Fetch embedding for the given text using the specified provider/model.
    Updated for openai>=1.0.0
    """
    if provider == 'openai':
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_KEY)
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    # Add other providers if needed
    raise NotImplementedError(f"Embedding provider {provider} not implemented.")


def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def find_similar_problems(problem_text, db_session=None, exclude_ids=None, threshold=SIMILARITY_THRESHOLD):
    """
    Given a problem text, fetch its embedding and compare to all existing problems.
    Returns a dict: {problem_id: similarity_score, ...} for all above threshold.
    
    Args:
        problem_text (str): The text to find similar problems for
        db_session: SQLAlchemy session (optional, for testing)
        exclude_ids (list): List of problem IDs to exclude
        threshold (float): Similarity threshold
    
    Returns:
        tuple: (similar_problems_dict, embedding)
    """
    if exclude_ids is None:
        exclude_ids = []
    
    embedding = fetch_embedding(problem_text)
    similars = {}
    
    # If no database session provided, return empty results
    if db_session is None:
        return similars, embedding
    
    # Import here to avoid circular imports
    from ..models import Problem
    
    # Query all problems with embeddings, excluding specified IDs
    problems = db_session.query(Problem).filter(
        Problem.id.notin_(exclude_ids),
        Problem.problem_embedding.isnot(None)
    ).all()
    
    for prob in problems:
        if prob.problem_embedding:
            sim = cosine_similarity(embedding, prob.problem_embedding)
        if sim >= threshold:
            similars[prob.id] = sim
    
    return similars, embedding 