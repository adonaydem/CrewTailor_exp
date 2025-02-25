# socketio_manager.py
class SocketIOManager:
    """
    A Singleton class that manages a Socket.IO object.

    This class ensures that only one instance of the Socket.IO object is created,
    and provides a way to access and set the object through the `socketio` property.

    Attributes:
        socketio (object): The managed Socket.IO object.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SocketIOManager, cls).__new__(cls)
            cls._socketio = None
        return cls._instance

    @property
    def socketio(self):
        return self._socketio

    @socketio.setter
    def socketio(self, socketio):
        self._socketio = socketio