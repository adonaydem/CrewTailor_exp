from .tool_defintions import Router, File_List, File_Read, File_Write
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import FunctionMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import random
import copy
import re
import time
import functools
import requests
import sqlite3
import json
import traceback
from threading import Event

from .globals import *
from .utils import *
from .socketio_manager import SocketIOManager
from .agent_chat import HumanChat, AutoChat

def manager(state, llm, workflow_data):
    """
    This langgraph manages the workflow of a team by binding tools to a large language model (LLM) and invoking the LLM with a prompt and a list of messages.
    
    It takes in three parameters:
    - state: The current state of the team, including the workflow data and messages.
    - llm: The large language model to be used for the workflow.
    - workflow_data: The data associated with the workflow.
    
    The function returns the state containing the updated messages and the next step in the workflow.
    """
    def create_tool_messages(tool_calls):
        """Helper function to create tool messages from tool calls."""
        tool_messages = {}
        picked = None
        try:
            if len(tool_calls) > 1:
                for tool_call in tool_calls:
                    #not a priority message
                    if tool_call['args']['To'] == "User":
                        tool_messages['User'] = ToolMessage(content=f"Only one message allowed at a time", name=tool_call['name'], tool_call_id=tool_call['id'])
                    else:
                        if not picked:
                            picked = ToolMessage(content=f"Route request sent to: {tool_call['args']['To']}", name=tool_call['name'], tool_call_id=tool_call['id'])
                        else:
                            tool_messages[tool_call['args']['To']] = ToolMessage(content=f"Request failed. Only one tool message at a time is allowed.", name=tool_call['name'], tool_call_id=tool_call['id'])
            else:
                return [
                    ToolMessage(content=f"Route request sent to: {tool_call['args']['To']}. Please wait until response.", name=tool_call['name'], tool_call_id=tool_call['id'])
                    for tool_call in tool_calls
                ]
            return [picked] + list(tool_messages.values())
        except:    
            return None
    def message_window(messages, window_size):
        """
        This function truncates a list of messages to a specified window size to minimize token input, 
        ensuring that the most recent message is not a ToolMessage or FunctionMessage. 
        If the most recent message is an AIMessage, it prepends a HumanMessage with content "____".
        
        Parameters:
        messages (list): The list of messages to be truncated.
        window_size (int): The desired size of the truncated list.
        
        Returns:
        list: The truncated list of messages.
        """
        # Ensure we are not modifying the original list directly
        final = messages[:]
        # Check window size against the length of messages
        while window_size < len(messages):
            # Check if the current message is not a ToolMessage
            if not isinstance(messages[-window_size], ToolMessage) and not isinstance(messages[-window_size], FunctionMessage):
                if isinstance(messages[-window_size], AIMessage):
                    final = messages[-window_size:]
                    final.insert(0, HumanMessage(content="____"))
                    break
                # Slice the list to the desired window size
                final = messages[-window_size:]
                break
            # Increment window size to check the next element
            window_size += 1
        
        return final
    manager_llm = llm.bind_tools([Router])
    messages = message_window(state['messages'], 50)

    prompt = manager_prompt(get_workflow(state['w_id']))

    # First invocation
    response = manager_llm.invoke([SystemMessage(content=prompt)] + messages)
    print("Response~~~~~~~~~~~~~~~~: ", response)
    if response.tool_calls:
        refined =create_tool_messages(response.tool_calls)
        if not refined:
            return {
                "messages": [AIMessage(content="Something is wrong with the team, try again later")]
            }
        return {
            "messages": [response] + refined,
            "Next": response.tool_calls[0]['args']['To']
        }

    # If no tool calls in the first response, attempt a second invocation with an error message
    error_message = SystemMessage(content="Error: you should use Manager_route tool.")
    response2 = manager_llm.invoke([SystemMessage(content=prompt)] + messages + [response] + [error_message])

    if not response2.tool_calls:
        return {
            "messages": [AIMessage(content="Something is wrong with the team, try again later")]
        }

    return {
        "messages": [response2] + create_tool_messages(response2.tool_calls),
        "Next": response2.tool_calls[0]['args']['To']
    }


    
def agent_node(state, graph, node_metadata):
    """
    Executes a node(agent) in the workflow graph.

    Args:
        state (dict): The current state of the agent.
        graph (Graph): The agent graph.
        node_metadata (dict): Metadata about the node.

    Returns:
        dict: A dictionary containing the updated messages and progress of the agent.

    Raises:
        None.

    """
     # Initialize a SocketIOManager object
    socketio_manager = SocketIOManager()
    name = node_metadata['name']
    messages = state['messages']
    refined_messages = []

    # Check if the node will be directed by human
    if node_metadata['human_direction'] == "yes":
        set_active_graph("human_chat")
        print("Human direction: ", node_metadata['human_direction'])
        human_chat = HumanChat(socketio_manager)
        i = -2
        while not isinstance(messages[i], AIMessage):
            i-=1    
        result = human_chat.run(graph, node_metadata, messages[i], state['thread_id'], state['progress'])
        if not result:
            return {"messages": [HumanMessage(content=f"User aborted.", name=name)]}
        
    else:
        print("human direction: ", node_metadata['human_direction'])
        auto_chat = AutoChat(socketio_manager)
        i = -2
        while not isinstance(messages[i], AIMessage):
            i-=1  
        result = auto_chat.run(graph, node_metadata, messages[i], state['thread_id'], state['progress'])
    set_active_graph("main")
    return {"messages": [FunctionMessage(content=f"Response from {name}: '{result}'. Now, decide where to go next.", name=name)], "progress":[{node_metadata['name']: result}]}
