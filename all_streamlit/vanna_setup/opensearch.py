from opensearchpy import OpenSearch, Index
from streamlit.connections import BaseConnection
from typing import Optional, Any
from streamlit.runtime.caching import cache_data
import logging
from vanna.base import VannaBase
import uuid

from typing import TypedDict


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

        host = config.get("host", "localhost")
        port = config.get("port", "9200")
        username = config.get("username")
        password = config.get("host")

        self.client = OpenSearch(
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
            index.save(using=self.client)

        self.n_results = config.get("n_results", 10)

    def add_ddl(self, ddl_list: list[DDL], **kwargs) -> str:
        body_list = []

        for ddl in ddl_list:
            id = str(uuid.uuid4()) + "-ddl"
            action = {"index": {"_index": self.ddl_index._name, "_id": id}}

            table_metadata = VannaBase.extract_table_metadata(ddl)
            ddl_dict = {
                "schema": table_metadata.schema,
                "table_name": table_metadata.table_name,
                "ddl": ddl["ddl"],
            }
            body_list.append(f"{str(action)}\n{str(ddl_dict)}")

        body_str = "\n".join(body_list)
        response = self.client.bulk(body=body_str)

        return response["_id"]

    def add_documentation(self, doc_list: list[Doc], **kwargs) -> str:
        body_list = []

        for doc in doc_list:
            id = str(uuid.uuid4()) + "-doc"
            action = {"index": {"_index": self.doc_index._name, "_id": id}}
            body_list.append(f"{str(action)}\n{str(doc)}")

        body_str = "\n".join(body_list)
        response = self.client.bulk(body=body_str)

        return response["_id"]

    def add_question_sql(self, pairs: list[QuestionSQL], **kwargs) -> str:
        # Assuming you have a Questions and SQL index in your OpenSearch
        body_list = []

        for pair in pairs:
            id = str(uuid.uuid4()) + "-sql"
            action = {"index": {"_index": self.doc_index._name, "_id": id}}
            body_list.append(f"{str(action)}\n{str(pair)}")

        body_str = "\n".join(body_list)
        response = self.client.bulk(body=body_str)

        return response["_id"]

    def get_related_ddl(self, question: str, **kwargs) -> list[str]:
        # Assume you have some vector search mechanism associated with your data
        query = {"query": {"match": {"ddl": question}}, "size": self.n_results}
        print(query)
        response = self.client.search(index=self.ddl_index, body=query, **kwargs)
        return [hit["_source"]["ddl"] for hit in response["hits"]["hits"]]

    def get_related_documentation(self, question: str, **kwargs) -> list[str]:
        query = {"query": {"match": {"doc": question}}, "size": self.n_results}
        print(query)
        response = self.client.search(index=self.doc_index, body=query, **kwargs)
        return [hit["_source"]["doc"] for hit in response["hits"]["hits"]]

    def get_similar_question_sql(self, question: str, **kwargs) -> list[str]:
        query = {"query": {"match": {"question": question}}, "size": self.n_results}
        print(query)
        response = self.client.search(
            index=self.question_sql_index, body=query, **kwargs
        )
        return [
            (hit["_source"]["question"], hit["_source"]["sql"])
            for hit in response["hits"]["hits"]
        ]


class OpenSearchConnection(BaseConnection[OpenSearch]):
    def _connect(self, host: str, port: int, user: str, password: str) -> OpenSearch:
        secrets = self._secrets.to_dict()
        secrets["localhost"]
        secrets["port"]
        secrets["user"]
        secrets["password"]

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


# # Create the client with SSL/TLS and hostname verification disabled.
# client = OpenSearch(
#     hosts=[{"host": "localhost", "port": 9200}],
#     http_auth=("admin", "PasASDWAW1111!"),
#     http_compress=True,  # enables gzip compression for request bodies
#     use_ssl=True,
#     verify_certs=False,
#     ssl_assert_hostname=False,
#     ssl_show_warn=False,
# )
