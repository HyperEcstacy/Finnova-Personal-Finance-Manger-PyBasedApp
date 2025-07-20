import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import csv
from fpdf import FPDF
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
from database.core import db_instance
from modules.utils import calculate_totals



class ReportWindow:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        self.data = db_instance.load_data()
        self.fig = None
        self._is_destroyed = False  # Track if window is destroyed
        
        # Setup styles
        self.setup_styles()
        
        # Configure grid layout
        self.frame.columnconfigure(0, weight=1, minsize=350)
        self.frame.columnconfigure(1, weight=2, minsize=500)
        self.frame.rowconfigure(0, weight=1, minsize=200)
        self.frame.rowconfigure(1, weight=1, minsize=300)
        
        # Create UI components
        self.create_financial_summary_panel()
        self.create_expense_breakdown_panel()
        self.create_transaction_history_panel()
        
        self.update_report()
        self.frame.bind("<Destroy>", self.on_destroy)


    def on_destroy(self, event):
        """Clean up when window is destroyed"""
        self._is_destroyed = True
        if self.fig:
            plt.close(self.fig)
        db_instance.unregister_callback(self.update_report)

    def safe_update(self):
        """Thread-safe update method"""
        if self._is_destroyed or not self.frame.winfo_exists():
            return
            
        try:
            self.update_report()
        except Exception as e:
            print(f"Safe update failed: {str(e)}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Panel.TFrame", background="#f8f9fa", relief="flat")
        style.configure("PanelTitle.TLabel",
                      background="#4a6fa5",
                      foreground="white",
                      font=("Segoe UI", 10, "bold"),
                      padding=8)
        style.configure("SummaryCard.TFrame",
                      background="#ffffff",
                      relief="raised",
                      borderwidth=1)
        style.configure("DataHeading.TLabel",
                      font=("Segoe UI", 9, "bold"),
                      foreground="#343a40")
        style.configure("DataItem.TLabel",
                      font=("Segoe UI", 9),
                      foreground="#495057")
        style.configure("Positive.TLabel",
                      foreground="#28a745",
                      font=("Segoe UI", 9, "bold"))
        style.configure("Negative.TLabel",
                      foreground="#dc3545",
                      font=("Segoe UI", 9, "bold"))
        style.configure("Action.TButton",
                      font=("Segoe UI", 9),
                      padding=4)
        style.configure("Treeview",
                      font=("Segoe UI", 9),
                      rowheight=25)

    def create_panel(self, row, column, rowspan=1, columnspan=1, title=""):
        panel = ttk.Frame(self.frame, style="Panel.TFrame")
        panel.grid(row=row, column=column,
                  rowspan=rowspan, columnspan=columnspan,
                  padx=5, pady=5, sticky="nsew")
        panel.grid_propagate(False)
        
        title_bar = ttk.Label(panel, text=title, style="PanelTitle.TLabel")
        title_bar.pack(fill=tk.X)
        
        content = ttk.Frame(panel)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        return panel, content

    def create_financial_summary_panel(self):
        panel, content = self.create_panel(0, 0, title="Financial Summary")
        panel.config(width=350, height=200)
        
        card_frame = ttk.Frame(content)
        card_frame.pack(fill=tk.BOTH, expand=True)
        
        card_frame.columnconfigure(0, weight=1)
        card_frame.columnconfigure(1, weight=1)
        card_frame.columnconfigure(2, weight=1)
        card_frame.rowconfigure(0, weight=1)
        
        # Income card
        income_card = ttk.Frame(card_frame, style="SummaryCard.TFrame", height=120)
        income_card.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        ttk.Label(income_card, text="INCOME", style="DataHeading.TLabel").pack(pady=(8,4))
        self.income_label = ttk.Label(income_card, text="Rs0.00", style="Positive.TLabel")
        self.income_label.pack(pady=(0,8))
        
        # Expenses card
        expenses_card = ttk.Frame(card_frame, style="SummaryCard.TFrame", height=120)
        expenses_card.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        ttk.Label(expenses_card, text="EXPENSES", style="DataHeading.TLabel").pack(pady=(8,4))
        self.expenses_label = ttk.Label(expenses_card, text="Rs0.00", style="Negative.TLabel")
        self.expenses_label.pack(pady=(0,8))
        
        # Balance card
        balance_card = ttk.Frame(card_frame, style="SummaryCard.TFrame", height=120)
        balance_card.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        ttk.Label(balance_card, text="BALANCE", style="DataHeading.TLabel").pack(pady=(8,4))
        self.balance_label = ttk.Label(balance_card, text="Rs0.00")
        self.balance_label.pack(pady=(0,8))
        
        refresh_btn = ttk.Button(content, text="⟳ Refresh", 
                               style="Action.TButton",
                               command=self.update_report)
        refresh_btn.pack(side=tk.BOTTOM, pady=4, fill=tk.X)

    def create_expense_breakdown_panel(self):
        """Create the expense breakdown panel with chart and breakdown"""
        panel, content = self.create_panel(1, 0, title="Expense Breakdown")
        
        # Main container with two sections: chart (top) and breakdown (bottom)
        main_frame = ttk.Frame(content)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chart frame (top 60% of space)
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Breakdown frame (bottom 40% of space)
        self.breakdown_frame = ttk.Frame(main_frame)
        self.breakdown_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add loading indicator
        self.loading_label = ttk.Label(self.chart_frame, text="Loading chart...", 
                                    style="DataItem.TLabel")
        self.loading_label.pack(expand=True)


    def create_transaction_history_panel(self):
        panel, content = self.create_panel(0, 1, rowspan=2, title="Recent Transactions")
        panel.config(width=500, height=500)
        
        main_container = ttk.Frame(content)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        tree_frame = ttk.Frame(main_container, height=350)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("date", "category", "amount", "type")
        self.transaction_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=12,
            style="Treeview"
        )
        
        self.transaction_tree.heading("date", text="Date", anchor=tk.W)
        self.transaction_tree.heading("category", text="Category", anchor=tk.W)
        self.transaction_tree.heading("amount", text="Amount", anchor=tk.E)
        self.transaction_tree.heading("type", text="Type", anchor=tk.W)
        
        self.transaction_tree.column("date", width=90, stretch=False)
        self.transaction_tree.column("category", width=120, stretch=True)
        self.transaction_tree.column("amount", width=90, stretch=False, anchor=tk.E)
        self.transaction_tree.column("type", width=70, stretch=False)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                command=self.transaction_tree.yview)
        self.transaction_tree.configure(yscroll=scrollbar.set)
        
        self.transaction_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        filter_frame = ttk.Frame(main_container)
        filter_frame.pack(fill=tk.X, pady=(5,0))
        
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(date_frame, text="Date Range:", style="DataHeading.TLabel").pack(side=tk.LEFT)
        
        start_frame = ttk.Frame(date_frame)
        start_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(start_frame, text="From:").pack(side=tk.LEFT)
        self.start_date = DateEntry(start_frame, date_pattern='yyyy-mm-dd', 
                                  width=10,
                                  year=datetime.date.today().year,
                                  month=datetime.date.today().month,
                                  day=datetime.date.today().day)
        self.start_date.pack(side=tk.LEFT, padx=2)
        
        end_frame = ttk.Frame(date_frame)
        end_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(end_frame, text="To:").pack(side=tk.LEFT)
        self.end_date = DateEntry(end_frame, date_pattern='yyyy-mm-dd',
                                width=10,
                                year=datetime.date.today().year,
                                month=datetime.date.today().month,
                                day=datetime.date.today().day)
        self.end_date.pack(side=tk.LEFT, padx=2)
        
        quick_frame = ttk.Frame(filter_frame)
        quick_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(quick_frame, text="7 Days", 
                 style="Action.TButton",
                 command=lambda: self.set_date_range(7)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(quick_frame, text="30 Days", 
                 style="Action.TButton",
                 command=lambda: self.set_date_range(30)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X, pady=(5,0))
        
        filter_btn = ttk.Button(button_frame, text="Apply Filter",
                              style="Action.TButton",
                              command=self.filter_transactions)
        filter_btn.pack(fill=tk.X, pady=2)
        
        export_frame = ttk.Frame(button_frame)
        export_frame.pack(fill=tk.X)
        
        export_csv_btn = ttk.Button(export_frame, text="Export CSV",
                                  style="Action.TButton",
                                  command=self.export_to_csv)
        export_csv_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        export_pdf_btn = ttk.Button(export_frame, text="Export PDF",
                                  style="Action.TButton",
                                  command=self.export_to_pdf)
        export_pdf_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def update_expense_chart(self):
        """Update the expense breakdown chart with robust error handling"""
        # Check if required frames exist
        if not hasattr(self, 'chart_frame') or not self.chart_frame.winfo_exists():
            return
        if not hasattr(self, 'breakdown_frame') or not self.breakdown_frame.winfo_exists():
            return

        try:
            # Safely clear previous widgets
            for widget in self.chart_frame.winfo_children():
                if widget.winfo_exists():
                    widget.destroy()
            for widget in self.breakdown_frame.winfo_children():
                if widget.winfo_exists():
                    widget.destroy()

            # Get data with validation
            categories, expenses = [], []
            try:
                categories, expenses = self.get_expense_breakdown()
            except Exception as e:
                print(f"Error getting expense data: {str(e)}")

            if not categories or not expenses or len(categories) != len(expenses):
                if self.chart_frame.winfo_exists():
                    ttk.Label(self.chart_frame, 
                            text="No valid expense data available",
                            style="DataItem.TLabel").pack(expand=True)
                return

            # Clean up previous figure safely
            if hasattr(self, 'fig') and self.fig:
                try:
                    plt.close(self.fig)
                except Exception as e:
                    print(f"Error closing previous figure: {str(e)}")

            try:
                # Create new figure with error handling
                plt.style.use('seaborn-v0_8')
                self.fig = plt.figure(figsize=(5, 3), dpi=100)
                self.fig.patch.set_facecolor('#f8f9fa')
                ax = self.fig.add_subplot(111)
                ax.set_facecolor('#f8f9fa')

                # Generate colors safely
                try:
                    cmap = plt.cm.get_cmap('Pastel1')
                    colors = [cmap(i % cmap.N) for i in range(len(categories))]
                except:
                    colors = plt.cm.tab20.colors[:len(categories)]

                # Create pie chart with error boundaries
                wedges, texts, autotexts = ax.pie(
                    expenses,
                    labels=None,
                    autopct=lambda p: f'{p:.1f}%' if p >= 3 else '',
                    startangle=90,
                    colors=colors,
                    wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                    pctdistance=0.8,
                    textprops={'fontsize': 8}
                )

                # Add legend if we have space
                if self.chart_frame.winfo_exists():
                    legend = ax.legend(
                        wedges,
                        categories,
                        title="Categories",
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                        fontsize=8,
                        title_fontsize=9,
                        framealpha=0.8
                    )

                ax.set_title("Expense Breakdown", pad=10, fontsize=10, fontweight='bold')
                ax.axis('equal')
                self.fig.tight_layout()
                self.fig.subplots_adjust(right=0.65)

                # Draw on canvas if frame exists
                if self.chart_frame.winfo_exists():
                    canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
                    canvas.draw()
                    if self.chart_frame.winfo_exists():  # Double-check
                        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                # Create breakdown if frame exists
                if self.breakdown_frame.winfo_exists():
                    self.create_category_breakdown(categories, expenses, colors)

            except Exception as e:
                print(f"Chart creation error: {str(e)}")
                if self.chart_frame.winfo_exists():
                    ttk.Label(self.chart_frame, 
                            text=f"Error displaying chart: {str(e)}",
                            style="Negative.TLabel").pack(expand=True)

        except Exception as e:
            print(f"Unexpected error in update_expense_chart: {str(e)}")
            if hasattr(self, 'chart_frame') and self.chart_frame.winfo_exists():
                ttk.Label(self.chart_frame, 
                        text="Failed to load expense chart",
                        style="Negative.TLabel").pack(expand=True)
                
    def create_category_breakdown(self, categories, expenses, colors):
        """
        Create a detailed scrollable breakdown of categories with progress bars
        
        Args:
            categories: List of expense categories
            expenses: List of expense amounts
            colors: List of colors matching the pie chart
        """
        # Calculate total and percentages
        total = sum(expenses)
        percentages = [e/total*100 for e in expenses]
        
        # Create a scrollable frame for the breakdown
        canvas = tk.Canvas(self.breakdown_frame, bg='#f8f9fa', highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(self.breakdown_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scroll region
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Layout canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Create a progress bar style
        style = ttk.Style()
        style.layout("Color.Horizontal.TProgressbar", 
                    [('Horizontal.Progressbar.trough',
                    {'children': [('Horizontal.Progressbar.pbar',
                                    {'side': 'left', 'sticky': 'ns'})],
                    'sticky': 'nswe'})])
        
        # Add header row
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header_frame, text="Category", width=15, 
                style="DataHeading.TLabel").pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Amount", width=10,
                style="DataHeading.TLabel").pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="%", width=5,
                style="DataHeading.TLabel").pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Progress", 
                style="DataHeading.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Add category items with more compact layout
        for idx, (category, amount, pct, color) in enumerate(zip(categories, expenses, percentages, colors)):
            item_frame = ttk.Frame(scrollable_frame)
            item_frame.pack(fill=tk.X, pady=1)
            
            # Category name with color indicator
            color_canvas = tk.Canvas(item_frame, width=12, height=12, bg='#f8f9fa', highlightthickness=0)
            hex_color = '#%02x%02x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255))
            color_canvas.create_rectangle(1, 1, 11, 11, fill=hex_color, outline="")
            color_canvas.pack(side=tk.LEFT, padx=2)
            
            ttk.Label(item_frame, text=category, width=15,
                    style="DataItem.TLabel").pack(side=tk.LEFT, padx=2)
            
            # Amount
            ttk.Label(item_frame, text=f"Rs{amount:,.2f}", width=10,
                    style="Negative.TLabel").pack(side=tk.LEFT, padx=2)
            
            # Percentage
            ttk.Label(item_frame, text=f"{pct:.1f}%", width=5,
                    style="DataItem.TLabel").pack(side=tk.LEFT, padx=2)
            
            # Progress bar
            progress = ttk.Progressbar(item_frame, 
                                    orient=tk.HORIZONTAL,
                                    length=100,
                                    mode="determinate",
                                    value=pct,
                                    style="Color.Horizontal.TProgressbar")
            progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            
            # Set progress bar color
            style.configure("Color.Horizontal.TProgressbar",
                        background=hex_color,
                        troughcolor="#e9ecef")
        
    def set_date_range(self, days):
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        self.start_date.set_date(start_date)
        self.end_date.set_date(end_date)

    def update_report(self):
        """Update all report components with error handling"""
        if self._is_destroyed or not self.frame.winfo_exists():
            return
            
        try:
            # Load fresh data
            self.data = db_instance.load_data()
            
            # Update summary panel
            totals = calculate_totals(self.data)
            self.update_summary_panel(totals)
            
            # Update transaction list
            self.update_transaction_list()
            
            # Update expense chart
            self.update_expense_chart()
            
        except Exception as e:
            print(f"Report update error: {str(e)}")
            # Optionally show error to user
            # messagebox.showerror("Update Error", f"Failed to update report: {str(e)}")

    def update_summary_panel(self, totals):
        """Update summary panel with comprehensive checks"""
        # Validate totals input
        if not totals or not isinstance(totals, dict):
            print("Invalid totals data provided")
            return

        # Check required keys exist
        required_keys = ['income', 'expenses', 'balance']
        if not all(key in totals for key in required_keys):
            print("Missing required keys in totals data")
            return

        # Safely update each label with existence checks
        try:
            if hasattr(self, 'income_label') and self.income_label.winfo_exists():
                try:
                    formatted_income = f"Rs{totals['income']:,.2f}"
                    self.income_label.config(text=formatted_income, style="Positive.TLabel")
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Error formatting income: {str(e)}")
                    self.income_label.config(text="Rs0.00", style="Positive.TLabel")

            if hasattr(self, 'expenses_label') and self.expenses_label.winfo_exists():
                try:
                    formatted_expenses = f"Rs{totals['expenses']:,.2f}"
                    self.expenses_label.config(text=formatted_expenses, style="Negative.TLabel")
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Error formatting expenses: {str(e)}")
                    self.expenses_label.config(text="Rs0.00", style="Negative.TLabel")

            if hasattr(self, 'balance_label') and self.balance_label.winfo_exists():
                try:
                    formatted_balance = f"Rs{totals['balance']:,.2f}"
                    if totals['balance'] >= 0:
                        self.balance_label.config(text=formatted_balance, style="Positive.TLabel")
                    else:
                        self.balance_label.config(text=formatted_balance, style="Negative.TLabel")
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Error formatting balance: {str(e)}")
                    self.balance_label.config(text="Rs0.00")

        except Exception as e:
            print(f"Unexpected error in update_summary_panel: {str(e)}")

    def filter_transactions(self):
        try:
            start_date = self.start_date.get_date()
            end_date = self.end_date.get_date()
            
            filtered_transactions = []
            for transaction in self.data["income"] + self.data["expenses"]:
                transaction_date = datetime.datetime.strptime(
                    transaction["timestamp"].split()[0], "%Y-%m-%d").date()
                if start_date <= transaction_date <= end_date:
                    filtered_transactions.append({
                        "date": transaction["timestamp"].split()[0],
                        "category": transaction.get("category", "-"),
                        "amount": transaction["amount"],
                        "type": "Income" if "income" in transaction else "Expense"
                    })
            
            self.update_transaction_list(filtered_transactions)
            
        except Exception as e:
            messagebox.showerror("Filter Error", f"Failed to filter transactions: {str(e)}")

    def update_transaction_list(self, transactions=None):
        """Update the transaction list with newest items at top"""
        if not hasattr(self, 'transaction_tree') or not self.transaction_tree.winfo_exists():
            return
            
        try:
            # Clear existing items
            self.transaction_tree.delete(*self.transaction_tree.get_children())
            
            # Get sorted transactions (newest first)
            transactions = transactions or self.get_recent_transactions()
            
            if not transactions:
                self.transaction_tree.insert("", "end", values=("No transactions", "", "", ""))
                return
                
            # Insert items in reverse order (newest at top)
            for transaction in transactions:
                tag = 'income' if transaction["type"] == "Income" else 'expense'
                amount_text = f"Rs{float(transaction['amount']):,.2f}"
                category = transaction["category"] if transaction["category"] != "-" else ""
                
                # Insert each new item at position 0 (top of list)
                self.transaction_tree.insert(
                    "", 
                    0,  # This is the key change - inserts at top instead of end
                    values=(
                        transaction["date"],
                        category,
                        amount_text,
                        transaction["type"]
                    ),
                    tags=(tag,)
                )
                
        except Exception as e:
            print(f"Error updating transaction list: {str(e)}")

    def get_recent_transactions(self, limit=20):
        """Get transactions sorted newest first (reverse chronological)"""
        all_transactions = []
        
        # Process income records
        for income in self.data["income"]:
            all_transactions.append({
                "date": income["timestamp"].split()[0],  # Just the date part
                "full_timestamp": income["timestamp"],    # Full timestamp for sorting
                "category": "-",
                "amount": income["amount"],
                "type": "Income"
            })
        
        # Process expense records
        for expense in self.data["expenses"]:
            all_transactions.append({
                "date": expense["timestamp"].split()[0],   # Just the date part
                "full_timestamp": expense["timestamp"],    # Full timestamp for sorting
                "category": expense["category"],
                "amount": expense["amount"],
                "type": "Expense"
            })
        
        # Sort by timestamp in descending order (newest first)
        all_transactions.sort(key=lambda x: x["full_timestamp"], reverse=True)
        
        return all_transactions[:limit]
        
       

    def get_expense_breakdown(self):
        categories = []
        expenses = []
        
        for expense in self.data["expenses"]:
            category = expense['category']
            amount = expense['amount']
            if category in categories:
                expenses[categories.index(category)] += amount
            else:
                categories.append(category)
                expenses.append(amount)
        
        return categories, expenses

    def export_to_csv(self):
        try:
            if not self.transaction_tree.get_children():
                messagebox.showinfo("Export", "No transactions to export")
                return
                
            filename = "transactions_export.csv"
            
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Category", "Amount", "Type"])
                
                for transaction in self.transaction_tree.get_children():
                    values = self.transaction_tree.item(transaction, 'values')
                    writer.writerow(values)
                    
            messagebox.showinfo("Export Successful", f"Transactions exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export to CSV: {str(e)}")

    def export_to_pdf(self):
        try:
            if not self.transaction_tree.get_children():
                messagebox.showinfo("Export", "No transactions to export")
                return
                
            filename = "transactions_export.pdf"
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", 'B', size=16)
            pdf.cell(200, 10, txt="Transaction Report", ln=True, align='C')
            pdf.ln(5)
            
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, 
                   txt=f"Period: {self.start_date.get_date()} to {self.end_date.get_date()}", 
                   ln=True)
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(40, 10, "Date", border=1)
            pdf.cell(60, 10, "Category", border=1)
            pdf.cell(40, 10, "Amount", border=1)
            pdf.cell(40, 10, "Type", border=1)
            pdf.ln()
            
            pdf.set_font("Arial", size=10)
            for transaction in self.transaction_tree.get_children():
                values = self.transaction_tree.item(transaction, 'values')
                pdf.cell(40, 10, values[0], border=1)
                pdf.cell(60, 10, values[1], border=1)
                pdf.cell(40, 10, values[2], border=1)
                pdf.cell(40, 10, values[3], border=1)
                pdf.ln()
            
            pdf.output(filename)
            messagebox.showinfo("Export Successful", f"Transactions exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export to PDF: {str(e)}")