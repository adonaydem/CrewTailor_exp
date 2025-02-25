import json
import traceback
import random
import re
import requests
import operator
import sqlite3
from langgraph.prebuilt import ToolExecutor, ToolNode, ToolInvocation
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, FunctionMessage, BaseMessage
from .tools import *

def pam_prompt():
    system ="""
    You are PAM, a professional assistant machine. You are part of an AI application called CrewTailor that allows users to customize workflows and get a team of AI agents to get the workflows done.
    Your role in this app is to assist the user in understanding of the app and accomplishing some actions.

    Here are the use cases of the app:
    - Create a new workflow of AI agents(PAM can do this)
    - Edit and see an existing workflow(PAM can only see workflows)
    - Run the workflow using the team of Ai agents
    - A feature called Store, to show public workflows from the community.

    **Workflow of your task. Each step must be fulfilled before going to the next**:
    1. Get instructions from user.
    2. Does the user ask about the following topics: new workflow creation, editing, features, services? If so, You MUST read the documentation first. Use retrieve_app_info tool to read the documentation. 
    3. from retrieve_app_info tool, get the raw output and refine/summarize/transform it. If the output doesn't answer the user's question(your question), look for alternatives or say you don't know.
    4. Provide the result.



    You also have tools needed to create a workflow(new_workflow), get an existing a workflow(search_workflow), and edit. 
    Consider the retrieve_app_info tool as a Cheat Sheet.
    DO NOT use JSON when communicating with user, JSON formats are for internal purposes.

    Remember, You must use the above workflow for your task.
    """
    return system
def pam(state):
    messages = state["messages"]
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    model = model.bind_tools([retrieve_app_info, new_workflow, search_workflow])
    system_prompt = pam_prompt()
    response = model.invoke([SystemMessage(content=system_prompt)] + messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def where_to_go(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish

    if "function_call" not in last_message.additional_kwargs:
        return "end"

    return "continue"

def call_tool(state):
    messages = state["messages"]
    
    
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    tool = last_message.additional_kwargs["function_call"]["name"]
    # We construct an ToolInvocation from the function_call
    action = ToolInvocation(
        tool=tool,
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )

    try:
        response = tool_executor.invoke(action)
    except Exception as e:
        response = e
    print(response)
    # We use the response to create a FunctionMessage
    function_message = ToolMessage(content=str(response), name=action.tool, tool_call_id=last_message.tool_calls[0]['id'])
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}

