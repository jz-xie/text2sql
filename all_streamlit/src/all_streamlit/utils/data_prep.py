import json
from sentence_transformers import SentenceTransformer
from pathlib import Path

from typing import TypedDict
from torch import Tensor


class DDL(TypedDict):
    ddl: str
    ddl_emb: Tensor


class Doc(TypedDict):
    doc: str
    doc_emb: Tensor


class QuestionSQL(TypedDict):
    question: str
    question_emb: Tensor
    sql: str
    sql_emb: Tensor


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
        {"ddl": ddl, "ddl_emb": ddl_emb}
        for ddl, ddl_emb in zip(ddl_statements, ddl_embeddings)
    ]

    return output


def generate_question_sql(db_name: str = "superhero") -> list[QuestionSQL]:
    with open(f"{Path(__file__).parent}/../sample_data/dev.json", "r") as file:
        data = json.load(file)

    db_data = [i for i in data if i["db_id"] == db_name]
    questions = [i["question"] for i in db_data]
    sql_list = [i["sql"] for i in db_data]
    question_emb_list = generate_embeddings(questions)
    sql_emb_list = generate_embeddings(sql_list)

    output = [
        {"question": a, "question_emb": b, "sql": c, "sql_emb": d}
        for a, b, c, d in zip(questions, question_emb_list, sql_list, sql_emb_list)
    ]

    return output


def generate_embeddings(texts: list[str]):
    model = SentenceTransformer(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2"
    )
    output = model.encode(texts)
    return output
