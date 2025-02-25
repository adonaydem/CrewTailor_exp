
thread_id = None
active_graph = "main"
toolkits = {}
toolkit_keys = ["file_management", "project_management", "task_management", "event_management", "database_management", "finance&economics_apipack"]

def set_active_graph(graph_name):
    """
    Sets the currently active graph, either manager or agent's name.

    Args:
        graph_name (str): The name of the graph to be set as active.

    Returns:
        None
    """
    global active_graph
    active_graph = graph_name

def get_active_graph():
    """
    Retrieves the currently active graph.

    Returns:
        str: The name of the active graph.
    """
    return active_graph