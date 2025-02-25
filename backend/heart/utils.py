from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from .workflow_master_db import workflow_master_db
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
import logging
from .globals import *
import importlib
from .customizer_v3 import save_graph_structure, generate_code_string


def get_object(_id):
    """
    Retrieves a workflow's langgraph object and workflow details based on the provided ID.

    Parameters:
        _id (str): The ID of the workflow to retrieve.

    Returns:
        tuple: A tuple containing the workflow data and the graph object.

    Raises:
        Exception: If an error occurs during the retrieval process.
    """
    try:
        workflow_data = get_workflow(_id)
    except Exception as e:
        logging.error(str(e))



    workflow_name = workflow_data['metadata']['name'].replace(" ", "_")
    uid = workflow_data['uid']
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if not os.path.exists(f"w_modules/{uid}/{workflow_name}.py") or workflow_data["uptodate"][0] == "no":
        logging.info("creating module")
        save_graph_structure(workflow_data)
        db_obj = workflow_master_db()
        result, status = db_obj.set_workflow_uptodate_db(_id)
    
    try:
        # Adjust the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        # Use absolute import
        module = importlib.import_module(f"heart.w_modules.{uid}.{workflow_name}")
        graph_object = getattr(module, "graph_object")
        return workflow_data, graph_object
    except ImportError:
        logging.error(f"Module '{workflow_name}' not found")
    except AttributeError:
        logging.error(f"graph_object not found in module '{workflow_name}'")

def get_workflow(_id):
    """
    Retrieves a workflow from the database based on the provided ID.

    Args:
        _id (str): The ID of the workflow to retrieve.

    Returns:
        dict: The workflow data.

    Raises:
        Exception: If an error occurs during the retrieval process.
    """
    db_obj = workflow_master_db()
    result, status = db_obj.get_workflow_db(_id)
    if status != 200:
        raise Exception("Database error when getting workflow: " + str(status))

    return result

def parse_nodes_data(nodes_data):
    wanted = ['id','name', 'description', 'toolkits', 'human_direction', 'children']
    filtered = [{key: value for key,value in node.items() if key in wanted} for node in nodes_data]
    json_data = json.dumps(filtered)
    return json_data

def manager_prompt(workflow_data):
    """
    Generates a system prompt for a manager to manage a workflow in the CrewTailor AI app.

    Args:
        workflow_data (dict): A dictionary containing the workflow data, including nodes and metadata.

    Returns:
        str: A formatted system prompt for the manager to manage the workflow.
    """
    nodes_name = [node['name'] for node in workflow_data['nodes']]
    nodes_data = parse_nodes_data(workflow_data['nodes'])

    feedbacks = ""

    if "approved_feedbacks" in workflow_data:
        fb_list = [row['content'] for row in workflow_data['approved_feedbacks'][:10]]

        intro = "Here are the feedbacks you and your team recieved from previous interactions.\n\t-"

        feedbacks += intro

        content = "\n".join(f"{i+1}. {feedback}" for i, feedback in enumerate(fb_list))

        feedbacks += content

        conclusion = "Analyse the feedbacks, and figure out which team members it applies to and tell them during work. You are responsible for disseminating the relevant feedbacks to the agents."



    system_prompt = f"""
    You are part of CrewTailor, an AI app for customizable workflows and teams of AI agents.
    Your role: Manage the workflow "{workflow_data['metadata']['name']}" and facilitate communication, division of labour, task allocation between AI agents and the User.
    **Key Details**:
    1. Agents have defined purposes ({", ".join(nodes_name)}). Some have `children` attributes indicating their workflow hierarchy (not strict).
    2. Communicate only via the **Router tool**: 
    - **To**: Specify "User" or an agent's name.
    - **Message**: Provide instructions or updates.
    - **Context**: Short description of current overall status.
    - In one instance, One Router tool call is allowed. Meaning, you can only message one entity at a time.
    **Workflow of instructions for you:**
    1. **Feedback**:
    - Analyze past feedback and see how it applies to current instructions.
    2. **Task Allocation**:
    - If user's request seems irrelevant to your team, abort and return to the User.
    - Either talk back to the User or Decide on the next 1 appropriate task to perform.
    - Decide on which - an agent or User to contact next. Choose one recipient(either one agent or the User) at a time and give it one task only. 
    - Dependent agents (`human_direction = "yes"`) can talk to the User directly.
    - Autonomous agents (`human_direction = "no"`) only respond to you.
    3. **Messaging**:
    - If message is to an agent, be imperative. The agent requires a very detailed sequence of instructions(sentences) including: 1. Objective 2. General steps of how to do it(eg. using what tools)
    - If message is to the User, be friendly and conversational.
    4. **Validation and Workflow Management**:
    - Ensure progress by responding to agent outputs or clarifying with the User.
    - Handle errors by logging issues and informing the User.
    - Evaluate the response for factual accuracy, logical consistency, and unsupported claims, flagging hallucinations and suggesting corrections. The relpies from agents must be lengthy and full transparency. For example the following reply from agent is unacceptable: The analysis has been done and the task has been recorded. 
    **Data**:
    - Workflow Metadata: {json.dumps(workflow_data['metadata'])}
    - Agent Purposes: {nodes_data}
    Feedbacks:
    {feedbacks}

    Keep communication concise and aligned with the workflow goal.
    """

    return system_prompt

def decode_unicode_escapes(text):
    """
    Decodes Unicode escape sequences in a given text.

    This is made to fix Gemini's models' emoji outputs, since they generate emojis in unicode.

    Parameters:
    text (str): The input text containing Unicode escape sequences.

    Returns:
    str: The decoded text with Unicode escape sequences replaced by their corresponding characters.
    """
    # This regex finds all escape sequences in the text
    unicode_escape_re = re.compile(r'\\([0-9]{3})')

    # Function to convert each match to the corresponding character
    def replace_match(match):
        try:
            octal_str = match.group(1)
            # Convert the octal to an integer
            char = int(octal_str, 8)
            # Convert the integer to a character
            return chr(char)
        except Exception as e:
            # If any error occurs, return the original match
            print(f"Error decoding {match.group(0)}: {e}")
            return match.group(0)

    # Replace the octal escapes with their actual characters
    try:
        decoded_text = unicode_escape_re.sub(replace_match, text)
        # Decode the UTF-8 bytes to get the final string
        return decoded_text.encode('latin1').decode('utf-8')
    except Exception as e:
        print(f"Error during decoding: {e}")
        return text

def get_tools(node_toolkits):
    """
    Retrieves a list of approved tools based on the provided node toolkits.

    This is a utility for create_agent to verify and provide the necessary tools based on the node's toolkits.
    Args:
        node_toolkits: A list of toolkits to filter the approved tools from.

    Returns:
        A list of approved tools.
    """
    global toolkit_keys
    global toolkits
    approved = []
    approved = copy.deepcopy(toolkits['core'])

    for possible_toolkit in node_toolkits:

        if possible_toolkit in toolkit_keys:
            approved += toolkits[possible_toolkit]

    print("APPROVED TOOLS: ", approved)
    return approved


def create_agent(llm, team_members, node_metadata):
    """
    Creates an AI agent based on the provided parameters and returns a graph representing the agent.

    Args:
        llm: The language model used by the agent.
        team_members: A list of team members the agent will collaborate with.
        node_metadata: A dictionary containing metadata about the node the agent is part of.

    Returns:
        A langgraph graph representing the created agent.
    """
    conn = sqlite3.connect("agent_memory.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    tools = get_tools(node_metadata['toolkits'])
    tool_names = [tool.name for tool in tools]
    name = node_metadata['name']
    system_prompt = ""
    if node_metadata['human_direction'] == "yes":
        system_prompt += f"""
        You are an AI agent within CrewTailor, an app that customizes workflows by leveraging AI teams. You are an AI agent: {name}, and your AI agent team includes {team_members}. Each member operates autonomously within their expertise. Communication between team members is facilitated by manager.
        
        Your role is: {node_metadata['description']}

        **Strict Workflow: Complete each step before proceeding to the next.**

        1. Receive instructions from the manager pertinent to your expertise.
        2. Ask yourself: 1. Can my expertise or tools be used to address the user's or team's needs? 2. Do I have the necessary context to fulfill the request? If either of these conditions are not met, Abort and You must and encouraged to request and obtain additional information from the manager.
        3.Independently utilize your knowledge, past **team_progress** and available tools ({", ".join(tool_names)}) to execute tasks. 
        4. **important** Present your work openly, in full details(including the execution/retrieval process) and await user feedback.
        5. If the user is unsatisfied, revisit Step 2, employing alternative methods.
        7. When you identify very important feedback from the user that may be critical for improving future interactions, record it using the Note_Taker tool (if you decide to use it, use only once(and one short sentence) per session).
        8. If you require input from another team member, request the manager to obtain it. 
        9. When the user indicates the chat should conclude, use the chat_finalizer tool. In the final outcome, copy and paste the refined, detailed result you come up with, since it'll be noted as team progress.

        **Instructions:**
        - Directly employ tools without seeking permission or announcing their use.
        - Ensure all necessary parameters are included when invoking tools.
        - If you're not equipped to perform a task, inform the user: "I am not configured to accomplish that task, but you can set me up in the software app."
        - The human user and the manager are the only communication means between team members. 
        - Tools and team members are different, tools are basic functions. 

        Always use chat_finalizer to finalize the chat.
        Your objectives are to deliver accurate, helpful responses, maintain a record of critical feedback, and showing team collaboration and confirm user satisfaction prior to finalizing the chat.
        """
    else:
        system_prompt = f"""
        You are an AI agent within CrewTailor, an application that enables users to customize workflows by leveraging AI teams. You are an AI agent: {name}, and you are part of a team comprising AI agents: {team_members}.
        You are an autonomous agent with specialized expertise, working independently.
        
        **Strict Workflow:**
        1. **Instruction Reception and Discussion**: Receive instructions from the manager relevant to your expertise, and discuss for further info.
        2. **Condition**:  Ask yourself: 1. Can my expertise or tools be used to address the user's or team's needs? 2. Do I have the necessary context to fulfill the request? If either of these conditions are not met, Abort and You must and encouraged to request and obtain additional information from the manager.
        3. **Task Execution**: Independently utilize your knowledge, past **team_progress** and available tools ({", ".join(tool_names)}) to perform the necessary actions.
        4. **Outcome Evaluation**: Assess if the result aligns with the instructions. If not, revisit Step 2 and apply alternative techniques.
        5. **Feedback Recording**: Use the Note_Taker tool to document critical feedback or information that may enhance future interactions. Use this tool sparingly. Only one short sentence is allowed. The main interaction tool is chat_finalizer.
        6. **Finalization**: Once the task is complete, employ the chat_finalizer tool. In the outcome parameter, provide a detailed report of the task's execution, including the execution/retrieval process, the actual statisic, quantiative, qualitative data in detail.

        **Instructions:**
        - **Direct Tool Usage**: Invoke tools directly without seeking permission or announcing their use.
        - **Parameter Accuracy**: Ensure all required parameters are accurately provided when using tools.
        - **Task Limitations**: If unable to fulfill a request due to configuration constraints, inform the user: "I am not configured to accomplish that task, but you can set me up in the software app."

        Always use chat_finalizer to finalize the chat.
        Your objective is to provide accurate and helpful responses, maintain interaction records, and task completion without human intervention.
        """
    
    
    graph = create_react_agent(llm, tools=tools, messages_modifier=system_prompt, checkpointer=memory)
    return graph
