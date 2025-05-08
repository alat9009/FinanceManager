from logging_config import logging
import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from datetime import datetime
import csv, sys
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry
from database_manager import DatabaseManager
from budget_manager import BudgetManager
import sys,os 

CATEGORIES = ["Food", "Transport", "Entertainment", "Utilities", "Others"]

def get_user_data_path(filename="expenses.db"):
    """Return a path in the user's AppData/Local/PersonalFinanceManager directory."""
    appdata = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    folder = os.path.join(appdata, "PersonalFinanceManager")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)


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

class _CompatDateEntry(DateEntry):
    """DateEntry with .get() method returning date in YYYY-MM-DD format."""
    def __init__(self, master, **kw):
        kw.setdefault("dateformat", "%Y-%m-%d")
        super().__init__(master, **kw)
    def get(self) -> str:
        return self.entry.get().strip()

class FinanceApp:

    
    def __init__(self, root: tb.Window, db_file=None):
        self.root = root
        self.style = self.root.style
        self._dark = False
        self.root.title("Personal Finance Manager")
        icon_path = resource_path("assets/icon.ico")
        self.root.iconbitmap(icon_path)
        self.root.geometry("1400x680")

        # Database manager
        if db_file is None:
            db_file = get_user_data_path()
        self.db_manager = DatabaseManager(db_file)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Unified container for theme
        self.container = tb.Frame(self.root)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        for r in range(3):
            self.container.grid_rowconfigure(r, weight=1 if r == 1 else 0)
        for c in range(3):
            self.container.grid_columnconfigure(c, weight=1 if c < 2 else 0)

        # Input frame
        input_frame = tb.Frame(self.container, padding=10)
        input_frame.grid(row=0, column=0, sticky="nsew")
        input_frame.grid_rowconfigure(6, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)

        tb.Label(input_frame, text="Date:", bootstyle="secondary")\
            .grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = _CompatDateEntry(input_frame, bootstyle="info")
        self.date_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tb.Label(input_frame, text="Amount:", bootstyle="secondary")\
            .grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.amount_entry = tb.Entry(input_frame, bootstyle="info")
        self.amount_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        tb.Label(input_frame, text="Category:", bootstyle="secondary")\
            .grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.categories = CATEGORIES
        self.category_combobox = tb.Combobox(
            input_frame, values=self.categories, state="readonly", bootstyle="info"
        )
        self.category_combobox.set("Select Category")
        self.category_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        tb.Label(input_frame, text="Notes:", bootstyle="secondary")\
            .grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.desc_text = tb.Text(input_frame, height=4, width=30)
        self.desc_text.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        tb.Button(
            input_frame, text="Add Expense", command=self.add_expense, bootstyle="success"
        ).grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

        self.budget_label = tb.Label(
            input_frame, text="Budget: N/A", bootstyle="danger",
            anchor="w", wraplength=300
        )
        self.budget_label.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        # Pie-chart frame
        self.chart_frame = tb.Frame(self.container, padding=10)
        self.chart_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.chart_frame.grid_propagate(False)
        self.chart_canvas = None

        # Search & Filter frame
        filter_frame = tb.Frame(self.container, padding=10)
        filter_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)

        tb.Label(filter_frame, text="Search:", bootstyle="secondary")\
            .grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.search_entry = tb.Entry(filter_frame, bootstyle="info")
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        tb.Label(filter_frame, text="Filter Category:", bootstyle="secondary")\
            .grid(row=1, column=0, sticky="w", padx=5, pady=2)
        filter_values = ["All"] + self.categories
        self.filter_category_combobox = tb.Combobox(
            filter_frame, values=filter_values, state="readonly", bootstyle="info"
        )
        self.filter_category_combobox.set("All")
        self.filter_category_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        tb.Button(
            filter_frame, text="Apply", command=self.load_expenses, bootstyle="primary"
        ).grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        tb.Button(
            filter_frame, text="Clear", command=self.clear_filters, bootstyle="secondary"
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Theme toggle
        toggle_frame = tb.Frame(self.container, padding=7)
        toggle_frame.grid(row=0, column=2, sticky="ne", padx=15, pady=8)
        self._theme_btn = tb.Button(
            toggle_frame, text="🌙", width=3,
            command=self._toggle_theme, bootstyle="warning-outline"
        )
        self._theme_btn.pack(anchor="ne")

        # Treeview + scrollbar
        tree_frame = tb.Frame(self.container)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = tb.Treeview(
            tree_frame,
            columns=("date", "amount", "category", "description"),
            show="headings", bootstyle="info-border"
        )
        for col in ("date", "amount", "category", "description"):
            self.tree.heading(
                col, text=col.capitalize(),
                command=lambda c=col: self.sort_treeview(c, False)
            )
        self.tree.grid(row=0, column=0, sticky="nsew")

        scroll = tb.Scrollbar(
            tree_frame, orient="vertical",
            command=self.tree.yview, bootstyle="dark"
        )
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        # Toolbar
        btn_frame = tb.Frame(self.container, padding=10)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        btn_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        tb.Button(btn_frame, text="Show Chart", command=self.show_chart, bootstyle="primary")\
            .grid(row=0, column=0, padx=5, pady=5)
        tb.Button(btn_frame, text="Export CSV", command=self.export_csv, bootstyle="secondary")\
            .grid(row=0, column=1, padx=5, pady=5)
        tb.Button(btn_frame, text="Import CSV", command=self.import_csv, bootstyle="secondary")\
            .grid(row=0, column=2, padx=5, pady=5)
        tb.Button(btn_frame, text="Manage Budgets", command=self.manage_budgets, bootstyle="info")\
            .grid(row=0, column=3, padx=5, pady=5)
        tb.Button(btn_frame, text="Delete Expense", command=self.delete_expense, bootstyle="danger")\
            .grid(row=0, column=4, padx=5, pady=5)

        # Initial load
        self.load_expenses()
        self.check_budget()
        self.update_pie_chart()

    def load_expenses(self):
        """Load and display expenses, applying search & category filters."""
        search_term = self.search_entry.get().strip().lower()
        selected_cat = self.filter_category_combobox.get()

        self.tree.delete(*self.tree.get_children())
        for _id, date, amount, category, desc in self.db_manager.get_all_expenses():
            if selected_cat != "All" and category != selected_cat:
                continue
            if search_term:
                if all(
                    search_term not in str(field).lower()
                    for field in (date, amount, category, desc)
                ):
                    continue
            self.tree.insert("", "end", values=(date, amount, category, desc))

        self.update_pie_chart()

    def clear_filters(self):
        """Reset search & category filters."""
        self.search_entry.delete(0, tk.END)
        self.filter_category_combobox.set("All")
        self.load_expenses()

    def add_expense(self):
        date_str = self.date_entry.get()
        amount_str = self.amount_entry.get().strip()
        category = self.category_combobox.get()
        desc = self.desc_text.get("1.0", tk.END).strip()

        if not date_str:
            messagebox.showerror("Input Error", "Please select a date."); return
        if category == "Select Category":
            messagebox.showerror("Input Error", "Please select a category."); return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must be YYYY-MM-DD."); return
        if not amount_str:
            messagebox.showerror("Input Error", "Amount field cannot be empty."); return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve)); return
        if not desc:
            messagebox.showerror("Input Error", "Description cannot be empty."); return
        if len(desc) > 255:
            messagebox.showerror("Input Error", "Description ≤ 255 characters."); return

        try:
            self.db_manager.add_expense(date_str, amount, category, desc)
        except Exception as e:
            logging.error(f"Failed to add expense: {e}")
            messagebox.showerror("Database Error", "Failed to add expense. Please try again.")
            return

        self.amount_entry.delete(0, tk.END)
        self.desc_text.delete("1.0", tk.END)
        self.category_combobox.set("Select Category")
        self.load_expenses()
        self.check_budget()
        self.update_pie_chart()
        messagebox.showinfo("Success", "Expense added successfully!")

    def delete_expense(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Selection Error", "Select an expense to delete."); return
        if not messagebox.askyesno("Confirm", "Delete selected expense(s)?"): return

        try:
            for item in sel:
                date, amount, category, desc = self.tree.item(item, "values")
                rec_id = self.db_manager.get_expense_id(date, float(amount), category, desc)
                if rec_id:
                    self.db_manager.delete_expense(rec_id)
                    self.tree.delete(item)
            self.check_budget()
            messagebox.showinfo("Success", "Deleted.")
        except Exception as e:
            logging.error(f"Failed to delete expense: {e}")
            messagebox.showerror("Deletion Error", "Failed to delete expense. Please try again.")
        self.update_pie_chart()

    def show_chart(self):
        try:
            rows = self.db_manager.get_all_expenses()
            if not rows:
                messagebox.showinfo("No Data", "No expenses to chart."); return
            dates = [datetime.strptime(r[1], "%Y-%m-%d") for r in rows]
            amounts = [r[2] for r in rows]
            dates, amounts = zip(*sorted(zip(dates, amounts)))

            plt.figure(figsize=(12, 8))
            plt.plot(dates, amounts, marker="o", linestyle="-", label="Spending")
            for d, a in zip(dates, amounts):
                plt.annotate(f"${a:.2f}", (d, a),
                             textcoords="offset points", xytext=(0, 10), ha="center")
            plt.gca().xaxis.set_major_formatter(DateFormatter("%b %d"))
            plt.gcf().autofmt_xdate()
            plt.title("Spending Trends Over Time")
            plt.xlabel("Date"); plt.ylabel("Amount ($)")
            plt.grid(True, linestyle="--", alpha=0.6); plt.legend()
            plt.tight_layout(); plt.show()
        except sqlite3.OperationalError as oe:
            logging.error(f"Database operation failed while showing chart: {oe}")
            messagebox.showerror("Database Error", "Failed to retrieve data for the chart.")
        except Exception as e:
            logging.error(f"Unexpected error while showing chart: {e}")
            messagebox.showerror("Unexpected Error", "An unexpected error occurred.")

    def export_csv(self):
        path = asksaveasfilename(defaultextension=".csv",
                                 filetypes=[("CSV files", "*.csv")])
        if not path: return
        rows = self.db_manager.get_all_expenses()
        if not rows:
            messagebox.showinfo("Export Error", "No expenses to export."); return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["ID", "Date", "Amount", "Category", "Description"])
                w.writerows(rows)
            messagebox.showinfo("Export Successful", f"Saved to {path}")
        except Exception as e:
            logging.error(f"Error exporting CSV: {e}")
            messagebox.showerror("Export Error", "Failed to export CSV.")

    def import_csv(self):
        path = askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path: return
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required = {"Date", "Amount", "Category", "Description"}
                if not required.issubset(reader.fieldnames):
                    raise ValueError("CSV missing required headers.")
                good, bad, bulk = 0, 0, []
                for row in reader:
                    try:
                        date = datetime.strptime(row["Date"], "%Y-%m-%d")\
                                       .strftime("%Y-%m-%d")
                        amt = round(float(row["Amount"]), 2)
                        cat = row["Category"]; desc = row["Description"]
                        if self.db_manager.expense_exists(date, amt, cat, desc):
                            continue
                        bulk.append((date, amt, cat, desc)); good += 1
                    except Exception:
                        bad += 1
                if bulk:
                    self.db_manager.add_expenses_bulk(bulk)
                self.load_expenses()
                messagebox.showinfo("Import Complete", f"Imported {good}, skipped {bad}.")
        except Exception as e:
            logging.error(f"Error importing CSV: {e}")
            messagebox.showerror("Import Error", str(e))

    def manage_budgets(self):
        if hasattr(self, "budget_window") and self.budget_window.winfo_exists():
            self.budget_window.lift()
            return

        def on_budget_update():
            self.check_budget()

        def on_budget_window_close():
            self.budget_manager = None  
            self.budget_window.destroy()

        self.budget_window = tk.Toplevel(self.root)
        self.budget_window.protocol("WM_DELETE_WINDOW", on_budget_window_close)  
        self.budget_manager = BudgetManager(self.budget_window, self.style, on_budget_update, db_file= self.db_manager.db_name)

    def check_budget(self):
        budgets = {cat: budget for cat, budget, *_ in self.db_manager.get_all_budgets()}
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        spent = {cat: total or 0.0 for cat, total in cursor.fetchall()}
        over = [f"{c}: ${spent[c]:.2f} > ${budgets[c]:.2f}"
                for c in budgets if spent.get(c, 0.0) > budgets[c]]
        if over:
            self.budget_label.config(
                text="Exceeded Budgets:\n" + "\n".join(over),
                foreground="red"
            )
        else:
            self.budget_label.config(
                text="All budgets are within limits.",
                foreground="green"
            )

    def sort_treeview(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        numeric = False
        try:
            float(data[0][0]); numeric = True
        except Exception:
            pass
        data.sort(
            key=lambda t: float(t[0]) if numeric else t[0].lower(),
            reverse=reverse
        )
        for idx, (_, k) in enumerate(data):
            self.tree.move(k, "", idx)
        self.tree.heading(
            col,
            command=lambda: self.sort_treeview(col, not reverse)
        )

    def update_pie_chart(self):
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
            data = cursor.fetchall()
            if not data:
                if self.chart_canvas:
                    self.chart_canvas.get_tk_widget().destroy()
                return
            cats, amounts = zip(*data)
            fig, ax = plt.subplots(figsize=(5, 4))
            bg_color = self.style.lookup("TFrame", "background")
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            text_color = "grey" if self._dark else "black"
            ax.pie(amounts, labels=cats, autopct="%1.1f%%", startangle=90,
                   colors=plt.cm.Paired.colors)
            ax.set_title("Expense Distribution", color=text_color)
            for text in ax.texts:
                text.set_color(text_color)
            if self.chart_canvas:
                self.chart_canvas.get_tk_widget().destroy()
            self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.chart_canvas.draw()
            self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)
        except Exception as e:
            logging.error(f"Error updating pie chart: {e}")
            messagebox.showerror("Unexpected Error", "Failed to update pie chart.")

    def _toggle_theme(self):
        new_theme = "darkly" if not self._dark else "flatly"
        self.style.theme_use(new_theme)
        self._dark = not self._dark
        self._theme_btn.configure(text="☀" if self._dark else "🌙")
        self.update_pie_chart()

        if hasattr(self, "budget_manager") and self.budget_manager:
            try:
                self.budget_manager.redraw_budget_chart()
            except Exception as e:
                logging.error(f"Error redrawing budget chart: {e}")

    def on_closing(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.db_manager.close()
            self.root.destroy()
            sys.exit()

if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    FinanceApp(root)
    root.mainloop()
