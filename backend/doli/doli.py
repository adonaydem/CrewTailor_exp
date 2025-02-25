from langchain_core.messages import FunctionMessage, HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_tool_calling_agent
from typing import Annotated, List
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.agents import AgentExecutor
from langchain import hub
from .doli_db import workflow_master_db
import json
from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotPromptTemplate,
        MessagesPlaceholder,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )

thread_id = None
challenge_id = None
@tool
def submit_evaluation(score : Annotated[float, "Overall score out of 40"], content : Annotated[str, "Full content of evaluation report"]) -> str:
    "Use this tool to submit a thoroughly calculated and summed up score AND to submit evaluation report.."
    global thread_id
    global challenge_id
    db_obj = workflow_master_db()
    result, status = db_obj.set_challenge_evaluation_db(thread_id, score, content)
    if status != 200:
        return result
    
    return "Evaluation Submitted successfully"



def get_progress(thread_id):
    """
    Retrieves the progress of a workflow based on the provided thread ID.

    Args:
        thread_id (str): The ID of the thread to retrieve progress for.

    Returns:
        The progress result.
    """
    db_obj = workflow_master_db()
    result, status = db_obj.get_progress_db(thread_id)
    if status != 200:
        raise Exception("P Database error: " + str(status))
    
    return result

def get_workflow(workflow_id):
    """
    Retrieves a workflow from the database based on the provided workflow ID.

    Args:
        workflow_id (str): The ID of the workflow to retrieve.

    Returns:
        dict: A dictionary containing the workflow data, including metadata and nodes.
    """
    db_obj = workflow_master_db()
    result, status = db_obj.get_workflow_db(workflow_id)
    if status != 200:
        raise Exception("W Database error: " + str(status))
    output = {}
    output['metadata'] = {"name": result['metadata']['name'], "description": result['metadata']['description'], "to_do_list": result['metadata']['to_do_list']}
    output['nodes'] = [{"name": node['name'], "description": node['description'], "toolkits": node['toolkits']} for node in result['nodes']]
    return output

def call_doli(thread_id_input):
    """
    This function is used to call Doli, an intelligent examiner, 
    to evaluate the progress of a team based on a challenge instance.

    Parameters:
    thread_id_input (int): The ID of the thread to be evaluated.

    Returns:
    bool: True if the evaluation is successful, False otherwise.
    """
    global thread_id
    print("THHH ", thread_id_input)
    db_obj = workflow_master_db()
    challenge_instance, status = db_obj.get_challenge_instance_db(thread_id_input)

    if status != 200:
        raise Exception("D Database error: " + str(status))
    
    thread_id = thread_id_input
    print("THREAD ", thread_id)

    team_progress = get_progress(thread_id)
    workflow = get_workflow(challenge_instance['workflow_id'])
    challenge_id = challenge_instance['challenge_id']
    challenge_content = challenge_instance['challenge_content']
    system_prefix = f"""
    You are Doli, an intelligent examiner. You are part of an app called CrewTailor, that allows users to build custom workflows powered by AI team. Each team consists of a manager and specialized team members.
    There is a feature called challenge in the app, that allows users to compete with eachother. The challenge will contain a certain task in a certain context.
    The human will enter this challenge and try to give the best outcome as described in the challenge. You will recieve the summary progress of each of the team members.

    You will score them based on:
    Quality of Work:
    Accuracy: Are the outputs from all team members correct and free of errors?
    Thoroughness: Is the task completed with sufficient detail by each member?

    Creativity and Problem-Solving:
    Innovation: Did the team collectively bring new ideas or solutions?
    Adaptability: How well did the team handle unexpected challenges?

    Collaboration and Communication:
    Teamwork: How effectively did the team work together?
    Clarity: Is the overall progress report clear, concise, and easy to understand?

    Adherence to Guidelines:
    Compliance: Did the team follow the provided guidelines and instructions?
    Consistency: How consistent is the team’s output with the Challenge’s standards?

    
    Each of the above subcategories are 5 points, for a total of 40 points. 5 being "I strongly agree" and 1 being "I strongly disagree" and 3 being neutral. Be critical and give reasonable and objective scoring, don't try to be nice.
    When calculating the score, think step by step and becareful not to commit a mistake.
    Once you have calculated the score, you will create a very consice summary evaluation report.
    After that, proceed to submission of these things using the submit_evaluation tool.


    #Do NOT talk to the user, There is no conversation. Just do your work.

    Here is the proposed result:

    **The skeleton of the workflow: node represents an AI agent **
    {json.dumps(workflow, indent=4)}

    **Challenge content**:
    {challenge_content}

    **Outcomes of each member**:
    {json.dumps(team_progress, indent=4)}

    Immediately proceed to your task.
    """
    print(system_prefix)
    full_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(system_prefix),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    tools = [submit_evaluation]
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    llm = llm.bind_tools([submit_evaluation])
    agent = create_tool_calling_agent(llm, tools, full_prompt)

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    result = agent_executor.invoke({"input": "go ahead"})
    return True

