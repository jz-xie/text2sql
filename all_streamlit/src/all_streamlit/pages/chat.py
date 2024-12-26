import logging
import streamlit as st
from vanna_setup.vanna_calls import (
    generate_questions_cached,
    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    generate_followup_cached,
    should_generate_chart_cached,
    is_sql_valid_cached,
    generate_summary_cached
)

avatar_url = "https://vanna.ai/img/vanna.svg"
def clear_messages():
    st.session_state.messages = []
    
st.set_page_config(layout="wide")
st.title("Text to SQL")
st.sidebar.button("Reset", on_click=clear_messages, use_container_width=True)
# st.sidebar.title("Output Settings")
# st.sidebar.checkbox("Show SQL", value=True, key="show_sql")
# st.sidebar.checkbox("Show Table", value=True, key="show_table")
# st.sidebar.checkbox("Show Plotly Code", value=True, key="show_plotly_code")
# st.sidebar.checkbox("Show Chart", value=True, key="show_chart")
# st.sidebar.checkbox("Show Summary", value=True, key="show_summary")
# st.sidebar.checkbox("Show Follow-up Questions", value=True, key="show_followup")

def set_question(question):
    st.session_state["my_question"] = question


# assistant_message_suggested = st.chat_message(
#     "assistant"
# )
# if assistant_message_suggested.button("Click to show suggested questions"):
#     st.session_state["my_question"] = None
#     questions = generate_questions_cached()
#     for i, question in enumerate(questions):
#         time.sleep(0.05)
#         button = st.button(
#             question,
#             on_click=set_question,
#             args=(question,),
#         )

def answer_question(question: str):

    sql = generate_sql_cached(question=question)

    if not is_sql_valid_cached(sql=sql):
        content = [
            {"type": "error", "value": "SQL is invalid"},
            {"type": "sql", "value": sql}
        ]
    else:
        df = run_sql_cached(sql=sql)
        content = [
            {"type": "sql", "value": sql},
            {"type": "df", "value": df}
        ]

    message = {"role": "assistant", "content": content}
    st.session_state.messages.append(message)

    return message

def display_message(message: dict):
    with st.chat_message(message["role"]):
        for i in message["content"]:
            match i["type"]:
                case "error":
                    st.error(i["value"])
                case "text":
                    st.markdown(i["value"])
                case "sql":
                    st.code(i["value"], language="sql", line_numbers=True)
                case "df":
                    st.dataframe(i["value"])


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    display_message(message)

# React to user input
if question := st.chat_input("Ask me a question about your data"):
    logging.debug(f"question: {question}")
    # Display user message in chat message container
    st.chat_message("user").markdown(question)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": [{"type": "text", "value":question}]})

    answer = answer_question(question=question)
    display_message(answer)


# my_question = st.session_state.get("my_question", default=None)

# if my_question is None:
#     my_question = st.chat_input(
#         "Ask me a question about your data",
#     )


# if my_question:
#     st.session_state["my_question"] = my_question
#     user_message = st.chat_message("user")
#     user_message.write(f"{my_question}")

#     sql = generate_sql_cached(question=my_question)

#     if sql:
#         if is_sql_valid_cached(sql=sql):
#             if st.session_state.get("show_sql", True):
#                 assistant_message_sql = st.chat_message(
#                     "assistant", avatar=avatar_url
#                 )
#                 assistant_message_sql.code(sql, language="sql", line_numbers=True)
#         else:
#             assistant_message = st.chat_message(
#                 "assistant", avatar=avatar_url
#             )
#             assistant_message.write(sql)
#             st.stop()

#         df = run_sql_cached(sql=sql)

#         if df is not None:
#             st.session_state["df"] = df

#         if st.session_state.get("df") is not None:
#             if st.session_state.get("show_table", True):
#                 df = st.session_state.get("df")
#                 assistant_message_table = st.chat_message(
#                     "assistant",
#                     avatar=avatar_url,
#                 )
#                 if len(df) > 10:
#                     assistant_message_table.text("First 10 rows of data")
#                     assistant_message_table.dataframe(df.head(10))
#                 else:
#                     assistant_message_table.dataframe(df)

#             if should_generate_chart_cached(question=my_question, sql=sql, df=df):

#                 code = generate_plotly_code_cached(question=my_question, sql=sql, df=df)

#                 if st.session_state.get("show_plotly_code", False):
#                     assistant_message_plotly_code = st.chat_message(
#                         "assistant",
#                         avatar=avatar_url,
#                     )
#                     assistant_message_plotly_code.code(
#                         code, language="python", line_numbers=True
#                     )

#                 if code is not None and code != "":
#                     if st.session_state.get("show_chart", True):
#                         assistant_message_chart = st.chat_message(
#                             "assistant",
#                             avatar=avatar_url,
#                         )
#                         fig = generate_plot_cached(code=code, df=df)
#                         if fig is not None:
#                             assistant_message_chart.plotly_chart(fig)
#                         else:
#                             assistant_message_chart.error("I couldn't generate a chart")

#             if st.session_state.get("show_summary", True):
#                 assistant_message_summary = st.chat_message(
#                     "assistant",
#                     avatar=avatar_url,
#                 )
#                 summary = generate_summary_cached(question=my_question, df=df)
#                 if summary is not None:
#                     assistant_message_summary.text(summary)

#             if st.session_state.get("show_followup", True):
#                 assistant_message_followup = st.chat_message(
#                     "assistant",
#                     avatar=avatar_url,
#                 )
#                 followup_questions = generate_followup_cached(
#                     question=my_question, sql=sql, df=df
#                 )
#                 st.session_state["df"] = None

#                 if len(followup_questions) > 0:
#                     assistant_message_followup.text(
#                         "Here are some possible follow-up questions"
#                     )
#                     # Print the first 5 follow-up questions
#                     for question in followup_questions[:5]:
#                         assistant_message_followup.button(question, on_click=set_question, args=(question,))

#     else:
#         assistant_message_error = st.chat_message(
#             "assistant", avatar=avatar_url
#         )
#         assistant_message_error.error("I wasn't able to generate SQL for that question")

