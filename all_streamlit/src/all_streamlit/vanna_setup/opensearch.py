import hashlib
import logging
import uuid
from typing import Any, Optional

import pandas as pd
from opensearchpy import Index, OpenSearch
from streamlit.connections import BaseConnection
from streamlit.runtime.caching import cache_data
from utils.data_prep import DDL, Doc, QuestionSQL
from utils.utils import extract_table_metadata
from vanna.base import VannaBase


class OpenSearch_VectorStore(VannaBase):
    def __init__(self, config: dict = {}):
        VannaBase.__init__(self, config=config)

        client = config.get("client", None)
        if isinstance(client, OpenSearch):
            # allow providing client directly
            self.opensearch_client = client
        else:
            host = config.get("host", "localhost")
            port = config.get("port", "9200")
            username = config.get("username", "admin")
            password = config.get("password")

            self.opensearch_client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                http_auth=(username, password),
                http_compress=True,  # enables gzip compression for request bodies
                use_ssl=True,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )

        indices = [Doc, DDL, QuestionSQL]
        for index in indices:
            if not self.opensearch_client.exists(index=index.opensearch_index_name):
                create_index(
                    client=self.opensearch_client,
                    index_name=index.opensearch_index_name,
                    index_target=index,
                )

        self.doc_index_name = Doc.opensearch_index_name
        self.ddl_index_name = DDL.opensearch_index_name
        self.question_sql_index_name = QuestionSQL.opensearch_index_name

        self.n_results = config.get("n_results", 10)

    def add_ddl(self, ddl_list: list[dict]) -> str:
        for ddl in ddl_list:
            table_metadata = extract_table_metadata(ddl)
            ddl.update(
                {
                    "schema": table_metadata.schema,
                    "table_name": table_metadata.table_name,
                }
            )

        response = index_dococument(
            client=self.opensearch_client,
            index_name=self.ddl_index_name,
            doc_list=ddl_list,
        )
        return response

    def add_documentation(self, doc_list: list[dict]) -> str:
        response = index_dococument(
            client=self.opensearch_client,
            index_name=self.doc_index_name,
            doc_list=doc_list,
        )
        return response

    def add_question_sql(self, pairs: list[dict]) -> str:
        response = index_dococument(
            client=self.opensearch_client,
            index_name=self.question_sql_index_name,
            doc_list=pairs,
        )
        return response

    def get_related_ddl(self, question: str) -> list[str]:
        # Assume you have some vector search mechanism associated with your data
        query = {"query": {"match": {"ddl": question}}, "size": self.n_results}
        print(query)
        response = self.opensearch_client.search(index=self.ddl_index_name, body=query)
        return [hit["_source"]["ddl"] for hit in response["hits"]["hits"]]

    def get_related_documentation(self, question: str) -> list[str]:
        query = {"query": {"match": {"doc": question}}, "size": self.n_results}
        print(query)
        response = self.opensearch_client.search(index=self.doc_index_name, body=query)
        return [hit["_source"]["doc"] for hit in response["hits"]["hits"]]

    def get_similar_question_sql(self, question: str) -> list[str]:
        query = {"query": {"match": {"question": question}}, "size": self.n_results}
        print(query)
        print(self.question_sql_index_name)
        response = self.opensearch_client.search(
            index=self.question_sql_index_name, body=query
        )
        return [
            (hit["_source"]["question"], hit["_source"]["sql"])
            for hit in response["hits"]["hits"]
        ]

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        # This will be a simple example pulling some data from an index
        data = []
        search_body = []
        for index_name in [
            self.doc_index_name,
            self.ddl_index_name,
            self.question_sql_index_name,
        ]:
            search_body += [
                {"index": index_name},
                {"query": {"match_all": {}}, "size": 10},
            ]

        response = self.opensearch_client.msearch(body=search_body)
        data = [
            {
                "id": hit["_id"],
                "index": hit["_index"],
                "source": hit["_source"],
            }
            for hit in response["hits"]["hits"]
        ]

        return pd.DataFrame(data)

    def remove_training_data(self, index:str, id: str, **kwargs) -> bool:
        try:
            self.opensearch_client.delete(index=index, id=id)
            return True
        except Exception as e:
            Exception("Error deleting training dataError deleting training data: ", e)
            return False

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        # opensearch doesn't need to generate embeddings
        pass


def index_dococument(client: OpenSearch, index_name: str, doc_list: list[dict]):
    body_list = []

    for doc in doc_list:
        id = hashlib.sha256(bytes(str(doc), encoding="utf-8")).hexdigest()
        action = {"index": {"_index": index_name, "_id": id}}
        body_list.append(action)
        body_list.append(doc)

    response = client.bulk(body=body_list)

    return response


def create_index(client: OpenSearch, index_name: str, index_target):
    index_name
    index_body = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "index": {"knn": True},
        },
        "mappings": {
            "properties": {
                i: j.metadata["opensearch_properties"]
                for i, j in index_target.__dataclass_fields__.items()
            }
        },
    }
    response = client.indices.create(index_name, body=index_body)
    return response
