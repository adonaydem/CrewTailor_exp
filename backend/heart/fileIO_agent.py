from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from tempfile import TemporaryDirectory
from langchain_community.agent_toolkits import FileManagementToolkit
import os
from langchain_google_genai import ChatGoogleGenerativeAI

def fileIO_agent(query, thread_id):
    """
    This function, fileIO_agent, handles file input/output operations based on the provided query and thread_id.
    It leverages ReAct agent to and FileManagementToolkit to perform the file operations.
    It takes two parameters: 
    query (str): The input query that determines the file operation to be performed.
    thread_id (str): A unique identifier that contains user_id and workflow_id, used to construct the working directory.
    
    The function returns a dictionary containing the result of the file operation. 
    If the operation is successful, it returns a dictionary with a 'message' key containing the response content.
    If an error occurs, it returns a dictionary with an 'error' key containing the error message.
    """
    parts = thread_id.split('_')
    user_id = parts[1]
    workflow_id = parts[2]
    working_directory = os.path.join(os.getcwd(), 'filespace', user_id, workflow_id, thread_id)

    try:
        if not os.path.exists(working_directory):
            os.makedirs(working_directory)
        
        file_management_toolkit = FileManagementToolkit(
            root_dir=working_directory,
            selected_tools=["read_file", "write_file", "list_directory"],
        )
        file_management_tools = file_management_toolkit.get_tools()

        from langchain_openai import ChatOpenAI


        chat_llm = ChatOpenAI(model="gpt-4o-mini")
        graph = create_react_agent(chat_llm, tools=file_management_tools)
        inputs = {"messages": query}
        response = graph.invoke(inputs)
        print("!!!fileio:", response)
        return {"message": response['messages'][-1].content}
    
    except Exception as e:
        print("!!!error fileio: ", str(e))
        return {"error": str(e)}