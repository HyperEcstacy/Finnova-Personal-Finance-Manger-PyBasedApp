import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database.core import db_instance
from modules.utils import get_current_timestamp
import webbrowser
import random

class TransactionWindow:
    def __init__(self, notebook):
        # Main frame with fixed dimensions
        self.frame = ttk.Frame(notebook, width=1200, height=800, style='Main.TFrame')
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.notebook = notebook  
        # Create content frame immediately
        self.content_frame = tk.Frame(self.frame, bg='#f5f7fa')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        db_instance.register_callback(self.on_data_updated)
        # Configure styles
        self.configure_styles()

        # Create main view
        self.create_main_view()

    def configure_styles(self):
        """Configure all custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main styles
        style.configure('Main.TFrame', background='#f5f7fa')
        
        # Button styles
        style.configure('Transaction.TButton', 
                      font=('Montserrat', 16, 'bold'),
                      foreground='white',
                      padding=20,
                      borderwidth=0,
                      relief='flat')
        style.map('Transaction.TButton',
                 background=[('active', '#3a7ca5'), ('pressed', '#2f6690')],
                 relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Specific button styles
        style.configure('Expense.TButton', background='#ff6b6b')
        style.configure('Income.TButton', background='#51cf66')
        
        # Header styles
        style.configure('ContainerHeader.TFrame', 
                      background='#343a40', 
                      foreground='white')
        style.configure('ContainerHeader.TLabel', 
                      background='#343a40', 
                      foreground='white', 
                      font=('Montserrat', 18, 'bold'))
        
        # Form styles
        style.configure('Form.TFrame', background='#ffffff')
        style.configure('Form.TLabel', 
                      background='#ffffff', 
                      foreground='#495057',
                      font=('Open Sans', 12))

    def clear_content_frame(self):
        """Clear all widgets from the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def create_main_view(self):
        """Create the main view with transaction buttons"""
        self.clear_content_frame()

        # Main container with shadow
        self.main_container = tk.Frame(self.content_frame, bg='#f5f7fa')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.create_shadow(self.main_container, offset=4)

        # Header with gradient
        header_frame = tk.Frame(self.main_container, bg='#343a40', height=80)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, 
               text="TRANSACTIONS",
               bg='#343a40',
               fg='white',
               font=('Montserrat', 24, 'bold')
               ).place(relx=0.5, rely=0.5, anchor='center')

        # Create transaction buttons
        self.create_transaction_buttons()

    
    def create_shadow(self, widget, offset=3):
        """Create a subtle shadow effect"""
        shadow = tk.Frame(self.content_frame, bg='#adb5bd')
        shadow.place(in_=widget, x=offset, y=offset, 
                    relwidth=1, relheight=1, anchor='nw')
        shadow.lower(belowThis=widget)

    def create_transaction_buttons(self):
        """Create main transaction buttons"""
        button_container = tk.Frame(self.main_container, bg='#f5f7fa')
        button_container.pack(expand=True, pady=20)
        
        # Add decorative elements (just the separator line now)
        self.create_decorative_elements(button_container)

        # Button frame to center the buttons
        center_frame = tk.Frame(button_container, bg='#f5f7fa')
        center_frame.pack(expand=True)

        # Expense Button - made more compact
        expense_frame = tk.Frame(center_frame, bg='#f5f7fa')
        expense_frame.pack(pady=10)
        
        tk.Button(
            expense_frame,
            text="ADD EXPENSE",
            bg='#ff6b6b',
            fg='white',
            activebackground='#fa5252',
            font=('Montserrat', 16, 'bold'),
            bd=0,
            padx=30,
            pady=15,
            command=lambda: self.show_transaction_form('expense')
        ).pack(side=tk.LEFT)
        
        tk.Label(expense_frame, 
            text="💸", 
            bg='#f5f7fa',
            font=('Arial', 24)).pack(side=tk.LEFT, padx=10)

        # Income Button - made more compact
        income_frame = tk.Frame(center_frame, bg='#f5f7fa')
        income_frame.pack(pady=10)
        
        tk.Button(
            income_frame,
            text="ADD INCOME",
            bg='#51cf66',
            fg='white',
            activebackground='#40c057',
            font=('Montserrat', 16, 'bold'),
            bd=0,
            padx=30,
            pady=15,
            command=lambda: self.show_transaction_form('income')
        ).pack(side=tk.LEFT)
        
        tk.Label(income_frame, 
            text="💰", 
            bg='#f5f7fa',
            font=('Arial', 24)).pack(side=tk.LEFT, padx=10)

        # Add tips section with adjusted padding
        self.create_enhanced_tips_section()

    def create_decorative_elements(self, parent):
        """Add decorative UI elements"""
        tk.Frame(parent, bg='#dee2e6', height=2).pack(fill=tk.X, pady=20)

    def create_enhanced_tips_section(self):
        """Create the tips section with adjusted spacing"""
        tips_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        tips_frame.pack(fill=tk.X, pady=(10, 10), padx=50)
        
        # Header - made more compact
        header_frame = tk.Frame(tips_frame, bg='#f5f7fa')
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Frame(header_frame, bg='#51cf66', width=3, height=24).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(header_frame,
            text="💡 FINANCIAL TIPS",
            bg='#f5f7fa',
            fg='#343a40',
            font=('Montserrat', 14, 'bold')).pack(side=tk.LEFT)
        
        tk.Button(header_frame,
                text="MORE TIPS →",
                bg='#228be6',
                fg='white',
                activebackground='#1c7ed6',
                font=('Montserrat', 10, 'bold'),
                bd=0,
                padx=12,
                pady=3,
                command=lambda: webbrowser.open("https://finnova.in/")
                ).pack(side=tk.RIGHT)
        
        # Tips card - made more compact
        tips_card = tk.Frame(tips_frame,
                            bg='#ffffff',
                            bd=0,
                            highlightbackground='#dee2e6',
                            highlightthickness=1,
                            padx=12,
                            pady=12)
        tips_card.pack(fill=tk.X)
        self.create_shadow(tips_card, offset=2)
        
        # Random tips with tighter spacing
        tips = [
            "📌 Track daily expenses to identify spending patterns",
            "💡 Set aside 20% of income for savings automatically",
            "💰 Negotiate bills annually to reduce fixed expenses",
            "📊 Review spending weekly to stay on budget",
            "🛒 Use shopping lists to avoid impulse purchases"
        ]
        
        for tip in random.sample(tips, 3):
            tip_frame = tk.Frame(tips_card, bg='#ffffff')
            tip_frame.pack(fill=tk.X, pady=3)
            
            tk.Label(tip_frame, 
                text=tip.split()[0],
                bg='#ffffff',
                font=('Arial', 12)).pack(side=tk.LEFT, padx=(0, 8))
            
            tk.Label(tip_frame,
                text=' '.join(tip.split()[1:]),
                bg='#ffffff',
                fg='#495057',
                font=('Open Sans', 10),
                anchor='w').pack(side=tk.LEFT, fill=tk.X)

    def show_transaction_form(self, transaction_type):
        """Show the appropriate transaction form"""
        self.clear_content_frame()
        self.data = db_instance.load_data()

        # Back button
        back_button = tk.Button(
            self.content_frame, 
            text="◀ BACK TO MENU", 
            bg='#f5f7fa',
            fg='#495057',
            activebackground='#f5f7fa',
            activeforeground='#343a40',
            font=('Montserrat', 12, 'bold'),
            bd=0,
            command=self.create_main_view
        )
        back_button.pack(anchor='nw', padx=10, pady=10)

        if transaction_type == 'expense':
            self.create_expense_form()
        else:
            self.create_income_form()

    def create_expense_form(self):
        """Create expense form"""
        form_container = tk.Frame(
            self.content_frame,
            bg='#ffffff',
            bd=0,
            highlightbackground='#ff6b6b',
            highlightthickness=2,
            padx=25,
            pady=25
        )
        form_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        self.create_shadow(form_container, offset=4)

        # Header
        header_frame = tk.Frame(form_container, bg='#fff5f5')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        icon_frame = tk.Frame(header_frame, bg='#fff5f5')
        icon_frame.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(icon_frame, text="🛒", bg='#fff5f5', font=('Arial', 28)).pack()
        
        title_frame = tk.Frame(header_frame, bg='#fff5f5')
        title_frame.pack(side=tk.LEFT)
        tk.Label(title_frame,
               text="NEW EXPENSE",
               bg='#fff5f5',
               fg='#343a40',
               font=('Montserrat', 20, 'bold')
               ).pack(anchor='w')
        tk.Label(title_frame,
               text="Track where your money goes",
               bg='#fff5f5',
               fg='#868e96',
               font=('Open Sans', 12)
               ).pack(anchor='w')

        # Form content
        form_content = tk.Frame(form_container, bg='#ffffff')
        form_content.pack(fill=tk.BOTH, expand=True)
        field_container = tk.Frame(form_content, bg='#ffffff')
        field_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Amount field
        tk.Label(field_container,
               text="AMOUNT:",
               bg='#ffffff',
               fg='#495057',
               font=('Montserrat', 14, 'bold'),
               anchor='w'
               ).pack(fill=tk.X, pady=(10, 15))
        
        currency_frame = tk.Frame(field_container, bg='#ffffff')
        currency_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(currency_frame, text="₹", bg='#ffffff', fg='#495057', font=('Open Sans', 16)
               ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.expense_amount_entry = tk.Entry(
            currency_frame,
            font=('Open Sans', 14),
            bd=1,
            relief='flat',
            bg='#fff5f5',
            highlightcolor='#ff6b6b',
            highlightbackground='#ffc9c9',
            highlightthickness=1
        )
        self.expense_amount_entry.pack(fill=tk.X, expand=True)
        self.expense_amount_entry.bind('<FocusIn>', lambda e: self.expense_amount_entry.config(
            highlightbackground='#ff6b6b', highlightthickness=1))
        self.expense_amount_entry.bind('<FocusOut>', lambda e: self.expense_amount_entry.config(
            highlightbackground='#ffc9c9', highlightthickness=1))

        # Category field
        tk.Label(field_container,
               text="CATEGORY:",
               bg='#ffffff',
               fg='#495057',
               font=('Montserrat', 14, 'bold'),
               anchor='w'
               ).pack(fill=tk.X, pady=(15, 5))
        
        self.expense_category_var = tk.StringVar()
        self.expense_category_combobox = ttk.Combobox(
            field_container,
            textvariable=self.expense_category_var,
            values=self.data.get("categories", []),
            font=('Open Sans', 12),
            state='readonly'
        )
        self.expense_category_combobox.pack(fill=tk.X)
        self.expense_category_combobox.bind("<Button-1>", self.refresh_categories)

        # Description field
        tk.Label(field_container,
               text="DESCRIPTION:",
               bg='#ffffff',
               fg='#495057',
               font=('Montserrat', 14, 'bold'),
               anchor='w'
               ).pack(fill=tk.X, pady=(15, 5))
        
        self.expense_description_entry = tk.Entry(
            field_container,
            font=('Open Sans', 12),
            bd=1,
            relief='flat',
            bg='#fff5f5',
            highlightcolor='#ff6b6b',
            highlightbackground='#ffc9c9',
            highlightthickness=1
        )
        self.expense_description_entry.pack(fill=tk.X, pady=(0, 5))
        self.expense_description_entry.bind('<FocusIn>', lambda e: self.expense_description_entry.config(
            highlightbackground='#ff6b6b', highlightthickness=1))
        self.expense_description_entry.bind('<FocusOut>', lambda e: self.expense_description_entry.config(
            highlightbackground='#ffc9c9', highlightthickness=1))
        
        self.desc_counter = tk.Label(field_container,
                                   text="0/100 characters",
                                   bg='#ffffff',
                                   fg='#adb5bd',
                                   font=('Open Sans', 9),
                                   anchor='e')
        self.desc_counter.pack(fill=tk.X)
        self.expense_description_entry.bind('<KeyRelease>', self.update_desc_counter)

        # Buttons
        button_frame = tk.Frame(form_content, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Button(button_frame,
                text="CANCEL",
                bg='#f8f9fa',
                fg='#495057',
                activebackground='#e9ecef',
                font=('Montserrat', 12),
                bd=0,
                padx=25,
                pady=10,
                command=self.create_main_view
                ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame,
                text="RECORD EXPENSE",
                bg='#ff6b6b',
                fg='white',
                activebackground='#fa5252',
                font=('Montserrat', 12, 'bold'),
                bd=0,
                padx=25,
                pady=10,
                command=self.add_expense
                ).pack(side=tk.RIGHT)

    def create_income_form(self):
        """Create income form"""
        form_container = tk.Frame(
            self.content_frame,
            bg='#ffffff',
            bd=0,
            highlightbackground='#51cf66',
            highlightthickness=2,
            padx=25,
            pady=25
        )
        form_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        self.create_shadow(form_container, offset=4)

        # Header
        header_frame = tk.Frame(form_container, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        icon_frame = tk.Frame(header_frame, bg='#f8f9fa')
        icon_frame.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(icon_frame, text="💰", bg='#f8f9fa', font=('Arial', 28)).pack()
        
        title_frame = tk.Frame(header_frame, bg='#f8f9fa')
        title_frame.pack(side=tk.LEFT)
        tk.Label(title_frame,
               text="NEW INCOME",
               bg='#f8f9fa',
               fg='#343a40',
               font=('Montserrat', 20, 'bold')
               ).pack(anchor='w')
        tk.Label(title_frame,
               text="Record your money sources",
               bg='#f8f9fa',
               fg='#868e96',
               font=('Open Sans', 12)
               ).pack(anchor='w')

        # Form content
        form_content = tk.Frame(form_container, bg='#ffffff')
        form_content.pack(fill=tk.BOTH, expand=True)
        field_container = tk.Frame(form_content, bg='#ffffff')
        field_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Amount field
        tk.Label(field_container,
               text="AMOUNT:",
               bg='#ffffff',
               fg='#495057',
               font=('Montserrat', 14, 'bold'),
               anchor='w'
               ).pack(fill=tk.X, pady=(10, 15))
        
        currency_frame = tk.Frame(field_container, bg='#ffffff')
        currency_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(currency_frame, text="₹", bg='#ffffff', fg='#495057', font=('Open Sans', 16)
               ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.income_amount_entry = tk.Entry(
            currency_frame,
            font=('Open Sans', 14),
            bd=1,
            relief='flat',
            bg='#ebfbee',
            highlightcolor='#51cf66',
            highlightbackground='#d3f9d8',
            highlightthickness=1
        )
        self.income_amount_entry.pack(fill=tk.X, expand=True)
        self.income_amount_entry.bind('<FocusIn>', lambda e: self.income_amount_entry.config(
            highlightbackground='#51cf66', highlightthickness=1))
        self.income_amount_entry.bind('<FocusOut>', lambda e: self.income_amount_entry.config(
            highlightbackground='#d3f9d8', highlightthickness=1))

        # Description field
        tk.Label(field_container,
               text="DESCRIPTION:",
               bg='#ffffff',
               fg='#495057',
               font=('Montserrat', 14, 'bold'),
               anchor='w'
               ).pack(fill=tk.X, pady=(15, 5))
        
        self.income_description_entry = tk.Entry(
            field_container,
            font=('Open Sans', 12),
            bd=1,
            relief='flat',
            bg='#ebfbee',
            highlightcolor='#51cf66',
            highlightbackground='#d3f9d8',
            highlightthickness=1
        )
        self.income_description_entry.pack(fill=tk.X, pady=(0, 5))
        self.income_description_entry.bind('<FocusIn>', lambda e: self.income_description_entry.config(
            highlightbackground='#51cf66', highlightthickness=1))
        self.income_description_entry.bind('<FocusOut>', lambda e: self.income_description_entry.config(
            highlightbackground='#d3f9d8', highlightthickness=1))
        
        self.income_desc_counter = tk.Label(field_container,
                                          text="0/100 characters",
                                          bg='#ffffff',
                                          fg='#adb5bd',
                                          font=('Open Sans', 9),
                                          anchor='e')
        self.income_desc_counter.pack(fill=tk.X)
        self.income_description_entry.bind('<KeyRelease>', self.update_income_desc_counter)

        # Buttons
        button_frame = tk.Frame(form_content, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Button(button_frame,
                text="CANCEL",
                bg='#f8f9fa',
                fg='#495057',
                activebackground='#e9ecef',
                font=('Montserrat', 12),
                bd=0,
                padx=25,
                pady=10,
                command=self.create_main_view
                ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame,
                text="RECORD INCOME",
                bg='#51cf66',
                fg='white',
                activebackground='#40c057',
                font=('Montserrat', 12, 'bold'),
                bd=0,
                padx=25,
                pady=10,
                command=self.add_income
                ).pack(side=tk.RIGHT)

    def update_desc_counter(self, event):
        """Update expense description counter"""
        text = self.expense_description_entry.get()
        self.desc_counter.config(text=f"{len(text)}/100 characters")
        self.desc_counter.config(fg='#ff6b6b' if len(text) > 90 else '#adb5bd')

    def update_income_desc_counter(self, event):
        """Update income description counter"""
        text = self.income_description_entry.get()
        self.income_desc_counter.config(text=f"{len(text)}/100 characters")
        self.income_desc_counter.config(fg='#ff6b6b' if len(text) > 90 else '#adb5bd')

    def refresh_categories(self, event=None):
        """Always load fresh data before updating categories"""
        self.data = db_instance.load_data()
        categories = self.data.get("categories", [])
        
        if hasattr(self, 'expense_category_combobox'):
            self.expense_category_combobox['values'] = categories
            current = self.expense_category_combobox.get()
            if current and current in categories:
                self.expense_category_combobox.set(current)
            elif categories:
                self.expense_category_combobox.set(categories[0])

    def on_category_update(self):
        """Callback for when categories are updated"""
        self.data = db_instance.load_data()
        if hasattr(self, 'expense_category_combobox'):
            self.expense_category_combobox['values'] = self.data.get("categories", [])      

    def on_data_updated(self):
        """Callback when database changes"""
        self.data = db_instance.load_data()
        if hasattr(self, 'expense_category_combobox'):
            self.refresh_categories()              

    def add_expense(self):
        """Add new expense"""
        try:
            amount = float(self.expense_amount_entry.get())
            category = self.expense_category_var.get()
            description = self.expense_description_entry.get()

            if not category:
                messagebox.showerror("Error", "Please select a category!")
                return

            # Load fresh data
            self.data = db_instance.load_data()

            # Ensure categories list exists and contains this category
            if "categories" not in self.data:
                self.data["categories"] = []
            
            if category not in self.data["categories"]:
                self.data["categories"].append(category)
                db_instance.save_data(self.data)  # Save the updated categories

            # Rest of your existing expense adding logic...
            if "budget" in self.data and category in self.data["budget"]:
                budget_amount = self.data["budget"][category]
                if amount > budget_amount:
                    # Clear the input fields
                    self.expense_amount_entry.delete(0, tk.END)
                    self.expense_category_var.set('')
                    self.expense_description_entry.delete(0, tk.END)
                    
                    messagebox.showerror(
                        "Budget Exceeded", 
                        f"This expense exceeds the budget of Rs{budget_amount:.2f} for {category}!\n"
                        "Transaction not recorded."
                    )
                    return

            # Create transaction data
            transaction_data = {
                "timestamp": get_current_timestamp(),
                "amount": amount,
                "category": category,
                "description": description
            }

            # Add transaction without overwriting categories
            success = db_instance.add_transaction('expenses', transaction_data)

            if success:
                messagebox.showinfo("Success", "Expense added successfully!")
                
                # Clear entries after successful addition
                self.expense_amount_entry.delete(0, tk.END)
                self.expense_category_var.set('')
                self.expense_description_entry.delete(0, tk.END)
                self.desc_counter.config(text="0/100 characters")
                
                # Refresh categories in dropdown
                self.data = db_instance.load_data()
                if hasattr(self, 'expense_category_combobox'):
                    self.expense_category_combobox['values'] = self.data.get("categories", [])
            else:
                messagebox.showerror("Error", "Failed to save expense!")

        except ValueError:
            messagebox.showerror("Error", "Invalid amount! Please enter a valid number.")
                
    def add_income(self):
        """Add new income"""
        try:
            amount = float(self.income_amount_entry.get())
            description = self.income_description_entry.get()

            # Create transaction data
            transaction_data = {
                "timestamp": get_current_timestamp(),
                "amount": amount,
                "description": description
            }

            # Use add_transaction method which will handle callbacks
            success = db_instance.add_transaction('income', transaction_data)

            if success:
                messagebox.showinfo("Success", "Income added successfully!")
                
                # Clear entries after successful addition
                self.income_amount_entry.delete(0, tk.END)
                self.income_description_entry.delete(0, tk.END)
                self.income_desc_counter.config(text="0/100 characters")
            else:
                messagebox.showerror("Error", "Failed to save income!")

        except ValueError:
            messagebox.showerror("Error", "Invalid amount! Please enter a valid number.")