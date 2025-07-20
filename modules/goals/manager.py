import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime
import webbrowser
from database.core import db_instance
from tkcalendar import Calendar  # Import the Calendar widget

# --------------------------
# Database Helper Functions 
# --------------------------

def add_goal(name, target_amount, deadline, allocation_percent=0):
    """Add a new goal to the database."""
    data = db_instance.load_data()
    goal = {
        "name": name,
        "target_amount": target_amount,
        "deadline": deadline,
        "saved_amount": 0,
        "allocation_percent": allocation_percent
    }
    data["goals"].append(goal)
    db_instance.save_data(data)
    return goal

def update_goal_savings(goal_name, amount):
    """Update the saved amount for a specific goal."""
    data = db_instance.load_data()
    for goal in data["goals"]:
        if goal["name"] == goal_name:
            goal["saved_amount"] += amount
            db_instance.save_data(data)
            break

def get_goals():
    """Retrieve all goals from the database."""
    return db_instance.load_data().get("goals", [])

def calculate_goal_progress(goal):
    """Calculate progress, time remaining, and required monthly savings for a goal."""
    target_amount = goal["target_amount"]
    saved_amount = goal["saved_amount"]
    deadline = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
    today = datetime.now().date()

    progress = (saved_amount / target_amount) * 100 if target_amount > 0 else 0
    days_remaining = (deadline - today).days
    months_remaining = max(days_remaining / 30, 0.1)  # Avoid division by zero
    remaining_amount = target_amount - saved_amount
    required_monthly_savings = remaining_amount / months_remaining if months_remaining > 0 else 0

    return {
        "progress": progress,
        "days_remaining": days_remaining,
        "required_monthly_savings": required_monthly_savings
    }

# --------------------------
# Enhanced GUI Class
# --------------------------

class GoalsWindow:
    def __init__(self, notebook):
        """Initialize the Goals tab with modern UI."""
        self.frame = ttk.Frame(notebook, width=1200, height=800)
        self.data = db_instance.load_data()
        
        # Custom fonts
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.subtitle_font = font.Font(family="Segoe UI", size=10)
        self.body_font = font.Font(family="Segoe UI", size=10)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.card_title_font = font.Font(family="Segoe UI", size=12, weight="bold")
        
        self.configure_styles()
        self.create_header()
        self.create_main_content()
        self.display_goals()

    def configure_styles(self):
        """Configure custom styles for modern look"""
        style = ttk.Style()
        
        # Modern color scheme
        style.configure('Modern.TFrame', background='#f8f9fa')
        style.configure('Header.TFrame', background='#4e73df')
        style.configure('Header.TLabel', 
                       background='#4e73df', 
                       foreground='white', 
                       font=self.title_font)
        
        # Form styling
        style.configure('Form.TLabelframe', 
                       borderwidth=0, 
                       relief='flat', 
                       background='#f8f9fa')
        style.configure('Form.TLabel', 
                       background='#f8f9fa', 
                       font=self.body_font,
                       foreground='#5a5c69')
        style.configure('Modern.TEntry', 
                       fieldbackground='white', 
                       bordercolor='#d1d3e2', 
                       lightcolor='#d1d3e2', 
                       darkcolor='#d1d3e2',
                       font=self.body_font,
                       padding=5)
        
        # Button styles
        style.configure('Primary.TButton', 
                       foreground='white', 
                       background='#4e73df', 
                       font=self.button_font,
                       borderwidth=0,
                       padding=8)
        style.map('Primary.TButton',
                 background=[('active', '#2e59d9'), ('pressed', '#1c3fb0')])
        
        style.configure('Success.TButton', 
                       foreground='white', 
                       background='#1cc88a', 
                       font=self.button_font,
                       borderwidth=0,
                       padding=8)
        style.map('Success.TButton',
                 background=[('active', '#17a673'), ('pressed', '#13855c')])
        
        style.configure('Danger.TButton', 
                       foreground='white', 
                       background='#e74a3b', 
                       font=self.button_font,
                       borderwidth=0,
                       padding=8)
        style.map('Danger.TButton',
                 background=[('active', '#d52a1a'), ('pressed', '#b82114')])
        
        style.configure('Secondary.TButton', 
                       foreground='#858796', 
                       background='#f8f9fa', 
                       font=self.button_font,
                       borderwidth=1,
                       lightcolor='#d1d3e2',
                       darkcolor='#d1d3e2',
                       padding=8)
        style.map('Secondary.TButton',
                 background=[('active', '#e2e6ea'), ('pressed', '#d1d7dc')])
        
        # Progress bar styles
        style.configure('Modern.Horizontal.TProgressbar',
                       thickness=12,
                       troughcolor='#e3e6f0',
                       background='#4e73df',
                       lightcolor='#4e73df',
                       darkcolor='#4e73df')
        
        style.configure('Success.Horizontal.TProgressbar',
                       thickness=12,
                       troughcolor='#e3e6f0',
                       background='#1cc88a',
                       lightcolor='#1cc88a',
                       darkcolor='#1cc88a')
        
        style.configure('Warning.Horizontal.TProgressbar',
                       thickness=12,
                       troughcolor='#e3e6f0',
                       background='#f6c23e',
                       lightcolor='#f6c23e',
                       darkcolor='#f6c23e')
        
        style.configure('Danger.Horizontal.TProgressbar',
                       thickness=12,
                       troughcolor='#e3e6f0',
                       background='#e74a3b',
                       lightcolor='#e74a3b',
                       darkcolor='#e74a3b')

    def create_header(self):
        """Create a modern header with inspirational quote"""
        header = ttk.Frame(self.frame, style='Header.TFrame')
        header.pack(fill='x', padx=0, pady=0)
        
        
        
        title = ttk.Label(header, 
                         text="Goals Setting",
                         font=("Helvetica Neue", 16, "bold"),
                         style='Header.TLabel',
                         wraplength=600)
        title.pack(pady=15, padx=20)
        
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', pady=0)

    def create_main_content(self):
        """Create the main content area with form and goals list"""
        main_content = ttk.Frame(self.frame, style='Modern.TFrame')
        main_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left side - Form
        form_container = ttk.Frame(main_content, style='Modern.TFrame')
        form_container.pack(side='left', fill='y', padx=(0, 20), pady=0)
        self.create_goal_form(form_container)
        
        # Right side - Goals list
        goals_container = ttk.Frame(main_content, style='Modern.TFrame')
        goals_container.pack(side='right', fill='both', expand=True, padx=0, pady=0)
        self.create_goals_list(goals_container)

    def create_goal_form(self, parent):
        """Create the new goal form with modern styling"""
        form_frame = ttk.LabelFrame(parent, 
                                  text="  Create New Goal  ",
                                  style='Form.TLabelframe',
                                  padding=(15, 10))
        form_frame.pack(fill='y', padx=0, pady=0)
        
        # Form title
        form_title = ttk.Label(form_frame,
                              text="Set Your Financial Goal",
                              style='Form.TLabel',
                              font=self.title_font)
        form_title.pack(pady=(0, 15))
        
        # Goal Name
        name_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        name_frame.pack(fill='x', pady=5)
        ttk.Label(name_frame, 
                 text="Goal Name", 
                 style='Form.TLabel').pack(anchor='w')
        self.goal_name_entry = ttk.Entry(name_frame, 
                                       style='Modern.TEntry',
                                       font=self.body_font)
        self.goal_name_entry.pack(fill='x', pady=(5, 0))
        
        # Target Amount
        amount_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        amount_frame.pack(fill='x', pady=5)
        ttk.Label(amount_frame, 
                 text="Target Amount (₹)", 
                 style='Form.TLabel').pack(anchor='w')
        self.target_amount_entry = ttk.Entry(amount_frame, 
                                           style='Modern.TEntry',
                                           font=self.body_font)
        self.target_amount_entry.pack(fill='x', pady=(5, 0))
        
        # Deadline
        deadline_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        deadline_frame.pack(fill='x', pady=5)
        ttk.Label(deadline_frame, 
                 text="Deadline", 
                 style='Form.TLabel').pack(anchor='w')
        
        # Create a frame for the calendar button and entry
        deadline_input_frame = ttk.Frame(deadline_frame, style='Modern.TFrame')
        deadline_input_frame.pack(fill='x', pady=(5, 0))
        
        self.deadline_entry = ttk.Entry(deadline_input_frame,
                                      style='Modern.TEntry',
                                      font=self.body_font)
        self.deadline_entry.pack(side='left', fill='x', expand=True)
        
        # Calendar button
        calendar_btn = ttk.Button(deadline_input_frame,
                                text="📅",
                                style='Secondary.TButton',
                                command=self.show_calendar)
        calendar_btn.pack(side='left', padx=(5, 0))
        
        # Allocation Percentage
        alloc_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        alloc_frame.pack(fill='x', pady=5)
        ttk.Label(alloc_frame, 
                 text="Auto-Allocation Percentage", 
                 style='Form.TLabel').pack(anchor='w')
        self.allocation_percent_entry = ttk.Entry(alloc_frame, 
                                               style='Modern.TEntry',
                                               font=self.body_font)
        self.allocation_percent_entry.pack(fill='x', pady=(5, 0))
        ttk.Label(alloc_frame, 
                 text="0-100% of income to auto-allocate", 
                 style='Form.TLabel',
                 font=self.subtitle_font).pack(anchor='w', pady=(2, 0))
        
        # Save Button
        save_btn = ttk.Button(form_frame, 
                            text="Create Goal", 
                            style='Primary.TButton',
                            command=self.save_goal)
        save_btn.pack(fill='x', pady=(15, 5))
        
        # Help link
        help_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        help_frame.pack(fill='x', pady=(10, 0))
        help_link = ttk.Label(help_frame, 
                            text="Need help setting financial goals?",
                            style='Form.TLabel',
                            cursor="hand2",
                            font=self.subtitle_font)
        help_link.pack()
        help_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.mindtools.com/page6.html"))

    def show_calendar(self):
        """Show calendar popup for date selection"""
        def set_date():
            self.deadline_entry.delete(0, tk.END)
            self.deadline_entry.insert(0, cal.get_date())
            top.destroy()
        
        top = tk.Toplevel(self.frame)
        top.title("Select Deadline")
        top.transient(self.frame)
        top.grab_set()
        
        # Set minimum size
        top.minsize(300, 250)
        
        # Center the window
        top.update_idletasks()
        width = top.winfo_width()
        height = top.winfo_height()
        x = (top.winfo_screenwidth() // 2) - (width // 2)
        y = (top.winfo_screenheight() // 2) - (height // 2)
        top.geometry(f'+{x}+{y}')
        
        # Create calendar widget
        cal = Calendar(top, 
                      selectmode='day', 
                      date_pattern='yyyy-mm-dd',
                      mindate=datetime.now().date())
        cal.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Add select button
        btn_frame = ttk.Frame(top, style='Modern.TFrame')
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_frame,
                  text="Select Date",
                  style='Primary.TButton',
                  command=set_date).pack(fill='x')

    def create_goals_list(self, parent):
        """Create the scrollable goals list area"""
        self.goals_frame = ttk.LabelFrame(parent, 
                                        text="  Your Financial Goals  ",
                                        style='Form.TLabelframe',
                                        padding=(15, 15))
        self.goals_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Goals list header
        header_frame = ttk.Frame(self.goals_frame, style='Modern.TFrame')
        header_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(header_frame,
                 text="Track Your Progress",
                 style='Form.TLabel',
                 font=self.title_font).pack(side='left')
        
        ttk.Label(header_frame,
                 text=f"{len(get_goals())} active goals",
                 style='Form.TLabel',
                 font=self.subtitle_font).pack(side='right')
        
        # Scrollable canvas
        self.canvas = tk.Canvas(self.goals_frame, 
                               bg='#f8f9fa',
                               highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.goals_frame, 
                                orient="vertical", 
                                command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, 
                                        style='Modern.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.create_window((0, 0), 
                                 window=self.scrollable_frame, 
                                 anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empty state
        self.empty_state = ttk.Label(self.scrollable_frame,
                                   text="You haven't set any goals yet.\nStart by creating your first financial goal!",
                                   style='Form.TLabel',
                                   font=self.body_font)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(1, width=event.width)
    
    def save_goal(self):
        """Save a new goal with validation and feedback"""
        try:
            name = self.goal_name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a goal name", parent=self.frame)
                return
                
            try:
                target_amount = float(self.target_amount_entry.get().strip())
                if target_amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid target amount", parent=self.frame)
                return
                
            deadline = self.deadline_entry.get().strip()
            try:
                datetime.strptime(deadline, "%Y-%m-%d")
                if datetime.strptime(deadline, "%Y-%m-%d").date() < datetime.now().date():
                    messagebox.showerror("Error", "Deadline cannot be in the past", parent=self.frame)
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD", parent=self.frame)
                return
                
            try:
                allocation_percent = float(self.allocation_percent_entry.get().strip() or "0")
                if not 0 <= allocation_percent <= 100:
                    raise ValueError("Percentage must be 0-100")
            except ValueError:
                messagebox.showerror("Error", "Allocation must be between 0 and 100", parent=self.frame)
                return

            add_goal(name, target_amount, deadline, allocation_percent)
            self.display_goals()
            
            # Clear form
            self.goal_name_entry.delete(0, tk.END)
            self.target_amount_entry.delete(0, tk.END)
            self.deadline_entry.delete(0, tk.END)
            self.allocation_percent_entry.delete(0, tk.END)
            
            # Show success notification
            success_frame = ttk.Frame(self.frame, style='Modern.TFrame')
            success_frame.place(relx=0.5, rely=0.9, anchor='center')
            
            success_label = ttk.Label(success_frame,
                                    text=f"✓ Goal '{name}' created successfully!",
                                    style='Form.TLabel',
                                    background='#1cc88a',
                                    foreground='white',
                                    font=self.button_font,
                                    padding=(20, 5))
            success_label.pack()
            
            # Auto-hide after 3 seconds
            self.frame.after(3000, success_frame.destroy)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}", parent=self.frame)

    def display_goals(self):
        """Display all goals with modern cards"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        goals = get_goals()
        
        if not goals:
            self.empty_state.pack(pady=50)
            return
        
        # Sort goals by deadline (soonest first)
        goals.sort(key=lambda x: datetime.strptime(x["deadline"], "%Y-%m-%d"))
        
        for goal in goals:
            self.create_goal_card(goal)
            
        # Add some padding at the bottom
        ttk.Label(self.scrollable_frame, style='Modern.TFrame').pack(pady=10)

    def create_goal_card(self, goal):
        """Create a modern card for a single goal"""
        progress = calculate_goal_progress(goal)
        deadline = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
        today = datetime.now().date()
        days_remaining = (deadline - today).days
        
        # Determine card styling based on status
        if days_remaining < 0:
            card_bg = '#f8f9fa'
            border_color = '#e74a3b'
            status_text = "OVERDUE"
            status_color = '#e74a3b'
            progress_style = 'Danger.Horizontal.TProgressbar'
            icon = "⏰"
        elif days_remaining < 7:
            card_bg = '#f8f9fa'
            border_color = '#f6c23e'
            status_text = f"URGENT - {days_remaining} days left"
            status_color = '#f6c23e'
            progress_style = 'Warning.Horizontal.TProgressbar'
            icon = "⚠️"
        elif progress['progress'] >= 100:
            card_bg = '#f8f9fa'
            border_color = '#1cc88a'
            status_text = "COMPLETED!"
            status_color = '#1cc88a'
            progress_style = 'Success.Horizontal.TProgressbar'
            icon = "✅"
        else:
            card_bg = '#f8f9fa'
            border_color = '#4e73df'
            status_text = f"{days_remaining} days remaining"
            status_color = '#4e73df'
            progress_style = 'Modern.Horizontal.TProgressbar'
            icon = "📌"
        
        # Create card container
        card = tk.Frame(self.scrollable_frame,
                       bg=card_bg,
                       bd=1,
                       highlightbackground=border_color,
                       highlightthickness=2,
                       relief='solid')
        card.pack(fill='x', pady=(0, 15), padx=5)
        
        # Card content
        content = tk.Frame(card, bg=card_bg)
        content.pack(fill='x', padx=15, pady=15)
        
        # Card header (title + status)
        header = tk.Frame(content, bg=card_bg)
        header.pack(fill='x', pady=(0, 10))
        
        icon_label = tk.Label(header, 
                            text=icon, 
                            bg=card_bg,
                            font=('Helvetica', 14))
        icon_label.pack(side='left', padx=(0, 5))
        
        title = tk.Label(header,
                        text=goal['name'],
                        bg=card_bg,
                        font=self.card_title_font,
                        anchor='w')
        title.pack(side='left', fill='x', expand=True)
        
        status = tk.Label(header,
                         text=status_text,
                         bg=card_bg,
                         fg=status_color,
                         font=self.button_font)
        status.pack(side='right')
        
        # Progress bar
        pb_frame = tk.Frame(content, bg=card_bg)
        pb_frame.pack(fill='x', pady=(0, 15))
        
        pb = ttk.Progressbar(pb_frame,
                            style=progress_style,
                            length=1000,  # Will be resized by pack
                            value=progress['progress'])
        pb.pack(fill='x')
        
        # Progress percentage
        progress_frame = tk.Frame(content, bg=card_bg)
        progress_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(progress_frame,
                text=f"Progress: {progress['progress']:.1f}%",
                bg=card_bg,
                font=self.body_font).pack(side='left')
        
        tk.Label(progress_frame,
                text=f"₹{goal['saved_amount']:,.2f} / ₹{goal['target_amount']:,.2f}",
                bg=card_bg,
                font=self.body_font).pack(side='right')
        
        # Details section
        details_frame = tk.Frame(content, bg=card_bg)
        details_frame.pack(fill='x')
        
        # Left column - Target info
        left_frame = tk.Frame(details_frame, bg=card_bg)
        left_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(left_frame,
                text=f"Target Amount: ₹{goal['target_amount']:,.2f}",
                bg=card_bg,
                font=self.body_font).pack(anchor='w', pady=2)
        
        tk.Label(left_frame,
                text=f"Deadline: {goal['deadline']}",
                bg=card_bg,
                font=self.body_font).pack(anchor='w', pady=2)
        
        if goal.get('allocation_percent', 0) > 0:
            tk.Label(left_frame,
                    text=f"Auto-Allocation: {goal['allocation_percent']}% of income",
                    bg=card_bg,
                    font=self.body_font).pack(anchor='w', pady=2)
        
        # Right column - Savings info
        right_frame = tk.Frame(details_frame, bg=card_bg)
        right_frame.pack(side='right', fill='x')
        
        tk.Label(right_frame,
                text=f"Monthly Needed: ₹{progress['required_monthly_savings']:,.2f}",
                bg=card_bg,
                font=self.body_font).pack(anchor='e', pady=2)
        
        tk.Label(right_frame,
                text=f"Days Remaining: {days_remaining}",
                bg=card_bg,
                font=self.body_font).pack(anchor='e', pady=2)
        
        # Action buttons
        actions_frame = tk.Frame(content, bg=card_bg)
        actions_frame.pack(fill='x', pady=(15, 0))
        
        add_btn = ttk.Button(actions_frame,
                            text="Add Savings",
                            style='Success.TButton',
                            command=lambda n=goal['name']: self.update_savings(n))
        add_btn.pack(side='left', padx=(0, 5))
        
        del_btn = ttk.Button(actions_frame,
                            text="Delete Goal",
                            style='Danger.TButton',
                            command=lambda n=goal['name']: self.delete_goal(n))
        del_btn.pack(side='right')

    def update_savings(self, goal_name):
        """Show dialog to add manual savings to a goal"""
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Add Savings to {goal_name}")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.frame)  # Set to be on top of the main window
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Style the dialog
        dialog.configure(bg='#f8f9fa')
        
        content = ttk.Frame(dialog, style='Modern.TFrame')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Dialog header
        ttk.Label(content,
                 text=f"Add to '{goal_name}'",
                 style='Form.TLabel',
                 font=self.title_font).pack(pady=(0, 15))
        
        # Amount entry
        amount_frame = ttk.Frame(content, style='Modern.TFrame')
        amount_frame.pack(fill='x', pady=10)
        
        ttk.Label(amount_frame,
                 text="Amount to Add (₹)",
                 style='Form.TLabel').pack(anchor='w')
        
        amount_entry = ttk.Entry(amount_frame,
                               style='Modern.TEntry',
                               font=('Helvetica', 12))
        amount_entry.pack(fill='x', pady=(5, 0))
        amount_entry.focus_set()
        
        # Button frame
        btn_frame = ttk.Frame(content, style='Modern.TFrame')
        btn_frame.pack(fill='x', pady=(20, 0))
        
        def save():
            try:
                amount = float(amount_entry.get())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                
                update_goal_savings(goal_name, amount)
                self.display_goals()
                dialog.destroy()
                
                # Show success notification
                success_frame = ttk.Frame(self.frame, style='Modern.TFrame')
                success_frame.place(relx=0.5, rely=0.9, anchor='center')
                
                success_label = ttk.Label(success_frame,
                                        text=f"✓ Added ₹{amount:,.2f} to '{goal_name}'",
                                        style='Form.TLabel',
                                        background='#1cc88a',
                                        foreground='white',
                                        font=self.button_font,
                                        padding=(20, 5))
                success_label.pack()
                
                # Auto-hide after 3 seconds
                self.frame.after(3000, success_frame.destroy)
                
            except ValueError:
                messagebox.showerror("Error",
                                   "Please enter a valid positive amount",
                                   parent=dialog)
        
        ttk.Button(btn_frame,
                  text="Save",
                  style='Primary.TButton',
                  command=save).pack(side='left', padx=(0, 5), fill='x', expand=True)
        
        ttk.Button(btn_frame,
                  text="Cancel",
                  style='Secondary.TButton',
                  command=dialog.destroy).pack(side='left', fill='x', expand=True)

    def delete_goal(self, goal_name):
        """Confirm and delete a goal with modern dialog"""
        confirm_dialog = tk.Toplevel(self.frame)
        confirm_dialog.title("Confirm Delete")
        confirm_dialog.geometry("450x250")
        confirm_dialog.resizable(False, False)
        confirm_dialog.transient(self.frame)
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Style the dialog
        confirm_dialog.configure(bg='#f8f9fa')
        
        content = ttk.Frame(confirm_dialog, style='Modern.TFrame')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Warning icon
        warning_icon = ttk.Label(content,
                               text="⚠️",
                               font=('Helvetica', 24),
                               style='Form.TLabel')
        warning_icon.pack(pady=(0, 15))
        
        # Message
        ttk.Label(content,
                 text=f"Are you sure you want to delete '{goal_name}'?",
                 style='Form.TLabel',
                 font=self.title_font).pack(pady=(0, 5))
        
        ttk.Label(content,
                 text="This action cannot be undone.",
                 style='Form.TLabel',
                 font=self.body_font).pack(pady=(0, 20))
        
        # Button frame
        btn_frame = ttk.Frame(content, style='Modern.TFrame')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        def confirm_delete():
            data = db_instance.load_data()
            data["goals"] = [g for g in data["goals"] if g["name"] != goal_name]
            db_instance.save_data(data)
            
            if "goal_allocations" in data:
                data["goal_allocations"] = [
                    a for a in data["goal_allocations"] 
                    if a["goal_name"] != goal_name
                ]
                db_instance.save_data(data)
            
            self.display_goals()
            confirm_dialog.destroy()
            
            # Show success notification
            success_frame = ttk.Frame(self.frame, style='Modern.TFrame')
            success_frame.place(relx=0.5, rely=0.9, anchor='center')
            
            success_label = ttk.Label(success_frame,
                                    text=f"✓ Goal '{goal_name}' deleted",
                                    style='Form.TLabel',
                                    background='#1cc88a',
                                    foreground='white',
                                    font=self.button_font,
                                    padding=(20, 5))
            success_label.pack()
            
            # Auto-hide after 3 seconds
            self.frame.after(3000, success_frame.destroy)
        
        ttk.Button(btn_frame,
                  text="Delete Goal",
                  style='Danger.TButton',
                  command=confirm_delete).pack(side='left', padx=(0, 5), fill='x', expand=True)
        
        ttk.Button(btn_frame,
                  text="Cancel",
                  style='Secondary.TButton',
                  command=confirm_dialog.destroy).pack(side='left', fill='x', expand=True)