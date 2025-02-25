from gevent import monkey
monkey.patch_all()

from flask import Flask, jsonify, request, render_template, send_from_directory, session
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
from model.workflow_master_db import workflow_master_db
from pam.main_010 import call_graph as call_graph_pam
from heart.workflow_heart_v3 import call_graph as call_graph_heart
from heart.socketio_manager import SocketIOManager
from heart.db_config import Config
from doli.doli import call_doli
import random
from datetime import datetime
import os
from flask_caching import Cache
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app, resources={r"/*": {"origins": [os.getenv('FRONTEND_URL')]}}, supports_credentials=True)
#socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
socketio = SocketIO(app, cors_allowed_origins="*")
socketio_manager  = SocketIOManager()
socketio_manager.socketio = socketio
#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
#cache = Cache(app, config={'CACHE_TYPE': 'simple'}) 



@app.route('/upload_file', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def upload_file():
    """
    Handles file uploads from the client.

    This function is responsible for receiving file uploads from the client, 
    validating the request, and saving the file to the server's file system.

    Parameters:
    None

    Returns:
    A JSON response indicating the result of the file upload operation.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    user_id = request.form['userId']
    workflow_id = request.form['workflowId']
    thread_id = request.form['threadId']
    cwd = os.getcwd()

    # Check if 'heart' is already in the current working directory path
    if cwd.endswith('heart'):
        directory = os.path.join(cwd, 'filespace', user_id, workflow_id, thread_id)
    else:
        directory = os.path.join(cwd, 'heart', 'filespace', user_id, workflow_id, thread_id)
        
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, file.filename)
    file.save(file_path)

    return jsonify({"message": "File uploaded successfully"}), 200

@app.route('/list_files/<user_id>/<workflow_id>/<thread_id>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def list_files(user_id, workflow_id, thread_id):
    """
    Handles file uploads from the client.

    This function is responsible for receiving file uploads from the client, 
    validating the request, and saving the file to the server's file system.

    Parameters:
    None

    Returns:
    A JSON response indicating the result of the file upload operation.
    """
    # Get current working directory
    cwd = os.getcwd()

    # Check if 'heart' is already in the current working directory path
    if cwd.endswith('heart'):
        directory = os.path.join(cwd, 'filespace', user_id, workflow_id, thread_id)
    else:
        directory = os.path.join(cwd, 'heart', 'filespace', user_id, workflow_id, thread_id)


    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            return jsonify([])

        # Force directory and files to be refreshed
        os.utime(directory, None)
        files = os.listdir(directory)
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]


        # Check if the files are actually accessible
        for file in files:
            file_path = os.path.join(directory, file)

        return jsonify(files)
    except Exception as e:
        return jsonify([]), 404


@app.route('/download_file/<user_id>/<workflow_id>/<thread_id>/<filename>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def download_file(user_id, workflow_id, thread_id, filename):
    """
    A function to download a file based on user, workflow, thread, and filename.
    """
    cwd = os.getcwd()

    # Check if 'heart' is already in the current working directory path
    if cwd.endswith('heart'):
        directory = os.path.join(cwd, 'filespace', user_id, workflow_id, thread_id)
    else:
        directory = os.path.join(cwd, 'heart', 'filespace', user_id, workflow_id, thread_id)


    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/get_tables', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_tables():
    """
    Retrieves a list of tables from a SQLite database based on user ID and workflow ID.

    Args:
        user_id (str): The ID of the user.
        workflow_id (str): The ID of the workflow.

    Returns:
        A JSON response containing a list of tables if successful, or an error message if not.

    Raises:
        400: If user ID or workflow ID is missing.
        500: If an error occurs while connecting to the database or retrieving tables.
    """
    user_id = request.args.get('user_id')
    workflow_id = request.args.get('workflow_id')

    if not user_id or not workflow_id:
        return jsonify({'error': 'Missing user_id or workflow_id'}), 400

    db_path = Config.get_workflow_database_path(user_id, workflow_id)
    
    if not os.path.exists(db_path):
        return jsonify({'tables': []})

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_table_data', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_table_data():
    """
    Retrieves table data from a SQLite database based on user ID, workflow ID, and table name.

    Parameters:
        None

    Returns:
        A JSON response containing the fetched data if successful, or an error message if an exception occurs.

    Raises:
        None
    """
    user_id = request.args.get('user_id')
    workflow_id = request.args.get('workflow_id')
    table_name = request.args.get('table_name')

    if not user_id or not workflow_id or not table_name:
        return jsonify({'error': 'Missing user_id or workflow_id or table_name'}), 400

    db_path = Config.get_workflow_database_path(user_id, workflow_id)
    
    if not os.path.exists(db_path):
        return jsonify({'error': "Database doesn't exist"}), 400

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Set the row factory to sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        
        # Convert each row to a dictionary
        data = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_user', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def add_user():
    """
    Handles the POST request to add a new user.

    Parameters:
        None (request data is retrieved from the request object)

    Returns:
        A JSON response containing the result of the add user operation, along with a corresponding HTTP status code.
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    workflows_db_object = workflow_master_db()



    response, status_code = workflows_db_object.add_user_db(data)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/add_workflow/<uid>', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def add_workflow(uid):
    """
    Handles the POST request to add a new workflow for a given user.

    Parameters:
        uid (str): The unique identifier of the user.

    Returns:
        A JSON response containing the result of the add workflow operation, along with a corresponding HTTP status code.
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    required_metadata_keys = {"description", "name", "public", "to_do_list"}
    required_node_keys = {"description", "human_direction", "id", "name"}
    valid_toolkits = {"file_management", "project_management", "task_management", "event_management", "database_management"}

    # Validate metadata
    metadata = data.get("metadata")
    if not metadata or not required_metadata_keys.issubset(metadata):
        error_message = "Invalid metadata format"
        return jsonify({"error": error_message}), 400

    # Validate nodes
    nodes = data.get("nodes")
    if not nodes or not isinstance(nodes, list):
        error_message = "Invalid nodes format"
        return jsonify({"error": error_message}), 400

    for node in nodes:
        if not required_node_keys.issubset(node):
            error_message = f"Invalid node format: {node}"
            return jsonify({"error": error_message}), 400
        if not isinstance(node["children"], list):
            error_message = f"Invalid children format in node: {node}"
            return jsonify({"error": error_message}), 400
        if node["human_direction"] not in {"yes", "no"}:
            error_message = f"Invalid human_direction in node: {node}"
            return jsonify({"error": error_message}), 400
        if "toolkits" in node and (not all(toolkit in valid_toolkits for toolkit in node["toolkits"])):
            if (not isinstance(node["toolkits"], list)):
                node['toolkits'] = []
            error_message = f"Invalid toolkits in node: {node}"
            return jsonify({"error": error_message}), 400

    # Proceed with database operations
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.add_workflow_db(uid, metadata, nodes)
    workflows_db_object.close()


    return jsonify(response), status_code


@app.route('/save_messages/<uid>', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def save_messages(uid):
    """
    Saves messages to the database.

    Args:
        uid (str): The user ID.

    Returns:
        A JSON response containing the result of the save operation and a status code.
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    workflows_db_object = workflow_master_db()
    messages = data.get("messages")
    thread_id = data.get("threadId")
    workflow_id = data.get("workflowId")
    response, status_code = workflows_db_object.save_messages_db(uid, thread_id, workflow_id, messages)
    workflows_db_object.close()
    return jsonify(response), status_code

# SocketIO event handler for PAM
@socketio.on('start_process')
def handle_start_process(data):
    """
    Handles the 'start_process' event by processing user input and emitting output.
    This socket event is to connect PAM to the frontend.

    Parameters:
        data (dict): Event data containing 'user_input' and 'thread_id'.

    Returns:
        None
    """
    user_input = data['user_input']
    thread_id = str(data['thread_id'])
    for output in call_graph_pam(user_input, thread_id):
        socketio.emit('process_output', {'output': output})
    socketio_manager.socketio.emit('request_user_input', {'thread_id': thread_id, 'message': 'Please provide input'})


# SocketIO event handler for worflows
@socketio.on('start_process_crew')
def handle_start_process_crew(data):
    """
    Handles the 'start_process_crew' event by processing user input and emitting output.
    This socket event is to connect Workflow Run to the frontend.

    Parameters:
        data (dict): Event data containing 'user_input', 'w_id', and 'thread_id'.

    Returns:
        None
    """
    user_input = data['user_input']
    w_id = data['w_id']
    thread_id = str(data['thread_id'])
    
    for output in call_graph_heart(user_input, thread_id, w_id):
        socketio.emit('process_output', {'output': output, 'agent': "manager"})
    socketio_manager.socketio.emit('request_user_input', {'thread_id': thread_id, 'message': 'Please provide input'})

@socketio.on('evaluate_challenge')
def handle_evaluate_challenge(data):
    """
    Handles the 'evaluate_challenge' event by processing user input and emitting output.
    This socket event is to connect Doli to the frontend.

    Parameters:
        data (dict): Event data containing 'thread_id'.

    Returns:
        None
    """
    try:
        thread_id = data['thread_id']
        call = call_doli(thread_id)
        if call:
            workflows_db_object = workflow_master_db()
            response, status_code = workflows_db_object.get_challenge_instance_db(thread_id)
            output = f"""
            Doli's Evaluation report:

            Overall Score: {response['score'] } / 40
            
            Rewarded Compute points: {response['reward']}

            Feedback:
            {response['content']}
            """
            socketio.emit('challenge_evaluation_output', {'output': output})
    except Exception as e:
        socketio.emit('challenge_evaluation_output', {'output': "Something went wrong. Please try again later."})

@socketio.on('likeWorkflow')
def handle_like_workflow(data):
    """
        Handle the 'likeWorkflow'(like workflow) socket event.

        Parameters:
            data (dict): A dictionary containing the 'workflow_id' and 'uid' keys.

        Returns:
            None
    """
    try:
        workflow_id = data['workflow_id']
        uid = data['uid']
    except KeyError as e:
        return
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.like_workflow_db(uid, workflow_id)
    
    if status_code == 200:
        socketio.emit('workflowLikeUpdate', {"workflow_id": workflow_id, "uid": uid})


@socketio.on('submitFeedback')
def handle_submit_feedback(data):
    """
    Handle the 'submitFeedback'(submit feedback) socket event.

    Parameters:
        data (dict): A dictionary containing the 'workflow_id', 'uid', and 'content' keys.

    Returns:
        None

    """
    try:
        workflow_id = data['workflow_id']
        uid = data['uid']
        feedback = data['content']
    except KeyError as e:
        return
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.submit_feedback_db(uid, workflow_id, feedback)
    
    if status_code == 200:
        socketio.emit('workflowFeedbackUpdate', response)

@app.route('/store/get_feedbacks', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_feedbacks():
    """
    Retrieves feedbacks for a given workflow ID.

    Parameters:
        None

    Returns:
        - If the workflow ID is not provided, returns a JSON response with an error message and a status code of 409.
        - If the feedbacks are retrieved successfully, returns a JSON response with the feedbacks and a status code of 200.
        - If there is an error retrieving the feedbacks, returns a JSON response with an error message and a status code of 500.

    Raises:
        None
    """
    workflow_id = request.args.get("workflowId")
    if not workflow_id:
        return jsonify({"error": "Id is required"}), 409

    # Mocking the database response for demonstration
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.get_feedbacks_db(workflow_id) 
    
    if response:
        for feedback_data in response['feedbacks']:
            user_info, status_code2 = workflows_db_object.get_user_info(feedback_data['uid'])
            if status_code2 == 200:
                feedback_data['user'] = user_info['firstname'] + " "  +  user_info['lastname']
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/approved_feedback', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def submit_approved_feedback():
    """
    Submits approved feedback for a given workflow ID.

    This function is an HTTP POST endpoint that handles the submission of approved feedback for a given workflow ID. 
    It expects a JSON payload in the request body with the following fields:
    - `_id`: The ID of the workflow.
    - `uid`: The ID of the user submitting the feedback.
    - `content`: The content of the feedback.

    Parameters:
        None

    Returns:
        - If the request body is empty or missing required fields, returns a JSON response with an error message and a status code of 409.
        - If the feedback is submitted successfully, returns a JSON response with the feedback content and a status code of 200.
        - If there is an error submitting the feedback, returns a JSON response with an error message and a status code of 500.

    Raises:
        None
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    workflow_id = data.get("_id")
    uid = data.get("uid")
    content = data.get("content")

    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.submit_approved_feedback_db(uid, workflow_id, content)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/threads/<uid>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def list_threads(uid):
    """
    Retrieves a list of threads for a given user ID.

    This function is an HTTP GET endpoint that handles the retrieval of threads for a given user ID.
    It expects a 'workflowId' query parameter in the request URL.

    Parameters:
        uid (str): The ID of the user.

    Returns:
        A JSON response containing the list of threads and a status code.
    """
    workflow_id = request.args.get("workflowId")

    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.list_threads_db(uid, workflow_id)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/get_thread/<thread_id>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_thread(thread_id):
    """
    Retrieves a thread based on the provided thread ID.

    Parameters:
        thread_id (str): The ID of the thread to retrieve.

    Returns:
        - If the thread ID is missing, returns a JSON response with an error message and a status code of 400.
        - If the thread is retrieved successfully, returns a JSON response with the thread content and a status code.
    """
    if not thread_id:
        return jsonify({"error": "Thread ID is required"}), 400

    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.get_thread_db(thread_id)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/list_my_workflows/<uid>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def list_my_workflows(uid):
    """
    Retrieves a list of workflows for a given user ID.

    Args:
        uid (str): The user ID.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.

    Raises:
        None
    """
    workflows_db_object = workflow_master_db()
    name = request.args.get("name", "")
    timestamp = request.args.get("timestamp", "")
    visibility = request.args.get("visibility", "")
    response, status_code = workflows_db_object.list_workflows_db(uid, visibility, name, timestamp, False)#false for community
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/list_community_workflows/<uid>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def list_community_workflows(uid):

    workflows_db_object = workflow_master_db()
    name = request.args.get("name", "")
    timestamp = request.args.get("timestamp", "")
    visibility = request.args.get("visibility", "")
    response, status_code = workflows_db_object.list_workflows_db(uid, visibility, name, timestamp, True)

    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/get_recent_logs/<uid>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_recent_logs(uid):
    """
    Retrieves recent logs based on the user ID and workflow ID.
    Logs are recent activities of users.
    Args:
        uid (str): The ID of the user.
        workflow_id (str): The ID of the workflow.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    workflow_id = request.args.get('workflow_id')

    workflows_db_object = workflow_master_db()

    response, status_code = workflows_db_object.get_recent_logs_db(uid, workflow_id)
    workflows_db_object.close()
    return jsonify(response), status_code


@app.route('/get_workflow', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_workflow():
    """
    Retrieves a workflow based on the provided ID.
    
    This function is an HTTP GET endpoint that handles the retrieval of a workflow based on the specified ID.
    It expects an '_id' query parameter in the request URL.
    
    Parameters:
        None
    
    Returns:
        A JSON response containing the workflow data and a status code.
    """
    _id = request.args.get("_id")

    if not _id:
        return jsonify({"error": "Id is required"}), 409

    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.get_workflow_db(_id)
    workflows_db_object.close()
    
    return jsonify(response), status_code

@app.route('/update_workflow', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def update_workflow():
    """
    Update a workflow based on the provided data.

    This function is an HTTP POST endpoint that handles the update of a workflow based on the provided data.

    Parameters:
        None

    Returns:
        - If the request body is empty or missing required fields, returns a JSON response with an error message and a status code of 409.
        - If the workflow is updated successfully, returns a JSON response with the updated workflow data and a status code of 200.
        - If there is an error updating the workflow, returns a JSON response with an error message and a status code of 500.

    Raises:
        None
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    workflows_db_object = workflow_master_db()

    _id = data.get("_id")
    workflowData = data.get("workflowData")
    uid = data.get("uid")
    if not _id:
        return {"error": "Id is required"}, 409
    if not workflowData:
        return {"error": "workflowData is required"}, 409

    response, status_code = workflows_db_object.update_workflow_db(_id, workflowData, uid)
    workflows_db_object.close()
    return jsonify(response), status_code

    
@app.route('/store/list_public_workflows', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def list_public_workflows():
    """
    Update a workflow based on the provided data.

    This function is an HTTP POST endpoint that handles the update of a workflow based on the provided data.

    Parameters:
        None

    Returns:
        - If the request body is empty or missing required fields, returns a JSON response with an error message and a status code of 409.
        - If the workflow is updated successfully, returns a JSON response with the updated workflow data and a status code of 200.
        - If there is an error updating the workflow, returns a JSON response with an error message and a status code of 500.

    Raises:
        None
    """
    search_term = request.args.get('name', '')
    category = request.args.get('category', '')
    tags = request.args.get('tags').split(',')
    uid = request.args.get('uid', '')

    if not uid:
        return jsonify({"error": "Id is required"}), 409
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.list_public_workflows_db(uid, search_term, category, tags)
    workflows_db_object.close()

    return jsonify(response), status_code

@app.route('/store/add_public_workflow', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def add_public_workflow():
    """
    Handles the HTTP POST request to add a public workflow.

    Parameters:
        uid (str): The user ID.
        workflow_id (str): The ID of the workflow to be added.

    Returns:
        A JSON response containing the result of the add public workflow operation and a corresponding HTTP status code.
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    uid = data.get('uid')
    workflow_id = data.get('workflow_id')
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.add_public_workflow_db(uid, workflow_id)
    workflows_db_object.close()

    return jsonify(response), status_code


@app.route('/get_progress/<thread_id>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_progress(thread_id):
    """
    Retrieves the progress of a workflow based on the provided thread ID.

    Parameters:
        thread_id (str): The ID of the thread to retrieve progress for.

    Returns:
        A JSON response containing the progress result and a corresponding HTTP status code.
    """
    workflows_db_object = workflow_master_db()
    result, status = workflows_db_object.get_progress_db(thread_id)
    workflows_db_object.close()

    return jsonify({"progress": result}), status

@app.route('/app_data/<data>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def app_data(data):
    """
    Retrieves data from the app based on the provided data parameter.
    This will contain app metadata such as: app challenges, and store metadata
    Parameters:
        data (str): The data parameter used to retrieve data from the app.

    Returns:
        A JSON response containing the retrieved data and a corresponding HTTP status code.
    """
    workflows_db_object = workflow_master_db()
    result, status = workflows_db_object.get_app_data_db(data)
    workflows_db_object.close()

    return jsonify({"data": result}), status

@app.route('/post_my_challenge/<uid>', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def post_my_challenge(uid):
    """
    Handles the HTTP POST request to post a challenge for a specific user.

    Parameters:
        uid (str): The ID of the user.

    Returns:
        A JSON response containing the result of the post_my_challenge operation and a corresponding HTTP status code.
        If the request body is empty or missing required fields, returns a JSON response with an error message and a status code of 409.
        If the post_my_challenge operation is successful, returns a JSON response with the result and a status code of 200.
        If there is an error during the post_my_challenge operation, returns a JSON response with an error message and a status code of 500.
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    if not data:
        return {"error": "data is required"}, 409

    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.post_my_challenge_db(uid, data)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/my_challenges/<uid>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def get_my_challenges(uid):
    """
    Retrieves the challenges for a specific user.

    Parameters:
        uid (str): The ID of the user.

    Returns:
        A JSON response containing the challenges and a corresponding HTTP status code.

    Raises:
        None
    """
    c_type = request.args.get('type')
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.get_my_challenges_db(uid, c_type)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/start_challenge', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def start_challenge():
    """
    Starts a challenge instance for a user.

    This function handles the HTTP POST request to start a challenge for a user. It expects the request to have a JSON payload with the required data. If the request does not have a JSON payload, it will use the form data instead.

    Parameters:
        None

    Returns:
        A JSON response containing the result of the start_challenge operation and a corresponding HTTP status code.
        If the request body is empty or missing required fields, returns a JSON response with an error message and a status code of 409.
        If the start_challenge operation is successful, returns a JSON response with the result and a status code of 200.
        If there is an error during the start_challenge operation, returns a JSON response with an error message and a status code of 500.

    Raises:
        None
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    if not data:
        return {"error": "data is required"}, 409
    
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.start_challenge_db(data)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/get_compute_points/<uid>', methods=['GET'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def fetch_compute_points(uid):
    """
    Retrieves the compute points for a specific user.

    Parameters:
        uid (str): The ID of the user.

    Returns:
        A JSON response containing the compute points and a corresponding HTTP status code.

    Raises:
        None
    """
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.get_compute_points_db(uid)
    workflows_db_object.close()
    return jsonify(response), status_code

@app.route('/challenge_deduct_points/<uid>', methods=['POST'])
@cross_origin(origin=os.getenv('FRONTEND_URL'))
def deduct_challenge_points(uid):
    """
    Handles the HTTP POST request to deduct challenge points for a specific user.
    This happens when a user enters a challenge.
    Parameters:
        uid (str): The ID of the user.

    Returns:
        A JSON response containing the result of the deduct_challenge_points operation and a corresponding HTTP status code.
        If the request body is empty or missing required fields, returns a JSON response with an error message and a status code of 409.
        If the deduct_challenge_points operation is successful, returns a JSON response with the result and a status code of 200.
        If there is an error during the deduct_challenge_points operation, returns a JSON response with an error message and a status code of 500.

    Raises:
        None
    """
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    if not data:
        return {"error": "data is required"}, 409
    
    workflows_db_object = workflow_master_db()
    response, status_code = workflows_db_object.deduct_challenge_points_db(uid, data['compute_points'])
    workflows_db_object.close()
    return jsonify(response), status_code

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)



