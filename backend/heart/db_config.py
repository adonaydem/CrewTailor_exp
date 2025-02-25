import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'dbs')

    @staticmethod
    def get_workflow_database_path( user_id, workflow_id):
        return os.path.join(Config.DB_PATH, str(user_id), f"{str(workflow_id)}.db")

