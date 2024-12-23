from opensearchpy import OpenSearch, Index
from streamlit.connections import BaseConnection
from typing import Optional, Any
from streamlit.runtime.caching import cache_data
import logging
from vanna.base import VannaBase
import uuid
import pandas as pd
from typing import TypedDict
from utils import extract_table_metadata
import hashlib


class DDL(TypedDict):
    ddl: str


class Doc(TypedDict):
    doc: str


class QuestionSQL(TypedDict):
    question: str
    sql: str


class OpenSearch_VectorStore(VannaBase):
    def __init__(self, config: dict = {}):
        VannaBase.__init__(self, config=config)

        doc_index = Index("doc_index")
        doc_index.settings(number_of_shards=6, number_of_replicas=2)
        ddl_index: Index = doc_index.clone(name="ddl_index")
        question_sql_index: Index = doc_index.clone(name="question_sql_index")

        self.doc_index = doc_index
        self.ddl_index = ddl_index
        self.question_sql_index = question_sql_index

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

        # Create the indices if they don't exist
        for index in [self.doc_index, self.ddl_index, self.question_sql_index]:
            index.save(using=self.opensearch_client)

        self.n_results = config.get("n_results", 10)

    def add_ddl(self, ddl_list: list[DDL], **kwargs) -> str:
        body_list = []

        for ddl in ddl_list:
            id = hashlib.sha256(bytes(str(ddl), encoding="utf-8")).hexdigest() + "-ddl"
            action = {"index": {"_index": self.ddl_index._name, "_id": id}}

            table_metadata = extract_table_metadata(ddl)
            ddl_dict = {
                "schema": table_metadata.schema,
                "table_name": table_metadata.table_name,
                "ddl": ddl,
            }
            body_list.append(action)
            body_list.append(ddl_dict)

        response = self.opensearch_client.bulk(body=body_list)
        return response

    def add_documentation(self, doc_list: list[Doc], **kwargs) -> str:
        body_list = []

        for doc in doc_list:
            id = hashlib.sha256(bytes(str(doc), encoding="utf-8")).hexdigest() + "-doc"
            action = {"index": {"_index": self.doc_index._name, "_id": id}}
            body_list.append(action)
            body_list.append(doc)

        response = self.opensearch_client.bulk(body=body_list)

        return response

    def add_question_sql(self, pairs: list[QuestionSQL], **kwargs) -> str:
        # Assuming you have a Questions and SQL index in your OpenSearch
        body_list = []

        for pair in pairs:
            id = hashlib.sha256(bytes(str(pair), encoding="utf-8")).hexdigest() + "-sql"
            action = {"index": {"_index": self.doc_index._name, "_id": id}}
            body_list.append(action)
            body_list.append(pair)

        response = self.opensearch_client.bulk(body=body_list)

        return response

    def get_related_ddl(self, question: str) -> list[str]:
        # Assume you have some vector search mechanism associated with your data
        query = {"query": {"match": {"ddl": question}}, "size": self.n_results}
        print(query)
        response = self.opensearch_client.search(index=self.ddl_index._name, body=query)
        return [hit["_source"]["ddl"] for hit in response["hits"]["hits"]]

    def get_related_documentation(self, question: str) -> list[str]:
        query = {"query": {"match": {"doc": question}}, "size": self.n_results}
        print(query)
        response = self.opensearch_client.search(index=self.doc_index._name, body=query)
        return [hit["_source"]["doc"] for hit in response["hits"]["hits"]]

    def get_similar_question_sql(self, question: str) -> list[str]:
        query = {"query": {"match": {"question": question}}, "size": self.n_results}
        print(query)
        print(self.question_sql_index._name)
        response = self.opensearch_client.search(
            index=self.question_sql_index._name, body=query
        )
        return [
            (hit["_source"]["question"], hit["_source"]["sql"])
            for hit in response["hits"]["hits"]
        ]

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        # This will be a simple example pulling some data from an index
        data = []
        for index in [self.doc_index, self.doc_index, self.question_sql_index]:
            response = self.opensearch_client.search(
                index=index, body={"query": {"match_all": {}}}, size=10
            )
            match self.doc_index._name:
                case "question_sql_index":
                    content = "sql"
                case "doc":
                    content = "doc"
                case "ddl":
                    content = "ddl"
            for hit in response["hits"]["hits"]:
                data.append(
                    {
                        "id": hit["_id"],
                        "training_data_type": index._name,
                        "question": ""
                        if not content == "sql"
                        else hit.get("_source", {}).get("question", ""),
                        "content": hit["_source"][content],
                    }
                )

        return pd.DataFrame(data)

    def remove_training_data(self, id: str, **kwargs) -> bool:
        try:
            if id.endswith("-sql"):
                self.opensearch_client.delete(index=self.question_sql_index, id=id)
                return True
            elif id.endswith("-ddl"):
                self.opensearch_client.delete(index=self.ddl_index, id=id, **kwargs)
                return True
            elif id.endswith("-doc"):
                self.opensearch_client.delete(index=self.doc_index, id=id, **kwargs)
                return True
            else:
                return False
        except Exception as e:
            print("Error deleting training dataError deleting training data: ", e)
            return False

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        # opensearch doesn't need to generate embeddings
        pass


class OpenSearchConnection(BaseConnection[OpenSearch]):
    def _connect(self, host: str, port: int, user: str, password: str) -> OpenSearch:
        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(user, password),
            http_compress=True,  # enables gzip compression for request bodies
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        return client

    def query(
        self,
        *,
        index: str,
        query: Optional[dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> dict:
        """
        Queries an Opensearch index and returns the results as dict.

        Parameters
        ----------
        index: str
            Opensearch index to query.

        query: Dict[Any]
            Opensearch query to filter data in the index. Defaults to None, all data from the index gets fetched.

        ttl: int
            How long to keep data cached in seconds. Defaults to never

        Returns
        -------
        dict
        """

        @cache_data(show_spinner=True, ttl=ttl)
        def _query(index, query):
            response = self._instance.search(body=query, index=index)
            response

        return _query(index=index, query=query)
