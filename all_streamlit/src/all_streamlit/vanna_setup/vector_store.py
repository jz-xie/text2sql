import hashlib

import pandas as pd
from opensearchpy import OpenSearch
from vanna.base import VannaBase
from sentence_transformers import SentenceTransformer
from typing import Any
from all_streamlit.data_prep import DDL, Doc, QuestionSQL


class OpenSearch_VectorStore(VannaBase):
    def __init__(self, client: OpenSearch, config: dict = {}):
        VannaBase.__init__(self, config=config)

        self.opensearch_client = client
        self.doc_index_name = Doc.opensearch_index_name
        self.ddl_index_name = DDL.opensearch_index_name
        self.question_sql_index_name = QuestionSQL.opensearch_index_name

        self.n_results = config.get("n_results", 10)

    def get_related_ddl(self, question: str, **kwargs: Any) -> list[str]:
        # Assume you have some vector search mechanism associated with your data
        if "embeddings" in kwargs:
            embeddings = kwargs.get("embeddings")
        else:
            raise Exception("Embeddings Not Provided")

        query = {
            "query": {"knn": {"ddl_emb": {"vector": embeddings, "k": self.n_results}}},
            "_source": ["ddl"],
        }
        response = self.opensearch_client.search(index=self.ddl_index_name, body=query)
        return [hit["_source"]["ddl"] for hit in response["hits"]["hits"]]

    def get_related_documentation(self, question: str, **kwargs: Any) -> list[str]:
        if "embeddings" in kwargs:
            embeddings = kwargs.get("embeddings")
        else:
            raise Exception("Embeddings Not Provided")
        query = {
            "query": {"knn": {"doc_emb": {"vector": embeddings, "k": self.n_results}}},
            "_source": ["doc"],
        }
        response = self.opensearch_client.search(index=self.doc_index_name, body=query)
        return [hit["_source"]["doc"] for hit in response["hits"]["hits"]]

    def get_similar_question_sql(self, question: str, **kwargs: Any) -> list[str]:
        if "embeddings" in kwargs:
            embeddings = kwargs.get("embeddings")
        else:
            raise Exception("Embeddings Not Provided")
        query = {
            "query": {
                "knn": {"question_emb": {"vector": embeddings, "k": self.n_results}}
            },
            "_source": ["question", "sql"],
        }
        response = self.opensearch_client.search(
            index=self.question_sql_index_name, body=query
        )
        return [
            {"question": hit["_source"]["question"], "sql": hit["_source"]["sql"]}
            for hit in response["hits"]["hits"]
        ]

    def remove_training_data(self, index: str, id: str, **kwargs) -> bool:
        try:
            self.opensearch_client.delete(index=index, id=id)
            return True
        except Exception as e:
            Exception("Error deleting training dataError deleting training data: ", e)
            return False

    def add_ddl(self, ddl: str, **kwargs) -> str:
        pass

    def add_documentation(self, documentation: str, **kwargs) -> str:
        pass

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        pass

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        pass

    def generate_embedding(self, data: str, **kwargs):
        pass
