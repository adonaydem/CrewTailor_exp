from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool, BaseTool, StructuredTool
from langchain_community.tools.tavily_search import TavilySearchResults
from .fileIO_agent import fileIO_agent
from .db_agent import db_agent
from .globals import thread_id
from .workflow_master_db import workflow_master_db
from .sql_worker import events_db, projects_db, tasks_db, users_db
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
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
from flask import session
from dotenv import load_dotenv

load_dotenv()

tavily_tool = TavilySearchResults()
@tool
def File_Write(content: Annotated[str, "The full content of the file"], file_type: Annotated[str, "either one of txt, csv ONLY"]) -> str:
    "Use this tool to write a ready-made content into a file. id, file_type and content are required inputs."
    thread_id = session.get('thread_id')
    query = f"Write a {file_type} file with the following content: {content}. The file name should be of the format: [title]. Create the title based on the content, maximum 70 characters."
    if file_type not in ["txt", "csv"]:
        return "Only accepted file types are txt and csv."
    return fileIO_agent(query, thread_id)

@tool
def File_Read(query : Annotated[str, "imperative query about reading a file"]) -> str:
    "Use this tool to read a file. query is required input."
    thread_id = session.get('thread_id')
    return fileIO_agent(query, thread_id)

@tool
def File_List(query : Annotated[str, "imperative query about list of files"]) -> str:
    "Use this tool to see a list of files created by you and your team members. query is required input."
    thread_id = session.get('thread_id')
    return fileIO_agent(query, thread_id)

@tool
def Database_Wizard(input_text : Annotated[str, "imperative non-SQL input about database CRUD"]) -> str:
    "Use this tool to accomplish database operations. input_text is a required input."
    thread_id = session.get('thread_id')
    return db_agent(input_text, thread_id)

@tool
def Note_Taker(note: Annotated[str, "A one sentence Note of worker activity."]) -> str:
    """Always Use this tool to take ONLY one senetence note of the recent activity for your future reference. Only note the latest activty."""
    thread_id = session.get('thread_id')
    db_obj = workflow_master_db()
    result, status = db_obj.take_note_db(thread_id, note)
    if status != 200:
        return result
    return {"message":"Note saved"}
    

class Router(BaseModel):
    """Always Use this tool to provide response/instructions. Use tool to select the next direction/recipient"""
    To: str = Field(description="The recipient of the next role or message or task. Either choose 'User' or an agent member.")
    Message: str = Field(description="Message given to the supervisor or user.")
    Context: str = Field(description="Short description of Previous tasks of workers and human.")

@tool
def Text_Generation(instruction: Annotated[str, "one sentence and only 5 words long instruction that explicitly states what needs to be generated."], context: Annotated[str, "Relevant tasks done by other teams and their output. For example: previous worker's output"]) -> str:
    "Use this tool to generate any english writing. query and context are required inputs. This tool is intelligent and can generate texts. Since it doesn't have context, give it a full background of what is happening."
    template = """
    You are a text generation assistant.
    Question: {query}
    Context: {context}

    Answer: Lets answer professionally
    """

    prompt = PromptTemplate.from_template(template)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    llm_chain = prompt | llm
    return llm_chain.invoke({"query":instruction, "context":context})

@tool
def chat_finalizer(outcome: Annotated[str, "The final result of your work"]) -> str:
    """When the user is satisified. Use this tool to pass on the final outcome, using the given format."""
    return {"node_done" : outcome}


#EMAIL

@tool("find_people")
def find_people(query: Annotated[str, "The needed input(in human language) for another worker to use in accessing 'users' table database."]):
    """Use this AI worker tool to search for users. It can understand human language."""
    response = users_db(query, thread_id)
    return response

#Project Management

@tool("projects_database")
def projects_database(query: Annotated[str, "The needed user input(in human language) for another worker to use in accessing 'projects' table database. Make this parameter enriched with as much detail as possible, because the worker is dumb."]):
    """Use this tool when you want to access or alter projects in database"""
    response = projects_db(query, thread_id)
    return response


#Task management
@tool("tasks_database")
def tasks_database(query: Annotated[str, "The needed user input(in human language) for another worker to use in accessing 'tasks' table database. Make this parameter enriched with as much detail as possible, because the worker is dumb."]):
    """Use this tool when you want to access or alter tasks in database"""
    response = tasks_db(query, thread_id)
    return response

#Events
@tool("calendar_events")
def calendar_events(query: Annotated[str, "The needed user input(in human language) for another worker to use in accessing 'events' table database. Make this parameter enriched with as much detail as possible, because the worker is dumb."]):
    "Use this tool when you want to access or alter events in database"
    response = events_db(query, thread_id)
    return response


#finance & economics
@tool("stock_market_time_series")
def stock_market_time_series(timeframe: Annotated[str, "The timeframe of the required data. Either 'daily' or 'weekly' or 'monthly'"], symbol: Annotated[str, "The symbol of the required stock"]):
    "Use this tool when you want to fetch realtime stock market time series data. Returns only the top 5 records."
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        return "{'error': 'API key not found, This service has not been configured, thus is not functional'}"
    
    timeframe_dict = {"daily": "TIME_SERIES_DAILY", "weekly": "TIME_SERIES_WEEKLY", "monthly": "TIME_SERIES_MONTHLY"}
    if timeframe.lower() not in timeframe_dict:
        return "{'error': Incorrect timeframe format. Use either daily, weekly or monthly'}"
    
    function = timeframe_dict[timeframe.lower()]
    

    url = 'https://www.alphavantage.co/query'
    params = {
        'function': function,
        'symbol': symbol,
        'apikey': api_key
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()

         # Check if the response contains an error message
        if "Error Message" in data:
            print(f"Error in response: {data['Error Message']}")
            return f"Error in response: {data['Error Message']}"
        # Extract the metadata and the top 5 records from the Weekly Time Series
        try:
            metadata = data.get("Meta Data", {})
            for key, value in timeframe_dict.items():
                time_series = data.get(f"{key.capitalize()} Time Series", {})
                if time_series:
                    break
            top_5_records = dict(list(time_series.items())[:5])
            
            return {
                "Meta Data": metadata,
                f"{timeframe.lower().capitalize()} Time Series": top_5_records
            }
        except Exception as err:
            print(f"Error processing data: {err}")
            return "Something went wrong, I can't proceed"
    else:
        return "Something went wrong, I can't proceed"


@tool("foreign_exchange_time_series")
def foreign_exchange_time_series(timeframe : Annotated[str, "The timeframe of the required data. Either 'daily' or 'weekly' or 'monthly'"], from_symbol: Annotated[str, "The symbol of currency you want to convert from. In three letter format, For example: USD, EUR"], to_symbol: Annotated[str, "The symbol of currency you want to convert to. In three letter format, For example: USD, EUR"]):
    "Use this tool to get realtime foreign currency exchange time series data. Returns only the top 5 records."
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        return "{'error': 'API key not found, This service has not been configured, thus is not functional'}"
    
    timeframe_dict = {
        "daily": "FX_DAILY",
        "weekly": "FX_WEEKLY",
        "monthly": "FX_MONTHLY"
    }
    if timeframe.lower() not in timeframe_dict:
        return "{'error': Incorrect timeframe format. Use either daily, weekly or monthly'}"
    
    function = timeframe_dict[timeframe.lower()]
    
    if len(from_symbol) != 3 or len(to_symbol) != 3:
        return "{'error': Incorrect symbol format. Use three letter format, For example: USD, EUR'}"

    url = 'https://www.alphavantage.co/query'
    params = {
        'function': function,
        'from_symbol': from_symbol,
        'to_symbol': to_symbol,
        'apikey': api_key
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()

         # Check if the response contains an error message
        if "Error Message" in data:
            print(f"Error in response: {data['Error Message']}")
            return f"Error in response: {data['Error Message']}"
        # Extract the metadata and the top 5 records from the Weekly Time Series
        try:
            metadata = data.get("Meta Data", {})
            time_series = data.get(f"Time Series FX ({timeframe.capitalize()})", {})
            top_5_records = dict(list(time_series.items())[:5])
            
            return {
                "Meta Data": metadata,
                f"Time Series FX ({timeframe.capitalize()})": top_5_records
            }
        except Exception as err:
            print(f"Error processing data: {err}")
            return "Something went wrong, I can't proceed"
    else:
        return "Something went wrong, I can't proceed"

@tool("currency_exchange_rate")
def currency_exchange_rate(from_symbol: Annotated[str, "The symbol of currency you want to convert from. In three letter format, For example: USD, BTC"], to_symbol: Annotated[str, "The symbol of currency you want to convert to. In three letter format, For example: USD, BTC"]):
    "Use this tool to get realtime currency exchange rate."
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        return "{'error': 'API key not found, This service has not been configured, thus is not functional'}"
    
    if len(from_symbol) != 3 or len(to_symbol) != 3:
        return "{'error': Incorrect symbol format. Use three letter format, For example: USD, EUR'}"

    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'CURRENCY_EXCHANGE_RATE',
        'from_currency': from_symbol,
        'to_currency': to_symbol,
        'apikey': api_key
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()

         # Check if the response contains an error message
        if "Error Message" in data:
            print(f"Error in response: {data['Error Message']}")
            return f"Error in response: {data['Error Message']}"
        
        return data
    else:
        return "Something went wrong"
        

@tool("crypto_currency_time_series")
def crypto_currency_time_series(timeframe: Annotated[str, "The timeframe of the required data. Either 'daily' or 'weekly' or 'monthly'"], symbol: Annotated[str, "The symbol of digital currency. In three letter format, For example: BTC"], market: Annotated[str, "The exchange market. For example: 'EUR'"]):
    "Use this tool when you want to fetch realtime crypto currency time series data. Returns only the top 5 records."
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        return "{'error': 'API key not found, This service has not been configured, thus is not functional'}"
    
    timeframe_dict = {
        "daily": "DIGITAL_CURRENCY_DAILY",
        "weekly": "DIGITAL_CURRENCY_WEEKLY",
        "monthly": "DIGITAL_CURRENCY_MONTHLY"
    }
    if timeframe.lower() not in timeframe_dict:
        return "{'error': Incorrect timeframe format. Use either daily, weekly or monthly'}"
    
    function = timeframe_dict[timeframe.lower()]
    
    if len(symbol) != 3:
        return "{'error': Incorrect symbol format. Use three letter format, For example: BTC'}"

    url = 'https://www.alphavantage.co/query'
    params = {
        'function': function,
        'symbol': symbol,
        'market': market,
        'apikey': api_key
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()

         # Check if the response contains an error message
        if "Error Message" in data:
            print(f"Error in response: {data['Error Message']}")
            return f"Error in response: {data['Error Message']}"
        # Extract the metadata and the top 5 records from the Weekly Time Series
        try:
            metadata = data.get("Meta Data", {})
            time_series = data.get(f"Time Series (Digital Currency {timeframe.lower().capitalize()})", {})
            top_5_records = dict(list(time_series.items())[:5])
            
            return {
                "Meta Data": metadata,
                f"Time Series ({timeframe.capitalize()})": top_5_records
            }
        except Exception as err:
            print(f"Error processing data: {err}")
