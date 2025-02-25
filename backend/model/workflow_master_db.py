import pymongo
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import traceback
import json
import logging
from dotenv import load_dotenv
import os

load_dotenv()
# Create a logger instance
logger = logging.getLogger(__name__)

class workflow_master_db():
    """
    A class representing the Workflow Master database.

    This class provides methods for interacting with the Workflow Master database,
    including initializing the database connection, checking if the app is initialized,
    and accessing various collections.

    Attributes:
        db (pymongo.database.Database): The MongoDB database object.

    Methods:
        demo_app_configuration(): Initializes the app with demo data.
        is_app_initialized(): Checks if the app is initialized.
    """
    def __init__(self):
        """
        Initializes a new instance of the workflow_master_db class.

        Establishes a connection to the MongoDB database and sets up the various collections.
        Checks if the app is initialized and initializes it if necessary.

        Parameters:
            None

        Returns:
            None
        """
        try:
            self.client = MongoClient(os.getenv('MONGODB_URI'))
            self.db = self.client['workflow_master']
            self.workflows = self.db['workflows']
            self.users = self.db['users']
            self.messages = self.db['messages']
            self.public_workflow_metadata = self.db['public_workflow_metadata']
            self.app_data = self.db['app_data']
            self.feedbacks = self.db['feedbacks']
            self.logs = self.db['logs']
            self.team_progress = self.db['team_progress'] 
            self.my_challenges = self.db['my_challenges']
            self.challenge_instances = self.db['challenge_instances']


            if self.app_data.find_one({'data': 'app_initialized'}) is None:
                self.demo_app_configuration()
                self.app_data.insert_one({'data': 'app_initialized'})

            
        except Exception as e:
            logger.error("Error initializing database: %s", str(e))
    
    def demo_app_configuration(self):
        """
        Initializes the app configuration by loading data from the 'data.json' file.
        
        This function reads the contents of the 'data.json' file and checks if the 'store_metadata' and 'app_challenges' documents exist in the 'app_data' collection. If they do not exist, new documents are inserted with the corresponding data from the 'data.json' file.
        
        Parameters:
            None
        
        Returns:
            None
        
        Raises:
            Exception: If there is an error loading the app data.
        """
        try:
            with open('model/app_data.json', 'r') as file:
                data = json.load(file)

            if self.app_data.find_one({"data": "store_metadata"}) is None:
                self.app_data.insert_one({
                    "data": "store_metadata",
                    "content": data["store_metadata"]
                })

            if self.app_data.find_one({"data": "app_challenges"}) is None:
                self.app_data.insert_one({
                    "data": "app_challenges",
                    "content": data["app_challenges"]
                })

        except Exception as e:
            logger.error("Error loading app data: ", str(e))
    
    def demo_user_configuration(self, uid):
        """
        Initializes the user configuration by loading demo data from the 'demo_user.json' file.
        
        This function reads the contents of the 'demo_user.json' file and checks if any workflows exist for the given user ID. If no workflows exist, it inserts demo workflows into the database.
        
        Parameters:
            uid (str): The ID of the user to initialize the configuration for.
        
        Returns:
            None
        
        Raises:
            Exception: If there is an error loading the demo data.
        """
        def load_demo_data():
            try:
                with open('model/demo_user.json', 'r') as file:
                    return json.load(file)
            except Exception as e:
                logger.error(f"Error loading demo data: {e}")
                return {}
        
        demo_data = load_demo_data()

        if not demo_data:
            logger.error("No demo data found.")
            return
        
        # Insert demo workflows if no workflows exist for the user
        if self.workflows.count_documents({'uid': uid}) == 0:
            demo_workflows = demo_data.get('workflows', [])

            if len(demo_workflows) > 0:
                for workflow in demo_workflows:
                    result = self.add_workflow_db(uid, workflow['metadata'], workflow['nodes'])
                logger.error("Demo workflows have been inserted.")
            else:
                logger.error("No demo workflows data found in demo_data.json.")


            
    def add_user_db(self, user_data):
        """
        Adds a new user to the database.

        Parameters:
            user_data (dict): A dictionary containing the user's data.

        Returns:
            tuple: A tuple containing a dictionary with the response and the HTTP status code.
                - response (dict): A dictionary containing the response message.
                - status_code (int): The HTTP status code of the response.

        Raises:
            Exception: If an error occurs during the execution of the function.
        """
        try:
            user_data['compute_points'] = 100
            result = self.users.insert_one(user_data)
            self.logs.insert_one({"type":"new_user", "uid":user_data['uid'], "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.demo_user_configuration(user_data['uid'])
            return {"response": "success"}, 200
        except Exception as e:
            logger.error("error: ", str(e))
            return {'error': str(e)}, 500
        
    def get_user_info(self, uid):
        """
        Retrieves user information from the database based on the provided user ID.

        Parameters:
            uid (str): The unique identifier of the user.

        Returns:
            tuple: A tuple containing the user's information and the HTTP status code.
                - user_info (dict): A dictionary containing the user's data.
                - status_code (int): The HTTP status code of the response.
        """
        try:
            result = self.users.find_one({"uid": uid})
            return result, 200
        except Exception as e:
            return {'error': str(e)}, 500
    
    def save_messages_db(self, uid, thread_id, workflow_id, messages):
        """
        Saves messages to the database.

        Parameters:
            uid (str): The user ID.
            thread_id (str): The ID of the thread.
            workflow_id (str): The ID of the workflow.
            messages (str): The messages to be saved.

        Returns:
            tuple: A tuple containing a dictionary with the response and the HTTP status code.
                - response (dict): A dictionary containing the response message.
                - status_code (int): The HTTP status code of the response.
        """
        try:
            check = self.messages.find_one({"thread_id": thread_id})
            if check:
                fields_to_update = {"messages": messages, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                result = self.messages.update_one({"thread_id":thread_id}, {"$set": fields_to_update})
            else:
                result = self.messages.insert_one({"uid": uid, "thread_id": thread_id, "workflow_id": workflow_id, "messages": messages, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

            return {"response": "success"}, 200
        except Exception as e:
            print("error: ", str(e))
            return {'error': str(e)}, 500

    def list_threads_db(self, uid, workflow_id):
        """
        Retrieves a list of threads based on the provided user ID and workflow ID.

        Parameters:
            uid (str): The unique identifier of the user.
            workflow_id (str): The ID of the workflow.

        Returns:
            tuple: A tuple containing the list of threads and the HTTP status code.
                - threads_list (list): A list of threads retrieved based on the user ID and workflow ID.
                - status_code (int): The HTTP status code of the response.
        """
        try:
            threads = self.messages.find({
                "$and":[
                    {"uid": uid},
                    {"workflow_id": workflow_id}
                ]
            }).sort('timestamp', pymongo.DESCENDING)
            
            threads_list = list(threads)
            for entity in threads_list:
                entity["_id"] = str(entity["_id"]) 
            
            return threads_list, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def get_thread_db(self,thread_id):
        """
        Retrieves a thread from the database based on the provided thread ID.

        Parameters:
            thread_id (str): The ID of the thread to retrieve.

        Returns:
            tuple: A tuple containing the retrieved thread and the HTTP status code.
                - thread (dict or None): The retrieved thread, or None if not found.
                - status_code (int): The HTTP status code of the response.
        """
        try:
            
            result = self.messages.find_one({"thread_id":thread_id})

            if not result:
                return None, 200
            
            result["_id"] = str(result["_id"])
            return  result, 200
        except Exception as e:
            logger.error("error", str(e))
            return {"error": str(e)}, 500

    def add_workflow_db(self, uid, workflow_metadata, nodes, community=False):
        """
        Adds a new workflow to the database.

        Parameters:
            uid (str): The unique identifier of the user creating the workflow.
            workflow_metadata (dict): A dictionary containing metadata about the workflow.
            nodes (list): A list of nodes in the workflow.
            community (bool): Whether the workflow is a community workflow (default is False).

        Returns:
            tuple: A tuple containing a dictionary with the response and the workflow ID, and the HTTP status code.
                - response (dict): A dictionary with the response message and the workflow ID.
                - status_code (int): The HTTP status code of the response.
        """
        workflow_name = workflow_metadata["name"]
       
        #print("All Workflows:", list(self.workflows.find()))
        check = self.workflows.find_one({
            "$and": [
                {"uid": uid},
                {"metadata.name": workflow_name}
            ]})


        if check:
            workflow_metadata['name'] = workflow_name + '(new)'
        new_workflow = {"uid": uid}
        new_workflow["metadata"] = workflow_metadata
        new_workflow['nodes'] = nodes
        new_workflow["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_workflow["uptodate"] = ["yes", new_workflow['timestamp']]
        new_workflow["community"] = community
        new_workflow["approved_feedbacks"] = []
        try:
            result = self.workflows.insert_one(new_workflow)
            if community:
                self.logs.insert_one({"type":"add_public_workflow", "uid":uid, "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "workflow_name":workflow_metadata['name'], "workflow_id":str(result.inserted_id)})
            else:
                self.logs.insert_one({"type":"new_workflow", "uid":uid, "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "workflow_name":workflow_metadata['name'], "workflow_id":str(result.inserted_id)})
            
            # Create a document in public_workflow_metadata if the workflow is public
            if workflow_metadata['public']:
                public_metadata = {
                    "workflow_id": str(result.inserted_id),
                    "likes": [],
                    "feedback_id": 0,
                    "categories": [],
                    "tags": [],
                    "downloads": []
                }
                result2 = self.public_workflow_metadata.insert_one(public_metadata)
            return {"response": "success", "workflow_id":str(result.inserted_id)}, 200
        except Exception as e:
            logger.error("error: ", str(e))
            return {'error': str(e)}, 500
    
    def list_workflows_db(self, uid, visibility, name="", timestamp="", community=False):
        """
        Lists workflows from the database based on the provided filters.

        Args:
            uid (str): The ID of the user.
            visibility (str): The visibility of the workflows to filter by.
            name (str, optional): The name of the workflows to filter by. Defaults to "".
            timestamp (str, optional): The timestamp of the workflows to filter by. Defaults to "".
            community (bool, optional): Whether to filter by community workflows. Defaults to False.

        Returns:
            list: A list of workflows that match the filters, along with a status code.
        """
        try:
            regex_name = f".*{name}.*"
            regex_timestamp = f".*{timestamp}.*"
            query = {
                "$and": [
                    {"uid": uid},
                    {"community": community},
                    {"metadata.name": {"$regex": regex_name, "$options": "i"}},
                    {"timestamp": {"$regex": regex_timestamp, "$options": "i"}}
                ]
            }

            # Add metadata.public criteria if visibility is not blank
            if visibility:
                query["$and"].append({"metadata.public": visibility == "public"})

            # Perform the query and sort
            workflows = self.workflows.find(query).sort('timestamp', pymongo.DESCENDING)
            workflows_list = list(workflows)
            for entity in workflows_list:
                entity["_id"] = str(entity["_id"]) 
            return workflows_list, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500
    
    def get_workflow_db(self, _id):
        """
        Retrieves a workflow from the database based on the provided ID.

        Args:
            _id (str): The ID of the workflow to retrieve.

        Returns:
            A dictionary containing the workflow data, along with a status code.
            If the workflow is not found, returns an error message with a status code of 409.
            If an error occurs, returns an error message with a status code of 500.
        """
        try:
            object_id = ObjectId(_id)
            result = self.workflows.find_one({"_id":object_id})

            if not result:
                return {"error": "Workflow not found"}, 409
                
            result["_id"] = str(result["_id"])
            if 'approved_feedbacks' not in result:
                result['approved_feedbacks'] = []

            # Add public metadata if the workflow is public
            if result['metadata']['public']:
                public_metadata = self.public_workflow_metadata.find_one({"workflow_id":_id})
                result['metadata']['public_metadata'] = {
                    'likes': len(public_metadata['likes']),
                    'categories':public_metadata['categories'],
                    'tags':public_metadata['tags'],
                    'downloads': len(public_metadata['downloads'])
                }
            return  result, 200
        except Exception as e:
            logger.error("error", str(e))
            return {"error": str(e)}, 500

    def update_workflow_db(self, _id, workflowData, uid):
        """
        Updates a workflow in the database.

        Args:
            _id (str): The ID of the workflow to update.
            workflowData (dict): A dictionary containing the updated workflow data.
            uid (str): The ID of the user making the update.

        Returns:
            A success message with a status code of 200 if the update is successful.
            An error message with a status code of 409 if the workflow is not found or the workflow data is invalid.
            An error message with a status code of 500 if an error occurs during the update process.
        """
        try:
            object_id = ObjectId(_id)
            result = self.workflows.find_one({"_id":object_id})
            if not result:
                return {"error": "Workflow not found"}, 409

            if not "metadata" in workflowData or not "nodes" in workflowData:
                return {"error": "Invalid workflow data"}, 409

            if not result['metadata']['public'] and workflowData["metadata"]['public']:
                if not self.public_workflow_metadata.find_one({"workflow_id":_id}):
                    public_metadata = {
                        "workflow_id": _id,
                        "likes": [],
                        "feedback_id": 0,
                        "categories": [],
                        "tags": [],
                        "downloads": []
                    }
                    result = self.public_workflow_metadata.insert_one(public_metadata)
            fields_to_update = {"metadata": workflowData["metadata"], "nodes": workflowData["nodes"], "uptodate": ["no", datetime.now().strftime("%Y-%m-%d %H:%M:%S")], "approved_feedbacks": workflowData['approved_feedbacks']}
            self.logs.insert_one({"type":"update_workflow", "uid":uid, "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "workflow_name": workflowData['metadata']['name'], "workflow_id":_id})
            result = self.workflows.update_one({"_id":object_id}, {"$set": fields_to_update})

            return "Workflow updated successfully", 200
        except Exception as e:
            logger.error("error", str(e))
            traceback.print_exc()
            return {"error": str(e)}, 500    

    def search_public_workflow_metadata(self, workflow_id, category='', tags=['']):
        try:
            query = {"workflow_id": workflow_id}

            if category:
                query["categories"] = {"$in": [category]}

            # Conditionally add 'tags' to the query if 'tags' is provided, not empty, and does not contain only empty strings
            if tags and any(tag.strip() for tag in tags):
                query["tags"] = {"$in": [tag for tag in tags if tag.strip()]}


            result = self.public_workflow_metadata.find_one(query)

            if result:
                result["_id"] = str(result["_id"])
                return result
            return None
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500
        
    def list_public_workflows_db(self, uid, search_term, category, tags):
        """
        Lists public workflows from the database based on the provided search term, category, and tags.

        Args:
            uid (str): The user ID to exclude from the search results.
            search_term (str): The term to search for in the workflow names.
            category (str): The category to filter the search results by.
            tags (list): The tags to filter the search results by.

        Returns:
            list: A list of public workflows that match the search criteria, along with their metadata and public workflow metadata.
            int: The HTTP status code (200 for success, 500 for error).
        """
        try:
            regex_name = f".*{search_term}.*"
            regex_category = f".*{category}.*"
            workflows = self.workflows.find({
                "$and": [
                    {"uid": {"$not": {"$eq": uid}}},
                    {"metadata.public": True},
                    {"metadata.name": {"$regex": regex_name, "$options": "i"}},
                ]
            }).sort('timestamp', pymongo.DESCENDING)
            workflows_list = list(workflows)
            
            # Add public metadata of the workflows
            workflows_list_more = []
            for entity in workflows_list:

                entity["_id"] = str(entity["_id"])
                search = self.search_public_workflow_metadata(entity["_id"], category, tags)
                if search:
                    entity = entity["metadata"] | search
                    workflows_list_more.append(entity)

            return workflows_list_more, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def add_public_workflow_db(self, uid, workflow_id):
        """
        Adds a public(community) workflow to the database.
        Same as the Download feature in the frontend.
        Parameters:
            uid (str): The user ID.
            workflow_id (str): The ID of the workflow to be added.

        Returns:
            dict: A dictionary containing the new workflow ID, or an error message if the operation fails.
            int: The status code of the operation (200 for success, 409 for conflict, 500 for internal server error).
        """
        try:
            workflow, status = self.get_workflow_db(workflow_id)
            if status != 200:
                return {"error": workflow}, 409

            public_metadata = self.search_public_workflow_metadata(workflow_id)

            if uid not in public_metadata['downloads']:
                result = self.public_workflow_metadata.update_one({"workflow_id": workflow_id}, {"$push": {"downloads": uid}})
            
            insert_in_db, status = self.add_workflow_db(uid, workflow['metadata'], workflow["nodes"], True)
            if status != 200:
                return {"error": insert_in_db}, 409
   
            return {"new_workflow_id": insert_in_db['workflow_id']}, 200

        except Exception as e:
            logger.error("Error: ", str(e))
            traceback.print_exc()
            return  {'error': str(e)}, 500




    def like_workflow_db(self, uid, workflow_id):
        """
        Likes a public workflow in the database.

        Parameters:
            uid (str): The user ID of the user liking the workflow.
            workflow_id (str): The ID of the workflow to be liked.

        Returns:
            dict: A dictionary containing a success message or an error message.
            int: The status code of the operation (200 for success, 409 for conflict, 500 for internal server error).
        """
        try:
            check = self.public_workflow_metadata.find_one({"workflow_id": workflow_id})
            if not check:
                return {"error": "Workflow not found"}, 409
            if uid in check["likes"]:
                return {"error": "Workflow already liked"}, 409
            result = self.public_workflow_metadata.update_one({"workflow_id": workflow_id}, {"$push": {"likes": uid}})
            print(result)
            return "Workflow liked successfully", 200

        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def submit_feedback_db(self, uid, workflow_id, feedback):
        """
        Submits a feedback for a given workflow ID.

        Parameters:
            uid (str): The user ID of the user submitting the feedback.
            workflow_id (str): The ID of the workflow for which the feedback is being submitted.
            feedback (str): The content of the feedback.

        Returns:
            dict: A dictionary containing the feedback data, or an error message if the workflow is not found.
            int: The status code of the operation (200 for success, 409 for conflict, 500 for internal server error).
        """
        try:
            check = self.public_workflow_metadata.find_one({"workflow_id": workflow_id}) 
            if not check:
                return {"error": "Workflow not found"}, 409
            
            check = self.feedbacks.find_one({"workflow_id": workflow_id})
            if check:
                result_update = self.feedbacks.update_one({"workflow_id": workflow_id}, {"$push": {"feedbacks": {"uid": uid, "contentc": feedback, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}})
            else:
                result_insert = self.feedbacks.insert_one({"workflow_id": workflow_id, "feedbacks": [{"uid": uid, "content": feedback, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]})
            
            result_final = self.feedbacks.find_one({"workflow_id": workflow_id})
            result_final["_id"] = str(result_final["_id"])
            return result_final, 200

        except Exception as e: 
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def submit_approved_feedback_db(self, uid, workflow_id, content):
        """
        Submits approved feedback for a given workflow ID.

        This function is used to submit approved feedback for a specific workflow ID. It checks if the workflow exists and if the user is approved to submit feedback. It also checks if the feedback content exceeds the maximum allowed length and if the maximum number of feedbacks has been reached.

        Parameters:
            uid (str): The ID of the user submitting the feedback.
            workflow_id (str): The ID of the workflow for which the feedback is being submitted.
            content (str): The content of the feedback.

        Returns:
            dict: A dictionary containing the feedback content, or an error message if the workflow is not found, the user is not approved, the feedback content is too long, or the maximum number of feedbacks has been reached.
            int: The status code of the operation (200 for success, 409 for conflict, 500 for internal server error).
        """
        try:
            object_id = ObjectId(workflow_id)
            check  = self.workflows.find_one({"_id": object_id, "uid":uid})

            if not check:
                return {"error": "Workflow not found or user not approved"}, 409
            
            if len(check['approved_feedbacks']) >= 10:
                return {"error": "maximum_feedbacks_reached_refine_prority_only"}, 409
            if len(content) >= 150:
                return {"error": "maximum_letters_reached"}, 409

            result_update = self.workflows.update_one({"_id": object_id}, {"$push": {"approved_feedbacks": {"content": content, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}})
            
            if result_update.modified_count > 0:
                return {"content": content}, 200

        except Exception as e:
            print("Error: ", str(e))
            return {'error': str(e)}, 500

            

    def get_feedbacks_db(self, workflow_id):
        """
        Retrieves feedbacks for a given workflow ID.

        Args:
            workflow_id (str): The ID of the workflow for which the feedbacks are being retrieved.

        Returns:
            tuple: A tuple containing the feedbacks and a status code.
                - feedbacks (dict or None): The feedbacks for the given workflow ID. If no feedbacks are found, None is returned.
                - status_code (int): The status code indicating the success or failure of the operation. 200 if successful, 500 if an exception occurred.

        Raises:
            Exception: If an error occurs while retrieving the feedbacks.
        """
        try:
            result = self.feedbacks.find_one({"workflow_id": workflow_id})
 
            if result:
                result["_id"] = str(result["_id"])
            return result, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500
    
    def get_Note(self, w_i_id):
        """
        Retrieves the last three notes for a given workflow item ID.
        This is for internal use for LLM agents.

        Args:
            w_i_id (str): The ID of the workflow item for which the notes are being retrieved.

        Returns:
            dict or None: A dictionary containing the last three notes for the given workflow item ID. If no notes are found, None is returned.
        """
        db2 = self.client['workflow_master']
        notes = db2['Note_supervisor']
        result = notes.find_one({'i_id':w_i_id})
        if result:
            return {'data': result['note'][-3:]}
        return None

    def get_recent_logs_db(self, uid, workflow_id=None):
        """
        Retrieves the most recent logs from the database.

        Args:
            uid (str): The unique identifier of the user.
            workflow_id (str, optional): The ID of the workflow. Defaults to None.

        Returns:
            tuple: A tuple containing the list of logs and the status code.
                - logs_list (list): A list of dictionaries representing the logs.
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 500 if an exception occurred.

        Raises:
            Exception: If an error occurs while retrieving the logs.
        """
        try:
            if workflow_id:
                result = self.logs.find({"uid": uid, "workflow_id": workflow_id}).sort('timestamp', pymongo.DESCENDING).limit(5)
            else:
                result = self.logs.find({"uid": uid}).sort('timestamp', pymongo.DESCENDING).limit(5)
            logs_list = list(result)
            for log in logs_list:
                log['_id'] = str(log['_id'])
            
            return logs_list, 200
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {"error": str(e)}, 500

    def get_progress_db(self, thread_id):
        """
        Retrieves the progress of a team from the database.

        Args:
            thread_id (str): The unique identifier of the thread.

        Returns:
            tuple: A tuple containing the progress and the status code.
                - progress (list): A list representing the progress.
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 500 if an exception occurred.
        """
        try:
            result = self.team_progress.find_one({"thread_id": thread_id})

            if not result:
                return [], 200
            result['_id'] = str(result['_id'])

            return result['progress'], 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500   
        
    def get_app_data_db(self, data):
        """
        Retrieves application data from the database based on the provided data identifier.

        Args:
            data (str): The unique identifier of the data to be retrieved.

        Returns:
            tuple: A tuple containing the application data and the status code.
                - data (dict): The application data retrieved from the database. This may include challenges for the Challenge feature, store metadata....
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 409 if data not found, 500 if an exception occurred.
        """
        try:
            result = self.app_data.find_one({"data": data})
            if not result:
                return {"error": "Data not found"}, 409

            return result['content'], 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def post_my_challenge_db(self, uid, data):
        """
        Attempts to insert a new challenge entry into the 'my_challenges' collection.
        
        Parameters:
            uid (str): The user ID associated with the challenge.
            data (dict): The metadata of the challenge.
        
        Returns:
            tuple: A tuple containing the success message with the inserted ID and the status code.
                - success_message (str): A message indicating the success and the inserted ID.
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 500 if an exception occurred.
        """
        try:
            result = self.my_challenges.insert_one({"uid": uid, "metadata": data, "apps": [], "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            return {"success": str(result.inserted_id)}, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500
    
    def get_my_challenges_db(self, uid, c_type):
        """
        Retrieves a list of challenges from the database based on the provided user ID and challenge type.

        Parameters:
            uid (str): The ID of the user.
            c_type (str): The type of challenges to retrieve. Can be either "mine" for challenges owned by the user or any other value for challenges not owned by the user.

        Returns:
            tuple: A tuple containing the list of challenges and the status code.
                - challenges (list): A list of challenge documents.
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 500 if an exception occurred.
        """
        try:
            if c_type == "mine":
                result = self.my_challenges.find({"uid": uid}).sort('timestamp', pymongo.DESCENDING)
            else:
                result = self.my_challenges.find({
                                "$and": [
                                    {"uid": {"$ne": uid}},
                                    {"apps": {"$nin": [uid]}}
                                ]
                            }).sort('timestamp', pymongo.DESCENDING)

            if not result:
                return [], 200

            result = list(result)
 
            for r in result:
                r['_id'] = str(r['_id'])

            return result, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def start_challenge_db(self, data):
        """
        Inserts a new challenge instance into the database.

        Parameters:
            self: The object instance.
            data: The data representing the challenge instance to be inserted.

        Returns:
            tuple: A tuple containing the ID of the inserted challenge instance and the status code.
                - id (str): The ID of the inserted challenge instance.
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 500 if an exception occurred.
        """
        try:
            result = self.challenge_instances.insert_one(data)
            return {"id": str(result.inserted_id)}, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def set_challenge_evaluation_db(self, thread_id, score, content):
        """
        Adds the evaluation of a challenge instance in the database.

        Parameters:
            thread_id (str): The ID of the challenge instance to be updated.
            score (int): The score of the challenge instance.
            content (str): The content of the challenge instance.

        Returns:
            tuple: A tuple containing the status message and the status code.
                - status (str): The status message indicating the success or failure of the operation.
                - status_code (int): The status code indicating the success or failure of the operation.
                    200 if successful, 409 if the challenge trial is not found.
        """
        check = self.challenge_instances.find_one({"thread_id": thread_id})
        if not check:
            return "challenge trial not found", 409

        result = self.challenge_instances.update_one({"thread_id":thread_id}, {"$set": {"score": score, "content": content}})

        return "success", 200
        
    def get_challenge_instance_db(self, thread_id):
        """
        Retrieves a challenge instance from the database based on the provided thread ID.

        Parameters:
            thread_id (str): The ID of the challenge instance to retrieve.

        Returns:
            tuple: A tuple containing the retrieved challenge instance and the HTTP status code.
                - challenge_instance (dict or None): The retrieved challenge instance, or None if not found.
                - status_code (int): The HTTP status code of the response.
        """
        try:
            result = self.challenge_instances.find_one({"thread_id": thread_id})
            if not result:
                return "Not found", 409
            result['_id'] = str(result['_id'])
            return result, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500

    def get_compute_points_db(self, uid):
        """
        Retrieves the compute points for a specific user from the database.

        Parameters:
            uid (str): The ID of the user.

        Returns:
            tuple: A tuple containing the compute points and the HTTP status code.
                - compute_points (dict): A dictionary containing the compute points of the user.
                - status_code (int): The HTTP status code of the response.
                    200 if successful, 409 if the user is not found, 500 if an error occurs.
        """
        try:
            result = self.users.find_one({"uid": uid})
            if not result:
                return "User Not found", 409
            result['_id'] = str(result['_id'])
            
            if 'compute_points' not in result:
                update = self.users.update_one({"uid": uid}, {"$set": {"compute_points": 0}})
                result['compute_points'] = 0
            return {"compute_points" : result['compute_points']}, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500
    
    def deduct_challenge_points_db(self, uid, points):
        """
        Deducts challenge points from a user's account.

        Parameters:
            uid (str): The ID of the user.
            points (int): The number of points to deduct.

        Returns:
            tuple: A tuple containing the response and the HTTP status code.
                - response (dict): A dictionary containing the result of the operation.
                - status_code (int): The HTTP status code of the response.
                    200 if successful, 409 if the user is not found or has insufficient points, 500 if an error occurs.
        """
        try:
            result = self.users.find_one({"uid": uid})
            if not result:
                return {"response":"User Not found"}, 409
            
            if result['compute_points'] < int(points):
                return {"response":"Insufficient points"}, 409
            
            result = self.users.update_one({"uid": uid}, {"$set": {"compute_points": result['compute_points'] - int(points)}})
            return {"response":"success"}, 200
        except Exception as e:
            logger.error("Error: ", str(e))
            return {'error': str(e)}, 500
            
    def close(self):
        """
        Closes the connection to the MongoDB client.

        This method is used to close the connection to the MongoDB client. 
        It is typically called when the database operations are complete and the connection is no longer needed.

        Parameters:
            None

        Returns:
            None
        """
        self.client.close()
        