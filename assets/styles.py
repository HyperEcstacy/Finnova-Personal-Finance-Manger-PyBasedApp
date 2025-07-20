from tkinter import ttk

def set_theme(root):
    style = ttk.Style()
    style.theme_use("clam")

    # Set colors
    style.configure("TNotebook", background="#e3f2fd")
    style.configure("TFrame", background="#e3f2fd")
    style.configure("TLabel", background="#e3f2fd", font=("Arial", 12))
    style.configure("TButton", background="#64b5f6", font=("Arial", 10, "bold"), padding=5)
    style.configure("TEntry", font=("Arial", 10))
