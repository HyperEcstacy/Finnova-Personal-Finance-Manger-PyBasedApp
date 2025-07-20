import json
import os
import face_recognition
import hashlib
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

DATA_FILE = "database/data.json"
FACE_DATA_FILE = "assets/face_models/known_faces.dat"

class Database:
    def __init__(self):
        print(f"[INIT] Initializing database, data file: {DATA_FILE}")
        self.data = self.load_data()
        self.face_data = self.load_face_data()
        self._callbacks = []  # Add this line for callback registry
        print(f"[INIT] Loaded {len(self.data['users'])} users and {len(self.face_data['encodings'])} face encodings")

    def load_data(self):
        """Load financial data from JSON file with enhanced error handling"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as file:
                    data = json.load(file)
            else:
                data = {
                    "income": [],
                    "expenses": [],
                    "categories": [],  # Ensure categories exists
                    "budget": {},
                    "goals": [],
                    "users": []
                }
                self.save_data(data)

            # Validate and repair data structure
            required_keys = {
                "income": list,
                "expenses": list,
                "categories": list,  # This is crucial
                "budget": dict,
                "goals": list,
                "users": list
            }
            
            for key, expected_type in required_keys.items():
                if key not in data or not isinstance(data[key], expected_type):
                    data[key] = expected_type()
                    
            # Ensure categories contains only strings and no duplicates
            if 'categories' in data:
                data['categories'] = list({str(c) for c in data['categories'] if c})
                    
            return data

        except Exception as e:
            print(f"Error loading data: {e}")
            return {
                "income": [],
                "expenses": [],
                "categories": [],  # Always include categories
                "budget": {},
                "goals": [],
                "users": []
            }
        
    def load_face_data(self):
        """Load face recognition data from file"""
        try:
            face_data_path = Path(FACE_DATA_FILE)
            if face_data_path.exists():
                with open(face_data_path, 'rb') as f:
                    data = pickle.load(f)
                    # Ensure the loaded data has the correct structure
                    if 'encodings' not in data or 'usernames' not in data:
                        print("[WARNING] Face data file has invalid structure, creating new")
                        return {'encodings': [], 'usernames': []}
                    return data
            return {'encodings': [], 'usernames': []}
        except Exception as e:
            print(f"[ERROR] Loading face data: {str(e)}")
            return {'encodings': [], 'usernames': []}
    
    def save_data(self, data=None):
        """Save financial data to JSON file with atomic write"""
        data_to_save = data if data is not None else self.data
        success = False
        temp_file = None
        
        try:
            # Debug output to verify categories are present
            print(f"[DEBUG] Saving data with categories: {data_to_save.get('categories', [])}")
            
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            temp_file = DATA_FILE + ".tmp"
            with open(temp_file, 'w') as file:
                json.dump(data_to_save, file, indent=4)
            
            # Atomic save operation
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            os.rename(temp_file, DATA_FILE)
            success = True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            
        finally:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
        
        if success:
            self.notify_callbacks()
        
        return success
    
    def save_face_data(self):
        """Save face recognition data to file with atomic write"""
        try:
            os.makedirs(os.path.dirname(FACE_DATA_FILE), exist_ok=True)
            # Write to temporary file first
            temp_file = FACE_DATA_FILE + ".tmp"
            with open(temp_file, 'wb') as f:
                pickle.dump(self.face_data, f)
            # Replace original file
            if os.path.exists(FACE_DATA_FILE):
                os.remove(FACE_DATA_FILE)
            os.rename(temp_file, FACE_DATA_FILE)
            print("[SAVE] Face data saved successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Saving face data: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

    def register_user(self, username, password=None, face_encoding=None):
        """
        Register user with both password and face authentication
        Args:
            username (str): Unique username
            password (str): Optional password for traditional auth
            face_encoding: Optional face encoding for face auth
        Returns:
            bool: True if registration successful
        """
        print(f"[REGISTER] Attempting to register user: {username}")
        
        # Validation
        if not username or not isinstance(username, str):
            print("[ERROR] Invalid username format")
            return False
            
        if self.user_exists(username):
            print(f"[ERROR] Username '{username}' already exists")
            return False

        try:
            # Convert numpy array to list for JSON serialization
            face_encoding_list = None
            if face_encoding is not None:
                try:
                    if isinstance(face_encoding, np.ndarray):
                        face_encoding_list = face_encoding.tolist()
                    elif hasattr(face_encoding, '__iter__'):
                        face_encoding_list = list(face_encoding)
                    else:
                        raise ValueError("Invalid face encoding format")
                    
                    # Validate the face encoding
                    if len(face_encoding_list) != 128:  # Standard face encoding length
                        raise ValueError("Invalid face encoding length")
                except Exception as e:
                    print(f"[ERROR] Invalid face encoding: {str(e)}")
                    return False

            # Create user data structure
            user_data = {
                "username": username,
                "password_hash": self._hash_password(password) if password else None,
                "face_encoding": face_encoding_list,
                "registration_date": datetime.now().isoformat(),
                "auth_methods": []
            }

            # Track enabled auth methods
            if password:
                user_data["auth_methods"].append("password")
            if face_encoding is not None:
                user_data["auth_methods"].append("face")

            # Validate at least one auth method
            if not user_data["auth_methods"]:
                print("[ERROR] No authentication method provided")
                return False

            # Store data
            self.data["users"].append(user_data)
            
            # Store face data separately if provided
            if face_encoding is not None:
                try:
                    # Ensure face_encoding is in numpy array format
                    if not isinstance(face_encoding, np.ndarray):
                        face_encoding = np.array(face_encoding)
                    
                    self.face_data["encodings"].append(face_encoding)
                    self.face_data["usernames"].append(username)
                    
                    if not self.save_face_data():
                        raise RuntimeError("Failed to save face data")
                except Exception as e:
                    print(f"[ERROR] Failed to process face encoding: {str(e)}")
                    # Rollback user data if face data fails
                    self.data["users"] = [u for u in self.data["users"] if u["username"] != username]
                    return False

            if not self.save_data():
                print("[WARNING] User data may not have saved correctly")
                # Rollback face data if user data fails
                if face_encoding is not None and username in self.face_data["usernames"]:
                    idx = self.face_data["usernames"].index(username)
                    self.face_data["usernames"].pop(idx)
                    self.face_data["encodings"].pop(idx)
                    self.save_face_data()
                return False

            print(f"[SUCCESS] User {username} registered with methods: {user_data['auth_methods']}")
            return True

        except Exception as e:
            print(f"[ERROR] Registration failed: {str(e)}")
            # Cleanup partial registration
            if username in [u["username"] for u in self.data["users"]]:
                self.data["users"] = [u for u in self.data["users"] if u["username"] != username]
            if face_encoding is not None and username in self.face_data["usernames"]:
                idx = self.face_data["usernames"].index(username)
                self.face_data["usernames"].pop(idx)
                self.face_data["encodings"].pop(idx)
                self.save_face_data()
            return False

    def add_transaction(self, transaction_type, transaction_data):
        """Add income or expense transaction"""
        if transaction_type not in ['income', 'expenses']:
            raise ValueError("Invalid transaction type")
        
        # Load fresh data to ensure we're working with current state
        current_data = self.load_data()
        
        # Ensure the transaction type exists
        if transaction_type not in current_data:
            current_data[transaction_type] = []
        
        # Add the transaction
        current_data[transaction_type].append(transaction_data)
        
        # Preserve categories if this is an expense with a new category
        if transaction_type == 'expenses' and 'category' in transaction_data:
            category = transaction_data['category']
            if 'categories' not in current_data:
                current_data['categories'] = []
            if category not in current_data['categories']:
                current_data['categories'].append(category)
        
        # Save the updated data
        success = self.save_data(current_data)
        
        if success:
            self.notify_callbacks()
        
        return success
        
    def authenticate_password(self, username, password):
        """Authenticate user with password"""
        user = next((u for u in self.data['users'] if u['username'] == username), None)
        if not user or not user['password_hash']:
            return False
        return user['password_hash'] == self._hash_password(password)
    
    def authenticate_face(self, face_encoding):
        """Authenticate user with face recognition"""
        if not self.face_data['encodings']:
            return None
        
        # Convert input to numpy array if it isn't already
        try:
            if not isinstance(face_encoding, np.ndarray):
                face_encoding = np.array(face_encoding)
        except Exception as e:
            print(f"[ERROR] Invalid face encoding format: {str(e)}")
            return None
        
        matches = face_recognition.compare_faces(
            self.face_data['encodings'], 
            face_encoding,
            tolerance=0.4  # Slightly stricter tolerance
        )
        
        if True in matches:
            idx = matches.index(True)
            # Verify the user exists in main database
            username = self.face_data['usernames'][idx]
            if self.user_exists(username):
                return username
            else:
                print(f"[WARNING] Face match found but user {username} not in main database")
                return None
        return None
    
    def _hash_password(self, password):
        """Hash password using SHA-256 with salt and pepper"""
        if not password:
            return None
        # Using a pepper for additional security
        pepper = "finnova_secret_pepper"
        # Add a salt from environment variable or default
        salt = os.getenv("FINNOVA_PASSWORD_SALT", "default_salt_value")
        return hashlib.sha256((password + pepper + salt).encode()).hexdigest()
    
    def user_exists(self, username):
        """Check if username exists"""
        return any(user['username'] == username for user in self.data['users'])
    
    def get_user_auth_methods(self, username):
        """Get user's available authentication methods"""
        user = next((u for u in self.data['users'] if u['username'] == username), None)
        if not user:
            return []
        methods = []
        if user.get('password_hash'):
            methods.append('password')
        if user.get('face_encoding'):
            methods.append('face')
        return methods

    def get_user_face_encoding(self, username):
        """Get stored face encoding for a user"""
        user = next((u for u in self.data['users'] if u['username'] == username), None)
        if not user or not user.get('face_encoding'):
            return None
        try:
            return np.array(user['face_encoding'])
        except Exception as e:
            print(f"[ERROR] Failed to convert face encoding for user {username}: {str(e)}")
            return None
        

    def register_callback(self, callback):
        """Register a callback to be notified when data changes"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            print(f"[CALLBACK] Registered new callback, total: {len(self._callbacks)}")

    def unregister_callback(self, callback):
        """Remove a callback from the notification list"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            print(f"[CALLBACK] Unregistered callback, remaining: {len(self._callbacks)}")

    def notify_callbacks(self):
        """Safely notify all registered callbacks"""
        for callback in self._callbacks[:]:  # Use copy of list
            try:
                if hasattr(callback, '__call__'):
                    # Use after() to schedule callback in main thread
                    if hasattr(callback, 'root') and hasattr(callback.root, 'after'):
                        callback.root.after(0, callback)
                    else:
                        callback()
            except Exception as e:
                print(f"Error notifying callback: {str(e)}")
                # Optionally remove faulty callback
                self._callbacks.remove(callback)

# Singleton database instance
db_instance = Database()