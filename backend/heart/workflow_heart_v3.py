import os
import json
import random
import copy
import re
import time
import functools
import requests
import sqlite3
import traceback
import importlib
import logging
from flask import session
from threading import Event
from pymongo import MongoClient
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.memory import ChatMessageHistory
from .customizer_v3 import save_graph_structure, generate_code_string
from .sql_worker import events_db, projects_db, tasks_db, users_db
from .socketio_manager import SocketIOManager
from .globals import *
from .agent_chat import HumanChat, AutoChat
from .tool_defintions import *
from .toolkits import *
from .utils import *
from .state import *



load_dotenv('../.env')


def call_graph(user_input, threadId, _id):
    """
    Calls the given workflow's graph with the given user input, thread ID, and workflow ID.
    
    Args:
        user_input (str): The input provided by the user.
        threadId (str): The ID of the thread.
        _id (str): The ID of the workflow.
    
    Yields:
        str: The output message from the workflow graph.
    
    Returns:
        None
    
    Raises:
        Exception: If an error occurs during the execution of the workflow graph.
    """
    session["thread_id"] = threadId
    workflow_data, graph_object = get_object(_id)
    workflow_graph = graph_object(manager, create_agent, agent_node, workflow_data)
    config = {"configurable": {"thread_id": threadId}}
    socketio_manager = SocketIOManager()
    active = True
    set_active_graph("main")
    
    logging.info("everything is set up, launching....")

    while active and get_active_graph() == "main":
        loop_count = 0
        warning = 0
        print("looping...")
        try:
            for output in workflow_graph.stream(
                {
                    "messages": [HumanMessage(content=user_input)], 
                    "w_id": _id, 
                    "thread_id": threadId
                }, 
                config, 
                stream_mode="values"
            ):
                
                for key, value in output.items():
                    
                    if key == "messages":
                        if isinstance(value[-1], HumanMessage) and value[-1].content == "User aborted.":
                            active = False
                        if isinstance(value[-1], ToolMessage):
                            if value[-1].name == "Router":
                                if isinstance(value[-2], AIMessage) and len(value[-2].tool_calls) > 0 and value[-2].tool_calls[0]["args"]["To"] == "User":
                                    
                                    mes = (value[-2].tool_calls[0]["args"]["Message"])
                                    try:
                                        yield decode_unicode_escapes(mes)
                                    except:
                                        yield mes
                                    active = False  # Stop the loop after processing the input
                                else:
                                    i = -2
                                    while isinstance(value[i], AIMessage):
                                        if len(value[i].tool_calls) > 0 and value[i].tool_calls[0]["args"]["To"] != "User":
                                            try:
                                                yield f"I have reached out to: {decode_unicode_escapes(value[i].tool_calls[0]['args']['To'])}. Please wait for their response."
                                            except:
                                                yield f"I have reached out to: {value[i].tool_calls[0]['args']['To']}. Please wait for their response."
                                            break
                                        i -= 1
                    if key == "progress":

                        if socketio_manager.socketio and value is not None:
                            socketio_manager.socketio.emit('team_progress', value)
                            db_obj = workflow_master_db()
                            result, status = db_obj.set_progress_db(threadId, value)

            loop_count += 1
            if loop_count == 3:
                inputs = {"messages": [HumanMessage(content="Notice: The system has seen you are in a loop of tasks without user interuption. If you are encountering an error, please give up and go back to user and try to use other options(far from current process) and don't make the same actions. However, if you are accomplishing tasks successfully, please proceed and try to finish sooner and sorry for the interuption.")]}
                warning += 1
            elif loop_count >= 5 and not isinstance(message, ToolMessage):
                break
        except Exception as e:
            print("Error in call_graph:", str(e))
            traceback.print_exc()
            yield "Something went wrong, please try again later"
            active = False  
        
    logging.info("not active anymore")