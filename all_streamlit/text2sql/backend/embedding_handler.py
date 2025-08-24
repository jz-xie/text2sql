from text2sql.backend.connectors.clients import get_openai_embedding_client
from functools import lru_cache


@lru_cache
def generate_embeddings_openai(
    input: str | tuple[str],
) -> list[float] | list[list[float]]:
    # model = SentenceTransformer(
    #     model_name_or_path="sentence-transformers/all-MiniLM-L6-v2"
    # )
    # output = model.encode(texts).tolist()
    # SentenceTransformer hugging face has a certificate issue behind our corporate proxy
    client = get_openai_embedding_client()
    if isinstance(input, str):
        response = client.embeddings.create(input=input, model="text-embedding-ada-002")
        output = response.data[0].embedding
    else:
        list_input = list(input)
        response = client.embeddings.create(
            input=list_input, model="text-embedding-ada-002"
        )
        output = [i.embedding for i in response.data]

    return output
