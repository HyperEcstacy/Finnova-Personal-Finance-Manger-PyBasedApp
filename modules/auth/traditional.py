import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog
from database.core import db_instance

class TraditionalAuthenticator:
    def __init__(self, parent_window=None):
        self.current_user = None
        self.parent_window = parent_window
        self.current_window = None  # Track current dialog window
    
    def register_user(self, username, password):
        """Register new user with password authentication"""
        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty", parent=self.current_window)
            return False
            
        if db_instance.user_exists(username):
            messagebox.showerror("Error", "Username already exists", parent=self.current_window)
            return False
            
        hashed_password = self._hash_password(password)
        if db_instance.register_user(username, password=hashed_password):
            messagebox.showinfo("Success", "Registration successful!", parent=self.current_window)
            return True
        messagebox.showerror("Error", "Registration failed", parent=self.current_window)
        return False
    
    def authenticate(self, username, password):
        """Authenticate user with username/password"""
        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty", parent=self.current_window)
            return False
            
        hashed_password = self._hash_password(password)
        if db_instance.authenticate_password(username, hashed_password):
            self.current_user = username
            return True
        
        messagebox.showerror("Error", "Invalid username or password", parent=self.current_window)
        return False
    
    def change_password(self, username, old_password, new_password):
        """Change user password after verifying old password"""
        # Allow admin reset if old_password is empty (called from reset dialog)
        if old_password and not self.authenticate(username, old_password):
            return False
            
        if len(new_password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters", parent=self.current_window)
            return False
            
        hashed_password = self._hash_password(new_password)
        if db_instance.update_user_password(username, hashed_password):
            messagebox.showinfo("Success", "Password changed successfully!", parent=self.current_window)
            return True
        return False
    
    def show_register_dialog(self):
        """Show registration dialog with validation"""
        self.current_window = tk.Toplevel(self.parent_window)
        self.current_window.title("Register New Account")
        self.current_window.geometry("400x350")
        self.current_window.resizable(False, False)
        
        # Ensure window is focused
        self.current_window.grab_set()
        
        # Main container frame
        container = tk.Frame(self.current_window)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Username Section
        tk.Label(container, text="Username:", font=("Helvetica", 12)).pack(pady=(0, 5), anchor="w")
        username_entry = tk.Entry(container, font=("Helvetica", 12))
        username_entry.pack(fill=tk.X, pady=5)
        
        # Password Section
        tk.Label(container, text="Password (min 8 chars):", font=("Helvetica", 12)).pack(anchor="w", pady=(10, 5))
        password_entry = tk.Entry(container, show="*", font=("Helvetica", 12))
        password_entry.pack(fill=tk.X, pady=5)
        
        # Confirm Password Section
        tk.Label(container, text="Confirm Password:", font=("Helvetica", 12)).pack(anchor="w", pady=(10, 5))
        confirm_entry = tk.Entry(container, show="*", font=("Helvetica", 12))
        confirm_entry.pack(fill=tk.X, pady=5)
        
        def on_register():
            username = username_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "All fields are required", parent=self.current_window)
                return
                
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match", parent=self.current_window)
                return
                
            if len(password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters", parent=self.current_window)
                return
                
            if self.register_user(username, password):
                self.current_window.destroy()
                self.current_window = None
        
        register_btn = tk.Button(
            container,
            text="Register",
            command=on_register,
            font=("Helvetica", 14),
            bg="#3498DB",
            fg="white",
            padx=20,
            pady=5
        )
        register_btn.pack(pady=20, fill=tk.X)
        
        # Force window to update and display properly
        self.current_window.update_idletasks()
        
        # Set focus to username entry
        username_entry.focus_set()
    
    def show_change_password_dialog(self, username):
        """Show change password dialog with validation"""
        self.current_window = tk.Toplevel(self.parent_window)
        self.current_window.title("Change Password")
        self.current_window.geometry("400x350")
        self.current_window.resizable(False, False)
        
        # Ensure window is focused
        self.current_window.grab_set()
        
        # Main container frame
        container = tk.Frame(self.current_window)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Current Password
        tk.Label(container, text="Current Password:", font=("Helvetica", 12)).pack(anchor="w", pady=(0, 5))
        old_pw_entry = tk.Entry(container, show="*", font=("Helvetica", 12))
        old_pw_entry.pack(fill=tk.X, pady=5)
        
        # New Password
        tk.Label(container, text="New Password (min 8 chars):", font=("Helvetica", 12)).pack(anchor="w", pady=(10, 5))
        new_pw_entry = tk.Entry(container, show="*", font=("Helvetica", 12))
        new_pw_entry.pack(fill=tk.X, pady=5)
        
        # Confirm New Password
        tk.Label(container, text="Confirm New Password:", font=("Helvetica", 12)).pack(anchor="w", pady=(10, 5))
        confirm_entry = tk.Entry(container, show="*", font=("Helvetica", 12))
        confirm_entry.pack(fill=tk.X, pady=5)
        
        def on_change():
            old_password = old_pw_entry.get()
            new_password = new_pw_entry.get()
            confirm = confirm_entry.get()
            
            if not old_password or not new_password:
                messagebox.showerror("Error", "All fields are required", parent=self.current_window)
                return
                
            if new_password != confirm:
                messagebox.showerror("Error", "New passwords do not match", parent=self.current_window)
                return
                
            if len(new_password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters", parent=self.current_window)
                return
                
            if self.change_password(username, old_password, new_password):
                self.current_window.destroy()
                self.current_window = None
        
        change_btn = tk.Button(
            container,
            text="Change Password",
            command=on_change,
            font=("Helvetica", 14),
            bg="#3498DB",
            fg="white",
            padx=20,
            pady=5
        )
        change_btn.pack(pady=20, fill=tk.X)
        
        # Force window to update and display properly
        self.current_window.update_idletasks()
        
        # Set focus to current password entry
        old_pw_entry.focus_set()
    
    def show_reset_password_dialog(self):
        """Show password reset dialog"""
        self.current_window = tk.Toplevel(self.parent_window)
        self.current_window.title("Reset Password")
        self.current_window.geometry("400x300")
        self.current_window.resizable(False, False)
        
        # Ensure window is focused
        self.current_window.grab_set()
        
        # Main container frame
        container = tk.Frame(self.current_window)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Username field
        tk.Label(container, text="Username:", font=("Helvetica", 12)).pack(pady=(0, 5), anchor="w")
        username_entry = tk.Entry(container, font=("Helvetica", 12))
        username_entry.pack(fill=tk.X, pady=5)
        
        # New Password field
        tk.Label(container, text="New Password (min 8 chars):", font=("Helvetica", 12)).pack(anchor="w", pady=(10, 5))
        new_pass_entry = tk.Entry(container, show="*", font=("Helvetica", 12))
        new_pass_entry.pack(fill=tk.X, pady=5)
        
        def on_reset():
            username = username_entry.get().strip()
            new_password = new_pass_entry.get()
            
            if not username or not new_password:
                messagebox.showerror("Error", "All fields are required", parent=self.current_window)
                return
                
            if len(new_password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters", parent=self.current_window)
                return
                
            if self.change_password(username, "", new_password):  # Empty old password for admin reset
                self.current_window.destroy()
                self.current_window = None
        
        reset_btn = tk.Button(
            container,
            text="Reset Password",
            command=on_reset,
            font=("Helvetica", 14),
            bg="#3498DB",
            fg="white",
            padx=20,
            pady=5
        )
        reset_btn.pack(pady=20, fill=tk.X)
        
        # Force window to update and display properly
        self.current_window.update_idletasks()
        
        # Set focus to username entry
        username_entry.focus_set()
    
    def _hash_password(self, password):
        """Hash password using SHA-256 with salt/pepper"""
        if not password:
            return None
        # Using salt + pepper for additional security
        salt = "finnova_salt_"
        pepper = "_secret_pepper"
        return hashlib.sha256((salt + password + pepper).encode()).hexdigest()
    
    def get_current_user(self):
        """Get currently authenticated user"""
        return self.current_user