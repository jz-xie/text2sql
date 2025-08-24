import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from text2sql.backend.connectors.my_openai import system_message, user_message, submit_prompt
import logging

logger = logging.getLogger(__name__)


def generate_plotly_code(
    df_metadata: pd.Series, question: Optional[str], sql: Optional[str] = None
) -> str | None:
    if question is not None:
        system_msg = f"The following is a pandas DataFrame that contains the results of the query that answers the question the user asked: '{question}'"
    else:
        system_msg = "The following is a pandas DataFrame "

    if sql is not None:
        system_msg += f"\n\nThe DataFrame was produced using this query: {sql}\n\n"

    system_msg += f"The following is information about the resulting pandas DataFrame 'df': \n{df_metadata}"
    message_log = [
        system_message(system_msg),
        user_message(
            "Can you generate the Python plotly code to chart the results of the dataframe? Assume the data is in a pandas dataframe called 'df'. If there is only one value in the dataframe, use an Indicator. Respond with only Python code. Do not answer with any explanations -- just the code."
        ),
    ]

    raw_plotly_code = submit_prompt(message_log)

    if raw_plotly_code is not None:
        processed = raw_plotly_code.replace("fig.show()", "")
        final_plotly_code = processed.strip("```").strip("python")
        return final_plotly_code
    else:
        print("Plotly Code Not Available")


def get_plotly_figure(
    plotly_code: str, df: pd.DataFrame, dark_mode: bool = True
) -> go.Figure | None:
    """
    **Example:**
    ```python
    fig = vn.get_plotly_figure(
        plotly_code="fig = px.bar(df, x='name', y='salary')",
        df=df
    )
    fig.show()
    ```
    Get a Plotly figure from a dataframe and Plotly code.

    Args:
        df (pd.DataFrame): The dataframe to use.
        plotly_code (str): The Plotly code to use.

    Returns:
        plotly.graph_objs.Figure: The Plotly figure.
    """
    ldict = {"df": df, "px": px, "go": go}
    try:
        exec(plotly_code, globals(), ldict)

        fig = ldict.get("fig", None)
    except Exception as e:
        # Inspect data types
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        # Decision-making for plot type
        if len(numeric_cols) >= 2:
            # Use the first two numeric columns for a scatter plot
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1])
        elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
            # Use a bar plot if there's one numeric and one categorical column
            fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0])
        elif len(categorical_cols) >= 1 and df[categorical_cols[0]].nunique() < 10:
            # Use a pie chart for categorical data with fewer unique values
            fig = px.pie(df, names=categorical_cols[0])
        else:
            # Default to a simple line plot if above conditions are not met
            fig = px.line(df)

    if fig is None:
        return None

    if dark_mode:
        fig.update_layout(template="plotly_dark")

    return fig


def generate_chart(
    question: str, sql: str, df: pd.DataFrame
) -> tuple[str | None, go.Figure | None] | None:  

    if len(df) > 1: # Plot when df has more than 1 record
        code = generate_plotly_code(question=question, sql=sql, df_metadata=df.dtypes)
        fig = None

        if code is not None and code != "":
            fig = get_plotly_figure(plotly_code=code, df=df)

        return (code, fig)

    else:
        return None
