import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import time
from datetime import datetime
import cv2
import face_recognition
import pickle
import os
import gc
import numpy as np
import webbrowser
import random
from modules.auth.face_auth import FaceAuthenticator
from modules.auth.traditional import TraditionalAuthenticator
from database.core import db_instance
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
from modules.transactions import TransactionWindow
from modules.reports import ReportWindow
from modules.budget import BudgetWindow
from modules.categories import CategoriesWindow
from modules.goals.manager import GoalsWindow, get_goals, calculate_goal_progress
from assets.styles import set_theme
import requests  # Added for Hugging Face API
import json  # Added for Hugging Face API

# Add your Hugging Face API token here
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")  # Store in .env file

class FinanceAIChatbot:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        self.chat_history = []
        self.model_ready = False
        self.finance_context = (
            "You are Finnova, an expert financial assistant. Your responses should be:\n"
            "- Concise and professional\n"
            "- Focused on personal finance topics\n"
            "- Formatted with bullet points when listing items\n"
            "- Include emojis for better readability (💰, 📈, etc.)\n"
            "Specializations:\n"
            "• Budgeting\n• Investing\n• Debt management\n• Savings strategies"
        )
        self.check_model_status()

    def check_model_status(self):
        """Check if the model is ready to use"""
        try:
            status_url = HUGGINGFACE_API_URL.replace("/models/", "/status/").split("@")[0]
            response = requests.get(status_url, headers=self.headers, timeout=10)
            self.model_ready = response.status_code == 200
            if not self.model_ready:
                print(f"Model status: {response.json().get('status', 'unknown')}")
        except Exception as e:
            print(f"Model status check failed: {str(e)}")
            self.model_ready = False

    def query(self, payload):
        """Send query to Hugging Face API with robust error handling"""
        try:
            response = requests.post(
                HUGGINGFACE_API_URL,
                headers=self.headers,
                json=payload,
                timeout=20  # Increased timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Model is loading
                wait_time = response.json().get('estimated_time', 30)
                return {
                    "error": f"Model is loading. Please wait {wait_time} seconds and try again",
                    "retry_after": wait_time
                }
            else:
                return {
                    "error": f"API Error {response.status_code}",
                    "details": response.text[:200]  # Truncate long error messages
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": "Connection error",
                "details": str(e)
            }

    def generate_response(self, user_input):
        """Generate AI response with conversation context"""
        # Initialize with finance context if empty history
        if not self.chat_history:
            self.chat_history.append({
                "role": "system",
                "content": self.finance_context
            })
        
        # Add user message to history
        self.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Prepare payload with conversation history
        payload = {
            "inputs": {
                "text": user_input,
                "past_user_inputs": [
                    msg["content"] for msg in self.chat_history 
                    if msg["role"] == "user"
                ],
                "generated_responses": [
                    msg["content"] for msg in self.chat_history 
                    if msg["role"] == "assistant"
                ]
            },
            "parameters": {
                "max_length": 150,  # More concise responses
                "temperature": 0.7,
                "repetition_penalty": 1.2,
                "return_full_text": False
            }
        }
        
        # Get API response
        response = self.query(payload)
        
        # Handle errors
        if "error" in response:
            error_msg = f"{response['error']}"
            if "details" in response:
                error_msg += f"\nDetails: {response['details']}"
            return {"error": error_msg}
        
        # Add assistant response to history
        assistant_response = response.get("generated_text", "I didn't get a response. Please try again.")
        self.chat_history.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # Limit history to last 5 exchanges (10 messages)
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]
            
        return assistant_response


class FinanceTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Hide main window until login
        
        # Store reference to self in root for access from login window
        self.root.app = self
        
        # Initialize AI Chatbot
        self.ai_chatbot = FinanceAIChatbot()
        
        # Initialize login window
        self.login_window = LoginWindow(self.root)
        self.login_window.parent = self  # Explicitly set parent reference
        self.login_window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize main app components but don't show yet
        self.main_frame = None
        self.username = None
        self.initialized = False
        self.dashboard_frame = None
        self.chat_history = []  # Store chat history for context
        self.game_score = 0  # Track financial game score


    def on_close(self):
        """Handle application close"""
        try:
            if hasattr(self, 'login_window') and self.login_window.winfo_exists():
                self.login_window.destroy()
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.destroy()
        except Exception as e:
            print(f"Error during close: {e}")
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.destroy()

    def set_username(self, username):
        """Update the GUI with the logged in username"""
        self.username = username
        if not self.initialized:
            self.initialize_main_app()
            self.initialized = True
        
        # Update welcome label in separator
        if hasattr(self, 'welcome_label'):
            self.welcome_label.config(text=f"Welcome {username}")
            
        # Ensure main window is visible
        self.root.deiconify()

    def initialize_main_app(self):
        """Initialize all main app components"""
        try:
            self.root.title("Finnova - Personal Finance Manager")
            self.root.geometry("1200x800")
            self.root.minsize(1000, 700)

            set_theme(self.root)

            # Main Frame Layout
            self.main_frame = tk.Frame(self.root, bg="#E8F0FF")
            self.main_frame.pack(fill=tk.BOTH, expand=True)

            # Simplified Header
            self.header_frame = tk.Frame(self.main_frame, bg="#1C2E40")
            self.header_frame.pack(fill=tk.X)
            
            # Only keep the app name in header
            self.header_label = tk.Label(self.header_frame, 
                                     text="Finnova",
                                     font=("Helvetica Neue", 22, "bold"),
                                     bg="#1C2E40",
                                     fg="white",
                                     pady=18)
            self.header_label.pack(side=tk.LEFT, padx=25)

            # Separator Frame - Now contains all the info that was in header
            self.separator_frame = tk.Frame(self.main_frame, bg="#D0E0F0", height=36)
            self.separator_frame.pack(fill=tk.X)

            self.separator_frame.grid_columnconfigure(0, weight=1)
            self.separator_frame.grid_columnconfigure(1, weight=1)
            self.separator_frame.grid_columnconfigure(2, weight=1)

            # Welcome message (left)
            self.welcome_label = tk.Label(self.separator_frame,
                                        text=f"Welcome {self.username}",
                                        font=("Helvetica Neue", 13, "bold"),
                                        bg="#D0E0F0",
                                        fg="#1A2530")
            self.welcome_label.grid(row=0, column=0, padx=25, pady=0, ipady=3, sticky=tk.W)

            # Current date (center)
            self.date_label = tk.Label(self.separator_frame,
                                      text="",
                                      font=("Helvetica Neue", 13, "bold"),
                                      bg="#D0E0F0",
                                      fg="#1A2530")
            self.date_label.grid(row=0, column=1, pady=0, ipady=3)
            
            # Current time (right)
            self.time_label = tk.Label(self.separator_frame,
                                     text="",
                                     font=("Helvetica Neue", 13, "bold"),
                                     bg="#D0E0F0",
                                     fg="#1A2530")
            self.time_label.grid(row=0, column=2, padx=25, pady=0, ipady=3, sticky=tk.E)
            
            self.update_time()

            # Content Frame (Sidebar + Main Content)
            self.content_frame = tk.Frame(self.main_frame, bg="#E8F0FF")
            self.content_frame.pack(fill=tk.BOTH, expand=True)

            # Sidebar
            self.sidebar = tk.Frame(self.content_frame, bg="#2C3E50", width=250)
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
            self.sidebar.pack_propagate(False)

            self.create_sidebar_buttons()

            # Main Content Area
            self.main_content = tk.Frame(self.content_frame, bg="#E8F0FF")
            self.main_content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            # Initialize all tabs (but don't show yet)
            self.transaction_tab = TransactionWindow(self.main_content)
            self.report_tab = ReportWindow(self.main_content)
            self.budget_tab = BudgetWindow(self.main_content)
            self.categories_tab = CategoriesWindow(self.main_content)
            self.goals_tab = GoalsWindow(self.main_content)
            self.transaction_tab.report_window = self.report_tab

            # Show dashboard by default
            self.show_dashboard()
            
            self.initialized = True
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize app: {str(e)}")
            self.on_close()

    def update_time(self):
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")
        formatted_time = now.strftime("%H:%M:%S")
        self.date_label.config(text=formatted_date)
        self.time_label.config(text=formatted_time)
        self.date_label.after(1000, self.update_time)

    def create_sidebar_buttons(self):
        # Add logo or app name at the top of sidebar
        logo_label = tk.Label(
            self.sidebar,
            text="FINNOVA",
            font=("Helvetica Neue", 18, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1",
            pady=20
        )
        logo_label.pack(fill="x")

        # Add separator
        separator = ttk.Separator(self.sidebar, orient="horizontal")
        separator.pack(fill="x", padx=15, pady=5)

        menu_items = [
            ("🏠 Overview", self.show_dashboard),
            ("💰 Transactions", lambda: self.show_tab(self.transaction_tab.frame)),
            ("📊 Reports", lambda: self.show_tab(self.report_tab.frame)),
            ("📅 Budget", lambda: self.show_tab(self.budget_tab.frame)),
            ("📂 Categories", lambda: self.show_tab(self.categories_tab.frame)),
            ("🎯 Goals", lambda: self.show_tab(self.goals_tab.frame)),
        ]

        # Create a frame for buttons
        button_frame = tk.Frame(self.sidebar, bg="#2C3E50")
        button_frame.pack(fill="x", pady=10)

        for text, command in menu_items:
            button = tk.Button(
                button_frame,
                text=text,
                font=("Helvetica Neue", 14, "bold"),
                bg="#34495E",
                fg="white",
                bd=0,
                relief="flat",
                activebackground="#1A2939",
                activeforeground="#ECF0F1",
                command=command,
                pady=14,
                padx=25,
                anchor="w",
                cursor="hand2",
            )
            button.pack(fill="x", pady=6, padx=15)

        # Add logout button
        logout_button = tk.Button(
            button_frame,
            text="🔒 Logout",
            command=self.logout,
            font=("Helvetica Neue", 14, "bold"),
            bg="#E74C3C",
            fg="white",
            bd=0,
            relief="flat",
            activebackground="#C0392B",
            activeforeground="#ECF0F1",
            pady=14,
            padx=25,
            anchor="w",
            cursor="hand2",
        )
        logout_button.pack(fill="x", pady=(20, 10), padx=15)

        # Add social media section
        social_frame = tk.Frame(self.sidebar, bg="#2C3E50", pady=10)
        social_frame.pack(fill="x", side=tk.BOTTOM)

        # Add separator
        ttk.Separator(social_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Social media title
        tk.Label(
            social_frame,
            text="Connect With Us",
            font=("Helvetica Neue", 8, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        ).pack(pady=(0, 2))

        # Social media buttons frame
        social_buttons_frame = tk.Frame(social_frame, bg="#2C3E50")
        social_buttons_frame.pack()

        # Social media platforms
        platforms = [
            ("Facebook", "#3B5998", "https://facebook.com/finnova"),
            ("Twitter", "#1DA1F2", "https://twitter.com/finnova"),
            ("Instagram", "#E1306C", "https://instagram.com/finnova")
        ]

        for platform, color, url in platforms:
            btn = tk.Button(
                social_buttons_frame,
                text=platform,
                font=("Helvetica Neue", 8, "bold"),
                bg=color,
                fg="white",
                bd=0,
                relief="flat",
                padx=7,
                pady=3,
                command=lambda u=url: webbrowser.open(u)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5, fill="x")

        # Add version info at bottom
        version_label = tk.Label(
            social_frame,
            text="Version 1.0",
            font=("Helvetica Neue", 10),
            bg="#2C3E50",
            fg="#95A5A6",
            pady=10
        )
        version_label.pack(side="bottom", fill="x")

    def show_tab(self, tab_frame):
        self.dashboard_frame.pack_forget()
        self.transaction_tab.frame.pack_forget()
        self.report_tab.frame.pack_forget()
        self.budget_tab.frame.pack_forget()
        self.categories_tab.frame.pack_forget()
        self.goals_tab.frame.pack_forget()
        tab_frame.pack(fill=tk.BOTH, expand=True)

    def show_dashboard(self):
        """Show the dashboard view with adjusted column sizes"""
        # Clear main content area
        for widget in self.main_content.winfo_children():
            widget.pack_forget()

        # Create main dashboard frame that fills all space
        self.dashboard_frame = tk.Frame(self.main_content, bg="#E8F0FF")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=0)

        # Create container frame for the three panels
        panels_container = tk.Frame(self.dashboard_frame, bg="#E8F0FF")
        panels_container.pack(fill=tk.BOTH, expand=True)

        # Calculate available height
        header_height = 60  # Approximate height of header
        separator_height = 36  # Height of separator
        available_height = self.root.winfo_height() - header_height - separator_height - 40  # 40px buffer

        # Set equal height for all panels (using 90% of available height)
        panel_height = int(available_height * 0.9)

        # Left panel - Recent Transactions and Financial Game (wider)
        left_panel = tk.Frame(panels_container, bg="#E8F0FF", width=400, height=panel_height)  # Increased width
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8.7))
        left_panel.pack_propagate(False)

        # Middle panel - Expense Breakdown (slimmer)
        middle_panel = tk.Frame(panels_container, bg="#E8F0FF", width=300, height=panel_height)  # Reduced width
        middle_panel.grid(row=0, column=1, sticky="nsew", padx=5)
        middle_panel.pack_propagate(False)

        # Right panel - Recent Goal and Financial Tips (smaller but visible)
        right_panel = tk.Frame(panels_container, bg="#E8F0FF", width=250, height=panel_height)  # Reduced width
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        right_panel.pack_propagate(False)

        # Configure grid weights - left gets more space, middle gets less, right gets fixed
        panels_container.grid_columnconfigure(0, weight=3)  # Left panel (chat/trivia) - more weight
        panels_container.grid_columnconfigure(1, weight=2)  # Middle panel (pie chart) - less weight
        panels_container.grid_columnconfigure(2, weight=1)  # Right panel (goals) - least weight
        panels_container.grid_rowconfigure(0, weight=1)     # Full height

        # Create the dashboard cards
        recent_transactions_card = self.create_dashboard_card(
            left_panel, "Recent Transactions", height=panel_height//2
        )
        
        # Add financial game/chatbot card below transactions
        financial_chat_card = self.create_dashboard_card(
            left_panel, "Financial Assistant & Trivia", height=panel_height//2
        )
        self._setup_chatbot_interface(financial_chat_card)  # This will now be larger

        expense_breakdown_card = self.create_dashboard_card(
            middle_panel, "Expense Breakdown", height=panel_height
        )

        # Right panel - smaller goals section
        goal_tracker_card = self.create_dashboard_card(
            right_panel, "Recent Goal", height=panel_height // 3  # Smaller height
        )
        
        # Add tips section below goals
        tips_card = self.create_dashboard_card(
            right_panel, "Quick Tips", height=panel_height // 3 * 2  # Larger height
        )
        self.update_financial_tips(tips_card)

        # Update content in each card
        self.update_recent_transactions(recent_transactions_card)
        self.update_expense_breakdown(expense_breakdown_card)
        self.update_goal_trackers(goal_tracker_card)

    def _setup_chatbot_interface(self, parent):
        """Setup the combined chatbot and trivia interface"""
        chatbot_frame = tk.Frame(parent, bg="white", bd=1, relief=tk.RIDGE)
        chatbot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook for tabs (chat and trivia)
        self.chat_notebook = ttk.Notebook(chatbot_frame)
        self.chat_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Chat tab
        chat_tab = tk.Frame(self.chat_notebook, bg="white")
        self.chat_notebook.add(chat_tab, text="Assistant")
        
        # Trivia tab
        trivia_tab = tk.Frame(self.chat_notebook, bg="white")
        self.chat_notebook.add(trivia_tab, text="Trivia Game")
        
        # Setup chat interface
        self._setup_chat_tab(chat_tab)
        
        # Setup trivia game in its own tab
        self.create_financial_game(trivia_tab)

    def _setup_chat_tab(self, parent):
        """Setup the enhanced AI chat interface"""
        # Chat display area
        self.chat_display = tk.Text(
            parent,
            height=12,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Helvetica Neue", 11),
            bg="white",
            fg="#2C3E50",
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for message styling
        self.chat_display.tag_config("assistant", foreground="#3498DB")
        self.chat_display.tag_config("user", foreground="#2C3E50")
        self.chat_display.tag_config("error", foreground="#E74C3C")
        self.chat_display.tag_config("typing", foreground="#7F8C8D")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.chat_display)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.chat_display.yview)
        
        # Input frame
        input_frame = tk.Frame(parent, bg="white")
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.user_input = tk.Entry(
            input_frame,
            font=("Helvetica Neue", 11),
            bd=1,
            relief=tk.SOLID
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", lambda e: self.process_chat_input())
        
        # Send button
        send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.process_chat_input,
            font=("Helvetica Neue", 10, "bold"),
            bg="#3498DB",
            fg="white",
            bd=0
        )
        send_button.pack(side=tk.RIGHT)
        
        # Add quick action buttons
        quick_actions_frame = tk.Frame(parent, bg="white")
        quick_actions_frame.pack(fill=tk.X, pady=(5, 0))
        
        common_questions = [
            ("Budget Help", "How do I create a budget?"),
            ("Savings Tips", "Best ways to save money?"),
            ("Invest Advice", "How should I start investing?")
        ]
        
        for text, question in common_questions:
            btn = tk.Button(
                quick_actions_frame,
                text=text,
                command=lambda q=question: self.ask_predefined_question(q),
                font=("Helvetica Neue", 9),
                bg="#ECF0F1",
                fg="#2C3E50",
                relief=tk.FLAT
            )
            btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Initial greeting
        self.add_chat_message(
            "assistant",
            "Hello! I'm Finnova, your AI financial assistant. 💰\n"
            "Ask me about budgeting, saving, investing, or use the quick buttons above!"
        )

    def ask_predefined_question(self, question):
        """Handle quick action button questions"""
        self.user_input.delete(0, tk.END)
        self.user_input.insert(0, question)
        self.process_chat_input()

    def process_chat_input(self):
        """Process user input with enhanced error handling"""
        user_text = self.user_input.get().strip()
        self.user_input.delete(0, tk.END)
        
        if not user_text:
            return
        
        self.add_chat_message("user", user_text)
        self.show_typing_indicator()
        
        # Process in background to prevent UI freeze
        self.root.after(100, lambda: self.get_ai_response(user_text))

    def show_typing_indicator(self):
        """Show typing indicator animation"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\nFinnova is typing...", "typing")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.chat_display.update()

    def remove_typing_indicator(self):
        """Remove typing indicator"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("end-2l linestart", "end-1c")
        self.chat_display.config(state=tk.DISABLED)

    def get_ai_response(self, user_input):
        """Get and display AI response"""
        try:
            # Get response from AI chatbot
            response = self.ai_chatbot.generate_response(user_input)
            self.remove_typing_indicator()
            
            if isinstance(response, dict) and "error" in response:
                self.add_chat_message("error", f"⚠️ {response['error']}")
                
                # Special handling for loading model case
                if "wait" in response.get("error", "").lower():
                    retry_time = response.get("retry_after", 30) * 1000
                    self.root.after(retry_time, lambda: self.process_chat_input(user_input))
            else:
                self.add_chat_message("assistant", response)
                
        except Exception as e:
            self.remove_typing_indicator()
            self.add_chat_message("error", f"⚠️ Error: {str(e)}")

    def create_financial_game(self, container):
        """Create a simple financial literacy game"""
        # Initialize game score if not already set
        if not hasattr(self, 'game_score'):
            self.game_score = 0
        
        game_frame = tk.Frame(container, bg="white")
        game_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Game title and score
        header_frame = tk.Frame(game_frame, bg="white")
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(header_frame, 
                text="Test Your Financial Knowledge",
                font=("Helvetica Neue", 10, "bold"),
                bg="white").pack(side=tk.LEFT)
        
        self.score_label = tk.Label(header_frame, 
                                  text=f"Score: {self.game_score}",
                                  font=("Helvetica Neue", 11),
                                  bg="white")
        self.score_label.pack(side=tk.RIGHT)
        
        # Question area
        self.question_label = tk.Label(game_frame,
                                     text="",
                                     font=("Helvetica Neue", 10),
                                     bg="white",
                                     wraplength=350,  # Increased for wider space
                                     justify=tk.LEFT)
        self.question_label.pack(fill=tk.X, pady=5)
        
        # Answer buttons
        self.answer_buttons = []
        for i in range(4):
            btn = tk.Button(game_frame,
                          text="",
                          font=("Helvetica Neue", 10),
                          bg="#3498DB",
                          fg="white",
                          command=lambda idx=i: self.check_answer(idx),
                          wraplength=350,  # Increased for wider space
                          justify=tk.LEFT)
            btn.pack(fill=tk.X, pady=2)
            self.answer_buttons.append(btn)
            button_frame = tk.Frame(game_frame, bg="white")
            button_frame.pack(fill=tk.X, pady=(5, 0))

        # Next question button
        self.next_btn = tk.Button(game_frame,
                                text="Next Question",
                                font=("Helvetica Neue", 11, "bold"),
                                bg="#2ECC71",
                                fg="white",
                                command=self.next_question,
                                state=tk.DISABLED,
                                padx=10, 
                                pady=5,
                                relief=tk.RAISED, 
                                bd=2) 
        self.next_btn.pack(fill=tk.X, expand=True)
        self.next_btn.pack_propagate(False)
        tk.Frame(game_frame, height=10, bg="white").pack(fill=tk.X)
        # Game questions and answers
        self.questions = [
            {
                "question": "What is the recommended percentage of income to save?",
                "answers": ["5-10%", "15-20%", "25-30%", "As much as possible"],
                "correct": 1
            },
            {
                "question": "Which debt should you pay off first?",
                "answers": ["The smallest debt", "The debt with highest interest", 
                          "The newest debt", "It doesn't matter"],
                "correct": 1
            },
            {
                "question": "What is an emergency fund for?",
                "answers": ["Vacations", "Unexpected expenses like medical bills", 
                          "Investing in stocks", "Buying luxury items"],
                "correct": 1
            },
            {
                "question": "What's the '50/30/20' budgeting rule?",
                "answers": ["50% needs, 30% wants, 20% savings", 
                          "50% spending, 30% investing, 20% saving",
                          "50% bills, 30% food, 20% entertainment",
                          "50% housing, 30% transportation, 20% other"],
                "correct": 0
            },
            {
                "question": "What's the benefit of starting to invest early?",
                "answers": ["More time to recover from losses", 
                          "Compound interest works longer",
                          "Both of the above",
                          "Neither, timing doesn't matter"],
                "correct": 2
            },
            {
                "question": "What's the best way to build credit?",
                "answers": ["Use credit cards heavily", 
                          "Pay bills on time and keep balances low",
                          "Take out as many loans as possible",
                          "Avoid all credit cards"],
                "correct": 1
            },
            {
                "question": "What's a good strategy for large purchases?",
                "answers": ["Buy immediately with credit", 
                          "Save up and pay cash when possible",
                          "Take out payday loans",
                          "Borrow from friends"],
                "correct": 1
            },
            {
                "question": "What's the most important factor in investment success?",
                "answers": ["Timing the market perfectly", 
                          "Consistent investing over time",
                          "Following hot stock tips",
                          "Investing only in cryptocurrency"],
                "correct": 1
            }
        ]
        
        # Store total questions count
        self.total_questions = len(self.questions)
        self.current_question = None
        self.next_question()

    def check_answer(self, answer_idx):
        """Check if the selected answer is correct"""
        if self.current_question is None:
            return
            
        correct_idx = self.current_question["correct"]
        
        for i, btn in enumerate(self.answer_buttons):
            if i == correct_idx:
                btn.config(bg="#2ECC71")  # Green for correct
            elif i == answer_idx and i != correct_idx:
                btn.config(bg="#E74C3C")  # Red for wrong
            else:
                btn.config(state=tk.DISABLED, bg="#BDC3C7")
        
        if answer_idx == correct_idx:
            self.game_score += 10
            self.score_label.config(text=f"Score: {self.game_score}")
        
        self.next_btn.config(state=tk.NORMAL)

    def next_question(self):
        """Load the next question in the game"""
        if not self.questions:
            # Game complete - show final score
            total_possible = self.total_questions * 10
            self.question_label.config(
                text=f"Game complete!\n\nFinal Score: {self.game_score}/{total_possible}",
                font=("Helvetica Neue", 12, "bold")
            )
            for btn in self.answer_buttons:
                btn.pack_forget()
            self.next_btn.config(text="Play Again", command=self.reset_game)
            return
            
        self.current_question = random.choice(self.questions)
        self.questions.remove(self.current_question)
        
        self.question_label.config(text=self.current_question["question"])
        
        answers = self.current_question["answers"]
        for i, btn in enumerate(self.answer_buttons):
            btn.config(text=answers[i], state=tk.NORMAL, bg="#3498DB")
        
        self.next_btn.config(state=tk.DISABLED)

    def reset_game(self):
        """Reset the game to play again"""
        self.game_score = 0
        self.score_label.config(text=f"Score: {self.game_score}")
        
        # Rebuild questions list
        self.questions = [
            {
                "question": "What is the recommended percentage of income to save?",
                "answers": ["5-10%", "15-20%", "25-30%", "As much as possible"],
                "correct": 1
            },
            {
                "question": "Which debt should you pay off first?",
                "answers": ["The smallest debt", "The debt with highest interest", 
                          "The newest debt", "It doesn't matter"],
                "correct": 1
            },
            {
                "question": "What is an emergency fund for?",
                "answers": ["Vacations", "Unexpected expenses like medical bills", 
                          "Investing in stocks", "Buying luxury items"],
                "correct": 1
            },
            {
                "question": "What's the '50/30/20' budgeting rule?",
                "answers": ["50% needs, 30% wants, 20% savings", 
                          "50% spending, 30% investing, 20% saving",
                          "50% bills, 30% food, 20% entertainment",
                          "50% housing, 30% transportation, 20% other"],
                "correct": 0
            },
            {
                "question": "What's the benefit of starting to invest early?",
                "answers": ["More time to recover from losses", 
                          "Compound interest works longer",
                          "Both of the above",
                          "Neither, timing doesn't matter"],
                "correct": 2
            },
            {
                "question": "What's the best way to build credit?",
                "answers": ["Use credit cards heavily", 
                          "Pay bills on time and keep balances low",
                          "Take out as many loans as possible",
                          "Avoid all credit cards"],
                "correct": 1
            },
            {
                "question": "What's a good strategy for large purchases?",
                "answers": ["Buy immediately with credit", 
                          "Save up and pay cash when possible",
                          "Take out payday loans",
                          "Borrow from friends"],
                "correct": 1
            },
            {
                "question": "What's the most important factor in investment success?",
                "answers": ["Timing the market perfectly", 
                          "Consistent investing over time",
                          "Following hot stock tips",
                          "Investing only in cryptocurrency"],
                "correct": 1
            }
        ]
        
        self.total_questions = len(self.questions)
        
        for btn in self.answer_buttons:
            btn.pack(fill=tk.X, pady=2)
            btn.config(state=tk.NORMAL, bg="#3498DB")
        
        self.next_btn.config(text="Next Question", command=self.next_question)
        self.current_question = None
        self.next_question()

    def add_chat_message(self, sender, message):
        """Add a message to the chat display with typing effect"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Configure tags for different senders
        self.chat_display.tag_config("assistant", foreground="#3498DB")
        self.chat_display.tag_config("user", foreground="#2C3E50")
        
        # Insert the message with appropriate tag
        if sender == "assistant":
            prefix = "Finnova: "
            tag = "assistant"
        else:
            prefix = "You: "
            tag = "user"
        
        # Store message in history (last 10 messages for context)
        self.chat_history.append((sender, message))
        if len(self.chat_history) > 10:
            self.chat_history.pop(0)
        
        # Insert message with typing effect
        full_message = prefix + message + "\n\n"
        self.chat_display.insert(tk.END, prefix, tag)
        
        # Simulate typing effect
        for i in range(len(message)):
            self.chat_display.insert(tk.END, message[i], tag)
            self.chat_display.see(tk.END)
            self.chat_display.update()
            time.sleep(0.03)  # Typing speed
        
        self.chat_display.insert(tk.END, "\n\n", tag)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def process_chat_input(self):
        """Process user input in the chatbot with more AI-like responses"""
        user_text = self.user_input.get().strip().lower()
        self.user_input.delete(0, tk.END)
        
        if not user_text:
            return
        
        self.add_chat_message("user", user_text)
        
        # Define responses with more natural language
        tips = [
            "A good rule is to save at least 20% of your income each month. This helps build wealth over time while still allowing for expenses.",
            "The 50/30/20 budgeting rule is excellent: allocate 50% to needs (rent, food, bills), 30% to wants (entertainment, dining out), and 20% to savings and debt repayment.",
            "Building an emergency fund should be a top priority - aim for 3-6 months of living expenses in a separate savings account.",
            "High-interest debt like credit cards can quickly spiral out of control. Focus on paying these off as quickly as possible before other financial goals.",
            "The power of compound interest means starting to invest early is crucial. Even small amounts invested regularly can grow significantly over decades.",
            "Review your insurance coverage annually - your needs change over time and you want to ensure you're neither underinsured nor overpaying.",
            "Automating your savings is one of the most effective strategies. Set up automatic transfers to savings/investments right after payday.",
            "Tracking your spending for just 1-2 months can reveal surprising patterns and opportunities to cut back on unnecessary expenses.",
            "When you get a raise, try to avoid lifestyle inflation. Instead, allocate at least half of the increase to savings or debt repayment.",
            "Diversification is key to investing. Don't put all your eggs in one basket - spread your investments across different asset classes."
        ]
        
        trivia = [
            "Did you know? Albert Einstein reportedly called compound interest the '8th wonder of the world' because of its powerful wealth-building effects over time.",
            "Fun fact: The first credit card was introduced in 1950 by Diners Club and was initially made of cardboard!",
            "Historical tidbit: The word 'salary' comes from 'salarium', the money Roman soldiers were paid to buy salt - which was extremely valuable at the time.",
            "Wall Street history: The New York Stock Exchange was founded in 1792 when 24 stockbrokers signed the Buttonwood Agreement under a buttonwood tree.",
            "Tech fact: The first ATM was installed in London in 1967 by Barclays Bank. The idea came to the inventor while he was in the bath!",
            "Surprising stat: About 40% of Americans couldn't cover a $400 emergency expense without borrowing or selling something.",
            "Debt reality: The average American has about $90,000 in total debt when including mortgages, student loans, and credit cards.",
            "Currency history: The first paper money appeared in China around 700 AD during the Tang Dynasty, replacing heavy metal coins.",
            "Investing term: The 'blue chip' label comes from poker, where blue chips traditionally have the highest value at the table.",
            "Mutual fund history: The first modern mutual fund was created in 1924 in Boston, paving the way for today's investment funds."
        ]
        
        # More comprehensive responses based on context
        if any(word in user_text for word in ["hello", "hi", "hey"]):
            responses = [
                f"Hello {self.username}! How can I assist with your financial questions today?",
                "Hi there! What financial topic would you like to discuss?",
                "Greetings! I'm here to help with budgeting, saving, and all things finance. What's on your mind?"
            ]
            response = random.choice(responses)
        elif any(word in user_text for word in ["tip", "advice", "suggest"]):
            response = "💡 " + random.choice(tips)
        elif any(word in user_text for word in ["trivia", "fact", "interesting", "history"]):
            response = "🧠 " + random.choice(trivia)
        elif any(word in user_text for word in ["thank", "appreciate"]):
            responses = [
                "You're very welcome! Don't hesitate to ask if you have more questions.",
                "Happy to help! Financial knowledge is power - keep learning!",
                "My pleasure! Remember, smart financial decisions today lead to a more secure tomorrow."
            ]
            response = random.choice(responses)
        elif any(word in user_text for word in ["budget", "spending"]):
            responses = [
                "Budgeting is the foundation of financial health. The 50/30/20 rule is a great starting point - would you like me to explain it?",
                "Tracking expenses is key to budgeting. Many people are surprised where their money actually goes each month!",
                "A budget isn't restrictive - it's about making your money work for your priorities. What are your financial goals?"
            ]
            response = random.choice(responses)
        elif any(word in user_text for word in ["save", "saving"]):
            responses = [
                "Saving consistently, even small amounts, can make a big difference over time thanks to compound interest.",
                "Automating your savings is one of the most effective strategies - pay yourself first!",
                "Having specific savings goals (like an emergency fund or down payment) can help motivate consistent saving."
            ]
            response = random.choice(responses)
        elif any(word in user_text for word in ["invest", "stock", "market"]):
            responses = [
                "Investing early gives your money more time to grow. Even small, regular investments can become significant over decades.",
                "Diversification is crucial in investing - don't put all your eggs in one basket!",
                "Index funds are a great low-cost way for beginners to start investing in the stock market."
            ]
            response = random.choice(responses)
        elif any(word in user_text for word in ["debt", "loan", "credit"]):
            responses = [
                "High-interest debt should be a priority to pay off. The avalanche method (paying highest rates first) saves the most money.",
                "Credit cards can be useful tools if paid off monthly, but carrying a balance leads to expensive interest charges.",
                "Consolidating multiple debts into one lower-interest loan can sometimes help simplify repayment."
            ]
            response = random.choice(responses)
        else:
            responses = [
                "I'm happy to help with financial questions! Try asking about budgeting, saving, investing, or request a financial tip.",
                "I specialize in personal finance topics. You could ask me for advice on saving money or about financial history facts!",
                "For personalized help, try asking about budgeting strategies, saving tips, or investment basics."
            ]
            response = random.choice(responses)
        
        # Simulate thinking delay
        self.root.after(500, lambda: self.add_chat_message("assistant", response))

    def create_dashboard_card(self, parent, title, width=None, height=None):
        """Create dashboard card that fills its parent completely"""
        card = tk.Frame(parent, bg="white", bd=1, relief=tk.RAISED)
        card.pack(fill=tk.BOTH, expand=True)
        
        if width:
            card.config(width=width)
        if height:
            card.config(height=height)
        card.pack_propagate(False)

        # Card header (fixed height)
        header = tk.Frame(card, bg="#3498DB", height=30)
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text=title,
                font=("Helvetica Neue", 12, "bold"),
                bg="#3498DB",
                fg="white",
                anchor="w",
                padx=10,
                pady=4).pack(fill=tk.X)

        # Card content area (fills remaining space)
        content = tk.Frame(card, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        return content

    def update_recent_transactions(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        # Add a scrollable frame for transactions with more compact styling
        transaction_canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=transaction_canvas.yview)
        scrollable_frame = tk.Frame(transaction_canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: transaction_canvas.configure(
                scrollregion=transaction_canvas.bbox("all")
            )
        )
        
        transaction_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        transaction_canvas.configure(yscrollcommand=scrollbar.set)
        
        transaction_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        transactions = self.report_tab.get_recent_transactions(5) if hasattr(self.report_tab, 'get_recent_transactions') else []
        
        if transactions:
            for i, transaction in enumerate(transactions):
                bg_color = "#F9F9F9" if i % 2 == 0 else "white"
                transaction_item = tk.Frame(scrollable_frame, bg=bg_color, padx=5, pady=5)  # Reduced padding
                transaction_item.pack(fill="x")
                
                # Compact date format (day/month)
                date_parts = transaction.get('date', '').split('-')
                display_date = f"{date_parts[2]}/{date_parts[1]}" if len(date_parts) == 3 else transaction.get('date', '')
                
                date_label = tk.Label(
                    transaction_item,
                    text=display_date,
                    font=("Helvetica Neue", 15),  # Smaller font
                    bg=bg_color,
                    fg="#2C3E50",
                    width=6
                )
                date_label.pack(side="left", padx=(0, 5))
                
                category_colors = {
                    "Food": "#27AE60",
                    "Transport": "#3498DB",
                    "Entertainment": "#F39C12"
                }
                category_color = category_colors.get(transaction.get('category', ''), "#7F8C8D")
                
                category_label = tk.Label(
                    transaction_item,
                    text=transaction.get('category', '')[:12],  # Truncate long category names
                    font=("Helvetica Neue", 15),  # Smaller font
                    bg=bg_color,
                    fg=category_color,
                    width=12
                )
                category_label.pack(side="left", padx=(0, 5))
                
                amount_label = tk.Label(
                    transaction_item,
                    text=f"₹{float(transaction.get('amount', 0)):.2f}",  # Format with 2 decimal places
                    font=("Helvetica Neue", 11, "bold"),  # Smaller font
                    bg=bg_color,
                    fg="#E74C3C" if float(transaction.get('amount', 0)) > 0 else "#27AE60",
                    width=8
                )
                amount_label.pack(side="right")
        else:
            no_transactions_label = tk.Label(
                scrollable_frame, 
                text="No recent transactions.",
                font=("Helvetica Neue", 12),  # Smaller font
                bg="white",
                fg="#7F8C8D",
                pady=15  # Reduced padding
            )
            no_transactions_label.pack(fill="x")

    def update_expense_breakdown(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        categories, expenses = self.report_tab.get_expense_breakdown() if hasattr(self.report_tab, 'get_expense_breakdown') else ([], [])
        
        if not expenses or sum(expenses) == 0:
            label = tk.Label(
                container, 
                text="No expense data available",
                font=("Helvetica Neue", 14),
                fg="#7F8C8D",
                bg="white"
            )
            label.place(relx=0.5, rely=0.5, anchor="center")
            return
            
        # Create figure that fills most of the container
        fig = Figure(figsize=(5, 4), dpi=100)  # Smaller figure size
        ax = fig.add_subplot(111)
            
        colors = ['#3498DB', '#E74C3C', '#27AE60', '#F39C12', '#9B59B6', '#1ABC9C']
        
        wedges, texts, autotexts = ax.pie(
            expenses, 
            labels=None,
            autopct=lambda p: f'{p:.1f}%' if p > 5 else '',
            startangle=90, 
            shadow=True,
            explode=[0.05] * len(categories),
            colors=colors[:len(categories)],
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
        )
        
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
            autotext.set_color('white')
        
        ax.set_title("Expense Breakdown", fontsize=15, pad=15, fontweight='bold')
        ax.axis("equal")
        
        ax.legend(
            wedges, 
            categories,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0.5),
            fontsize=9
        )
        
        fig.tight_layout()
        
        # Place chart to fill most of container
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_goal_trackers(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        goals = get_goals() if 'get_goals' in globals() else []
        if goals:
            latest_goal = goals[-1]
            self.display_latest_goal(container, latest_goal)
        else:
            empty_label = tk.Label(
                container,
                text="No goals set.",
                font=("Helvetica Neue", 14),
                fg="#7F8C8D",
                bg="white",
                pady=30
            )
            empty_label.pack(fill="both", expand=True)

    def display_latest_goal(self, container, goal):
        goal_details = tk.Frame(container, bg="white")
        goal_details.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Calculate progress percentage with error handling
        try:
            target_amount = float(goal.get('target_amount', 1))
            saved_amount = float(goal.get('saved_amount', 0))
            progress_pct = (saved_amount / target_amount) * 100 if target_amount > 0 else 0
        except (ValueError, TypeError):
            progress_pct = 0
            
        progress_data = calculate_goal_progress(goal) if 'calculate_goal_progress' in globals() else {}
        required_monthly = progress_data.get("required_monthly_savings", 0)

        # Goal name with ellipsis for long names
        name_label = tk.Label(
            goal_details,
            text=goal.get('name', '')[:20] + ('...' if len(goal.get('name', '')) > 20 else ''),  # Shorter max length
            font=("Helvetica Neue", 13, "bold"),  # Smaller font
            bg="white",
            fg="#2C3E50",
            anchor="w"
        )
        name_label.pack(fill=tk.X, pady=(0, 8))  # Reduced padding

        details_frame = tk.Frame(goal_details, bg="white")
        details_frame.pack(fill=tk.X, pady=3)  # Reduced padding

        # Use grid with fixed column widths
        details_frame.columnconfigure(0, weight=1, minsize=100)  # Smaller min width
        details_frame.columnconfigure(1, weight=1, minsize=100)  # Smaller min width

        # Target amount
        tk.Label(details_frame,
                text="Target:",
                font=("Helvetica Neue", 11),  # Smaller font
                bg="white",
                fg="#7F8C8D",
                anchor="w").grid(row=0, column=0, sticky="w", pady=1)  # Reduced padding

        tk.Label(details_frame,
                text=f"Rs{goal.get('target_amount', 0)}",
                font=("Helvetica Neue", 11, "bold"),  # Smaller font
                bg="white",
                fg="#2C3E50").grid(row=0, column=1, sticky="w", pady=1)  # Reduced padding

        # Saved amount
        tk.Label(details_frame,
                text="Saved:",
                font=("Helvetica Neue", 11),  # Smaller font
                bg="white",
                fg="#7F8C8D",
                anchor="w").grid(row=1, column=0, sticky="w", pady=1)  # Reduced padding

        tk.Label(details_frame,
                text=f"Rs{goal.get('saved_amount', 0)}",
                font=("Helvetica Neue", 11, "bold"),  # Smaller font
                bg="white",
                fg="#27AE60").grid(row=1, column=1, sticky="w", pady=1)  # Reduced padding

        # Progress bar
        progress_frame = tk.Frame(goal_details, bg="white", pady=10)  # Reduced padding
        progress_frame.pack(fill=tk.X)

        progress_container = tk.Frame(progress_frame, bg="white")
        progress_container.pack(fill=tk.X)

        progress_bg = tk.Canvas(
            progress_container, 
            height=15,  # Smaller height
            bg="#ECF0F1", 
            highlightthickness=0
        )
        progress_bg.pack(fill=tk.X, pady=3)  # Reduced padding

        # Function to update progress bar width
        def update_progress_bar():
            width = progress_bg.winfo_width()
            fill_width = (min(progress_pct, 100) / 100) * width
            progress_bg.delete("all")
            progress_bg.create_rectangle(0, 0, fill_width, 15, fill="#3498DB", outline="")
            progress_bg.after(100, update_progress_bar)
        
        update_progress_bar()

        # Percentage and monthly needed
        bottom_frame = tk.Frame(goal_details, bg="white")
        bottom_frame.pack(fill=tk.X)
        
        tk.Label(bottom_frame,
                text=f"{progress_pct:.1f}% Complete",
                font=("Helvetica Neue", 11, "bold"),  # Smaller font
                bg="white",
                fg="#2C3E50").pack(side=tk.LEFT)

        tk.Label(bottom_frame,
                text=f"Monthly: Rs{required_monthly:.2f}",
                font=("Helvetica Neue", 8),  # Smaller font
                bg="white",
                fg="#7F8C8D").pack(side=tk.RIGHT)

    def update_financial_tips(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        tips = [
            "Review your monthly subscriptions - cancel unused services",
            "Set up automatic transfers to savings on payday",
            "Use the 50/30/20 rule for budgeting (needs/wants/savings)",
            "Track your spending daily to avoid surprises",
            "Cook at home more often to save on dining out"
        ]

        # Add a scrollable frame for tips
        tips_canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=tips_canvas.yview)
        scrollable_frame = tk.Frame(tips_canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: tips_canvas.configure(
                scrollregion=tips_canvas.bbox("all")
            )
        )
        
        tips_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        tips_canvas.configure(yscrollcommand=scrollbar.set)
        
        tips_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, tip in enumerate(tips[:5]):  # Show only 5 tips
            bg_color = "#F9F9F9" if i % 2 == 0 else "white"
            tip_item = tk.Frame(scrollable_frame, bg=bg_color, padx=10, pady=6)  # Reduced padding
            tip_item.pack(fill="x")
            
            # Add bullet point
            tk.Label(tip_item,
                    text="• ",
                    font=("Helvetica Neue", 12),
                    bg=bg_color,
                    fg="#3498DB").pack(side="left")
            
            # Add tip text
            tk.Label(tip_item,
                    text=tip,
                    font=("Helvetica Neue", 10),
                    bg=bg_color,
                    fg="#2C3E50",
                    wraplength=200,  # Adjusted for smaller width
                    justify="left").pack(side="left", fill="x", expand=True)

    def logout(self):
        """Handle logout process"""
        # Reset game score when logging out
        if hasattr(self, 'game_score'):
            self.game_score = 0
        
        # Hide main window and show login window
        self.root.withdraw()
        self.login_window.deiconify()
        self.login_window.clear_fields()
        
        # Reset any other necessary states
        if hasattr(self, 'dashboard_frame'):
            self.show_dashboard()


class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Finnova - Login")
        self.geometry("1200x800")
        self.resizable(False, False)
        
        # State tracking
        self._register_window_open = False
        self.camera_retry_count = 0
        self.max_camera_retries = 5
        self.camera_lock = False
        self.register_window = None
        
        # Initialize authenticators
        self.face_auth = FaceAuthenticator(self)
        self.traditional_auth = TraditionalAuthenticator(self)
        self.parent = parent
        self.video_label = None
        self.is_camera_active = False
        self.login_face_encoding = None
        self.camera_frame = None
        self.container = None
        
        # Configure styles
        self._configure_styles()
        
        self._setup_ui()
        # Start camera with safety delay
        self.after(1000, self._restart_camera_guaranteed)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _configure_styles(self):
        """Configure custom styles for the window"""
        style = ttk.Style()
        style.configure("TFrame", background="#F5F7FA")
        style.configure("TLabel", background="#F5F7FA", foreground="#2C3E50")
        style.configure("TButton", font=("Helvetica", 12), padding=8)
        style.map("TButton",
                 background=[("active", "#2980B9")],
                 foreground=[("active", "white")])
        
    class CombinedRegisterWindow(tk.Toplevel):
        def __init__(self, parent):
            super().__init__(parent)
            self.title("Register New Account")
            self.geometry("1000x700")
            self.resizable(False, False)
            self.parent = parent
            self.face_encoding = None
            self.face_captured = False
            
            # Use separate camera instance for registration
            self.face_auth = FaceAuthenticator(self)
            
            # Make window modal
            self.transient(parent)
            self.grab_set()
            
            # Setup UI first
            self._setup_ui()
            
            # Then initialize camera after UI is ready
            self.after(500, self._initialize_camera)
            
        def _center_window(self):
            """Center the window on screen"""
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f'+{x}+{y}')
            
        def _setup_ui(self):
            """Setup the registration interface"""
            try:
                # Main container with grid layout
                self.container = tk.Frame(self, bg="#F5F7FA")
                self.container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
                
                # Configure grid weights
                self.container.grid_columnconfigure(0, weight=1)
                self.container.grid_columnconfigure(1, weight=1)
                self.container.grid_rowconfigure(0, weight=1)
                
                # Video feed frame (left side)
                self.video_frame = tk.Frame(self.container, bg="#2C3E50", 
                                          width=450, height=450, bd=2, relief=tk.RIDGE)
                self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
                self.video_frame.grid_propagate(False)
                
                self.video_label = tk.Label(self.video_frame, bg="#2C3E50")
                self.video_label.pack(expand=True, fill=tk.BOTH)
                
                # Registration form frame (right side)
                self.form_frame = tk.Frame(self.container, bg="#FFFFFF", 
                                          bd=2, relief=tk.RIDGE, padx=30, pady=30)
                self.form_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
                
                # Add scrollbar for the form frame
                self.canvas = tk.Canvas(self.form_frame, bg="#FFFFFF", highlightthickness=0)
                self.scrollbar = ttk.Scrollbar(self.form_frame, orient="vertical", command=self.canvas.yview)
                self.scrollable_frame = tk.Frame(self.canvas, bg="#FFFFFF")
                
                self.scrollable_frame.bind(
                    "<Configure>",
                    lambda e: self.canvas.configure(
                        scrollregion=self.canvas.bbox("all")
                    )
                )
                
                self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
                self.canvas.configure(yscrollcommand=self.scrollbar.set)
                
                self.canvas.pack(side="left", fill="both", expand=True)
                self.scrollbar.pack(side="right", fill="y")
                
                # Form content
                self._setup_form_content()
                
                # Center window
                self._center_window()
                
            except Exception as e:
                messagebox.showerror("Error", f"UI Setup Failed: {str(e)}", parent=self)
                self.destroy()
        
        def _setup_form_content(self):
            """Setup the registration form elements"""
            # Title
            tk.Label(
                self.scrollable_frame, 
                text="Create New Account", 
                font=("Helvetica", 20, "bold"),
                bg="#FFFFFF"
            ).pack(pady=(0, 20))
            
            # Form fields container
            form_fields = tk.Frame(self.scrollable_frame, bg="#FFFFFF")
            form_fields.pack(fill=tk.X, pady=10)
            
            # Username field
            tk.Label(form_fields, text="Username:", 
                    font=("Helvetica", 12), bg="#FFFFFF").pack(anchor="w", pady=(5,0))
            self.username_entry = tk.Entry(form_fields, font=("Helvetica", 12), bd=1, relief=tk.SOLID)
            self.username_entry.pack(fill=tk.X, pady=5, ipady=5)
            
            # Password field
            tk.Label(form_fields, text="Password (min 8 chars):", 
                    font=("Helvetica", 12), bg="#FFFFFF").pack(anchor="w", pady=(10,0))
            self.password_entry = tk.Entry(form_fields, show="*", font=("Helvetica", 12), bd=1, relief=tk.SOLID)
            self.password_entry.pack(fill=tk.X, pady=5, ipady=5)
            
            # Confirm Password
            tk.Label(form_fields, text="Confirm Password:", 
                    font=("Helvetica", 12), bg="#FFFFFF").pack(anchor="w", pady=(10,0))
            self.confirm_entry = tk.Entry(form_fields, show="*", font=("Helvetica", 12), bd=1, relief=tk.SOLID)
            self.confirm_entry.pack(fill=tk.X, pady=5, ipady=5)
            
            # Face registration section
            self._setup_face_registration_ui(form_fields)
            
            # Set focus to username field
            self.username_entry.focus_set()
            
            # Bind Enter key to registration
            self.bind('<Return>', lambda e: self._complete_registration())
        
        def _setup_face_registration_ui(self, parent_frame):
            """Setup the face registration UI elements"""
            # Section title
            tk.Label(
                parent_frame,
                text="Face Registration",
                font=("Helvetica", 14, "bold"),
                bg="#FFFFFF",
                pady=10
            ).pack(fill=tk.X, pady=(20, 5))
            
            # Register Face button
            self.face_btn = tk.Button(
                parent_frame,
                text="Register Face",
                command=self._capture_face,
                font=("Helvetica", 12),
                bg="#3498DB",
                fg="white",
                padx=15,
                pady=8,
                bd=0,
                activebackground="#2980B9",
                activeforeground="white"
            )
            self.face_btn.pack(pady=10, fill=tk.X)
            
            # Status label for face registration
            self.face_status = tk.Label(
                parent_frame,
                text="Face not registered yet",
                font=("Helvetica", 10),
                bg="#FFFFFF",
                fg="#E74C3C"
            )
            self.face_status.pack(pady=(0, 5))
            
            # Instructions label
            tk.Label(
                parent_frame,
                text="Please look directly at the camera\nand ensure good lighting",
                font=("Helvetica", 9),
                bg="#FFFFFF",
                fg="#7F8C8D"
            ).pack(pady=(0, 20))
            
            # Register button
            self.register_btn = tk.Button(
                parent_frame,
                text="Complete Registration",
                command=self._complete_registration,
                font=("Helvetica", 14, "bold"),
                bg="#2ECC71",
                fg="white",
                padx=20,
                pady=12,
                bd=0,
                activebackground="#27AE60",
                activeforeground="white",
                state=tk.DISABLED  # Disabled until face is registered
            )
            self.register_btn.pack(fill=tk.X, pady=(20, 10))
        
        def _capture_face(self):
            """Capture and register face data"""
            try:
                if not hasattr(self.face_auth, 'cap') or self.face_auth.cap is None:
                    raise Exception("Camera not initialized")
                
                # Temporarily pause the camera feed
                self.face_auth.pause_camera = True
                
                # Get a fresh frame for registration
                ret, frame = self.face_auth.cap.read()
                if not ret:
                    raise Exception("Could not capture frame")
                
                # Process the frame
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Find face locations
                face_locations = face_recognition.face_locations(rgb_frame)
                if not face_locations:
                    raise Exception("No face detected - please look at the camera")
                    
                if len(face_locations) > 1:
                    raise Exception("Multiple faces detected - please register one at a time")
                    
                # Get face encodings with proper parameters
                face_encodings = face_recognition.face_encodings(
                    rgb_frame,
                    known_face_locations=face_locations,
                    num_jitters=1,
                    model="small"
                )
                
                if not face_encodings:
                    raise Exception("Could not extract face features")
                    
                self.face_encoding = face_encodings[0]
                
                # Update UI
                self.face_status.config(
                    text="Face registered successfully!",
                    fg="#27AE60"
                )
                self.register_btn.config(state=tk.NORMAL)
                self.face_btn.config(state=tk.DISABLED)
                self.face_captured = True
                
                messagebox.showinfo("Success", "Face captured successfully!", parent=self)
                
            except Exception as e:
                messagebox.showerror("Error", f"Face capture failed: {str(e)}", parent=self)
            finally:
                # Resume camera feed
                if hasattr(self.face_auth, 'pause_camera'):
                    self.face_auth.pause_camera = False
                
        def _initialize_camera(self):
            """Initialize camera after UI is ready"""
            try:
                if not self.face_auth.start_camera(self.video_label):
                    messagebox.showerror("Error", "Camera initialization failed", parent=self)
                    self.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Camera Error: {str(e)}", parent=self)
                self.destroy()
        
        def _complete_registration(self):
            """Handle the complete registration process"""
            try:
                username = self.username_entry.get().strip()
                password = self.password_entry.get()
                confirm = self.confirm_entry.get()
                
                # Validate inputs
                if not username:
                    raise ValueError("Username cannot be empty")
                if not password or not confirm:
                    raise ValueError("All fields are required")
                if password != confirm:
                    raise ValueError("Passwords do not match")
                if len(password) < 8:
                    raise ValueError("Password must be at least 8 characters")
                if not self.face_captured:
                    raise ValueError("Please register your face first")
                
                # Register traditional credentials
                if not self.parent.traditional_auth.register_user(username, password):
                    raise RuntimeError("Failed to create account")
                
                # Register face data - convert to list for JSON serialization
                face_encoding_list = self.face_encoding.tolist()
                
                # Update database with face encoding
                user_data = next((u for u in db_instance.data['users'] if u['username'] == username), None)
                if user_data:
                    user_data['face_encoding'] = face_encoding_list
                    if not db_instance.save_data():
                        raise RuntimeError("Failed to save face encoding to database")
                
                # Also save to face recognition system
                self.parent.face_auth.known_face_encodings.append(self.face_encoding)
                self.parent.face_auth.known_face_names.append(username)
                
                if not self.parent.face_auth.save_known_faces():
                    raise RuntimeError("Account created but face data not saved")
                
                messagebox.showinfo(
                    "Success", 
                    "Account created with face recognition",
                    parent=self
                )
                
                self._on_close()
                
            except Exception as e:
                messagebox.showerror("Registration Error", str(e), parent=self)
        
        def _on_close(self):
            """Clean up resources"""
            try:
                if hasattr(self, 'face_auth'):
                    if hasattr(self.face_auth, 'stop_camera'):
                        self.face_auth.stop_camera()
                    
                    if hasattr(self.face_auth, 'cap') and self.face_auth.cap is not None:
                        self.face_auth.cap.release()
                        self.face_auth.cap = None
                        
                cv2.destroyAllWindows()
                
                # Force garbage collection
                gc.collect()
                
                # Signal to parent window that we're closing
                if hasattr(self.parent, 'register_window'):
                    self.parent.register_window = None
                
                # Schedule parent's camera restart
                if hasattr(self.parent, 'schedule_camera_restart'):
                    self.parent.after(1000, self.parent.schedule_camera_restart)
            finally:
                self.grab_release()  # Release modal state
                self.destroy()
    
    def _setup_ui(self):
        """Create login interface with proper frame structure"""
        # Main container
        self.container = tk.Frame(self, bg="#F5F7FA")
        self.container.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Content frame with shadow effect
        content_frame = tk.Frame(self.container, bg="#FFFFFF", bd=1, relief=tk.RIDGE)
        content_frame.pack(expand=True, fill=tk.BOTH)
        
        # Left side - Camera feed
        self.camera_frame = tk.Frame(content_frame, bg="#2C3E50", width=600)
        self.camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(self.camera_frame, bg="#2C3E50", 
                                  text="Initializing camera...", fg="white",
                                  font=("Helvetica", 16))
        self.video_label.pack(expand=True, padx=20, pady=20)
        
        # Right side - Login controls
        login_frame = tk.Frame(content_frame, bg="#FFFFFF", padx=40, pady=40)
        login_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            login_frame, 
            text="Welcome to Finnova", 
            font=("Helvetica", 24, "bold"),
            bg="#FFFFFF"
        )
        title.pack(pady=(0, 30))
        
        # Form container
        form_container = tk.Frame(login_frame, bg="#FFFFFF")
        form_container.pack(fill=tk.BOTH, expand=True)
        
        # Username field
        tk.Label(
            form_container,
            text="Username:",
            font=("Helvetica", 12),
            bg="#FFFFFF",
            anchor="w"
        ).pack(fill=tk.X, pady=(5, 0))
        
        self.entry_user = tk.Entry(
            form_container,
            font=("Helvetica", 12),
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightcolor="#3498DB",
            highlightbackground="#BDC3C7"
        )
        self.entry_user.pack(fill=tk.X, pady=5, ipady=5)
        
        # Password field
        tk.Label(
            form_container,
            text="Password:",
            font=("Helvetica", 12),
            bg="#FFFFFF",
            anchor="w"
        ).pack(fill=tk.X, pady=(10, 0))
        
        self.entry_pass = tk.Entry(
            form_container,
            show="*",
            font=("Helvetica", 12),
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightcolor="#3498DB",
            highlightbackground="#BDC3C7"
        )
        self.entry_pass.pack(fill=tk.X, pady=5, ipady=5)
        
        # Face capture button for login
        self.capture_face_btn = tk.Button(
            form_container,
            text="Capture Face",
            command=self._capture_face_for_login,
            font=("Helvetica", 12),
            bg="#3498DB",
            fg="white",
            pady=10,
            bd=0,
            activebackground="#2980B9",
            activeforeground="white"
        )
        self.capture_face_btn.pack(pady=15, fill=tk.X)
        
        # Status label for face capture
        self.face_capture_status = tk.Label(
            form_container,
            text="Face not captured yet",
            font=("Helvetica", 10),
            bg="#FFFFFF",
            fg="#E74C3C"
        )
        self.face_capture_status.pack(pady=(0, 10))
        
        # Login button
        btn_login = tk.Button(
            form_container,
            text="Login",
            command=self._combined_login,
            font=("Helvetica", 14, "bold"),
            bg="#2ECC71",
            fg="white",
            bd=0,
            padx=20,
            pady=12,
            activebackground="#27AE60",
            activeforeground="white"
        )
        btn_login.pack(fill=tk.X, pady=20)
        
        # Bottom options frame
        options_frame = tk.Frame(form_container, bg="#FFFFFF")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Register button
        btn_combined_register = tk.Button(
            options_frame,
            text="Register New Account",
            command=self._show_combined_register,
            font=("Helvetica", 10),
            fg="#3498DB",
            bg="#FFFFFF",
            bd=0,
            activeforeground="#2980B9"
        )
        btn_combined_register.pack(side=tk.LEFT, padx=5)
        
        # Forgot password
        btn_forgot = tk.Button(
            options_frame,
            text="Forgot Password?",
            command=self._show_forgot_password,
            font=("Helvetica", 10),
            fg="#E74C3C",
            bg="#FFFFFF",
            bd=0,
            activeforeground="#C0392B"
        )
        btn_forgot.pack(side=tk.RIGHT, padx=5)
        
        # Add retry button (initially hidden)
        self.retry_btn = tk.Button(
            self.camera_frame,
            text="Retry Camera Connection",
            command=self._restart_camera_guaranteed,
            bg="#E74C3C",
            fg="white",
            font=("Helvetica", 12),
            bd=0,
            activebackground="#C0392B",
            activeforeground="white"
        )
    
    
    def os_level_camera_cleanup(self):
        """Windows-specific camera cleanup"""
        try:
            if os.name == 'nt':
                # Check if process exists before trying to kill it
                import subprocess
                result = subprocess.run(['tasklist', '/fi', 'imagename eq WindowsCamera.exe'], 
                                     capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if 'WindowsCamera.exe' in result.stdout:
                    subprocess.run(['taskkill', '/f', '/im', 'WindowsCamera.exe'], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(0.5)
        except Exception as e:
            print(f"OS cleanup error: {e}")

    def _nuclear_camera_cleanup(self):
        """Completely nuke all camera resources"""
        try:
            # Release camera hardware
            if hasattr(self, 'face_auth'):
                if hasattr(self.face_auth, 'stop_camera'):
                    self.face_auth.stop_camera()
                
                if hasattr(self.face_auth, 'cap') and self.face_auth.cap is not None:
                    self.face_auth.cap.release()
                    self.face_auth.cap = None
            
            # Destroy OpenCV windows
            for i in range(5):  # Try multiple times to ensure all windows are closed
                cv2.destroyAllWindows()
                cv2.waitKey(1)
            
            # Force garbage collection
            gc.collect()
            
            # OS-level cleanup with subprocess instead of os.system
            self.os_level_camera_cleanup()
            
            # Small delay to ensure hardware release
            time.sleep(1.0)
            
        except Exception as e:
            print(f"Nuclear cleanup error: {e}")
            
    def schedule_camera_restart(self):
        """Schedule a camera restart with proper preparations"""
        if not self.winfo_exists():
            return
            
        self._register_window_open = False
        self._nuclear_camera_cleanup()
        
        if hasattr(self, 'video_label') and self.video_label.winfo_exists():
            self.video_label.config(text="Preparing camera...", fg="white")
        
        # Use a longer delay to ensure hardware is fully released
        self.after(2000, self._restart_camera_guaranteed)



    def _restart_camera_guaranteed(self):
        """Restart camera with 100% reliability"""
        if self._register_window_open or self.camera_lock:
            return False
            
        self.camera_lock = True
        
        if hasattr(self, 'video_label') and self.video_label.winfo_exists():
            self.video_label.config(text="Starting camera...", fg="white")
        
        # Hide retry button during restart attempt
        if hasattr(self, 'retry_btn') and self.retry_btn.winfo_exists():
            self.retry_btn.pack_forget()
        
        try:
            # More thorough cleanup before starting
            self._nuclear_camera_cleanup()
            
            if not self.winfo_exists(): 
                self.camera_lock = False
                return False
            
            # Create a fresh FaceAuthenticator instance
            self.face_auth = FaceAuthenticator(self)
            
            # Multiple camera start attempts with increasing delays
            for attempt in range(self.max_camera_retries):
                try:
                    if self.face_auth.start_camera(self.video_label):
                        self.is_camera_active = True
                        self.camera_retry_count = 0
                        self.camera_lock = False
                        return True
                    
                    # Clean up after failed attempt
                    if hasattr(self.face_auth, 'cap') and self.face_auth.cap is not None:
                        self.face_auth.cap.release()
                        self.face_auth.cap = None
                        
                    # Recreate FaceAuthenticator
                    self.face_auth = FaceAuthenticator(self)
                    
                    # Increasing delay between attempts
                    time.sleep(0.5 * (attempt + 1))
                except Exception as e:
                    print(f"Camera restart attempt {attempt+1} failed: {str(e)}")
                    time.sleep(1)
                    
                    # Recreate camera resources
                    self._nuclear_camera_cleanup()
                    self.face_auth = FaceAuthenticator(self)
            
            # If we get here, all attempts failed
            if hasattr(self, 'video_label') and self.video_label.winfo_exists():
                self.video_label.config(text="Camera failed to start", fg="red")
                
            if hasattr(self, 'retry_btn') and self.retry_btn.winfo_exists():
                self.retry_btn.pack(pady=20)
                
            return False
        except Exception as e:
            print(f"Camera restart error: {str(e)}")
            return False
        finally:
            # Always release the lock
            self.camera_lock = False

    def _show_combined_register(self):
        """Show registration window with guaranteed camera recovery"""
        if self._register_window_open or self.register_window is not None:
            return
            
        self._register_window_open = True
        
        # Completely stop camera
        self._nuclear_camera_cleanup()
        self.is_camera_active = False
        
        if hasattr(self, 'video_label') and self.video_label.winfo_exists():
            self.video_label.config(text="Camera in use by register window...", fg="white")
        
        # Open registration window
        self.register_window = self.CombinedRegisterWindow(self)
        
        # Define what happens when it closes
        def on_register_close():
            try:
                # Force immediate cleanup in registration window
                if self.register_window:
                    if hasattr(self.register_window, 'face_auth'):
                        if hasattr(self.register_window.face_auth, 'stop_camera'):
                            self.register_window.face_auth.stop_camera()
                        if hasattr(self.register_window.face_auth, 'cap') and self.register_window.face_auth.cap is not None:
                            self.register_window.face_auth.cap.release()
                            self.register_window.face_auth.cap = None
                    
                    self.register_window.grab_release()  # Release modal state
                    self.register_window.destroy()
                    self.register_window = None
            finally:
                self._register_window_open = False
                # Schedule camera restart with delay
                self.after(1000, self.schedule_camera_restart)
        
        # Set the close protocol
        self.register_window.protocol("WM_DELETE_WINDOW", on_register_close)

    def _capture_face_for_login(self):
        """Capture face with proper camera state checking"""
        if not self.is_camera_active:
            if self._register_window_open:
                messagebox.showerror("Error", "Please complete registration first", parent=self)
            else:
                messagebox.showerror("Error", "Camera is not ready", parent=self)
                # Try to restart the camera
                self.after(500, self._restart_camera_guaranteed)
            return
                
        try:
            # Verify camera health directly
            if not hasattr(self.face_auth, 'cap') or not self.face_auth.cap.isOpened():
                messagebox.showerror("Error", "Camera hardware not responding", parent=self)
                self.after(500, self._restart_camera_guaranteed)
                return
            
            # Instead of pausing, capture multiple frames to ensure a good one
            face_encoding = None
            max_attempts = 3
            
            for attempt in range(max_attempts):
                # Skip a few frames to ensure we get a fresh image
                if hasattr(self.face_auth, 'cap') and self.face_auth.cap is not None:
                    for _ in range(3):
                        self.face_auth.cap.grab()
                    
                    ret, frame = self.face_auth.cap.read()
                    if not ret:
                        continue
                    
                    # Process captured frame
                    frame = cv2.flip(frame, 1)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Find face locations
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if not face_locations:
                        continue
                        
                    # Get face encodings
                    face_encodings = face_recognition.face_encodings(
                        rgb_frame, 
                        known_face_locations=face_locations,
                        model="small"
                    )
                    
                    if face_encodings:
                        face_encoding = face_encodings[0]
                        break
                        
                time.sleep(0.2)  # Small delay between attempts
                
            if face_encoding is not None:
                self.login_face_encoding = face_encoding
                self.face_capture_status.config(
                    text="Face captured successfully!",
                    fg="#27AE60"
                )
                messagebox.showinfo("Success", "Face captured successfully!", parent=self)
            else:
                messagebox.showerror("Error", "Could not detect face after multiple attempts", parent=self)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Face capture failed: {str(e)}", parent=self)
    
    def _combined_login(self):
        """Handle login with both credentials and face"""
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()
        
        # Validate inputs
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required", parent=self)
            return
        
        # Verify traditional credentials
        if not self.traditional_auth.authenticate(username, password):
            self.entry_pass.delete(0, tk.END)
            return
        
        # Verify face capture
        if self.login_face_encoding is None:
            messagebox.showerror("Error", "Please capture your face first", parent=self)
            return
        
        # Retrieve stored face encoding
        user_data = next((u for u in db_instance.data['users'] if u['username'] == username), None)
        if not user_data or not user_data.get('face_encoding'):
            messagebox.showerror("Error", "No face registered for this user", parent=self)
            return
        
        # Compare face encodings
        try:
            stored_encoding = np.array(user_data['face_encoding'])
            matches = face_recognition.compare_faces([stored_encoding], self.login_face_encoding, tolerance=0.4)
            
            if True in matches:
                self._launch_app(username)
            else:
                messagebox.showerror("Login Failed", "Face verification failed", parent=self)
                self.login_face_encoding = None
                self.face_capture_status.config(
                    text="Face not captured yet",
                    fg="#E74C3C"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Face verification error: {str(e)}", parent=self)
    
    def _show_forgot_password(self):
        """Handle forgot password flow"""
        self.traditional_auth.show_reset_password_dialog()
    
    def _launch_app(self, username):
        """Close login and launch main app"""
        print("Launching main app...")
        self._nuclear_camera_cleanup()
        print("Camera cleanup complete")
        
        # Set username in parent (FinanceTrackerGUI)
        self.parent.set_username(username)
        print("Username set")
        
        # Initialize main app if not already done
        if not hasattr(self.parent, 'initialized') or not self.parent.initialized:
            print("Initializing main app")
            self.parent.initialize_main_app()
        else:
            print("Main app already initialized")
        
        # Ensure main window is visible
        self.parent.root.deiconify()
        print("Main window should be visible now")
        
        # Destroy login window
        self.destroy()
        print("Login window destroyed")
    
    def on_close(self):
        """Handle window close"""
        self._nuclear_camera_cleanup()
        self.destroy()
        self.parent.destroy()  # Close the entire application
    
    def destroy(self):
        """Override destroy to ensure complete cleanup"""
        self._nuclear_camera_cleanup()
        if hasattr(self, 'video_label') and self.video_label.winfo_exists():
            self.video_label.destroy()
        if hasattr(self, 'camera_frame') and self.camera_frame.winfo_exists():
            self.camera_frame.destroy()
        super().destroy()

    def clear_fields(self):
        """Clear login fields"""
        self.entry_user.delete(0, tk.END)
        self.entry_pass.delete(0, tk.END)
        self.login_face_encoding = None
        self.face_capture_status.config(
            text="Face not captured yet",
            fg="#E74C3C"
        )
    

def main():
    root = tk.Tk()
    app = FinanceTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main(), 