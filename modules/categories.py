import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from database.core import db_instance

class CategoriesWindow:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, width=1200, height=800)
        self.data = db_instance.load_data()
        self.notebook = notebook
        
        # Modern color scheme
        self.default_colors = ["#4899d4", "#e74c3c", "#2ecc71", "#f1c40f", 
                             "#9b59b6", "#e67e22", "#95a5a6", "#1abc9c", "#e91e63"]
        
        # Configure styles
        self.configure_styles()

        # Header with improved gradient background
        header_frame = tk.Frame(self.frame, bg="#1e2a3a", height=80)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, 
                             text="💰 Expense Categories", 
                             font=("Arial", 24, "bold"), 
                             fg="white", 
                             bg="#1e2a3a",
                             padx=20,
                             pady=15)
        title_label.pack(side=tk.LEFT)
        
        # Main container with shadow effect
        main_container = tk.Frame(self.frame, bg="#f5f7fa", padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Category List Container (Left Side) with subtle shadow
        list_card = tk.Frame(main_container, bg="white", bd=0, highlightthickness=1,
                            highlightbackground="#e0e0e0", relief=tk.RIDGE)
        list_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Card header with improved color
        list_header = tk.Frame(list_card, bg="#4899d4")
        list_header.pack(fill=tk.X)
        
        tk.Label(list_header, 
                text="📋 Your Categories", 
                font=("Arial", 16, "bold"), 
                fg="white", 
                bg="#4899d4",
                padx=15,
                pady=10).pack(side=tk.LEFT)

        # Add search functionality
        search_frame = tk.Frame(list_header, bg="#4899d4")
        search_frame.pack(side=tk.RIGHT, padx=10)
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 12), width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_categories)
        
        search_btn = tk.Button(search_frame, 
                             text="🔍", 
                             command=self.filter_categories,
                             bg="#3a87c4",
                             fg="white",
                             bd=0,
                             relief=tk.FLAT,
                             font=("Arial", 12))
        search_btn.pack(side=tk.LEFT)

        # Content area with scrollable list
        list_content = tk.Frame(list_card, bg="white")
        list_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas for Scrollbar
        self.canvas = tk.Canvas(list_content, bg="white", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_content, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.category_container = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.category_container, anchor=tk.NW, width=self.canvas.winfo_width())
        
        # Add New Category Container (Right Side) with adjusted sizing
        add_card = tk.Frame(main_container, bg="white", bd=0, highlightthickness=1,
                           highlightbackground="#e0e0e0", relief=tk.RIDGE, width=350)
        add_card.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Card header with improved color
        add_header = tk.Frame(add_card, bg="#2ecc71")
        add_header.pack(fill=tk.X)
        
        tk.Label(add_header, 
                text="➕ Add New Category", 
                font=("Arial", 16, "bold"), 
                fg="white", 
                bg="#2ecc71",
                padx=15,
                pady=10).pack(side=tk.LEFT)

        # Content area with form elements - now with better spacing
        add_content = tk.Frame(add_card, bg="white", padx=20, pady=15)
        add_content.pack(fill=tk.BOTH, expand=True)

        # Category Name with adjusted spacing
        tk.Label(add_content, 
                text="Category Name:", 
                font=("Arial", 12),
                bg="white",
                fg="#2c3e50").pack(anchor=tk.W, pady=(0, 5))
        
        self.category_entry = ttk.Entry(add_content, font=("Arial", 12))
        self.category_entry.pack(fill=tk.X, pady=(0, 10))

        # Icon Selection with compact layout
        tk.Label(add_content, 
                text="Select Icon:", 
                font=("Arial", 12),
                bg="white",
                fg="#2c3e50").pack(anchor=tk.W, pady=(0, 5))
        
        icon_frame = tk.Frame(add_content, bg="white")
        icon_frame.pack(fill=tk.X, pady=(0, 10))
        
        popular_icons = ["🏠", "🍔", "🚗", "💡", "🛍️", "🎬", "🏥", "👤", "✈️", "🎓", "🏋️", "🐶"]
        self.selected_icon = tk.StringVar(value="🏠")
        
        # More compact icon grid (4x3)
        for i, icon in enumerate(popular_icons[:12]):
            btn = tk.Radiobutton(icon_frame, 
                                text=icon, 
                                font=("Arial", 14),
                                variable=self.selected_icon, 
                                value=icon,
                                bg="white",
                                selectcolor="#f0f7ff",
                                indicatoron=0,
                                width=2,
                                relief=tk.RAISED)
            btn.grid(row=i//4, column=i%4, padx=3, pady=3)

        # Color Selection with more compact layout
        tk.Label(add_content, 
                text="Select Color:", 
                font=("Arial", 12),
                bg="white",
                fg="#2c3e50").pack(anchor=tk.W, pady=(0, 5))
        
        color_frame = tk.Frame(add_content, bg="white")
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Color buttons with smaller size
        self.selected_color = tk.StringVar(value="#4899d4")
        self.color_buttons = []
        
        for i, color in enumerate(self.default_colors):
            btn = tk.Button(color_frame, 
                          bg=color,
                          activebackground=color,
                          relief=tk.SUNKEN if color == "#4899d4" else tk.RAISED,
                          width=3,
                          height=1,
                          command=lambda c=color: self.select_color(c))
            btn.grid(row=i//5, column=i%5, padx=4, pady=4)
            self.color_buttons.append(btn)
        
        # Custom color button with smaller size
        custom_btn = tk.Button(color_frame, 
                             text="+", 
                             font=("Arial", 10),
                             command=self.choose_custom_color,
                             width=3,
                             height=1,
                             bg="#f0f0f0",
                             activebackground="#e0e0e0")
        custom_btn.grid(row=1, column=4, padx=4, pady=4)

        # Add space before the button
        tk.Frame(add_content, height=15, bg="white").pack(fill=tk.X, pady=(5, 0))

        # Add Category button - now with proper visibility
        self.add_btn = tk.Button(add_content, 
                          text="➕ Add Category", 
                          command=self.add_category,
                          bg="#2ecc71",
                          fg="white",
                          font=("Arial", 14),
                          bd=0,
                          padx=15,
                          pady=10)
        self.add_btn.pack(fill=tk.X, pady=(5, 0))
        
        # Add hover effect
        self.add_btn.bind("<Enter>", lambda e: self.add_btn.config(bg="#27ae60"))
        self.add_btn.bind("<Leave>", lambda e: self.add_btn.config(bg="#2ecc71"))

        # Initialize category list
        self.update_category_list()

    def filter_categories(self, event=None):
        """Filter categories based on search term"""
        search_term = self.search_entry.get().lower()
        for widget in self.category_container.winfo_children():
            if hasattr(widget, 'category_name'):
                category_name = widget.category_name.lower()
                if search_term in category_name:
                    widget.pack(fill=tk.X, pady=4, padx=5)
                else:
                    widget.pack_forget()
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def select_color(self, color):
        self.selected_color.set(color)
        for btn in self.color_buttons:
            btn.config(relief=tk.RAISED)
        for btn in self.color_buttons:
            if btn.cget("bg") == color:
                btn.config(relief=tk.SUNKEN)

    def choose_custom_color(self):
        color = colorchooser.askcolor(title="Choose a color")[1]
        if color:
            self.selected_color.set(color)
            for btn in self.color_buttons:
                btn.config(relief=tk.RAISED)

    def configure_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background="#f5f7fa")
        style.configure("TLabel", background="#f5f7fa", foreground="#2c3e50")
        style.configure("TEntry", font=("Arial", 12), padding=8)
        style.configure("TScrollbar", gripcount=0, background="#f0f0f0", troughcolor="#ffffff")

    def update_category_list(self):
        # Clear existing widgets
        for widget in self.category_container.winfo_children():
            widget.destroy()

        if not self.data.get("categories", []):
            empty_frame = tk.Frame(self.category_container, bg="white", height=100)
            empty_frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(empty_frame, 
                    text="No categories yet!\nAdd your first category to get started.", 
                    font=("Arial", 14), 
                    bg="white",
                    fg="#95a5a6").pack(expand=True)
            return

        # Create smaller category items
        for i, category in enumerate(self.data["categories"]):
            # Get color from category data or default to a color from the palette
            category_data = self.data.get("category_data", {}).get(category, {})
            color = category_data.get("color", self.default_colors[i % len(self.default_colors)])
            icon = category_data.get("icon", "🔹")
            
            # Category card with subtle shadow effect
            category_frame = tk.Frame(self.category_container, 
                                    bg="white",
                                    bd=0,
                                    highlightthickness=1,
                                    highlightbackground="#e0e0e0",
                                    height=65)
            category_frame.pack(fill=tk.X, pady=4, padx=5)
            category_frame.pack_propagate(False)
            category_frame.category_name = category  # Store category name for filtering
            
            # Content frame with better padding
            content_frame = tk.Frame(category_frame, bg="white")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
            
            # Left side - Icon and name
            left_frame = tk.Frame(content_frame, bg="white")
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Icon with color - rounded by using a label with colored background
            icon_frame = tk.Frame(left_frame, bg=color, width=36, height=36)
            icon_frame.pack_propagate(False)
            icon_frame.pack(side=tk.LEFT, padx=(0, 12))
            
            tk.Label(icon_frame, 
                    text=icon, 
                    font=("Arial", 16),
                    bg=color,
                    fg="white").pack(expand=True)
            
            # Category name with color indicator
            name_frame = tk.Frame(left_frame, bg="white")
            name_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)
            
            tk.Label(name_frame, 
                    text=category, 
                    font=("Arial", 13, "bold"),
                    bg="white",
                    anchor="w").pack(side=tk.TOP, anchor="w")
                    
            # Color indicator below name
            tk.Label(name_frame, 
                    text=color, 
                    font=("Arial", 10),
                    fg="#666666",
                    bg="white",
                    anchor="w").pack(side=tk.TOP, anchor="w")
            
            # Right side - Action buttons with improved styling
            button_frame = tk.Frame(content_frame, bg="white")
            button_frame.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Edit button with better styling
           
            
            # Add hover effect
           

            # Delete button with better styling
            delete_btn = tk.Button(button_frame, 
                                 text="🗑️", 
                                 command=lambda c=category: self.delete_category(c),
                                 bg="#e74c3c",
                                 fg="white",
                                 bd=0,
                                 font=("Arial", 11),
                                 padx=10,
                                 pady=3)
            delete_btn.pack(side=tk.LEFT, padx=4)
            
            # Add hover effect
            delete_btn.bind("<Enter>", lambda e, btn=delete_btn: btn.config(bg="#c0392b"))
            delete_btn.bind("<Leave>", lambda e, btn=delete_btn: btn.config(bg="#e74c3c"))

        # Update scroll region
        self.category_container.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Adjust canvas width
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(
            self.canvas.find_withtag('all')[0] if self.canvas.find_withtag('all') else 0, 
            width=e.width))

    def add_category(self):
        category = self.category_entry.get().strip()
        if not category:
            messagebox.showerror("Error", "Category name cannot be empty.", parent=self.frame)
            return
            
        if category in self.data.get("categories", []):
            messagebox.showerror("Error", "Category already exists.", parent=self.frame)
            return
            
        try:
            if "categories" not in self.data:
                self.data["categories"] = []
                
            if "category_data" not in self.data:
                self.data["category_data"] = {}
                
            self.data["categories"].append(category)
            self.data["category_data"][category] = {
                "color": self.selected_color.get(),
                "icon": self.selected_icon.get()
            }
            
            # Save data
            db_instance.save_data(self.data)
            
            # Refresh the category list
            self.update_category_list()
            self.category_entry.delete(0, tk.END)
            
            # Notify other windows
            self.notify_category_update()
            
            messagebox.showinfo("Success", f"Category '{category}' added!", parent=self.frame)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}", parent=self.frame)

    def notify_category_update(self):
        # Get all windows that might need updating
        for child in self.notebook.winfo_children():
            if hasattr(child, 'on_category_update'):
                child.on_category_update()

    def delete_category(self, category):
        confirm = messagebox.askyesno(
            "Confirm Deletion", 
            f"Are you sure you want to delete '{category}'?",
            parent=self.frame
        )
        
        if confirm:
            try:
                # Remove from categories list
                self.data["categories"].remove(category)
                
                # Remove from category_data if it exists
                if "category_data" in self.data and category in self.data["category_data"]:
                    del self.data["category_data"][category]
                
                db_instance.save_data(self.data)
                self.update_category_list()
                messagebox.showinfo("Success", "Category deleted successfully!", parent=self.frame)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete category: {str(e)}", parent=self.frame)