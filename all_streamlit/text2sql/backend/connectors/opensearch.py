import logging
from dataclasses import asdict
from hashlib import blake2b
from pathlib import Path

from opensearchpy import OpenSearch

from text2sql.backend.data_prep import (
    DDL,
    Doc,
    QuestionSQL,
    get_ddl,
    get_finance_context,
    get_verified_questions,
)

logger = logging.getLogger(__name__)
training_data_folder = f"{Path(__file__).parents[3]}/training_data"


def index_dococument(client: OpenSearch, index_name: str, doc_list: list[dict]):
    body_list = []

    for doc in doc_list:
        id = blake2b(str(doc).encode("utf-8")).hexdigest()

        action = {"index": {"_index": index_name, "_id": id}}
        body_list.append(action)
        body_list.append(doc)

    response = client.bulk(body=body_list)

    success_count = 0
    failure_count = 0
    failures = []

    for i, item_res in enumerate(response["items"]):
        if item_res["index"]["status"] < 300:
            success_count += 1
        else:
            failure_count += 1
            failures.append({"error_item": body_list[2 * i + 1], "reason": item_res})

    summary = {
        "total": len(doc_list),
        "successful": success_count,
        "failed": failure_count,
    }

    logger.info(f"Opensearch Indexing Summary: {str(summary)}")

    if failure_count != 0:
        logger.error(f"Opensearch Indexing Error: {str(failures)}")

    return summary


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


def init_indices(client: OpenSearch):
    for index in [Doc, DDL, QuestionSQL]:
        index_name = index.opensearch_index_name
        if not client.indices.exists(index=index_name):
            create_index(
                client=client,
                index_name=index_name,
                index_target=index,
            )
            logger.info(f"New Index Created: {index_name}")

            match index_name:
                case "ddl":
                    with open(f"{training_data_folder}/sql_tables.txt") as f:
                        ddl = f.read()
                        data = get_ddl(ddl)
                case "question_sql":
                    with open(f"{training_data_folder}/examples.txt") as f:
                        questions = f.read()
                        data = get_verified_questions(questions)
                case "doc":
                    data = get_finance_context()

            data_list_dict = [asdict(i) for i in data]
            index_dococument(client, index_name, data_list_dict)

            logger.info(f"Initiate Index Data: {index_name}")
        else:
            logger.info(f"Index Exists: {index_name}")

        logger.info(client.indices.get_mapping(index_name))
