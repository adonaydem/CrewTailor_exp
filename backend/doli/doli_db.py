import pymongo
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import traceback

class workflow_master_db():
    """
    A part of the workflow_master MongoDB database, suited for Doli module.


    Attributes:
        client (MongoClient): The MongoDB client instance.
        db (Database): The workflow_master database instance.
        workflows (Collection): The workflows collection.
        users (Collection): The users collection.
        team_progress (Collection): The team_progress collection.
        challenge_instances (Collection): The challenge_instances collection.

    Methods:
        get_workflow_db(_id): Retrieves a workflow document by its _id field.
        get_progress_db(thread_id): Retrieves a team's progress document by its thread_id field.
        get_challenge_instance_db(thread_id): Retrieves a challenge instance document by its thread_id field.
        calculate_reward(stake, score, max_score): Calculates a reward based on a score, stake, and maximum score.
        set_challenge_evaluation_db(thread_id, score, content): Updates a challenge instance document with a score, content, and reward.
    """
    def __init__(self):
        try:
            self.client = MongoClient('localhost', 27017)
            self.db = self.client['workflow_master']
            self.workflows = self.db['workflows']
            self.users = self.db['users']
            self.team_progress = self.db['team_progress'] 
            self.challenge_instances = self.db['challenge_instances']

        except Exception as e:
            print("Error: ", str(e))
            

    def get_workflow_db(self, _id):
        try:
            object_id = ObjectId(_id)
            result = self.workflows.find_one({"_id":object_id})

            if not result:
                return {"error": "Workflow not found"}, 409
                
            result["_id"] = str(result["_id"])
            return  result, 200
        except Exception as e:
            print("error", str(e))
            return {"error": str(e)}, 500

    def get_progress_db(self, thread_id):
        try:
            result = self.team_progress.find_one({"thread_id": thread_id})

            if not result:
                return [], 200
            result['_id'] = str(result['_id'])

            return result['progress'], 200
        except Exception as e:
            print("Error: ", str(e))
            return {'error': str(e)}, 500 
    
    def get_challenge_instance_db(self, thread_id):
        try:
            result = self.challenge_instances.find_one({"thread_id": thread_id})
            if not result:
                return "Not found", 409
            result['_id'] = str(result['_id'])
            return result, 200
        except Exception as e:
            print("Error: ", str(e))
            return {'error': str(e)}, 500
    
    def calculate_reward(self, stake, score, max_score):
        # Define thresholds as fractions of max_score
        thresholds = {
            '0_percent': 0.125 * max_score,
            '30_percent': 0.25 * max_score,
            '40_percent': 0.5 * max_score,
            '50_70_percent': 0.75 * max_score,
            '70_100_percent': 0.975 * max_score,
            '100_percent': max_score
        }
        
        if score <= thresholds['0_percent']:
            # Score in the 0% range
            return stake * 0.0
        
        elif score <= thresholds['30_percent']:
            # Score in the 30% range
            return stake * 0.3
        
        elif score <= thresholds['40_percent']:
            # Score in the 40% range
            return stake * 0.4
        
        elif score <= thresholds['50_70_percent']:
            # Score in the 50%-70% range
            proportion = (score - thresholds['40_percent']) / (thresholds['50_70_percent'] - thresholds['40_percent'])
            return stake * (0.5 + proportion * 0.2)
        
        elif score <= thresholds['70_100_percent']:
            # Score in the 70%-100% range
            proportion = (score - thresholds['50_70_percent']) / (thresholds['70_100_percent'] - thresholds['50_70_percent'])
            return stake * (0.7 + proportion * 0.3)
        
        elif score == thresholds['100_percent']:
            # Perfect score
            return stake * 2.0
        
        else:
            # Handle unexpected scores
            return 0

    
    def set_challenge_evaluation_db(self, thread_id, score, content):
        check = self.challenge_instances.find_one({"thread_id": thread_id})
        if not check:
            return "challenge trial not found", 409
        print(check)
        
        
        uid = thread_id.split("_")[1]
        points = check['points']
        reward = self.calculate_reward(float(points), float(score), 40)
        result = self.challenge_instances.update_one({"thread_id":thread_id}, {"$set": {"score": score, "content": content, "reward": reward}})
        self.users.update_one({"uid": uid}, {"$inc": {"compute_points": reward}})
        return "success", 200