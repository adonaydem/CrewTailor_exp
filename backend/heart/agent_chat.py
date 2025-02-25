from .socketio_manager import SocketIOManager
import json
from .tool_defintions import Router, File_List, File_Read, File_Write
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import FunctionMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from dotenv import load_dotenv
import os
import json
import random
import copy
import re
import time
import functools
import requests
import sqlite3
import json
import traceback
from .globals import *
from .utils import *
from threading import Event
class HumanChat:
    """
    Manages a conversation between a human user and an AI agent.

    This class uses a socket.io manager to emit and receive messages.
    It handles various types of messages, including AI messages, tool messages,
    and user input. It also detects when the conversation is stuck in a loop
    or needs to be ended.

    Attributes:
        socketio_manager (object): The socket.io manager used to emit and receive messages.

    Methods:
        get_arguments(inputmessage): Extracts arguments from an input message.
        build_instruction(arguments, team_progress, thread_id_agent): Builds an instruction message for the AI agent.
        handle_ai_message(message, name, socketio_manager, thread_id, inputs): Handles AI messages.
        handle_chat_finalizer(name, socketio_manager, thread_id, inputs): Handles chat finalizer messages.
        handle_tool_message(message): Handles tool messages.
        handle_loop_count(loop_count, warning, inputs, name, socketio_manager): Handles loop counts.
        get_user_input(socketio_manager, thread_id): Gets user input and waits for a response.
        wait_for_user_input(socketio_manager): Waits for user input and handles abort signals.
        run(graph, node_metadata, inputmessage, thread_id, team_progress): Runs the conversation loop.

    Returns:
        None
    """
    def __init__(self, socketio_manager):
        self.socketio_manager = socketio_manager

    def get_arguments(self, inputmessage):
        arguments = inputmessage.tool_calls[0]['args']
        if not isinstance(arguments, dict):
            arguments = json.loads(arguments)
        return arguments

    def build_instruction(self, arguments, team_progress, thread_id_agent):
        return f"""
        **Instruction** from Manager: {arguments['Message']}. 
        Context: {arguments['Context']}.
        team_progress: {json.dumps(team_progress)}.
        
        **Guidelines**
        ID of the current workflow is {thread_id_agent}. Use it in Note taking tool parameter. 
        If a **tool error/loop/hallucination** occurs, you have two tries to fix it, after that you MUST give up. 
        Before you proceed, communicate and recieve additional instructions from the user.
        When calling chat_finalizer tool, make sure to copy and paste detailed result you come up with, since it'll be noted as team progress.
        Never do redundant work(or be stuck in a loop with tools).
        """

    def handle_ai_message(self, message, name, socketio_manager, thread_id, inputs):
        if len(message.tool_calls) > 0 and message.tool_calls[0]['name'] == "chat_finalizer":
            return self.handle_chat_finalizer(name, socketio_manager, thread_id, inputs, message)
        elif len(message.tool_calls) > 0:
            print("Output from agent Tool EXTERNAL: ", message.tool_calls)
            socketio_manager.socketio.emit('process_output', {'output': "I am performing external actions, please wait....", 'agent': name})
        else:
            print("Output from agent EXTERNAL: ", message.content)
            try:
                decoded_output = decode_unicode_escapes(message.content)
            except:
                decoded_output = message.content
            socketio_manager.socketio.emit('process_output', {'output': decoded_output, 'agent': name})
        return True, 2, None

    def handle_chat_finalizer(self, name, socketio_manager, thread_id, inputs, message):
        socketio_manager.socketio.emit('process_output', {
            'output': f"{name} has asked to end this chat. Was this your intention? Yes/No.\nNote! An answer is required to move on.",
            'agent': name
        })
        socketio_manager.socketio.emit('request_user_input', {'thread_id': thread_id, 'message': 'Please provide input'})
        
        print("waiting for user input...")
        user_input = self.wait_for_user_input(socketio_manager)
        if not user_input:
            print("Aborted!")
            return False, 1, message.tool_calls[0]['id']
        
        print("user_input approval: ", user_input)
        if user_input.lower().replace(" ", "") == "no":
            return True, 1, message.tool_calls[0]['id']

        return False, 1, message.tool_calls[0]['id']

    def handle_tool_message(self, message):
        if not isinstance(message.content, dict):
            try:
                content = json.loads(message.content)
            except:
                content = {"tool_response": message.content}
        else:
            content = message.content

        if 'node_done' in content:
            global result
            result = json.dumps(content['node_done']) if isinstance(content['node_done'], dict) else content['node_done']
            return result
        return None

    def handle_loop_count(self, loop_count, warning, inputs, name, socketio_manager):
        if loop_count == 5:
            inputs['messages'] = [HumanMessage(content="Manager Notice: The system has seen you are in a loop of tasks without user interruption. If you are encountering an error, please give up and go back to the user and try to use other options (far from the current process) and don't make the same actions. However, if you are accomplishing tasks successfully, please proceed and try to finish sooner and sorry for the interruption.")]
            warning += 1
        if loop_count >= 10:
            inputs['messages'] = [HumanMessage(content="You have taken too long to respond, please end this conversation immediately!")]
            socketio_manager.socketio.emit('process_output', {'output': "Agent timed out, too many tasks at once....", 'agent': name})
        return warning, loop_count

    def get_user_input(self, socketio_manager, thread_id):
        socketio_manager.socketio.emit('request_user_input', {'thread_id': thread_id, 'message': 'Please provide input'})
        print("waiting for user input...")
        user_input = self.wait_for_user_input(socketio_manager)
        if not user_input:
            print("Aborted!")
            return None
        print("user_input: ", user_input)
        return user_input
        
    def wait_for_user_input(self, socketio_manager):
        user_input = None
        abort_received = False
        event = Event()

        print("Waiting for user input...")
        
        @socketio_manager.socketio.on('user_input')
        def handle_user_input(data):
            nonlocal user_input   
            user_input = data['input']
            print("Received user input: ", user_input)
            event.set()

        @socketio_manager.socketio.on('abort_process')
        def handle_abort_process(data):
            nonlocal abort_received
            abort_received = True
            print("Received abort process signal")
            event.set()

        while user_input is None and not abort_received:
            event.wait(timeout=1)  # Wait up to 1 second for user input or abort signal
            if user_input is None and not abort_received:
                print("Still waiting for user input...")

        if abort_received:
            print("Process aborted by user")
            return None

        return user_input

    def run(self, graph, node_metadata, inputmessage, thread_id, team_progress):
        name = node_metadata['name']
        thread_id_agent = f"{thread_id}_{name}"
        config = {"configurable": {"thread_id": thread_id_agent}}

        arguments = self.get_arguments(inputmessage)
        instruction = self.build_instruction(arguments, team_progress, thread_id_agent)
        inputs = {"messages": [SystemMessage(content=instruction)]}
        
        wants_to_continue, case, _id = True, None, None
        done = False
        result = None
        skip=False
        while not done:
            print("Input to agent: ", inputs)
            loop_count, warning= 0, 0
            skip=False

            for s in graph.stream(inputs, config, stream_mode="values"):
                
                message = s["messages"][-1]
                print("Output from agent INTERNAL OR EXTERNAL: ", message, "Done?", done)
                
                if isinstance(message, AIMessage):
                    wants_to_continue, case, _id = self.handle_ai_message(message, name, self.socketio_manager, thread_id, inputs)
                    print("!!!!!!!!!!!!!!!!!!!", wants_to_continue, case, _id)  
                elif isinstance(message, ToolMessage):
                    result = self.handle_tool_message(message)
                
                if not wants_to_continue and _id is not None:
                    #inputs = {"messages": [ToolMessage(content="The user has aborted.", tool_call_id=_id)]}
                    done = True
                    _id = None
                    print("Aborted")
                    skip=True
                elif wants_to_continue and _id is not None:
                    inputs = {"messages": [HumanMessage(content="Manager: The user is not satisfied or wants to continue chatting.")]}
                    skip=True
                    done = False
                    _id = None
                    print("Continued")
                    break
                
                loop_count += 1
                warning, loop_count = self.handle_loop_count(loop_count, warning, inputs, name, self.socketio_manager)
                if loop_count >= 10:
                   break 
            
            if not done and _id is None and not skip:
                user_input = self.get_user_input(self.socketio_manager, thread_id)
                if user_input is None:
                    return None
                inputs = {"messages": [HumanMessage(content=user_input)]}

        print("FINAL FROM AGENT!!!!!PPPPPPPPPPPPPPPPP: ", result)
        return result


class AutoChat:
    """
    Manages an autonomous agent.
    This class uses a socket.io manager to emit and receive messages.
    It handles various types of messages, including AI messages, tool messages,
    and user input. It also detects when the conversation is stuck in a loop
    or needs to be ended.

    Attributes:
        socketio_manager (object): The socket.io manager used to emit and receive messages.

    Methods:
        get_arguments(inputmessage): Extracts arguments from an input message.
        build_instruction(arguments, team_progress, thread_id_agent): Builds an instruction message for the AI agent.
        handle_ai_message(message, name, socketio_manager, thread_id, inputs): Handles AI messages.
        handle_chat_finalizer(name, socketio_manager, thread_id, inputs): Handles chat finalizer messages.
        handle_tool_message(message): Handles tool messages.
        handle_loop_count(loop_count, warning, inputs, name, socketio_manager): Handles loop counts.
        get_user_input(socketio_manager, thread_id): Gets user input and waits for a response.
        wait_for_user_input(socketio_manager): Waits for user input and handles abort signals.
        run(graph, node_metadata, inputmessage, thread_id, team_progress): Runs the conversation loop.

    Returns:
        None
    """
    def __init__(self, socketio_manager):
        self.socketio_manager = socketio_manager

    def run(self, graph, node_metadata, inputmessage, thread_id, team_progress):
        self.graph = graph
        self.node_metadata = node_metadata
        self.inputmessage = inputmessage
        self.thread_id = thread_id
        self.team_progress = team_progress
        self.name = node_metadata['name']
        self.thread_id_agent = f"{thread_id}_{self.name}"
        self.config = {"configurable": {"thread_id": self.thread_id_agent}}

        arguments = self.get_arguments(self.inputmessage)
        instruction = self.build_instruction(arguments, self.team_progress, self.thread_id_agent)
        print("Instruction!!!!!!: ", instruction)
        inputs = {"messages": [SystemMessage(content=instruction)]}

        response = self.graph.invoke(inputs, self.config)
        
        if not response:
            return None

        final_result = self.process_response(response)
        print("""response::::::::::: """, final_result )
        if final_result:
            return final_result

        return None

    def get_arguments(self, inputmessage):
        arguments = inputmessage.tool_calls[0]['args']
        if not isinstance(arguments, dict):
            arguments = json.loads(arguments)
        return arguments

    def build_instruction(self, arguments, team_progress, thread_id_agent):
        return f"""
        Instruction from Manager: {arguments['Message']}. 
        Context: {arguments['Context']}.
        team_progress: {json.dumps(team_progress)}
        **Guidelines**
        ID of the current workflow is {thread_id_agent}. Use it in Note taking tool parameter. 
        If a **tool error/loop/hallucination** occurs, you have two tries to fix it, after that you MUST give up.
        There is no user interaction. Work alone and do your best.
        Never do redundant work(or be stuck in a loop with tools).
        """

    def process_response(self, response):
        i = -1
        while abs(i) <= len(response['messages']):
            res = response['messages'][i]
            print("res", res)
            if isinstance(res, ToolMessage) and res.name == 'chat_finalizer':
                content = self.parse_content(res.content)
                result = content.get('node_done')
                if isinstance(result, dict):
                    result = json.dumps(result)
                if result:
                    self.emit_output(result)
                    return result
            i -= 1
        return None

    def parse_content(self, content):
        if not isinstance(content, dict):
            try:
                content = json.loads(content)
            except:
                content = {"tool_response": content}
        return content

    def emit_output(self, output):
        try:
            decoded_output = decode_unicode_escapes(output)
        except:
            decoded_output = output
        self.socketio_manager.socketio.emit('process_output', {'output': decoded_output, 'agent': self.name})
        print("Output from agent EXTERNAL: ", decoded_output)
