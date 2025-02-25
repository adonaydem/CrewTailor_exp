import json
import os
def generate_code_string(workflow_data):
    """
    Generates a code string representing a graph object based on the provided workflow data.

    Args:
        workflow_data (dict): A dictionary containing the nodes and their corresponding data.

    Returns:
        str: A code string representing the graph object.
    """



    base = """
def graph_object(manager, create_agent, agent_node, workflow_data):
        import operator
        from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
        import json
        import functools
        from langgraph.graph import END, StateGraph
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv


        llm = ChatOpenAI(model="gpt-4o-mini")

        manager_node = functools.partial(manager, llm=llm, workflow_data=workflow_data) 
         
    """
    team_members = ""
    nodes = workflow_data['nodes']
    node_state = ""
    for node in nodes:
        team_members += f"{node['name']}, "
        node_state += f"node_{node['id']}: Optional[str]\n            "
    for node in nodes:
        node_desc = json.dumps(node, indent=4)
        agent_init = f"""    
        {node['name'].replace(" ", "_")}_agent = create_agent(llm, "[{team_members}]", {node})
        {node['name'].replace(" ", "_")}_node = functools.partial(agent_node, graph={node['name'].replace(" ", "_")}_agent, node_metadata={node})
        """
        
        base += agent_init

    
    graph_start_code = f"""
    \n
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver
        from typing_extensions import TypedDict
        from typing import Annotated, List, Optional, Dict

        conn = sqlite3.connect("apps.db", check_same_thread=False)

        memory = SqliteSaver(conn)

        class AgentState(TypedDict):
            messages: Annotated[List[BaseMessage], operator.add]
            w_id: str
            Next: Optional[str]
            thread_id: Optional[str]
            progress: Annotated[Optional[List[Dict]], operator.add]
        
        graph = StateGraph(AgentState)
        graph.add_node("Manager", manager_node) 
        
    """
    base += graph_start_code

    map_dict = {}
    for node in nodes:
        edge_node_code = f"""\n
        graph.add_node("{node['name']}", {node['name'].replace(" ", "_")}_node)
        graph.add_edge("{node['name']}", "Manager")        
        """
        map_dict[node['name']] = node['name']
        base += edge_node_code

    map_dict['User'] = "END"

    map_str = json.dumps(map_dict)
    map_str = map_str.replace('"END"', 'END')
    map_code = f"""\n
        graph.add_conditional_edges(
            "Manager",
            lambda x: x['Next'],
            {map_str},
        )
    """
    base += map_code
    ending = """\n
        graph.set_entry_point("Manager")

        return graph.compile(checkpointer=memory)"""

    base += ending
    return base


def save_graph_structure(workflow_data):
    """
    Saves the generated graph structure code string to a file with the name
    `{workflow_name}.py` in the directory `w_modules/{uid}`. If the directory does
    not exist, it creates it. The `workflow_data` parameter is a dictionary
    containing the workflow data, including metadata and nodes. The function
    does not return anything.

    Parameters:
    - workflow_data (dict): A dictionary containing the workflow data.

    Returns:
    - None
    """

    
    code_string = generate_code_string(workflow_data)
    workflow_name = workflow_data['metadata']['name'].replace(" ", "_")
    uid = workflow_data['uid']
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Define the directory path
    directory = f"w_modules/{uid}"

    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Define the filename
    filename = f"{directory}/{workflow_name}.py"

    # Write the code string to the file
    with open(filename, 'w') as file:
        file.write(code_string)
