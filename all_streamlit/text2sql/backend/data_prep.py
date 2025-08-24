import re
from dataclasses import dataclass, field
from pathlib import Path

from text2sql.backend.connectors.clients import get_openai_embedding_client

opensearch_property_type_text = {"opensearch_properties": {"type": "text"}}
opensearch_property_type_vector = {
    "opensearch_properties": {
        "type": "knn_vector",
        "dimension": 1536,
    }  # The default length of the embedding vector from OpenAI text-embedding-3-small
}
training_data_folder = f"{Path(__file__).parents[2]}/training_data"


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


def prepare_ddl(ddl: str) -> list:
    ddl_list = re.split("\n*/\n|\n\n", ddl)[1::2]
    return ddl_list


def prepare_verified_questions(questions: str) -> list:
    pairs = questions.split(";")
    qn_list = []
    sql_list = []
    for pair in pairs[:-1]:
        items = pair.strip("\n\n").split("\n\n")
        question, sql = items[0].strip("Question: "), items[1]
        qn_list.append(question)
        sql_list.append(sql)
    return qn_list, sql_list


def prepare_doc(doc: str) -> list:
    doc_list = doc.split("\n\n")
    return doc_list


def get_ddl(ddl: str) -> list[DDL]:
    ddl_list = prepare_ddl(ddl)
    ddl_embeddings = generate_embeddings(ddl_list)
    output = [
        DDL(ddl=ddl, ddl_emb=ddl_emb) for ddl, ddl_emb in zip(ddl_list, ddl_embeddings)
    ]
    return output


def get_verified_questions(questions: str) -> list[QuestionSQL]:
    qn_list, sql_list = prepare_verified_questions(questions)

    embeddings = generate_embeddings(qn_list)
    output = [
        QuestionSQL(question=a, sql=b, question_emb=c)
        for a, b, c in zip(qn_list, sql_list, embeddings)
    ]
    return output


def get_documentation(doc: str) -> list[Doc]:
    doc_list = prepare_doc(doc)
    embeddings = generate_embeddings(doc_list)
    output = [Doc(doc=i, doc_emb=j) for i, j in zip(doc_list, embeddings)]
    return output


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    # model = SentenceTransformer(
    #     model_name_or_path="sentence-transformers/all-MiniLM-L6-v2"
    # )
    # output = model.encode(texts).tolist()
    # SentenceTransformer hugging face has a certificate issue behind our corporate proxy
    client = get_openai_embedding_client()
    response = client.embeddings.create(input=texts, model="text-embedding-ada-002")
    output = [i.embedding for i in response.data]

    return output

