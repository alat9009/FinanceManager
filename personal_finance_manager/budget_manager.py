import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import ttkbootstrap as tb
from database_manager import DatabaseManager
from logging_config import logging
import os,sys

def resource_path(rel_path: str) -> str:
    """
    Get the absolute path to a resource, both when
    running as a script (dev) or from a PyInstaller bundle.
    rel_path is always given relative to your project root's
    assets folder, e.g. "assets/icon.ico"
    """
    if getattr(sys, "_MEIPASS", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir)
        )
    return os.path.normpath(os.path.join(base_path, rel_path))

class BudgetManager:
    """
    Module Budget Manager: Users can set budgets, view them in a table,
    track actual spending, and compare budgets vs. spending with charts.
    """

    def __init__(self, root, style: tb.Style, on_budget_update=None, db_file: str = None):
        self.root = root
        self.style = style
        self._dark = style.theme_use().startswith("dark")
        self.on_budget_update = on_budget_update

        self.root.title("Budget Manager")
        icon_path = resource_path("assets/icon.ico")
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_propagate(False)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)

        # Set the window size and position
        self.root.geometry("1200x680")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Database
        self.db_manager = DatabaseManager(db_file)
        try:
            self.db_manager.create_budget_table()
        except Exception as e:
            logging.error(f"Failed to create budget table: {e}")
            messagebox.showerror("Database Error", "Initialization failed.")
            self.root.destroy()
            return

        CATEGORIES = ["Food", "Transport", "Entertainment", "Utilities", "Others"]

        # Input frame
        input_frame = tb.Frame(self.root, padding=10)
        input_frame.grid(row=0, column=0, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)

        tb.Label(input_frame, text="Category:", bootstyle="secondary").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        self.category_combobox = tb.Combobox(
            input_frame, values=CATEGORIES, state="readonly", bootstyle="info"
        )
        self.category_combobox.set("Select Category")
        self.category_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tb.Label(input_frame, text="Monthly Budget:", bootstyle="secondary").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)
        self.budget_entry = tb.Entry(input_frame, bootstyle="info")
        self.budget_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tb.Button(
            input_frame, text="Set Budget", command=self.set_budget, bootstyle="success"
        ).grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        self.exceeded_label = tb.Label(
            input_frame, text="", bootstyle="danger", anchor="w", wraplength=300
        )
        self.exceeded_label.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Display frame
        display_frame = tb.Frame(self.root, padding=10)
        display_frame.grid(row=1, column=0, sticky="nsew")
        display_frame.grid_columnconfigure(0, weight=3)
        display_frame.grid_columnconfigure(1, weight=2)
        display_frame.grid_rowconfigure(0, weight=1)

        # Treeview
        self.tree = tb.Treeview(
            display_frame, columns=("category","budget","spent"), show="headings",
            bootstyle="info-border"
        )
        for col in ("category","budget","spent"):  # columns
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Chart container
        chart_frame = tb.Frame(display_frame)
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(10,0))
        self.fig = Figure(figsize=(5,4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.draw_piechart()

        # Toolbar Buttons
        toolbar_frame = tb.Frame(self.root, padding=10)
        toolbar_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        toolbar_frame.grid_columnconfigure(0, weight=1)  
        toolbar_frame.grid_columnconfigure(1, weight=0)  
        toolbar_frame.grid_columnconfigure(2, weight=1)  

        button_frame = tb.Frame(toolbar_frame)  
        button_frame.grid(row=0, column=1)

        tb.Button(
            button_frame,
            text="Show Budget vs Spending",
            command=self.show_budget_vs_spending,
            bootstyle="primary"
        ).pack(side="left", padx=5, pady=5)

        tb.Button(
            button_frame,
            text="Export Table",
            command=self.export_table,
            bootstyle="secondary"
        ).pack(side="left", padx=5, pady=5)

        tb.Button(
            button_frame,
            text="Delete Budget",
            command=self.delete_budget,
            bootstyle="danger"
        ).pack(side="left", padx=5, pady=5)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.load_budgets()

    def draw_piechart(self):
        """Initial draw of empty pie chart with theme styling"""
        bg = self.style.lookup("TFrame","background")
        self.fig.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)
        title_color = "grey" if self._dark else "black"
        self.ax.clear()
        self.ax.text(0.5,0.5,"No Budget Data", ha='center', va='center',
                     fontsize=12, color=title_color)
        self.fig.tight_layout()
        self.canvas.draw()

    def update_piechart(self, categories, budgets):
        """
        Update the pie chart with the given categories and budgets.
        """
        self.ax.clear()

        bg_color = self.style.lookup("TFrame", "background")
        text_color = "grey" if self._dark else "black"


        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        if not budgets or not any(budgets):

            self.ax.text(
                0.5, 0.5, "No Budget Data",
                ha='center', va='center', fontsize=12, color=text_color
            )
        else:
            wedges, texts, autotexts = self.ax.pie(
                budgets,
                labels=categories,
                autopct="%1.1f%%",
                startangle=90,
                colors=plt.cm.Paired.colors
            )
            self.ax.set_title("Budget Distribution", color=text_color)

            for txt in texts + autotexts:
                txt.set_color(text_color)

        self.fig.tight_layout()
        self.canvas.draw()

    def on_closing(self):
        self.destroy()

    def destroy(self):
        """
        Cleanup resources when the BudgetManager window is closed.
        """
        self.db_manager.close()
        self.root.destroy()

    def load_budgets(self):
        """
        Load budgets into the table and refresh the pie chart & warning label.
        """
        try:
            self.tree.delete(*self.tree.get_children())
            rows = self.db_manager.get_all_budgets()
            spent_data = self.get_all_spent_amounts()
            for category, budget, _ in rows:
                spent = spent_data.get(category, 0.0)
                self.tree.insert(
                    "",
                    "end",
                    values=(category, f"{budget:.2f}", f"{spent:.2f}")
                )
            self.redraw_budget_chart()
            self.update_exceeded_budgets_label()
        except Exception as e:
            logging.error(f"Failed to load budgets: {e}")
            messagebox.showerror("Load Error", "Failed to load budgets. Please try again.")

    def set_budget(self):
        """
        Validate and save the budget for the selected category.
        """
        category = self.category_combobox.get()
        value = self.budget_entry.get().strip()
        if category == "Select Category":
            messagebox.showerror("Input Error", "Please select a category.")
            return
        if not value:
            messagebox.showerror("Input Error", "Budget cannot be empty.")
            return
        try:
            budget = float(value)
            if budget < 0:
                raise ValueError("Budget must be non-negative.")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            return

        try:
            spent = self.get_spent_amount(category)
            if spent > budget:
                messagebox.showwarning(
                    "Budget Warning",
                    f"Expenses ${spent:.2f} exceed budget ${budget:.2f} for '{category}'."
                )
            self.db_manager.add_or_update_budget(category, budget)
            logging.info(f"Budget set for '{category}' = ${budget:.2f}.")
            self.budget_entry.delete(0, tk.END)
            self.category_combobox.set("Select Category")
            if self.on_budget_update:
                self.on_budget_update()
            self.load_budgets()
        except Exception as e:
            logging.error(f"Failed to set budget: {e}")
            messagebox.showerror("Database Error", "Failed to set budget. Please try again.")

    def redraw_budget_chart(self):
        """
        Redraw the pie chart with current budget data, matching the current theme.
        """
        if not self.tree.winfo_exists():  # Check if the Treeview widget still exists
            logging.warning("Attempted to redraw chart, but Treeview widget no longer exists.")
            return
        categories = [self.tree.item(i)['values'][0] for i in self.tree.get_children()]
        budgets = [float(self.tree.item(i)['values'][1]) for i in self.tree.get_children()]
        self.update_piechart(categories, budgets)

        self.ax.clear()

        bg_color = self.style.lookup("TFrame", "background")
        text_color = "grey" if self.style.theme_use().startswith("dark") else "black"

        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        if not budgets or not any(budgets):
            self.ax.text(
                0.5, 0.5, "No Budget Data",
                ha='center', va='center', fontsize=12, color=text_color
            )
        else:
            wedges, texts, autotexts = self.ax.pie(
                budgets,
                labels=categories,
                autopct="%1.1f%%",
                startangle=90,
                colors=plt.cm.Paired.colors
            )
            self.ax.set_title("Budget Distribution", color=text_color)
            for txt in texts + autotexts:
                txt.set_color(text_color)

        self.fig.tight_layout()
        self.canvas.draw()

    def get_spent_amount(self, category):
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE category = ?",
            (category,)
        )
        result = cursor.fetchone()[0]
        return float(result) if result else 0.0

    def get_all_spent_amounts(self):
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        return {row[0]: float(row[1]) if row[1] else 0.0 for row in cursor.fetchall()}

    def show_budget_vs_spending(self):
        """
        Display a bar chart comparing budgets vs actual spending.
        """
        spent_data = self.get_all_spent_amounts()
        cats, budgets, spents = [], [], []
        for iid in self.tree.get_children():
            cat, bud_str, _ = self.tree.item(iid, 'values')
            bud = float(bud_str)
            sp = spent_data.get(cat, 0.0)
            self.tree.set(iid, 'spent', f"{sp:.2f}")
            cats.append(cat); budgets.append(bud); spents.append(sp)

        x = np.arange(len(cats))
        bar_w = 0.35
        plt.figure(figsize=(10, 6))
        bars1 = plt.bar(x - bar_w/2, budgets, bar_w, label='Budget')
        bars2 = plt.bar(x + bar_w/2, spents, bar_w, label='Spent')
        for bar in bars1 + bars2:
            h = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2, h + 0.05,
                f"{h:.2f}", ha='center', va='bottom', fontsize=9
            )
        plt.xticks(x, cats, rotation=45, ha='right')
        plt.ylabel('Amount')
        plt.title('Budget vs Spending')
        plt.legend()
        plt.tight_layout()
        plt.show()

    def export_table(self):
        """
        Export the budget table to CSV.
        """
        items = self.tree.get_children()
        if not items:
            messagebox.showerror("Export Error", "No data to export.")
            return
        path = asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv"), ("All files","*.*")]
        )
        if not path:
            return
        rows = [self.tree.item(i)['values'] for i in items]
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Category", "Budget", "Spent"]);
                writer.writerows(rows)
            messagebox.showinfo("Export Successful", f"Exported to {path}")
        except Exception as e:
            logging.error(f"Export error: {e}")
            messagebox.showerror("Export Error", "Failed to export data.")

    def delete_budget(self):
        """
        Delete the selected budget entry.
        """
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Selection Error", "Select a budget to delete.")
            return
        cat = self.tree.item(sel[0], 'values')[0]
        if not messagebox.askyesno("Confirm", f"Delete budget for '{cat}'?"):
            return
        try:
            self.db_manager.delete_budget(cat)
            self.tree.delete(sel[0])
            self.redraw_budget_chart()
            self.update_exceeded_budgets_label()  
            if self.on_budget_update:  
                self.on_budget_update()
            messagebox.showinfo("Deleted", f"Budget for {cat} deleted.")
        except Exception as e:
            logging.error(f"Delete error: {e}")
            messagebox.showerror("Deletion Error", "Failed to delete budget.")

    def update_exceeded_budgets_label(self):
        """
        Update label to show any categories over budget.
        """
        rows = self.db_manager.get_all_budgets()
        spent_data = self.get_all_spent_amounts()
        exceeded = [f"{c} (${spent_data.get(c,0):.2f} > ${b:.2f})" for c,b,_ in rows if spent_data.get(c,0) > b]
        self.exceeded_label.config(
            text="Exceeded Budgets:\n" + "\n".join(exceeded) if exceeded else ""
        )
