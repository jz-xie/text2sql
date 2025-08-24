import logging
from typing import Generator, Literal, Optional
from uuid import UUID, uuid4
import streamlit as st
import pandas as pd
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from plotly.graph_objs import Figure
from pydantic import BaseModel, Field
import snowflake.connector
from text2sql.backend.connectors.my_openai import (
    submit_prompt,
    system_message,
    user_message,
    assistant_message,
)
from text2sql.backend.connectors.my_snowflake import execute_sql
from text2sql.backend.core.chart_handler import generate_chart
from text2sql.backend.core.retrieval import (
    get_related_ddl,
    get_related_documentation,
    get_similar_question_sql,
)
from text2sql.frontend.auth import auth_by_refresh_token
from streamlit.logger import get_logger

logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = get_logger(__name__)

dialect = "Snowflake"
initial_prompt = f"At GXS Bank, a digitable bank in Singapore, you are a {dialect} SQL expert to help internal teams with their questions related GXS's data using SQL knowledge. Reply the message only if it is related to GXS bank's data or SQL questions"
response_guidelines = "\n".join(
    [
        "Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions. "
        "===SQL Response Guidelines",
        "1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question. \n",
        # "2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql \n",
        "3. If the provided context is insufficient, please explain why it can't be generated. \n",
        "4. Use the most relevant table(s). \n",
        "5. After you picked the tables, only use the columns that exist in those tables from the tables DDL. \n",
        "6. If the question has been asked and answered before, please repeat the answer exactly as it was given before. \n",
        f"7. Ensure that the output SQL is {dialect}-compliant and executable, and free of syntax errors. \n",
    ]
)


class QueryResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Literal["assistant", "user"]
    text: Optional[str] = None
    error: Optional[str] = None
    sql: Optional[str] = None
    df: Optional[pd.DataFrame] = None
    plotly_code: Optional[str] = None
    plotly_figure: Optional[Figure] = None

    class Config:
        arbitrary_types_allowed = True


def get_query_response(
    query: str,
    conversation_history: list[ChatCompletionMessageParam] = [],
) -> Generator[QueryResponse, None, None]:
    sql_required = is_sql_required(query)
    logger.info(f"\nQuestion: {query}\nSQL Required: {sql_required}")
    if sql_required is not None:
        if sql_required:
            response = answer_sql_question(query, conversation_history)
        else:
            response = answer_nonsql_question(query, conversation_history)
    else:
        error_message = (
            "Could Not Determine Whether SQL is Required to Answer the Question"
        )
        response = iter([QueryResponse(role="assistant", error=error_message)])
        logger.error(error_message)
        
    yield from response
    


def is_sql_required(question: str) -> bool | None:
    prompt = f"""
    question: {question}
    Is this question requesting data from a SQL database? Should this question answered by a SQL?
    Only answer by "yes" or "no"
    """
    system_prompt = initial_prompt + "\n" + response_guidelines
    final = [system_message(system_prompt), user_message(prompt)]

    output = submit_prompt(final)

    if output:
        match output.lower():
            case "yes":
                return True
            case "no":
                return False
    else:
        return None


def answer_nonsql_question(
    query: str, convo_history: list[ChatCompletionMessageParam]
) -> Generator[QueryResponse, None, None]:
    response = QueryResponse(role="assistant")

    prompt = f"{query}"
    final_prompt = (
        [system_message(initial_prompt)] + convo_history + [user_message(prompt)]
    )
    logger.info(final_prompt)
    
    store_prompt(final_prompt)
    output = submit_prompt(final_prompt)

    if output is not None:
        response.text = output
    else:
        response.error = "Failed to Get LLM Response"
    yield response


def answer_sql_question(
    question: str, conversation_history: list[ChatCompletionMessageParam]
) -> Generator[QueryResponse, None, None]:
    response = QueryResponse(role="assistant")
    
    sql = None
    llm_response = generate_sql(question=question)
    
    if llm_response is not None:
        if llm_response.startswith("```sql"):
            sql = llm_response.strip("\n").strip("```").strip("sql")
            response.sql = sql
        else:
            response.text = llm_response
    else:
        response.error = "Failed to generate SQL. Please try rephrase your question 🙏"

    yield response

    if not sql:
        return None

    username = st.session_state["username"]
    access_token = st.session_state["access_token"]
    try:
        df = execute_sql(sql=sql, username=username, access_token=access_token)
    except snowflake.connector.errors.DatabaseError:
        logger.info(
            "Access ooken expired. Attempt to renew it via refresh token before executing SQL query"
        )
        refresh_token = st.context.cookies.get("refresh_token")
        if refresh_token:
            auth_by_refresh_token(refresh_token, username)
            access_token = st.session_state["access_token"]
            df = execute_sql(sql=sql, username=username, access_token=access_token)
        else:
            raise snowflake.connector.errors.DatabaseError

    if df is not None:
        response.df = df
        yield response

        chart_result = generate_chart(question, sql, df)
        if chart_result:
            response.plotly_code, response.plotly_figure = chart_result
            yield response
    else:
        response.error = "SQL is invalid. Please try rephrase your question 🙏"
        yield response

    # return response


def generate_sql(question: str, allow_llm_to_see_data=False) -> str | None:
    question_sql_list = get_similar_question_sql(question)
    ddl_list = get_related_ddl(question)
    doc_list = get_related_documentation(question)
    prompt = get_sql_prompt(
        initial_prompt=initial_prompt,
        question=question,
        question_sql_list=question_sql_list,
        ddl_list=ddl_list,
        doc_list=doc_list,
    )
    logger.info(f"SQL Prompt:\n{prompt}")
    llm_response = submit_prompt(prompt)
    logger.info(f"LLM Response:\n{llm_response}")
    
    return llm_response
    # if llm_response is not None:
    #     if "intermediate_sql" in llm_response:
    #         if not allow_llm_to_see_data:
    #             return "The LLM is not allowed to see the data in your database. Your question requires database introspection to generate the necessary SQL. Please set allow_llm_to_see_data=True to enable this."

    #         if allow_llm_to_see_data:
    #             intermediate_sql = extract_sql(llm_response)

    #             try:
    #                 log(title="Running Intermediate SQL", message=intermediate_sql)
    #                 df = run_sql(intermediate_sql)

    #                 prompt = get_sql_prompt(
    #                     initial_prompt=initial_prompt,
    #                     question=question,
    #                     question_sql_list=question_sql_list,
    #                     ddl_list=ddl_list,
    #                     doc_list=doc_list
    #                     + [
    #                         f"The following is a pandas DataFrame with the results of the intermediate SQL query {intermediate_sql}: \n"
    #                         + df.to_markdown()
    #                     ],
    #                     **kwargs,
    #                 )
    #                 log(title="Final SQL Prompt", message=prompt)
    #                 llm_response = submit_prompt(prompt)
    #                 log(title="LLM Response", message=llm_response)
    #             except Exception as e:
    #                 return f"Error running intermediate SQL: {e}"


def get_sql_prompt(
    initial_prompt: str,
    question: str,
    question_sql_list: list,
    ddl_list: list,
    doc_list: list,
    dialect="Snowflake",
):
    system_prompt = f"""
    {initial_prompt}
    ===Tables DDL
    {ddl_list}
    ===Additional Context
    {doc_list}
    ===Response Guidelines
    {response_guidelines}
    """

    # initial_prompt = add_ddl_to_prompt(initial_prompt, ddl_list, max_tokens=max_tokens)
    # if static_documentation != "":
    #     doc_list.append(static_documentation)

    # initial_prompt = add_documentation_to_prompt(
    #     initial_prompt, doc_list, max_tokens=max_tokens
    # )

    # initial_prompt += (
    #     "\n"
    #     "1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question. \n"
    #     "2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql \n"
    #     "3. If the provided context is insufficient, please explain why it can't be generated. \n"
    #     "4. Please use the most relevant table(s). \n"
    #     "5. If the question has been asked and answered before, please repeat the answer exactly as it was given before. \n"
    #     f"6. Ensure that the output SQL is {dialect}-compliant and executable, and free of syntax errors. \n"
    # )

    message_log = [system_message(system_prompt)]

    for example in question_sql_list:
        if example is None:
            print("example is None")
        else:
            if example is not None and "question" in example and "sql" in example:
                message_log.append(user_message(example["question"]))
                message_log.append(assistant_message(example["sql"]))

    message_log.append(user_message(question))

    return message_log

def store_prompt(prompt:list[ChatCompletionMessageParam]):
    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
        
    st.session_state.latest_prompt = prompt
    st.session_state.prompt_history.append(prompt)

def prepare_prompt_from_message_history(messages: list[QueryResponse]):
    # st.session_state.latest_response = response