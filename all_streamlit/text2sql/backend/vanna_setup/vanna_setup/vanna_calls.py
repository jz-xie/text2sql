import logging
from dataclasses import asdict
from typing import Union

import pandas as pd
import snowflake.connector
import streamlit as st
from opensearchpy import OpenSearch
from streamlit.logger import get_logger
from vanna.openai import OpenAI_Chat

from text2sql.backend.connectors.clients import get_openai_chat_client, get_opensearch_client
from text2sql.backend.config import settings
from text2sql.backend.data_prep import (
    DDL,
    Doc,
    QuestionSQL,
    generate_embeddings,
    get_ddl,
    get_documentation,
    get_finance_context,
    get_verified_questions,
)
from text2sql.backend.connectors.opensearch import (
    index_dococument,
)
from text2sql.backend.vanna_setup.vector_store import OpenSearch_VectorStore
from text2sql.frontend.auth import auth_by_refresh_token

logger = get_logger(__name__)


class MyVanna(OpenSearch_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        OpenSearch_VectorStore.__init__(
            self, client=get_opensearch_client(), config=config
        )
        OpenAI_Chat.__init__(
            self,
            config=config,
            client=get_openai_chat_client(),
        )
        self.chat_history = []

    def connect_to_snowflake(
        self,
        account: Union[str, None] = None,
        username: Union[str, None] = None,
        password: Union[str, None] = None,
        database: Union[str, None] = None,
        role: Union[str, None] = None,
        warehouse: Union[str, None] = None,
        **kwargs,
    ):
        if settings.env == "local":
            account = "gxs-dev"
        else:
            account = f"gxs-{settings.env}"
        conn = snowflake.connector.connect(
            authenticator="oauth",
            user=st.session_state["username"],
            account=account,
            database="gold",
            token=st.session_state["access_token"],
            client_session_keep_alive=True,
            **kwargs,
        )

        def run_sql_snowflake(sql: str) -> pd.DataFrame:
            logging.info(f"sql: {sql}")

            cs = conn.cursor()

            if role is not None:
                cs.execute(f"USE ROLE {role}")

            if warehouse is not None:
                cs.execute(f"USE WAREHOUSE {warehouse}")
            # cs.execute(f"USE DATABASE {database}")

            cur = cs.execute(sql)

            results = cur.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(results, columns=[desc[0] for desc in cur.description])

            return df

        self.dialect = "Snowflake SQL"
        self.run_sql = run_sql_snowflake
        self.run_sql_is_set = True

    def get_sql_prompt(
        self,
        initial_prompt: str,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        """
        Example:
        ```python
        vn.get_sql_prompt(
            question="What are the top 10 customers by sales?",
            question_sql_list=[{"question": "What are the top 10 customers by sales?", "sql": "SELECT * FROM customers ORDER BY sales DESC LIMIT 10"}],
            ddl_list=["CREATE TABLE customers (id INT, name TEXT, sales DECIMAL)"],
            doc_list=["The customers table contains information about customers and their sales."],
        )

        ```

        This method is used to generate a prompt for the LLM to generate SQL.

        Args:
            question (str): The question to generate SQL for.
            question_sql_list (list): A list of questions and their corresponding SQL statements.
            ddl_list (list): A list of DDL statements.
            doc_list (list): A list of documentation.

        Returns:
            any: The prompt for the LLM to generate SQL.
        """

        if initial_prompt is None:
            initial_prompt = (
                f"You are a {self.dialect} expert. "
                + "Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions. "
            )

        initial_prompt = self.add_ddl_to_prompt(
            initial_prompt, ddl_list, max_tokens=self.max_tokens
        )

        if self.static_documentation != "":
            doc_list.append(self.static_documentation)

        initial_prompt = self.add_documentation_to_prompt(
            initial_prompt, doc_list, max_tokens=self.max_tokens
        )

        initial_prompt += (
            "===Response Guidelines \n"
            "1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question. \n"
            "2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql \n"
            "3. If the provided context is insufficient, please explain why it can't be generated. \n"
            "4. Please use the most relevant table(s). \n"
            "5. If the question has been asked and answered before, please repeat the answer exactly as it was given before. \n"
            f"6. Ensure that the output SQL is {self.dialect}-compliant and executable, and free of syntax errors. \n"
        )

        message_log = [self.system_message(initial_prompt)]

        for example in question_sql_list:
            if example is None:
                print("example is None")
            else:
                if example is not None and "question" in example and "sql" in example:
                    message_log.append(self.user_message(example["question"]))
                    message_log.append(self.assistant_message(example["sql"]))

        message_log.append(self.user_message(question))

        return message_log

    def submit_prompt(self, prompt, **kwargs) -> str:
        logging.info(prompt)

        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        ##extract chat history into prompt, index = -1 coz user question come last
        if len(self.chat_history) > 1:
            chat_history_prompt = []
            for chat in self.chat_history[:-1]:
                generated_chat_prompt = {
                    "role": chat["role"],
                    "content": [
                        item["value"]
                        for item in chat.get("content")
                        if item["type"] in ["sql", "text"]
                    ][0],
                }
                chat_history_prompt.append(generated_chat_prompt)

            prompt = prompt[:-1] + chat_history_prompt + prompt[-1:]

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        if self.config is not None and "model" in self.config:
            print(
                f"Using model {self.config['model']} for {num_tokens} tokens (approx)"
            )
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )
        else:
            if num_tokens > 3500:
                model = "gpt-3.5-turbo-16k"
            else:
                model = "gpt-3.5-turbo"

            print(f"Using model {model} for {num_tokens} tokens (approx)")
            response = self.client.chat.completions.create(
                model=model,
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )

        # Find the first response from the chatbot that has text in it (some responses may not have text)
        for choice in response.choices:
            if "text" in choice:
                return choice.text

        # If no response with text is found, return the first response's content (which may be empty)
        return response.choices[0].message.content


def upload_user_training_data(client: OpenSearch, uploaded_file, file_type):
    match file_type:
        case DDL.display_name:
            index = DDL.opensearch_index_name
            output = get_ddl(uploaded_file)
        case Doc.display_name:
            index = Doc.opensearch_index_name
            output = get_documentation(uploaded_file)
        case QuestionSQL.display_name:
            index = QuestionSQL.opensearch_index_name
            output = get_verified_questions(uploaded_file)

    for index_name, data in zip([index], [output]):
        data_list_dict = [asdict(i) for i in data]
        summary = index_dococument(client, index, data_list_dict)
        logger.info(f"Index: {index_name} data uploaded")
        st.session_state.upload_summary = summary


@st.cache_resource(ttl=3600)
def setup_vanna():
    vn = MyVanna(
        config={"model": "gpt-4o", "path": "tmp_vector"},
    )
    try:
        vn.connect_to_snowflake()
    except snowflake.connector.errors.DatabaseError:
        refresh_token = st.context.cookies.get("refresh_token")
        username = st.context.cookies.get("username")
        if refresh_token:
            auth_by_refresh_token(refresh_token, username)
            vn.connect_to_snowflake()
        else:
            st.error("Please log in first.")
            st.switch_page("auth.py")

    logger.info("Vanna Setup Done")
    return vn


@st.cache_data(show_spinner="Generating sample questions ...")
def generate_questions_cached():
    vn = setup_vanna()
    return vn.generate_questions()


@st.cache_data(show_spinner="Generating SQL query ...")
def generate_sql_cached(question: str):
    vn = setup_vanna()
    question_emb = generate_embeddings(texts=[question])[0]
    return vn.generate_sql(
        question=question, allow_llm_to_see_data=False, embeddings=question_emb
    )


@st.cache_data(show_spinner="Checking for valid SQL ...")
def is_sql_valid_cached(sql: str):
    # vn = setup_vanna()
    # return vn.is_sql_valid(sql=sql)
    return "SELECT" in sql.upper()


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
