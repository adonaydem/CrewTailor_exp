from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import AgentExecutor
from langchain import hub
from langchain_community.utilities import SQLDatabase
from langchain.memory import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.messages import FunctionMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
import os
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def system_prompt_creator(specific_use, tables):
    system_prefix = f"""SYSTEM MESSAGE: You are an agent designed to interact with a SQL database. You are part of a Professional Assistant System called PAM, that helps users in their day to day activities. 
    As part of this system, You are needed to help the user access the database to handle their professional and private issues. But the user doesn't know the technicality so all you response should be in non-technical tone.
    Given an input question, create a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
    
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    You have access to tools for interacting with the database.
    Only use the given tools. Only use the information returned by the tools to construct your final answer.
    You MUST double check your query before executing it. If you get an error while executing a query, edit the query and try again.
    Check the schema of the tables in the database, before doing your operations. 
    If you keep getting erros, check table schema. If you get errors more than 3 times, then give up. In your response explain every detail of the error.

    If you are going to use DELETE and INSERT operations in your SQL query, ALWAYS retrieve aprroval from the user, explaining your action, before executing. This is a must and no human CAN NOT bypass it.
    If you need to use DELETE and UPDATE operations in your SQL query, before you do, first check using the SELECT operation using the details provided, and verify the existence of the data and insure you are not affecting many other rows that you shouldn't. Then, tell the user how many data will be affected if you proceed with the UPDATE or DELETE operation and gain approval first.
    
    If your query yields an empty result, it means there are no data for the requested operation.
    REMEMBER, The following operations need user approval before execution: "INSERT", "DELETE", "UPDATE" 

    You can access current date and time by using the following query: "SELECT CURRENT_TIMESTAMP". If you want to use the current date you should use CURRENT_DATE, instead of DATE('now').
    Here in this application specfically, {specific_use}
    Here, you will find the columns of each table. Don't ever make mistakes in naming tables and columns because you have clear information below. Adjust your query according to them:
    {tables}

    When you have the result, provide the result of your observation, as the output.
    REMEMBER! if you get an error, tell the user the sql query you used.
    """
    return system_prefix


def events_db(query, s_id):
    """
    This is a utility for the tools give by the app.
    This function is used to interact with the events table in a database.

    It takes two parameters: query and s_id. The query parameter is a string representing the query to be executed on the database.
    The s_id parameter is a string representing the session id of the user.

    The function returns a dictionary containing the output of the sql agent.
    """
    db = SQLDatabase.from_uri("sqlite:///sql_tools.db")
    
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini")
        
        

    toolkit = SQLDatabaseToolkit(db=db,llm=llm)


    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )
    use = "You are part of a calendar app that helps users in scheduling, managing events, time management."
    tables = """
    1. table_name: events
        use the following column names in your queries:  {created_datetime, id, title, start_datetime, end_datetime, location, recurring, attendee, status, description}
    """
    system_prefix = system_prompt_creator(use, tables)
    full_prompt = ChatPromptTemplate.from_messages(
        [
            HumanMessage(system_prefix),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
   

    prompt = hub.pull("hwchase17/react")
    memory = ChatMessageHistory(session_id=s_id)
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        prompt=prompt,
        verbose=True,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )
    agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    )
    
    try:
        response = agent_with_chat_history.invoke(
            {"input": query},
            config={"configurable": {"session_id": s_id}},
            )
        print("EVENTTTTTT",response)
        return response['output']
    except:
        return "An error occured while processing your request. Please try again later."



def tasks_db(query, s_id):
    """
    This is a utility for the tools give by the app.
    This function is used to interact with the events table in a database.

    It takes two parameters: query and s_id. The query parameter is a string representing the query to be executed on the database.
    The s_id parameter is a string representing the session id of the user.

    The function returns a dictionary containing the output of the sql agent.
    """
    db = SQLDatabase.from_uri("sqlite:///sql_tools.db")
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o")
        
        



    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )
    use = "You are part of a task manager app that helps users in task creation, task organization and tracking."
    tables = """
    1. table_name: tasks
        use the following column names in your queries:  {id, timestamp, title, duedate, content, status}
    """
    system_prefix = system_prompt_creator(use, tables)
    full_prompt = ChatPromptTemplate.from_messages(
        [
            HumanMessage(system_prefix),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
   

    prompt = hub.pull("hwchase17/react")
    memory = ChatMessageHistory(session_id=s_id)
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        prompt=prompt,
        verbose=True,
        return_intermediate_steps=True
    )
    agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    )
    
    try:
        response = agent_with_chat_history.invoke(
            {"input": query},
            config={"configurable": {"session_id": s_id}},
            )
        print("EVENTTTTTT",response)
        return response['output']
    except:
        return "An error occured while processing your request. Please try again later."


def projects_db(query, s_id):
    """
    This is a utility for the tools give by the app.
    This function is used to interact with the projects table in a database.

    It takes two parameters: query and s_id. The query parameter is a string representing the query to be executed on the database.
    The s_id parameter is a string representing the session id of the user.

    The function returns a dictionary containing the output of the sql agent.
    """
    db = SQLDatabase.from_uri("sqlite:///sql_tools.db")
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini")
        
        



    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )
    use = "You are part of a project manager app that helps users in project creation, tracking and overall management."
    tables = """
    1. table_name: projects
        use the following column names in your queries:  {id, timestamp, project_name, description, start_date, end_date, status, priority}
    """
    system_prefix = system_prompt_creator(use, tables)
    full_prompt = ChatPromptTemplate.from_messages(
        [
            HumanMessage(system_prefix),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
   

    prompt = hub.pull("hwchase17/react")
    memory = ChatMessageHistory(session_id=s_id)
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        prompt=prompt,
        verbose=True,
        return_intermediate_steps=True
    )
    agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    )
    
    try:
        response = agent_with_chat_history.invoke(
            {"input": query},
            config={"configurable": {"session_id": s_id}},
            )
        print("EVENTTTTTT",response)
        return response['output']
    except:
        return "An error occured while processing your request. Please try again later."


def users_db(query, s_id):
    """
    This is a utility for the tools give by the app.
    This function is used to interact with the users table in a database.

    It takes two parameters: query and s_id. The query parameter is a string representing the query to be executed on the database.
    The s_id parameter is a string representing the session id of the user.

    The function returns a dictionary containing the output of the sql agent.
    """
    db = SQLDatabase.from_uri("sqlite:///sql_tools.db")
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini")
        
        



    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )
    use = "You are part of a personal assistant app that helps users in in keeping their profile information."
    tables = """
    1. table_name: users
        use the following column names in your queries:  {"user_id", "email", "full_name", "profession", "created_at", "contact_number", "address"}

    """
    system_prefix = system_prompt_creator(use, tables)
    full_prompt = ChatPromptTemplate.from_messages(
        [
            HumanMessage(system_prefix),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
   

    prompt = hub.pull("hwchase17/react")
    memory = ChatMessageHistory(session_id=s_id)
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        prompt=prompt,
        verbose=True,
        return_intermediate_steps=True
    )
    agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    # This is needed because in most real world scenarios, a session id is needed
    # It isn't really used here because we are using a simple in memory ChatMessageHistory
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    )
    
    try:
        response = agent_with_chat_history.invoke(
            {"input": query},
            config={"configurable": {"session_id": s_id}},
            )
        print("EVENTTTTTT",response)
        return response['output']
    except:
        return "An error occured while processing your request. Please try again later."









