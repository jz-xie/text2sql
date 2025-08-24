from dataclasses import dataclass, field

from functools import lru_cache

from text2sql.backend.connectors.clients import get_opensearch_client
from text2sql.backend.embedding_handler import generate_embeddings_openai

n_results = 5
opensearch_client = get_opensearch_client()

opensearch_property_type_text = {"opensearch_properties": {"type": "text"}}
opensearch_property_type_vector = {
    "opensearch_properties": {
        "type": "knn_vector",
        "dimension": 1536,
    }  # The default length of the embedding vector from OpenAI text-embedding-3-small
}


@dataclass
class DDL:
    opensearch_index_name = "ddl"
    display_name = "DDL"

    ddl: str = field(metadata=opensearch_property_type_text)
    ddl_emb: list[float] = field(
        default_factory=list, metadata=opensearch_property_type_vector
    )


@dataclass
class Doc:
    opensearch_index_name = "doc"
    display_name = "Documentation"

    doc: str = field(metadata=opensearch_property_type_text)
    doc_emb: list[float] = field(
        default_factory=list, metadata=opensearch_property_type_vector
    )


@dataclass
class QuestionSQL:
    opensearch_index_name = "question_sql"
    display_name = "Verified Questions & SQL"

    question: str = field(metadata=opensearch_property_type_text)
    sql: str = field(metadata=opensearch_property_type_text)
    question_emb: list[float] = field(
        default_factory=list, metadata=opensearch_property_type_vector
    )
    # sql_emb: list[float] = field(metadata=opensearch_property_type_vector)


@lru_cache
def get_related_ddl(question: str) -> list[str]:
    embeddings = generate_embeddings_openai(question)

    query = {
        "query": {"knn": {"ddl_emb": {"vector": embeddings, "k": n_results}}},
        "_source": ["ddl"],
    }
    response = opensearch_client.search(index=DDL.opensearch_index_name, body=query)
    return [hit["_source"]["ddl"] for hit in response["hits"]["hits"]]


@lru_cache
def get_related_documentation(question: str) -> list[dict]:
    embeddings = generate_embeddings_openai(question)

    query = {
        "query": {"knn": {"doc_emb": {"vector": embeddings, "k": n_results}}},
        "_source": ["doc"],
    }
    response = opensearch_client.search(index=Doc.opensearch_index_name, body=query)
    return [hit["_source"]["doc"] for hit in response["hits"]["hits"]]


@lru_cache
def get_similar_question_sql(question: str) -> list[dict]:
    embeddings = generate_embeddings_openai(question)

    query = {
        "query": {"knn": {"question_emb": {"vector": embeddings, "k": n_results}}},
        "_source": ["question", "sql"],
    }
    response = opensearch_client.search(
        index=QuestionSQL.opensearch_index_name, body=query
    )
    return [
        {"question": hit["_source"]["question"], "sql": hit["_source"]["sql"]}
        for hit in response["hits"]["hits"]
    ]
