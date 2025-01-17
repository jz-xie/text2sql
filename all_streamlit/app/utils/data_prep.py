import json
from sentence_transformers import SentenceTransformer
from pathlib import Path

from dataclasses import dataclass, field, asdict
from torch import Tensor

opensearch_property_type_text = {"opensearch_properties": {"type": "text"}}
opensearch_property_type_vector = {
    "opensearch_properties": {"type": "knn_vector", "dimension": 384}
}


@dataclass
class DDL:
    opensearch_index_name = "ddl"

    ddl: str = field(metadata=opensearch_property_type_text)
    ddl_emb: Tensor = field(metadata=opensearch_property_type_vector)


@dataclass
class Doc:
    opensearch_index_name = "doc"

    doc: str = field(metadata=opensearch_property_type_text)
    doc_emb: Tensor = field(metadata=opensearch_property_type_vector)


@dataclass
class QuestionSQL:
    opensearch_index_name = "question_sql"

    question: str = field(metadata=opensearch_property_type_text)
    question_emb: Tensor = field(metadata=opensearch_property_type_vector)
    sql: str = field(metadata=opensearch_property_type_text)
    # sql_emb: Tensor = field(metadata=opensearch_property_type_vector)


def generate_ddl(db_name: str = "superhero") -> list[DDL]:
    with open(f"{Path(__file__).parent}/../sample_data/dev_tables.json", "r") as file:
        data = json.load(file)

    db_data = [i for i in data if i["db_id"] == db_name][0]
    ddl_statements = []

    table_names = db_data["table_names_original"]
    column_names = db_data["column_names_original"]
    column_types = db_data["column_types"]

    for table_index in range(len(table_names)):
        table_name = table_names[table_index]

        ddl = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"

        columns = []

        for col_index in range(len(column_names)):
            if (
                column_names[col_index][0] == table_index
            ):  # Match column to the correct table
                col_name = column_names[col_index][1]
                col_type = column_types[col_index]  # Default to TEXT if type not found

                # Define primary key for id columns
                if col_name == "id":
                    column_definition = f"    {col_name} {col_type} PRIMARY KEY"
                else:
                    column_definition = f"    {col_name} {col_type}"

                columns.append(column_definition)

        ddl += ",\n".join(columns) + "\n);\n"

        ddl_statements.append(ddl)

    ddl_embeddings = generate_embeddings(ddl_statements)
    output = [
        asdict(DDL(ddl=ddl, ddl_emb=ddl_emb))
        for ddl, ddl_emb in zip(ddl_statements, ddl_embeddings)
    ]

    return output


def generate_question_sql(db_name: str = "superhero") -> list[QuestionSQL]:
    with open(f"{Path(__file__).parent}/../sample_data/dev.json", "r") as file:
        data = json.load(file)

    db_data = [i for i in data if i["db_id"] == db_name]
    questions = [i["question"] for i in db_data]
    sql_list = [i["SQL"] for i in db_data]
    question_emb_list = generate_embeddings(questions)

    output = [
        asdict(QuestionSQL(question=a, question_emb=b, sql=c))
        for a, b, c in zip(questions, question_emb_list, sql_list)
    ]

    return output


def generate_embeddings(texts: list[str]) -> list[float]:
    model = SentenceTransformer(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2"
    )
    output = model.encode(texts).tolist()
    return output