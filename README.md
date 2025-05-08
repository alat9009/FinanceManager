# Personal Finance Manager

The **Personal Finance Manager** is a feature-rich desktop application designed to help users efficiently manage their personal finances. Built with Python and Tkinter, the application provides an intuitive interface for tracking expenses, setting budgets, and visualizing spending trends through interactive charts.

## Features

- **Expense Management**: Add, view, and delete expenses with ease.
- **Budget Tracking**: Set and manage budgets for various categories.
- **Spending Alerts**: Receive alerts when spending exceeds the allocated budget.
- **Data Visualization**:
  - Pie charts for expense distribution.
  - Line charts for spending trends over time.
  - Bar charts for budget vs. spending comparisons.
- **Data Import/Export**: Import and export expenses in CSV format for easy data sharing.
- **Theming**: Toggle between light and dark themes for a personalized user experience.

## Installation

Follow these steps to install and run the application:

1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/alat9009/FinanceManager
   cd FinanceApp-with-Bootstrap
   ```

2. Install Python (version 3.10 or higher is recommended). You can download it from [python.org](https://www.python.org/).

3. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python finance_app.py
   ```

## Usage

1. **Launch the Application**: Start the application by running `finance_app.py`.
2. **Add Expenses**: Use the input fields to add expenses (date, amount, category, and description).
3. **Manage Budgets**: Click the "Manage Budgets" button to set or update budgets for different categories.
4. **Visualize Spending**: Use the "Show Chart" button to view spending trends and budget comparisons.
5. **Export/Import Data**: Use the respective buttons to export or import expenses in CSV format.

## File Structure

- **`finance_app.py`**: Main application file that handles the user interface and core functionality.
- **`budget_manager.py`**: Module for managing budgets and related operations.
- **`database_manager.py`**: Handles database operations for storing and retrieving expenses and budgets.
- **`expenses.db`**: SQLite database file for persistent storage of expenses and budgets.
- **`requirements.txt`**: List of required Python libraries for the application.

## Dependencies

The application relies on the following Python libraries:

- **`tkinter`**: For building the graphical user interface.
- **`ttkbootstrap`**: For modern-themed widgets and styling.
- **`matplotlib`**: For generating interactive charts.
- **`numpy`**: For numerical operations and data processing.
- **`sqlite3`**: For database management and storage.

Install all dependencies using the command:
```bash
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! If you'd like to contribute to the project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes and push them to your forked repository.
4. Submit a pull request with a detailed description of your changes.

## License

[[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## Contact

For any questions or feedback, feel free to reach out:

- **Author**: Alexander Atanasov
- **Email**: alex.atanasov@yahoo.com
- **GitHub**: [https://github.com/alat9009](https://github.com/alat9009)

---

Thank you for using the **Personal Finance Manager**! We hope it helps you take control of your finances.