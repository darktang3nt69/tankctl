class TankNotFoundError(Exception):
    def __init__(self, detail: str = "Tank not found"):
        self.status_code = 404
        self.detail = detail

class InvalidCommandError(Exception):
    def __init__(self, detail: str = "Invalid command"):
        self.status_code = 400
        self.detail = detail

class DatabaseError(Exception):
    def __init__(self, detail: str = "Database error"):
        self.status_code = 500
        self.detail = detail 