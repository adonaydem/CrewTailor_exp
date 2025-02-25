from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import AgentExecutor
from langchain import hub
import os
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.memory import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import FunctionMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]
#when needded:Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 3 results ONLY. This means, always put the LIMIT in your SELECT query, unless the user says otherwise.
def system_prompt():
    system_prefix = f"""
    You are an agent interacting with a SQL database as part of CrewTailor, an AI Workflow Automation System assisting users in daily activities.

    **Strict Workflow:**
    1. Receive the user's query and analyze(as per guideline below) in plain language.
    2. Check the tables and relevant table schema and construct a correct SQLite3 query(CREATE, SELECT, INSERT, UPDATE, DELETE).
    3. Execute the query after verifying its correctness.
    4. Handle errors (up to 3 attempts), explaining issues if unresolved. If you reciece logical or syntax errors more than third one, abourt immediately.
    5. Provide results in simple, non-technical language.
    6. For DELETE and UPDATE operations:
    - Use SELECT to verify data and inform the user of affected rows.

    **Guidelines:**
    - Query only relevant columns.
    - Don's stop at schema, use relevant CRUD operations, if necessary.
    - Use provided tools and their outputs for answers.
    - Inform the user if a query yields no results.
    - For date/time: Use `CURRENT_TIMESTAMP` or `CURRENT_DATE`.
    - Exit after 3 error-handling attempts and explain the issue.
    - Monitor repeated or excessive queries, especially those previously answered or unresolved. Politely inform the user and suggest refining their request.
    - If the same question is asked multiple times without valid changes, remind the user of prior responses.
    """
    return system_prefix


from .db_config import Config
def db_agent(query, s_id):
    print("QUERY to DB:",query)
    parts = s_id.split('_')
    user_id = parts[1]
    workflow_id = parts[2]
    current_db = Config.get_workflow_database_path(user_id, workflow_id)
    
    db_directory = os.path.dirname(current_db)
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
    
    # Create an empty file if the database file doesn't exist
    if not os.path.exists(current_db):
        open(current_db, 'a').close()
    
    # Connect to the SQLite database
    db = SQLDatabase.from_uri(f"sqlite:///{current_db}")
    llm = ChatOpenAI(model_name="gpt-4o-mini")

        

    toolkit = SQLDatabaseToolkit(db=db,llm=llm)


    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )

    system_prefix = system_prompt()
    full_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(system_prefix),
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
        prompt=full_prompt,
        agent_type="tool-calling",
        verbose=True,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        max_iterations=6
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
        print("DBDBDBBDBDB:",response)
        return response['output']
    except:
        return "An error occured. "