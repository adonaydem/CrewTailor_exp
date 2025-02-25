import json
import traceback
import random
import re
import requests
import operator
import sqlite3
from datetime import datetime
from flask import session

from .utils import *



def call_graph(user_input, thread_id):
    """
    This function calls a langgraph graph with the given user input and thread ID.

    Args:
        user_input (str): The input provided by the user.
        thread_id (str): The ID of the thread.

    Yields:
        str: The output message from the graph.

    Raises:
        Exception: If an error occurs during the execution of the graph.
    """
    app = initialize_graph()

    parts = thread_id.split('_')
    uid = parts[1]
    session['uid'] = uid
    config = {"configurable": {"thread_id": thread_id}}
    try:
        for output in app.stream({"messages": [HumanMessage(content=user_input)]}, config, stream_mode="values"):
            for key, value in output.items():
                    if key == "messages" and isinstance(value[-1], AIMessage):
                        if len(value[-1].tool_calls) == 0:
                            yield value[-1].content
    except Exception as e:
        traceback.print_exc()
        yield "Something went wrong, please try again later"



