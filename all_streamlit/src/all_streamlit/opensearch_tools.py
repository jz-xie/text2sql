from opensearchpy import OpenSearch
import hashlib
import pandas as pd
from all_streamlit.data_prep import DDL, Doc, QuestionSQL


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


def prepare(client: OpenSearch):
    indices = [Doc, DDL, QuestionSQL]
    for index in indices:
        if not client.indices.exists(index=index.opensearch_index_name):
            create_index(
                client=client,
                index_name=index.opensearch_index_name,
                index_target=index,
            )


def get_training_data(client: OpenSearch) -> pd.DataFrame:
    # This will be a simple example pulling some data from an index
    data = []
    search_body = []
    for index_name in [
        "ddl",
        "doc",
        "question_sql",
    ]:
        search_body += [
            {"index": index_name},
            {"query": {"match_all": {}}, "size": 10},
        ]

    response = client.msearch(body=search_body)
    data = [
        {
            "id": hit["_id"],
            "index": hit["_index"],
            "source": hit["_source"],
        }
        for hit in response["hits"]["hits"]
    ]

    return pd.DataFrame(data)