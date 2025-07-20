from .core import Database

class AuthDB(Database):
    def __init__(self):
        super().__init__()
        self._create_tables()
    
    def _create_tables(self):
        """Create authentication tables"""
        self.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            use_face_auth BOOLEAN DEFAULT 0
        )
        ''')
    
    def get_user_auth_method(self, username):
        """Check if user prefers face auth"""
        return self.query(
            'SELECT use_face_auth FROM users WHERE username = ?',
            (username,),
            single=True
        )