import sqlite3
from logging_config import logging  


class DatabaseManager:
    """Handles all database operations for expenses."""

    def __init__(self, db_name: str = "expenses.db"):
        self.db_name = db_name
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.create_table()
            self.create_budget_table()
            logging.info(f"Connected to database: {self.db_name}")
        except sqlite3.Error as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def create_table(self) -> None:
        """Creates the expenses table if it doesn't already exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expense_lookup
                ON expenses (date, amount, category, description)
                """
            )
            self.conn.commit()
            logging.info("Expenses table created or already exists.")
        except sqlite3.Error as e:
            logging.error(f"Failed to create expenses table: {e}")
            raise

    def create_budget_table(self) -> None:
        """Creates the budgets table if it doesn't already exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    budget REAL NOT NULL,
                    spent REAL DEFAULT 0
                )
                """
            )
            self.conn.commit()
            logging.info("Budgets table created or already exists.")
        except sqlite3.Error as e:
            logging.error(f"Failed to create budgets table: {e}")
            raise

    def add_expense(self, date: str, amount: float, category: str, description: str, *, commit: bool = True) -> None:
        """Inserts a new expense record into the expenses table."""
        try:
            with self.conn:  
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO expenses (date, amount, category, description) VALUES (?,?,?,?)",
                    (date, amount, category, description)
                )
                logging.info(f"Added expense: {date}, {amount}, {category}, {description}")
        except sqlite3.Error as e:
            logging.error(f"Failed to add expense: {e}")
            raise

    def delete_expense(self, record_id: int) -> None:
        """Deletes an expense record by its ID."""
        try:
            with self.conn:  
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id=?", (record_id,))
                logging.info(f"Deleted expense with ID: {record_id}")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete expense with ID {record_id}: {e}")
            raise

    def get_all_expenses(self):
        """Retrieves all expense records from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, date, amount, category, description FROM expenses")
            rows = cursor.fetchall()
            logging.info("Fetched all expenses.")
            return rows
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch all expenses: {e}")
            raise

    def expense_exists(self, date: str, amount: float, category: str, description: str) -> bool:
        """Checks if an expense with the given details already exists in the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM expenses
                WHERE date=? AND amount=? AND category=? AND description=?
                LIMIT 1
                """,
                (date, round(amount, 2), category, description)
            )
            exists = cursor.fetchone() is not None
            logging.info(f"Expense exists check for {date}, {amount}, {category}, {description}: {exists}")
            return exists
        except sqlite3.Error as e:
            logging.error(f"Failed to check if expense exists: {e}")
            raise

    def get_expense_id(self, date: str, amount: float, category: str, description: str):
        """Retrieves the ID of an expense based on its unique fields."""
        try:
            amount = float(amount)
        except ValueError:
            logging.error(f"Invalid amount value: {amount}")
            raise ValueError(f"Invalid amount value: {amount}")

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id FROM expenses
                WHERE date=? AND amount=? AND category=? AND description=?
                LIMIT 1
                """,
                (date, round(amount, 2), category, description)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Failed to retrieve expense ID: {e}")
            raise

    def add_expenses_bulk(self, expenses: list) -> None:
        """Bulk inserts expenses into the database."""
        try:
            cursor = self.conn.cursor()
            self.conn.execute("BEGIN TRANSACTION;")
            cursor.executemany(
                "INSERT INTO expenses (date, amount, category, description) VALUES (?, ?, ?, ?)",
                expenses
            )
            self.conn.commit()
            logging.info(f"Bulk inserted {len(expenses)} expenses.")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Failed to bulk insert expenses: {e}")
            raise

    def get_all_budgets(self):
        """Fetch all budget records from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT category, budget, spent FROM budgets")
            result = cursor.fetchall()
            logging.info("Fetched all budgets.")
            return result
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch all budgets: {e}")
            raise

    def add_or_update_budget(self, category: str, budget: float) -> None:
        """Insert or update a budget record."""
        try:
            with self.conn:  
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO budgets (category, budget)
                    VALUES (?, ?)
                    ON CONFLICT(category) DO UPDATE SET budget=excluded.budget
                    """,
                    (category, budget)
                )
                logging.info(f"Added or updated budget for category: {category}, budget: {budget}")
        except sqlite3.Error as e:
            logging.error(f"Failed to add or update budget for category {category}: {e}")
            raise

    def update_spent(self, category: str, amount: float) -> None:
        """Updates the spent amount for a specific category."""
        try:
            with self.conn: 
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    UPDATE budgets
                    SET spent = spent + ?
                    WHERE category = ?
                    """,
                    (amount, category)
                )
                logging.info(f"Updated spent amount for category: {category}, amount: {amount}")
        except sqlite3.Error as e:
            logging.error(f"Failed to update spent amount for category {category}: {e}")
            raise

    def delete_budget(self, category: str) -> None:
        """Delete a budget record by category."""
        try:
            with self.conn: 
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM budgets WHERE category=?", (category,))
                logging.info(f"Deleted budget for category: {category}")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete budget for category {category}: {e}")
            raise

    def get_remaining_budget(self) -> float:
        """Returns the remaining budget (total budget - total spent)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT SUM(budget - spent) FROM budgets")
            result = cursor.fetchone()[0]
            logging.info("Fetched remaining budget.")
            return result if result is not None else 0.0
        except sqlite3.Error as e:
            logging.error(f"Failed to fetch remaining budget: {e}")
            raise

    def close(self) -> None:
        """Close the database connection."""
        try:
            self.conn.close()
            logging.info("Database connection closed.")
        except sqlite3.Error as e:
            logging.error(f"Failed to close database connection: {e}")
            raise
