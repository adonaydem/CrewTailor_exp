import json
import traceback
import random
import re
import requests
import operator
import sqlite3
from flask import session
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.tools.retriever import create_retriever_tool
from typing import Union, Optional, Type, Any, Annotated, Sequence, List
from typing_extensions import TypedDict
from langchain_community.vectorstores import FAISS
from langgraph.prebuilt import ToolExecutor, ToolNode, ToolInvocation
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
@tool
def new_workflow(metadata: Annotated[str, "Workflow General metadata in json format."], nodes: Annotated[str, "python list of Nodes, each element is a node's information in json format"]) -> str:
    "Use this tool to create new workflows. Ensure you have what you need. The parameters are all in json format."
    uid = session['uid']
    if not uid:
        return "Something went wrong with user authentication, I can't proceed"
    
    url = f"http://localhost:5000/add_workflow/{uid}"
    if not isinstance(metadata, dict):
        try:
            metadata = json.loads(metadata)
        except:
            return "metadata should be in json format."

    if not isinstance(nodes, list):
        try:
            nodes = json.loads(nodes)
        except:
            return "nodes must be a json list of objects, I couldnt parse it"
    
    payload = {"metadata": metadata, "nodes": nodes}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@tool
def search_workflow(name: Annotated[str, "Name of the workflow"] = None, timestamp: Annotated[str, "Date and time of creation"] = None, public: Annotated[str, "yes/no"] = None):
    "Use this tool to search for user's workflows."
    uid = session['uid']
    if not uid:
        return "Something went wrong, I can't proceed"
    if public.lower() == "yes":
        url = "http://localhost:5000/list_community_workflows"
    else:
        url = "http://localhost:5000/list_my_workflows"

    params = {
        "name": name,       
        "timestamp": timestamp  
    }

    response = requests.get(f"{url}/{uid}", params=params)
    if response.status_code == 200:
        data = response.json()
        return data[:2]
    else:
        print(f"Error: {response.status_code}")
        return response.text
        







@tool
def retrieve_app_info(query: Annotated[str, "Key phrase for search."]):
    """Use to retrieve app info from documentation."""
    data_query = """
    SELECT * FROM guide;
    """

    conn = sqlite3.connect('./pam/documentation.db')
    cursor = conn.cursor()

    cursor.execute(data_query)
    rows = cursor.fetchall()
    result = [row[1] for row in rows]
    vector_db = FAISS.from_texts(result, GoogleGenerativeAIEmbeddings(model="models/embedding-001"))
    retriever = vector_db.as_retriever(search_kwargs={"k": 1})
    description = """Use to look up documentation for Software Application. Input is a human query with an approximate similarity to some context, output is \
    valid similar information. """
    retriever_tool = create_retriever_tool(
        retriever,
        name="retrieve_app_info",
        description=description,
    )
    response =retriever_tool.invoke(query)
    memory_list = response.split('\n\n')

    first = memory_list[0]
    cursor.execute("select guide from guide where topic = ?", (first,))
    row = cursor.fetchone()
    if row:
        return ("Closest search result: \n Please note that the search results may be irrelevant(which means there is no relevant data i can give you):\n", row[0])
    else:
        return ("No guide found for the specified topic.")
    return response

tool_executor = ToolExecutor([retrieve_app_info, new_workflow, search_workflow])