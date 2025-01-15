from typing import Literal, Optional
from uuid import UUID, uuid4

import pandas as pd
from pydantic import BaseModel, Field
import plotly.graph_objs as go


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Literal["assistant", "user"]
    text: Optional[str]
    error: Optional[str]
    sql: Optional[str]
    df: Optional[pd.DataFrame]
    plotly_code: Optional[str]
    plotly_figure: Optional[go.Figure]

    class Config:
        arbitrary_types_allowed = True