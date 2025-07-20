import tkinter as tk
from tkinter import ttk, messagebox
from database.core import db_instance

class BudgetWindow:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, width=1200, height=800)
        self.data = db_instance.load_data()
        self.notebook = notebook  
        db_instance.register_callback(self.on_data_updated)
        # Define color scheme
        self.colors = {
            "primary": "#3498db",
            "secondary": "#2ecc71",
            "accent": "#e74c3c",
            "background": "#f5f7fa",
            "card": "#ffffff",
            "text": "#2c3e50",
            "light_text": "#ecf0f1",
            "warning": "#f39c12"
        }
        
        # Define color mapping for categories
        self.color_mapping = {
            "Blue": "#3498db",
            "Green": "#2ecc71",
            "Red": "#e74c3c",
            "Purple": "#9b59b6",
            "Orange": "#e67e22",
            "Yellow": "#f1c40f",
            "Teal": "#1abc9c",
            "Gray": "#95a5a6"
        }
        
        # Configure styles
        self.configure_styles()
        
        # Main container
        main_container = tk.Frame(self.frame, bg=self.colors["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with title and icon
        header_frame = tk.Frame(main_container, bg=self.colors["primary"])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame, 
                             text="💰 Budget Management", 
                             font=("Arial", 20, "bold"),
                             fg=self.colors["light_text"], 
                             bg=self.colors["primary"],
                             padx=20,
                             pady=15)
        title_label.pack(side=tk.LEFT)
        
        # Add a visual chart icon
        chart_icon = tk.Label(header_frame, 
                             text="📊", 
                             font=("Arial", 28),
                             bg=self.colors["primary"],
                             fg=self.colors["light_text"],
                             padx=20)
        chart_icon.pack(side=tk.RIGHT)
        
        # Content area
        content_frame = tk.Frame(main_container, bg=self.colors["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Budget Table (70% width)
        table_container = tk.Frame(content_frame, bg=self.colors["background"])
        table_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Table card with shadow effect
        table_card = tk.Frame(table_container, 
                            bg=self.colors["card"],
                            bd=0,
                            highlightthickness=0,
                            relief=tk.RIDGE)
        table_card.pack(fill=tk.BOTH, expand=True)
        
        # Add shadow effect
        self.create_shadow(table_card, color="#e0e0e0", offset=3)
        
        # Table header
        table_header = tk.Frame(table_card, bg=self.colors["primary"])
        table_header.pack(fill=tk.X)
        
        tk.Label(table_header, 
                text="Budget Overview", 
                font=("Arial", 16, "bold"),
                fg=self.colors["light_text"], 
                bg=self.colors["primary"],
                padx=15,
                pady=10).pack(side=tk.LEFT)
        
        refresh_btn = tk.Button(table_header,
                              text="🔄 Refresh",
                              command=self.refresh_budget_data,
                              bg=self.colors["primary"],
                              fg="white",
                              bd=0,
                              relief=tk.FLAT,
                              font=("Arial", 11))
        refresh_btn.pack(side=tk.LEFT, padx=10)
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(bg="#2980b9"))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(bg=self.colors["primary"]))
        
        # Visualization button
        viz_frame = tk.Frame(table_header, bg=self.colors["primary"])
        viz_frame.pack(side=tk.RIGHT, padx=10)

        tk.Button(viz_frame, text="📈 Advanced Chart View", 
                command=self.show_chart_view,
                bg=self.colors["secondary"],
                fg="white",
                bd=0,
                relief=tk.FLAT,
                padx=10,
                pady=5,
                font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        # Table content
        table_content = tk.Frame(table_card, bg=self.colors["card"])
        table_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable frame for the table
        self.canvas = tk.Canvas(table_content, 
                              bg=self.colors["card"],
                              highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_content, 
                                 orient=tk.VERTICAL, 
                                 command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        self.table_frame = tk.Frame(self.canvas, bg=self.colors["card"])
        self.canvas_window = self.canvas.create_window((0, 0), 
                                                     window=self.table_frame, 
                                                     anchor=tk.NW)
        
        # Right panel - Set Budget Form (30% width)
        form_container = tk.Frame(content_frame, bg=self.colors["background"], width=350)
        form_container.pack(side=tk.RIGHT, fill=tk.Y)
        form_container.pack_propagate(False)
        
        # Form card with shadow effect
        form_card = tk.Frame(form_container, 
                           bg=self.colors["card"],
                           bd=0,
                           highlightthickness=0,
                           relief=tk.RIDGE)
        form_card.pack(fill=tk.BOTH, expand=True)
        
        # Add shadow effect
        self.create_shadow(form_card, color="#e0e0e0", offset=3)
        
        # Form header
        form_header = tk.Frame(form_card, bg=self.colors["primary"])
        form_header.pack(fill=tk.X)
        
        tk.Label(form_header, 
                text="Budget Controls", 
                font=("Arial", 16, "bold"),
                fg=self.colors["light_text"], 
                bg=self.colors["primary"],
                padx=15,
                pady=10).pack(side=tk.LEFT)
        
        # Form content
        form_content = tk.Frame(form_card, bg=self.colors["card"], padx=20, pady=20)
        form_content.pack(fill=tk.BOTH, expand=True)
        
        # Form elements
        tk.Label(form_content, 
                text="Select Category:", 
                font=("Arial", 12),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        self.category_combobox = ttk.Combobox(form_content, 
                                            values=self.data.get("categories", []),
                                            font=("Arial", 12))
        self.category_combobox.pack(fill=tk.X, pady=(0, 15))
        self.category_combobox.bind("<Button-1>", self.refresh_combobox_values)
        
        tk.Label(form_content, 
                text="Budget Amount (Rs):", 
                font=("Arial", 12),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        self.budget_entry = ttk.Entry(form_content, font=("Arial", 14))
        self.budget_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Set Budget button
        set_budget_btn = tk.Button(form_content, 
                                  text="💾 Set Budget", 
                                  command=self.set_budget,
                                  bg=self.colors["primary"],
                                  fg="white",
                                  font=("Arial", 14, "bold"),
                                  bd=0,
                                  relief=tk.FLAT,
                                  padx=20,
                                  pady=12)
        set_budget_btn.pack(fill=tk.X)
        
        # Add hover effect
        set_budget_btn.bind("<Enter>", lambda e: set_budget_btn.config(bg="#2980b9"))
        set_budget_btn.bind("<Leave>", lambda e: set_budget_btn.config(bg=self.colors["primary"]))
        
        # Summary section
        summary_frame = tk.Frame(form_content, bg=self.colors["card"])
        summary_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Label(summary_frame, 
                text="Budget Summary", 
                font=("Arial", 14, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(anchor=tk.W, pady=(0, 10))
        
        # Summary items with icons
        self.create_summary_item(summary_frame, "📊 Total Budget:", "total_budget", "Rs0")
        self.create_summary_item(summary_frame, "💸 Total Spent:", "total_spent", "Rs0")
        self.create_summary_item(summary_frame, "💰 Remaining:", "total_remaining", "Rs0")
        
        # Add initial data for demo purposes if needed
        self.initialize_demo_data()
        
        # Populate the table with data
        self.update_budget_table()

    def create_shadow(self, widget, color="#e0e0e0", offset=3):
        """Create a shadow effect for a widget using a solid color"""
        shadow = tk.Frame(widget.master, background=color)
        shadow.place(in_=widget, x=offset, y=offset, relwidth=1, relheight=1)
        widget.lift()
        
    def create_summary_item(self, parent, label_text, var_name, default_value):
        frame = tk.Frame(parent, bg=self.colors["card"])
        frame.pack(fill=tk.X, pady=5)
        
        tk.Label(frame, 
                text=label_text, 
                font=("Arial", 12),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(side=tk.LEFT)
        
        var = tk.StringVar(value=default_value)
        setattr(self, f"{var_name}_var", var)
        
        value_label = tk.Label(frame, 
                             textvariable=var,
                             font=("Arial", 12, "bold"),
                             bg=self.colors["card"],
                             fg=self.colors["text"])
        value_label.pack(side=tk.RIGHT)
        
        setattr(self, f"{var_name}_label", value_label)

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

    def initialize_demo_data(self):
        if "budget" not in self.data or not self.data["budget"]:
            demo_budgets = {
                "Housing": 1500,
                "Food": 600,
                "Transportation": 400,
                "Utilities": 300,
                "Entertainment": 200,
                "Shopping": 300,
                "Healthcare": 200,
                "Personal Care": 100
            }
            
            if "categories" not in self.data:
                self.data["categories"] = []
                
            for category in demo_budgets.keys():
                if category not in self.data["categories"]:
                    self.data["categories"].append(category)
            
            if "budget" not in self.data:
                self.data["budget"] = {}
                
            for category, amount in demo_budgets.items():
                self.data["budget"][category] = amount
                
            db_instance.save_data(self.data)
            self.category_combobox['values'] = self.data.get("categories", [])


    def refresh_budget_data(self):
        """Refresh all budget data from database and update UI"""
        self.data = db_instance.load_data()
        self.update_budget_table()
        messagebox.showinfo("Refreshed", "Budget data has been refreshed with latest transactions", parent=self.frame)

    def configure_styles(self):
        style = ttk.Style()
        
        # Configure the main styles
        style.configure("TFrame", background=self.colors["background"])
        style.configure("TLabel", background=self.colors["background"], foreground=self.colors["text"])
        
        # Combobox style
        style.map('TCombobox',
                 fieldbackground=[('readonly', self.colors["card"])],
                 background=[('readonly', self.colors["card"])])

    def create_table_headers(self):
        header_frame = tk.Frame(self.table_frame, bg=self.colors["card"])
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Header columns
        columns = [
            ("Category", 15, 'w'),
            ("Budget", 10, 'e'),
            ("Spent", 10, 'e'),
            ("Remaining", 10, 'e'),
            ("% of Total", 10, 'e')
        ]
        
        for i, (text, width, anchor) in enumerate(columns):
            tk.Label(header_frame, 
                    text=text, 
                    font=("Arial", 12, "bold"),
                    bg=self.colors["card"],
                    fg=self.colors["text"],
                    width=width,
                    anchor=anchor).grid(row=0, column=i, padx=5)
        
        # Separator
        tk.Frame(self.table_frame, 
                height=2,
                bg="#e0e0e0").pack(fill=tk.X, padx=10, pady=5)

    def update_budget_table(self):
        # Clear existing widgets
        for widget in self.table_frame.winfo_children():
            widget.destroy()
            
        self.create_table_headers()
            
        # Load FRESH data from database
        self.data = db_instance.load_data()
        
        if "budget" not in self.data:
            self.data["budget"] = {}
        
        # Get all categories (from both budget and categories list)
        all_categories = set(self.data.get("categories", []))
        all_categories.update(self.data.get("budget", {}).keys())
        all_categories = sorted(list(all_categories))
        
        # Initialize spent amounts
        spent_by_category = {category: 0 for category in all_categories}
        
        # Calculate spent amounts from ACTUAL transactions
        for transaction in self.data.get("expenses", []):  # Changed from "transactions" to "expenses"
            if "category" in transaction and transaction["category"] in spent_by_category:
                try:
                    # Changed from transaction.get("expenses.amount", 0) to transaction.get("amount", 0)
                    spent_by_category[transaction["category"]] += float(transaction.get("amount", 0))
                except (ValueError, TypeError):
                    print(f"Warning: Invalid amount for transaction in {transaction['category']}")
        
        # Calculate totals
        total_budget = sum(self.data["budget"].get(category, 0) for category in all_categories)
        row_index = 0
        total_spent = 0
        total_remaining = 0
        
        # Create table rows
        for category in all_categories:
            budget_amount = self.data["budget"].get(category, 0)
            if budget_amount == 0:
                continue
                
            spent_amount = spent_by_category.get(category, 0)
            remaining = budget_amount - spent_amount
            
            total_spent += spent_amount
            total_remaining += remaining
            
            row_frame = tk.Frame(self.table_frame, bg=self.colors["card"])
            row_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Get color for this row
            color_name = list(self.color_mapping.keys())[row_index % len(self.color_mapping)]
            color_hex = self.color_mapping[color_name]
            
            # Category cell with color indicator
            category_cell = tk.Frame(row_frame, bg=self.colors["card"])
            category_cell.grid(row=0, column=0, padx=5, sticky='w')
            
            # Color indicator circle
            color_canvas = tk.Canvas(category_cell, width=24, height=24, bg=self.colors["card"], highlightthickness=0)
            color_canvas.pack(side=tk.LEFT, padx=(0, 5))
            color_canvas.create_oval(2, 2, 22, 22, fill=color_hex, outline="")
            
            # Category label with icon
            tk.Label(category_cell, 
                    text=f"{self.get_icon_for_category(category)} {category}", 
                    font=("Arial", 12),
                    bg=self.colors["card"],
                    fg=self.colors["text"],
                    width=14,
                    anchor='w').pack(side=tk.LEFT)
            
            # Budget amount with edit button
            budget_cell = tk.Frame(row_frame, bg=self.colors["card"])
            budget_cell.grid(row=0, column=1, padx=5)
            
            tk.Label(budget_cell, 
                    text=f"Rs{budget_amount:.2f}", 
                    font=("Arial", 12),
                    bg=self.colors["card"],
                    fg=self.colors["text"],
                    width=8,
                    anchor='e').pack(side=tk.LEFT)
            
            edit_btn = tk.Button(budget_cell, 
                            text="✏️", 
                            command=lambda cat=category: self.edit_budget(cat),
                            bg=self.colors["card"],
                            fg=self.colors["primary"],
                            bd=0,
                            relief=tk.FLAT,
                            font=("Arial", 12))
            edit_btn.pack(side=tk.LEFT, padx=5)
            
            # Spent amount
            tk.Label(row_frame, 
                    text=f"Rs{spent_amount:.2f}", 
                    font=("Arial", 12),
                    bg=self.colors["card"],
                    fg=self.colors["text"],
                    width=10,
                    anchor='e').grid(row=0, column=2, padx=5)
            
            # Remaining amount
            remaining_color = "red" if remaining < 0 else self.colors["text"]
            tk.Label(row_frame, 
                    text=f"Rs{remaining:.2f}", 
                    font=("Arial", 12),
                    bg=self.colors["card"],
                    fg=remaining_color,
                    width=10,
                    anchor='e').grid(row=0, column=3, padx=5)
            
            # Percentage
            percentage = (budget_amount / total_budget * 100) if total_budget > 0 else 0
            tk.Label(row_frame, 
                    text=f"{percentage:.1f}%", 
                    font=("Arial", 12),
                    bg=self.colors["card"],
                    fg=self.colors["text"],
                    width=10,
                    anchor='e').grid(row=0, column=4, padx=5)
            
            # Separator
            tk.Frame(self.table_frame, 
                    height=1, 
                    bg="#f0f0f0").pack(fill=tk.X, padx=10, pady=0)
            
            row_index += 1
            
        # Total row
        total_row = tk.Frame(self.table_frame, bg=self.colors["card"])
        total_row.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(total_row, 
                text="Total", 
                font=("Arial", 13, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"],
                width=15,
                anchor='w').grid(row=0, column=0, padx=5)
        
        tk.Label(total_row, 
                text=f"Rs{total_budget:.2f}", 
                font=("Arial", 13, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"],
                width=10,
                anchor='e').grid(row=0, column=1, padx=5)
        
        tk.Label(total_row, 
                text=f"Rs{total_spent:.2f}", 
                font=("Arial", 13, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"],
                width=10,
                anchor='e').grid(row=0, column=2, padx=5)
        
        remaining_color = "red" if total_remaining < 0 else self.colors["text"]
        tk.Label(total_row, 
                text=f"Rs{total_remaining:.2f}", 
                font=("Arial", 13, "bold"),
                bg=self.colors["card"],
                fg=remaining_color,
                width=10,
                anchor='e').grid(row=0, column=3, padx=5)
        
        tk.Label(total_row, 
                text="100%", 
                font=("Arial", 13, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"],
                width=10,
                anchor='e').grid(row=0, column=4, padx=5)
        
        # Update summary
        self.total_budget_var.set(f"Rs{total_budget:.2f}")
        self.total_spent_var.set(f"Rs{total_spent:.2f}")
        self.total_remaining_var.set(f"Rs{total_remaining:.2f}")
        
        if total_remaining < 0:
            self.total_remaining_label.config(fg="red")
        else:
            self.total_remaining_label.config(fg=self.colors["text"])
        
        self.add_budget_progress(total_budget, total_spent, total_remaining)
        
        # Update canvas scroll region
        self.table_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)  # Scroll to top

    def add_budget_progress(self, total_budget, total_spent, total_remaining):
        """Add a compact budget progress visualization"""
        progress_frame = tk.Frame(self.table_frame, bg=self.colors["card"], pady=5)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)
        
        tk.Label(progress_frame, 
                text="📊 Budget Progress Dashboard", 
                font=("Arial", 14, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(anchor=tk.W, pady=(0, 5))
        
        # Create a canvas for the progress visualization
        canvas_width = 700
        canvas_height = 120  # Reduced height
        canvas = tk.Canvas(progress_frame, bg=self.colors["card"], 
                        width=canvas_width, height=canvas_height, 
                        highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Calculate percentages
        if total_budget > 0:
            spent_percent = (total_spent / total_budget) * 100
            remaining_percent = (total_remaining / total_budget) * 100 if total_remaining > 0 else 0
            overspent_percent = abs((total_remaining / total_budget) * 100) if total_remaining < 0 else 0
        else:
            spent_percent = 0
            remaining_percent = 0
            overspent_percent = 0
        
        # Draw main progress bar - more compact
        bar_height = 30  # Thinner bar
        bar_y = 10  # Higher up
        bar_width = 600
        bar_x = (canvas_width - bar_width) // 2
        
        # Total budget bar (gray background)
        canvas.create_rectangle(bar_x, bar_y, bar_x + bar_width, bar_y + bar_height, 
                            fill="#e0e0e0", outline="")
        
        # Spent portion (green)
        spent_width = (spent_percent / 100) * bar_width
        canvas.create_rectangle(bar_x, bar_y, bar_x + spent_width, bar_y + bar_height, 
                            fill=self.colors["secondary"], outline="")
        
        # Remaining portion (blue) if positive
        if total_remaining > 0:
            remaining_width = (remaining_percent / 100) * bar_width
            canvas.create_rectangle(bar_x + spent_width, bar_y, 
                                bar_x + spent_width + remaining_width, bar_y + bar_height, 
                                fill=self.colors["primary"], outline="")
        
        # Overspent portion (red) if negative
        if total_remaining < 0:
            overspent_width = (overspent_percent / 100) * bar_width
            canvas.create_rectangle(bar_x + spent_width, bar_y, 
                                bar_x + spent_width + overspent_width, bar_y + bar_height, 
                                fill=self.colors["accent"], outline="")
        
        # Add value labels on the bar
        middle_y = bar_y + bar_height // 2
        
        if total_remaining >= 0:
            # Spent label
            if spent_width > 80:
                canvas.create_text(bar_x + spent_width // 2, middle_y, 
                                text=f"Rs{total_spent:.0f}", 
                                font=("Arial", 8, "bold"), 
                                fill="white")
            
            # Remaining label
            if remaining_width > 80:
                canvas.create_text(bar_x + spent_width + remaining_width // 2, middle_y, 
                                text=f"Rs{total_remaining:.0f}", 
                                font=("Arial", 8, "bold"), 
                                fill="white")
        else:
            # Spent label
            if spent_width > 80:
                canvas.create_text(bar_x + spent_width // 2, middle_y, 
                                text=f"Rs{total_spent:.0f}", 
                                font=("Arial", 8, "bold"), 
                                fill="white")
            
            # Overspent label
            if overspent_width > 80:
                canvas.create_text(bar_x + spent_width + overspent_width // 2, middle_y, 
                                text=f"-Rs{abs(total_remaining):.0f}", 
                                font=("Arial", 8, "bold"), 
                                fill="white")
        
        # Add end markers
        canvas.create_text(bar_x, bar_y + bar_height + 2, 
                        text="0", 
                        font=("Arial", 8), 
                        anchor=tk.N)
        
        canvas.create_text(bar_x + bar_width, bar_y + bar_height + 2, 
                        text=f"Rs{total_budget:.0f}", 
                        font=("Arial", 8), 
                        anchor=tk.N)
        
        # Status message (inline with icon)
        status_frame = tk.Frame(progress_frame, bg=self.colors["card"])
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        if total_remaining > 0:
            status_icon = "✅"
            status_text = f"Good financial health! Rs{total_remaining:.0f} remaining ({remaining_percent:.0f}%)"
            status_color = self.colors["secondary"]
        elif total_remaining == 0:
            status_icon = "⚠️"
            status_text = "Budget spent exactly. Consider saving more."
            status_color = self.colors["warning"]
        else:
            status_icon = "❌"
            status_text = f"Overspent by Rs{abs(total_remaining):.0f} ({overspent_percent:.0f}%)"
            status_color = self.colors["accent"]
        
        tk.Label(status_frame, 
                text=status_icon, 
                font=("Arial", 12), 
                bg=self.colors["card"],
                fg=status_color).pack(side=tk.LEFT, padx=2)
        
        tk.Label(status_frame, 
                text=status_text, 
                font=("Arial", 12),
                bg=self.colors["card"],
                fg=status_color).pack(side=tk.LEFT)
        
        # Tips section with tighter spacing
        tips = []
        if total_remaining > (total_budget * 0.2):
            tips.append("💡 Consider investing remaining funds")
            tips.append("💡 Increase savings goals next month")
        elif total_remaining > 0:
            tips.append("💡 Review spending for saving opportunities")
        elif total_remaining < 0:
            tips.append("💡 Identify categories to cut spending")
            tips.append("💡 Set up spending alerts")
        
        if tips:
            tips_frame = tk.Frame(progress_frame, bg=self.colors["card"])
            tips_frame.pack(fill=tk.X, pady=(5, 0))
            
            for tip in tips:
                tk.Label(tips_frame, 
                        text=tip, 
                        font=("Arial", 10),
                        bg=self.colors["card"],
                        fg=self.colors["text"]).pack(anchor=tk.W, pady=0)

    def get_icon_for_category(self, category):
        icon_map = {
            "Housing": "🏠",
            "Food": "🍔",
            "Transportation": "🚗",
            "Utilities": "💡",
            "Entertainment": "🎬",
            "Shopping": "🛍️",
            "Healthcare": "🏥",
            "Personal Care": "👤"
        }
        return icon_map.get(category, "📊")
    
    def refresh_combobox_values(self, event=None):
        """Refresh the combobox values when clicked"""
        self.data = db_instance.load_data()
        self.category_combobox['values'] = self.data.get("categories", [])


    def on_category_update(self):
        """Callback for when categories are updated"""
        self.data = db_instance.load_data()
        self.category_combobox['values'] = self.data.get("categories", [])
        self.update_budget_table()    

    def on_data_updated(self):
        """Callback when database changes"""
        self.data = db_instance.load_data()
        self.update_budget_table()
        if hasattr(self, 'category_combobox'):
            self.category_combobox['values'] = self.data.get("categories", [])
            
    def set_budget(self):
        category = self.category_combobox.get()
        budget_text = self.budget_entry.get().strip()
        
        if not category:
            messagebox.showerror("Error", "Please select a category", parent=self.frame)
            return
            
        if not budget_text:
            messagebox.showerror("Error", "Please enter a budget amount", parent=self.frame)
            return
            
        try:
            budget_amount = float(budget_text)
            if budget_amount < 0:
                messagebox.showerror("Error", "Budget amount cannot be negative", parent=self.frame)
                return
        except ValueError:
            messagebox.showerror("Error", "Budget amount must be a number", parent=self.frame)
            return
            
        if "budget" not in self.data:
            self.data["budget"] = {}
            
        self.data["budget"][category] = budget_amount
        db_instance.save_data(self.data)
        
        self.update_budget_table()
        self.budget_entry.delete(0, tk.END)
        
        # Show success message
        success = tk.Toplevel(self.frame)
        success.title("Success")
        success.geometry("350x180")
        success.configure(bg=self.colors["secondary"])
        success.resizable(False, False)
        
        tk.Label(success, 
                text="✓", 
                font=("Arial", 28),
                bg=self.colors["secondary"],
                fg="white").pack(pady=(20, 5))
        
        tk.Label(success, 
                text=f"Budget for {category}\nset to Rs{budget_amount:.2f}", 
                font=("Arial", 14),
                bg=self.colors["secondary"],
                fg="white").pack()
        
        tk.Button(success, 
                 text="OK", 
                 command=success.destroy,
                 bg="white",
                 fg=self.colors["secondary"],
                 bd=0,
                 relief=tk.FLAT,
                 padx=25,
                 pady=8,
                 font=("Arial", 12)).pack(pady=10)

    def edit_budget(self, category):
        current_budget = self.data.get("budget", {}).get(category, 0)
        
        edit_win = tk.Toplevel(self.frame)
        edit_win.title("Edit Budget")
        edit_win.geometry("400x250")
        edit_win.configure(bg=self.colors["card"])
        edit_win.resizable(False, False)
        
        # Center the window
        x = self.frame.winfo_rootx() + self.frame.winfo_width() // 2 - 200
        y = self.frame.winfo_rooty() + self.frame.winfo_height() // 2 - 125
        edit_win.geometry(f"+{x}+{y}")
        
        tk.Label(edit_win, 
                text=f"Edit {category} Budget", 
                font=("Arial", 16, "bold"),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(pady=(20, 15))
        
        entry_frame = tk.Frame(edit_win, bg=self.colors["card"])
        entry_frame.pack(pady=15)
        
        tk.Label(entry_frame, 
                text="Amount (Rs):", 
                font=("Arial", 13),
                bg=self.colors["card"],
                fg=self.colors["text"]).pack(side=tk.LEFT)
        
        amount_entry = ttk.Entry(entry_frame, font=("Arial", 14), width=15)
        amount_entry.pack(side=tk.LEFT, padx=15)
        amount_entry.insert(0, current_budget)
        
        btn_frame = tk.Frame(edit_win, bg=self.colors["card"])
        btn_frame.pack(pady=25)
        
        tk.Button(btn_frame, 
                 text="Cancel", 
                 command=edit_win.destroy,
                 bg="#e0e0e0",
                 fg=self.colors["text"],
                 bd=0,
                 relief=tk.FLAT,
                 padx=25,
                 pady=8,
                 font=("Arial", 12)).pack(side=tk.LEFT, padx=15)
        
        tk.Button(btn_frame, 
                 text="Save", 
                 command=lambda: self.save_budget_edit(category, amount_entry.get(), edit_win),
                 bg=self.colors["primary"],
                 fg="white",
                 bd=0,
                 relief=tk.FLAT,
                 padx=25,
                 pady=8,
                 font=("Arial", 12)).pack(side=tk.LEFT)
        
        edit_win.transient(self.frame)
        edit_win.grab_set()
        self.frame.wait_window(edit_win)

    def save_budget_edit(self, category, amount_str, window):
        try:
            new_budget = float(amount_str)
            if new_budget < 0:
                messagebox.showerror("Error", "Budget amount cannot be negative", parent=window)
                return
                
            if "budget" not in self.data:
                self.data["budget"] = {}
                
            self.data["budget"][category] = new_budget
            db_instance.save_data(self.data)
            self.update_budget_table()
            window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number", parent=window)

    def show_chart_view(self):
        # Chart visualization window
        chart_win = tk.Toplevel(self.frame)
        chart_win.title("Advanced Budget Visualization")
        chart_win.geometry("1000x700")  # Larger window
        chart_win.configure(bg=self.colors["background"])
        
        # Header
        header = tk.Frame(chart_win, bg=self.colors["primary"])
        header.pack(fill=tk.X)
        
        tk.Label(header, 
                text="Advanced Budget Visualization Dashboard", 
                font=("Arial", 18, "bold"),
                fg="white", 
                bg=self.colors["primary"],
                padx=20,
                pady=15).pack(side=tk.LEFT)
        
        # Add a visual chart icon
        chart_icon = tk.Label(header, 
                             text="📊", 
                             font=("Arial", 28),
                             bg=self.colors["primary"],
                             fg="white",
                             padx=20)
        chart_icon.pack(side=tk.RIGHT)
        
        # Main chart area
        canvas = tk.Canvas(chart_win, bg="white", width=960, height=600, highlightthickness=0)
        canvas.pack(pady=20)
        
        if "budget" in self.data and self.data["budget"]:
            categories = list(self.data["budget"].keys())
            max_budget = max(self.data["budget"].values())
            
            # Calculate spending (using demo data if no transactions)
            spent = {}
            transactions = self.data.get("transactions", [])
            
            if transactions:
                for transaction in transactions:
                    if transaction.get("type") == "expenses":  # Only count expenses
                        category = transaction.get("category", "")
                        if category in categories:
                            spent[category] = spent.get(category, 0) + transaction.get("expenses.amount", 0)
            else:
                demo_spending = {
                    "Housing": 1200,
                    "Food": 450,
                    "Transportation": 350,
                    "Utilities": 280,
                    "Entertainment": 180,
                    "Shopping": 420,
                    "Healthcare": 50,
                    "Personal Care": 85
                }
                for category in categories:
                    spent[category] = demo_spending.get(category, 0)
            
            # Chart dimensions
            chart_width = 900
            chart_height = 450
            chart_x = 50
            chart_y = 50
            bar_width = 40  # Wider bars
            group_width = bar_width * 2 + 20  # Space for budget and spent bars
            spacing = 30
            max_bar_height = 400
            scale = max_bar_height / max_budget
            
            # Draw chart title
            canvas.create_text(chart_x + chart_width // 2, 20, 
                             text="Budget vs Actual Spending by Category", 
                             font=("Arial", 16, "bold"))
            
            # Draw axes
            canvas.create_line(chart_x, chart_y + chart_height, 
                             chart_x + chart_width, chart_y + chart_height, 
                             width=2)  # X-axis
            canvas.create_line(chart_x, chart_y, 
                             chart_x, chart_y + chart_height, 
                             width=2)  # Y-axis
            
            # Draw Y-axis labels and grid lines
            for i in range(0, int(max_budget) + 1, int(max_budget/5)):
                y = chart_y + chart_height - (i * scale)
                canvas.create_line(chart_x, y, chart_x + chart_width, y, 
                                 fill="#f0f0f0", dash=(2, 2))  # Grid line
                canvas.create_line(chart_x - 5, y, chart_x, y, width=1)  # Tick mark
                canvas.create_text(chart_x - 10, y, 
                                 text=f"Rs{i}", 
                                 font=("Arial", 10), 
                                 anchor=tk.E)
            
            # Draw bars and labels
            for i, category in enumerate(categories):
                group_x = chart_x + i * (group_width + spacing)
                
                # Budget bar
                budget_height = self.data["budget"][category] * scale
                budget_x = group_x
                canvas.create_rectangle(budget_x, chart_y + chart_height - budget_height, 
                                      budget_x + bar_width, chart_y + chart_height, 
                                      fill=self.color_mapping["Blue"],
                                      outline="")
                
                # Budget value label
                if budget_height > 20:  # Only show if there's enough space
                    canvas.create_text(budget_x + bar_width // 2, 
                                     chart_y + chart_height - budget_height - 10, 
                                     text=f"Budget\nRs{self.data['budget'][category]:.2f}", 
                                     font=("Arial", 9), 
                                     anchor=tk.S)
                
                # Spent bar
                spent_height = spent.get(category, 0) * scale
                spent_x = group_x + bar_width + 10
                canvas.create_rectangle(spent_x, chart_y + chart_height - spent_height, 
                                      spent_x + bar_width, chart_y + chart_height, 
                                      fill=self.color_mapping["Green"],
                                      outline="")
                
                # Spent value label
                if spent_height > 20:
                    canvas.create_text(spent_x + bar_width // 2, 
                                     chart_y + chart_height - spent_height - 10, 
                                     text=f"Spent\nRs{spent.get(category, 0):.2f}", 
                                     font=("Arial", 9), 
                                     anchor=tk.S)
                
                # Category label
                canvas.create_text(group_x + group_width // 2, 
                                 chart_y + chart_height + 15, 
                                 text=category, 
                                 font=("Arial", 10), 
                                 anchor=tk.N)
            
            # Add legend
            legend_x = chart_x + chart_width - 150
            legend_y = chart_y + 20
            
            canvas.create_rectangle(legend_x, legend_y, legend_x + 20, legend_y + 20, 
                                  fill=self.color_mapping["Blue"], outline="")
            canvas.create_text(legend_x + 30, legend_y + 10, 
                             text="Budget", 
                             font=("Arial", 11), 
                             anchor=tk.W)
            
            canvas.create_rectangle(legend_x, legend_y + 30, legend_x + 20, legend_y + 50, 
                                  fill=self.color_mapping["Green"], outline="")
            canvas.create_text(legend_x + 30, legend_y + 40, 
                             text="Spent", 
                             font=("Arial", 11), 
                             anchor=tk.W)
            
            # Add summary section
            summary_frame = tk.Frame(chart_win, bg=self.colors["background"])
            summary_frame.pack(fill=tk.X, pady=(0, 20))
            
            total_budget = sum(self.data["budget"].values())
            total_spent = sum(spent.values())
            remaining = total_budget - total_spent
            
            summary_text = f"Total Budget: Rs{total_budget:,.2f} | Total Spent: Rs{total_spent:,.2f} | "
            summary_text += f"Remaining: Rs{remaining:,.2f}" if remaining >= 0 else f"Overspent: Rs{abs(remaining):,.2f}"
            
            tk.Label(summary_frame, 
                    text=summary_text, 
                    font=("Arial", 12, "bold"),
                    bg=self.colors["background"],
                    fg=self.colors["text"]).pack()
            
            # Add analysis
            analysis_frame = tk.Frame(chart_win, bg=self.colors["background"])
            analysis_frame.pack(fill=tk.X, padx=20)
            
            if remaining > 0:
                analysis_text = f"✅ You have {remaining/total_budget*100:.1f}% of your budget remaining"
                analysis_color = self.colors["secondary"]
            elif remaining == 0:
                analysis_text = "⚠️ You've spent exactly your budget amount"
                analysis_color = self.colors["warning"]
            else:
                analysis_text = f"❌ You've overspent by {abs(remaining)/total_budget*100:.1f}% of your budget"
                analysis_color = self.colors["accent"]
            
            tk.Label(analysis_frame, 
                    text=analysis_text, 
                    font=("Arial", 12),
                    bg=self.colors["background"],
                    fg=analysis_color).pack()
            
            # Add top spending categories
            if spent:
                top_categories = sorted(spent.items(), key=lambda x: x[1], reverse=True)[:3]
                top_frame = tk.Frame(chart_win, bg=self.colors["background"])
                top_frame.pack(fill=tk.X, padx=20, pady=10)
                
                tk.Label(top_frame, 
                        text="Top Spending Categories:", 
                        font=("Arial", 12, "bold"),
                        bg=self.colors["background"],
                        fg=self.colors["text"]).pack(anchor=tk.W)
                
                for i, (category, amount) in enumerate(top_categories, 1):
                    percent = (amount / total_spent * 100) if total_spent > 0 else 0
                    tk.Label(top_frame, 
                            text=f"{i}. {category}: Rs{amount:,.2f} ({percent:.1f}% of spending)", 
                            font=("Arial", 11),
                            bg=self.colors["background"],
                            fg=self.colors["text"]).pack(anchor=tk.W)
        else:
            # No data message
            canvas.create_text(chart_x + chart_width // 2, chart_y + chart_height // 2, 
                             text="No budget data available.\nPlease set budgets to see visualizations.", 
                             font=("Arial", 14), 
                             justify=tk.CENTER)