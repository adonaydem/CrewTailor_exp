import json
import traceback
import random
import re
import requests
import operator
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph, START
from typing import Union, Optional, Type, Any, Annotated, Sequence, List
from typing_extensions import TypedDict
from .tools import *
from .state import *




def initialize_graph() -> StateGraph:
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], operator.add]
        Next: Optional[str]

    conn = sqlite3.connect("pam/pam_chkpnts.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    graph = StateGraph(AgentState)
    graph.add_node("pam", pam)
    graph.add_node("call_tool", call_tool)
    graph.set_entry_point("pam")
    graph.add_conditional_edges(
        "pam",
        where_to_go,
        {
            "continue": "call_tool",
            "end": END,
        },
    )
    graph.add_edge("call_tool", "pam")
    return graph.compile(checkpointer=memory)

