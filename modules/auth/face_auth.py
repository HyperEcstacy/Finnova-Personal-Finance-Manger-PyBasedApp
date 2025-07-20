import cv2
import face_recognition
import pickle
import os
import numpy as np
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import gc
from database.core import db_instance

class FaceAuthenticator:
    def __init__(self, parent_window=None):
        self.known_faces_path = Path(__file__).parent.parent.parent / "assets" / "face_models" / "known_faces.dat"
        self.known_face_encodings = []
        self.known_face_names = []
        self.parent_window = parent_window
        self.cap = None
        self.video_label = None
        self.current_window = None
        self.is_camera_active = False
        self.pause_camera = False
        self.camera_lock = False
        self.hardware_verified = False
        self.last_capture_time = 0
        self.camera_index = 0  # Track which camera index works
        self.backend_preference = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load pre-registered faces from file with error handling"""
        try:
            if self.known_faces_path.exists():
                with open(self.known_faces_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data['encodings']
                    self.known_face_names = data['names']
                    print(f"[FACE AUTH] Loaded {len(self.known_face_names)} registered faces")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load face data: {str(e)}", parent=self.parent_window)
            self.known_face_encodings = []
            self.known_face_names = []
    
    def save_known_faces(self):
        """Save current face data to file with atomic write"""
        try:
            os.makedirs(self.known_faces_path.parent, exist_ok=True)
            temp_path = str(self.known_faces_path) + ".tmp"
            with open(temp_path, 'wb') as f:
                pickle.dump({
                    'encodings': self.known_face_encodings,
                    'names': self.known_face_names
                }, f)
            
            # Atomic replacement
            if os.path.exists(self.known_faces_path):
                os.remove(self.known_faces_path)
            os.rename(temp_path, self.known_faces_path)
            print("[FACE AUTH] Saved known faces data")
            return True
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            messagebox.showerror("Error", f"Failed to save face data: {str(e)}", parent=self.parent_window)
            return False
    
    def verify_hardware(self):
        """Enhanced hardware verification with multiple attempts"""
        try:
            # Try different combinations of camera index and backend
            attempts = [
                {'index': self.camera_index, 'backend': self.backend_preference},
                {'index': self.camera_index, 'backend': cv2.CAP_ANY},
                {'index': 0, 'backend': self.backend_preference},
                {'index': 0, 'backend': cv2.CAP_ANY}
            ]
            
            for attempt in attempts:
                temp_cap = cv2.VideoCapture(attempt['index'], attempt['backend'])
                if temp_cap.isOpened():
                    # Test actual frame capture
                    temp_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    temp_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    
                    for _ in range(3):  # Try multiple frames
                        ret, _ = temp_cap.read()
                        if ret:
                            self.camera_index = attempt['index']  # Remember working index
                            temp_cap.release()
                            self.hardware_verified = True
                            return True
                    temp_cap.release()
            return False
        except Exception as e:
            print(f"[HARDWARE VERIFICATION ERROR] {str(e)}")
            return False
    
    def start_camera(self, video_label):
        """Robust camera initialization with multiple fallback strategies"""
        if self.camera_lock:
            return False
            
        self.camera_lock = True
        try:
            if self.is_camera_active:
                return True
                
            # Full cleanup before starting
            self._hard_stop_camera()
            time.sleep(0.3)  # Allow hardware to reset
            
            # Try different initialization strategies
            strategies = [
                {'index': self.camera_index, 'backend': self.backend_preference},
                {'index': self.camera_index, 'backend': cv2.CAP_ANY},
                {'index': 0, 'backend': self.backend_preference},
                {'index': 0, 'backend': cv2.CAP_ANY}
            ]
            
            for strategy in strategies:
                self.cap = cv2.VideoCapture(strategy['index'], strategy['backend'])
                if self.cap.isOpened():
                    self.camera_index = strategy['index']  # Remember working index
                    break
            
            if not self.cap.isOpened():
                print("[CAMERA] All initialization attempts failed")
                return False
            
            # Configure camera for stable operation
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus
            
            # Verify we can actually get frames
            for _ in range(3):
                if self.cap.grab():
                    break
            else:
                raise RuntimeError("Camera initialized but can't grab frames")
            
            self.video_label = video_label
            self.is_camera_active = True
            self.pause_camera = False
            self._update_camera()
            return True
            
        except Exception as e:
            print(f"[CAMERA START ERROR] {str(e)}")
            self._hard_stop_camera()
            return False
        finally:
            self.camera_lock = False
    
    def _hard_stop_camera(self):
        """Comprehensive camera resource cleanup"""
        try:
            if self.cap is not None:
                # Multiple release attempts
                for _ in range(3):
                    try:
                        self.cap.release()
                    except:
                        pass
                self.cap = None
            
            # Additional DirectShow cleanup on Windows
            if os.name == 'nt':
                for i in range(3):  # Try multiple camera indexes
                    try:
                        temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                        if temp_cap.isOpened():
                            temp_cap.release()
                    except:
                        pass
            
            self.is_camera_active = False
            self.pause_camera = False
            
            if self.video_label and self.video_label.winfo_exists():
                self.video_label.config(image='')
                if hasattr(self.video_label, 'imgtk'):
                    del self.video_label.imgtk
            
            gc.collect()
            time.sleep(0.1)  # Small delay for hardware reset
        except Exception as e:
            print(f"[HARD CAMERA STOP ERROR] {str(e)}")
    
    def _update_camera(self):
        """Camera feed update loop with robust error handling"""
        if (not self.is_camera_active or self.pause_camera or 
            not self.video_label or not self.video_label.winfo_exists()):
            return
            
        try:
            if self.camera_lock:
                self.video_label.after(100, self._update_camera)
                return
                
            # Clear buffer
            for _ in range(2):
                self.cap.grab()
                
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Maintain aspect ratio
                height, width = frame.shape[:2]
                max_height = 500
                if height > max_height:
                    ratio = max_height / float(height)
                    frame = cv2.resize(frame, (int(width * ratio), max_height))
                
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                if self.video_label.winfo_exists():
                    self.video_label.imgtk = imgtk
                    self.video_label.configure(image=imgtk)
            
            if self.is_camera_active and not self.pause_camera:
                self.video_label.after(30, self._update_camera)
                
        except Exception as e:
            print(f"[CAMERA UPDATE ERROR] {str(e)}")
            self._hard_stop_camera()
    
    def stop_camera(self):
        """Clean camera shutdown"""
        self._hard_stop_camera()
        self.hardware_verified = False
    
    def capture_face_encoding(self):
        """Capture face encoding with multiple attempts"""
        if not self.is_camera_active or self.pause_camera:
            return None
            
        # Prevent rapid consecutive captures
        current_time = time.time()
        if current_time - self.last_capture_time < 1.0:
            return None
            
        self.last_capture_time = current_time
        self.pause_camera = True
        
        try:
            face_encoding = None
            for attempt in range(3):  # Try multiple times
                # Clear buffer
                for _ in range(3):
                    self.cap.grab()
                    
                ret, frame = self.cap.read()
                if not ret:
                    continue
                    
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Enhanced face detection
                face_locations = face_recognition.face_locations(
                    rgb_frame,
                    model="cnn",
                    number_of_times_to_upsample=1
                )
                
                if not face_locations:
                    continue
                    
                # High-quality encoding
                face_encodings = face_recognition.face_encodings(
                    rgb_frame,
                    known_face_locations=face_locations,
                    num_jitters=3,
                    model="large"
                )
                
                if face_encodings:
                    face_encoding = face_encodings[0]
                    break
                
                time.sleep(0.2)  # Small delay between attempts
            
            return face_encoding
            
        except Exception as e:
            print(f"[FACE CAPTURE ERROR] {str(e)}")
            return None
        finally:
            self.pause_camera = False
    
    def register_user(self, username, max_attempts=3):
        """Register new user with validation"""
        if not username or not isinstance(username, str):
            messagebox.showerror("Error", "Username cannot be empty", parent=self.current_window)
            return False
            
        if username in self.known_face_names or db_instance.user_exists(username):
            messagebox.showerror("Error", "Username already exists", parent=self.current_window)
            return False
            
        for attempt in range(max_attempts):
            try:
                face_encoding = self.capture_face_encoding()
                if face_encoding is None:
                    messagebox.showwarning("No Face", "No face detected", parent=self.current_window)
                    continue
                    
                # Check for existing face
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding,
                    tolerance=0.35
                )
                
                if any(matches):
                    messagebox.showerror("Error", "Face already registered", parent=self.current_window)
                    return False
                
                # Store data
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(username)
                
                # Save to database
                if not db_instance.register_user(username, face_encoding=face_encoding.tolist()):
                    raise RuntimeError("Database save failed")
                
                if not self.save_known_faces():
                    raise RuntimeError("Face data save failed")
                
                messagebox.showinfo("Success", "Registration successful", parent=self.current_window)
                return True
                
            except Exception as e:
                # Rollback on error
                if username in self.known_face_names:
                    idx = self.known_face_names.index(username)
                    self.known_face_names.pop(idx)
                    self.known_face_encodings.pop(idx)
                
                print(f"[REGISTRATION ERROR] {str(e)}")
                messagebox.showerror("Error", f"Registration failed: {str(e)}", parent=self.current_window)
                
        return False
    
    def authenticate(self, face_encoding=None, max_attempts=3, confidence_threshold=0.6):
        """Authenticate user with face recognition"""
        if not self.known_face_encodings:
            messagebox.showinfo("No Users", "No registered users", parent=self.current_window)
            return None
            
        for attempt in range(max_attempts):
            try:
                current_encoding = face_encoding or self.capture_face_encoding()
                if current_encoding is None:
                    messagebox.showwarning("No Face", "No face detected", parent=self.current_window)
                    continue
                    
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    current_encoding,
                    tolerance=0.4
                )
                
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings,
                    current_encoding
                )
                
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index] and face_distances[best_match_index] < (1 - confidence_threshold):
                    username = self.known_face_names[best_match_index]
                    if db_instance.user_exists(username):
                        return username
                    else:
                        messagebox.showerror("Error", "User data mismatch", parent=self.current_window)
                        return None
                
                messagebox.showwarning("No Match", "Face not recognized", parent=self.current_window)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Authentication failed: {str(e)}", parent=self.current_window)
                
        return None
    
    def show_register_dialog(self):
        """Show registration dialog"""
        if self.current_window and self.current_window.winfo_exists():
            self.current_window.destroy()
            
        self.current_window = tk.Toplevel(self.parent_window)
        self.current_window.title("Register New Face")
        self.current_window.geometry("800x650")
        self.current_window.resizable(False, False)
        
        # Main container
        main_frame = tk.Frame(self.current_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Video feed
        video_frame = tk.Frame(main_frame, bd=2, relief=tk.SUNKEN)
        video_frame.pack(pady=(0, 20), fill=tk.BOTH, expand=True)
        
        video_label = tk.Label(video_frame)
        video_label.pack(fill=tk.BOTH, expand=True)
        
        # Form
        form_frame = tk.Frame(main_frame)
        form_frame.pack(fill=tk.X)
        
        tk.Label(form_frame, text="Username:", font=("Helvetica", 12)).pack(anchor=tk.W, pady=(0, 5))
        username_entry = tk.Entry(form_frame, font=("Helvetica", 12))
        username_entry.pack(fill=tk.X, pady=5)
        
        def on_register():
            username = username_entry.get().strip()
            if not username:
                messagebox.showerror("Error", "Username required", parent=self.current_window)
                return
                
            if self.register_user(username):
                self.current_window.destroy()
                self.current_window = None
        
        register_btn = tk.Button(
            main_frame,
            text="Register Face",
            command=on_register,
            font=("Helvetica", 14),
            bg="#3498DB",
            fg="white",
            padx=20,
            pady=10
        )
        register_btn.pack(pady=(10, 0), fill=tk.X)
        
        # Start camera with delay
        def start_camera():
            if not self.start_camera(video_label):
                self.current_window.destroy()
                messagebox.showerror("Error", "Could not initialize camera", parent=self.parent_window)
        
        self.current_window.after(300, start_camera)
        
        # Window close handler
        def on_window_close():
            self.stop_camera()
            self.current_window.destroy()
            self.current_window = None
            
        self.current_window.protocol("WM_DELETE_WINDOW", on_window_close)
        username_entry.focus_set()
    
    def __del__(self):
        """Destructor for cleanup"""
        self._hard_stop_camera()