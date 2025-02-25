import pymongo
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
import os
load_dotenv()

class workflow_master_db():
    """
    A class representing a portion of Workflow Master database.

    This is for ease of access for the heart module.
    
    This class provides methods for interacting with the Workflow Master database,
    including initializing the database connection, checking if the app is initialized,
    and accessing various collections.

    

    Attributes:
        db (pymongo.database.Database): The MongoDB database object.

    """
    def __init__(self):
        try:
            self.client = MongoClient(os.getenv('MONGODB_URI'))
            self.db = self.client['workflow_master']
            self.workflows = self.db['workflows']
            self.workflow_instances = self.db['workflow_instances']
            self.team_progress = self.db['team_progress']
            self.notes = self.db['notes']

        except Exception as e:
            print("Error: ", str(e))
        
    def add_workflow_db(self, workflow_metadata, nodes):
        workflow_name = workflow_metadata["name"]
       
        #print("All Workflows:", list(self.workflows.find()))
        check = self.workflows.find_one({"metadata.name": workflow_name})
    
        if check:

            return {'error': 'Workflow name already exists'}, 409
        new_workflow = {}
        new_workflow["metadata"] = workflow_metadata
        new_workflow['nodes'] = nodes
        new_workflow["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.workflows.insert_one(new_workflow)
            return {"response": "success", "workflow_id":str(result.inserted_id)}, 200
        except Exception as e:
            return {'error': str(e)}, 500
    def list_workflows_db(self, name, timestamp):
        try:
            regex_name = f".*{name}.*"
            regex_timestamp = f".*{timestamp}.*"
            workflows = self.workflows.find({
                "$and": [
                    {"metadata.name": {"$regex": regex_name, "$options": "i"}},
                    {"timestamp": {"$regex": regex_timestamp, "$options": "i"}}
                ]
            }).sort('timestamp', pymongo.DESCENDING)
            workflows_list = list(workflows)
            for entity in workflows_list:
                entity["_id"] = str(entity["_id"]) 
            print(f"Workflows with similar names to '{name}':", workflows_list)
            return workflows_list, 200
        except Exception as e:
            print("Error: ", str(e))
            return {'error': str(e)}, 500
    
    def get_workflow_db(self, _id):
        try:
            object_id = ObjectId(_id)
            result = self.workflows.find_one({"_id":object_id})

            if not result:
                return {"error": "Workflow not found"}, 409
            result["_id"] = str(result["_id"])
            return  result, 200
        except Exception as e:
            return {"error": str(e)}, 500
    def set_workflow_uptodate_db(self, _id):
        try:
            object_id = ObjectId(_id)
            result = self.workflows.find_one({"_id":object_id})
            if not result:
                return {"error": "Workflow not found"}, 409

            fields_to_update = {"uptodate": ['yes', datetime.now().strftime("%Y-%m-%d %H:%M:%S") ]}

            result = self.workflows.update_one({"_id":object_id}, {"$set": fields_to_update})
            return "success", 200
        except Exception as e:
            return {"error": str(e)}, 500

    def set_progress_db(self, thread_id, progress):
        try:
            check = self.team_progress.find_one({"thread_id": thread_id})
            if check:
                self.team_progress.update_one({"thread_id": thread_id}, {"$set": {"progress": progress}})
                return "success", 200
            result = self.team_progress.insert_one({"thread_id": thread_id, "progress": progress})
            return "success", 200
        except Exception as e:
            print("error", str(e))
            return {"error": str(e)}, 500
    
    def take_note_db(self, thread_id, note):
        try:
            existing = self.notes.find_one({"thread_id": thread_id})
            if existing:
                existing['note'] += [note]
                result = self.notes.update_one({"thread_id": thread_id}, {"$set": existing})
            else:
                document = {"note": [note], "thread_id": thread_id}
                result = self.notes.insert_one(document)

            return "success", 200
        except Exception as e:
            print("error", str(e))
            return {"error": str(e)}, 500    
    def close(self):
        self.client.close()
        

