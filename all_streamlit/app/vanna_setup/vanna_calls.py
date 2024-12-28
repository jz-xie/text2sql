import streamlit as st
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore
from vanna_setup.vector_store import OpenSearch_VectorStore
from opensearchpy import OpenSearch
from utils.opensearch_tools import index_dococument
from utils.data_prep import (
    DDL,
    QuestionSQL,
    generate_embeddings,
    generate_question_sql,
    generate_ddl,
)
# class MyVanna(ChromaDB_VectorStore, Ollama):
#     def __init__(self, config=None):
#         ChromaDB_VectorStore.__init__(self, config=config)
#         Ollama.__init__(self, config=config)


class MyVanna(OpenSearch_VectorStore, Ollama):
    def __init__(self, config=None):
        OpenSearch_VectorStore.__init__(
            self, client=config["opensearch_client"], config=config
        )
        Ollama.__init__(self, config=config)


def prepare_data(client: OpenSearch, ddl_index_name: str, question_sql_index_name: str):
    ddls = generate_ddl()
    index_dococument(client, ddl_index_name, ddls)
    qn_sql_pairs = generate_question_sql()
    index_dococument(client, question_sql_index_name, qn_sql_pairs)


@st.cache_resource(ttl=3600)
def setup_vanna():
    open_search_secrets = st.secrets["opensearch"]
    opensearch_client = OpenSearch(
        hosts=[
            {"host": open_search_secrets["host"], "port": open_search_secrets["port"]}
        ],
        http_auth=(open_search_secrets["user"], open_search_secrets["password"]),
        http_compress=True,  # enables gzip compression for request bodies
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )
    postgres_secrets = st.secrets["postgres"]
    vn = MyVanna(
        config={"model": "llama3.2:1b", "opensearch_client": opensearch_client}
    )
    # vn = VannaDefault(api_key=st.secrets.get("VANNA_API_KEY"), model='chinook')
    # vn.connect_to_sqlite("https://vanna.ai/Chinook.sqlite")
    prepare_data(
        client=opensearch_client,
        ddl_index_name=DDL.opensearch_index_name,
        question_sql_index_name=QuestionSQL.opensearch_index_name,
    )
    vn.connect_to_postgres(
        host="localhost",
        dbname="BIRD",
        user=postgres_secrets["username"],
        password=postgres_secrets["password"],
        port=5432,
    )
    return vn


@st.cache_data(show_spinner="Generating sample questions ...")
def generate_questions_cached():
    vn = setup_vanna()
    return vn.generate_questions()


@st.cache_data(show_spinner="Generating SQL query ...")
def generate_sql_cached(question: str):
    vn = setup_vanna()
    question_emb = generate_embeddings(question)
    return vn.generate_sql(
        question=question, allow_llm_to_see_data=True, embeddings=question_emb
    )


@st.cache_data(show_spinner="Checking for valid SQL ...")
def is_sql_valid_cached(sql: str):
    vn = setup_vanna()
    return vn.is_sql_valid(sql=sql)


@st.cache_data(show_spinner="Running SQL query ...")
def run_sql_cached(sql: str):
    vn = setup_vanna()
    return vn.run_sql(sql=sql)


@st.cache_data(show_spinner="Checking if we should generate a chart ...")
def should_generate_chart_cached(question, sql, df):
    vn = setup_vanna()
    return vn.should_generate_chart(df=df)


@st.cache_data(show_spinner="Generating Plotly code ...")
def generate_plotly_code_cached(question, sql, df):
    vn = setup_vanna()
    code = vn.generate_plotly_code(question=question, sql=sql, df=df)
    return code


@st.cache_data(show_spinner="Running Plotly code ...")
def generate_plot_cached(code, df):
    vn = setup_vanna()
    return vn.get_plotly_figure(plotly_code=code, df=df)


@st.cache_data(show_spinner="Generating followup questions ...")
def generate_followup_cached(question, sql, df):
    vn = setup_vanna()
    return vn.generate_followup_questions(question=question, sql=sql, df=df)


@st.cache_data(show_spinner="Generating summary ...")
def generate_summary_cached(question, df):
    vn = setup_vanna()
    return vn.generate_summary(question=question, df=df)
