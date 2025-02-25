import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('documentation.db')

# Create a cursor object
cursor = conn.cursor()

# Create the guide table
create_table_query = """
CREATE TABLE IF NOT EXISTS guide (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    guide TEXT NOT NULL
);
"""
cursor.execute(create_table_query)

# The guide content to insert
guides = {
    "new_wrokflow": """
        ## New workflow
        Users can tailor workflows according to their needs. They have the following options to create a workflow:
        1. Form
        2. Visualization
        3. Chat with PAM

        The input needed from the system is explained, using the following example. There are two  major aspects of a workflow. The first one is metadata(General workflow Details) and Nodes which represent the AI Agents.
        "metadata": {
            "description": "”,
            "name": "",
            "pad": "",
            "people": [],
            "public": boolean,
            "to_do_list": [ ] }
        "nodes": [
            {
            "children": [], #id of other nodes
            "description": "",
            "human_direction": "", #Choose either yes or no. yes means there is human supervision.
            "id": "", #Unique id for each node
            "name": "",
            "pad": "",
            "to_do_list": [],
            "toolkits": [] #choose from the following only: ["file_management", "project_management", "task_management", "event_management", "database_management"]
            }
        ]
        In each section, name and description are required.
        """,
    "run_workflow": """
        ## How to run a workflow
        User can only run a workflow manually.
        When a workflow runs, it will have steps, each handled by different ai agent. A workflow will additionally have an agent called manager.
        The manager will instruct and get info for you.

        The best practice is to tell user's needs to the manager, and he will automatically connect the user to the relevant team member.
        However, users can jump directly on to agents(Not recommended.)
    """,
    "doli": """
    Doli is an intelligent examiner. Users can't talk with this AI, she is integrated into the system. She is part of Challenge feature.
    She will score your workflow, based on the challenge content and the workflow structure(skeleton).
    """
}


for key, value in guides.items():
    # Insert a record into the guide table
    insert_query = """
    INSERT INTO guide (topic, guide)
    VALUES (?, ?);
    """
    cursor.execute(insert_query, (key, value))

# Commit the transaction
conn.commit()

# Select and print the records to verify insertion
select_query = "SELECT * FROM guide;"
cursor.execute(select_query)

rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()

print("Record inserted and verified successfully.")
