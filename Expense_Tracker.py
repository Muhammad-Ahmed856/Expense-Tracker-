import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum


def clear_console() -> None:
    """Clear the terminal/console screen in a platform-independent way."""
    try:
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
    except Exception:
        # Best-effort only; if it fails, continue without crashing
        pass


def pause(prompt: str = "Press Enter to continue...") -> None:
    """Pause and wait for the user to press Enter. Safe on KeyboardInterrupt."""
    try:
        input(prompt)
    except (KeyboardInterrupt, EOFError):
        # swallow and return to avoid crashing the app when user presses Ctrl+C
        print()

class ExpenseCategory(Enum):
    FOOD = "Food"
    TRANSPORTATION = "Transportation"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    EDUCATION = "Education"
    HEALTHCARE = "Healthcare"
    OTHER = "Other"

class Expense:
    def __init__(self, amount: float, category: ExpenseCategory, description: str, date: str = None):
        self.amount = amount
        self.category = category
        self.description = description
        self.date = date if date else datetime.now().strftime("%Y-%m-%d")
        self.id = f"{self.date}_{secrets.token_hex(8)}"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category.value,
            'description': self.description,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Expense':
        expense = cls(
            amount=data['amount'],
            category=ExpenseCategory(data['category']),
            description=data['description'],
            date=data['date']
        )
        expense.id = data['id']
        return expense

class Budget:
    def __init__(self, category: ExpenseCategory, amount: float, period: str = "monthly"):
        self.category = category
        self.amount = amount
        self.period = period  # "daily", "weekly", "monthly"
        self.id = f"budget_{category.value}_{period}"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'category': self.category.value,
            'amount': self.amount,
            'period': self.period
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Budget':
        return cls(
            category=ExpenseCategory(data['category']),
            amount=data['amount'],
            period=data['period']
        )

class UserManager:
    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading users: {e}")
                self.users = {}
    
    def save_users(self):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256((password + salt).encode()).hexdigest()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hashed password"""
        try:
            salt, stored_hash = hashed_password.split('$')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == stored_hash
        except:
            return False
    
    def register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Register a new user"""
        if username in self.users:
            return False, "Username already exists"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 4:
            return False, "Password must be at least 4 characters"
        
        # Store hashed password
        self.users[username] = {
            'password_hash': self.hash_password(password),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'last_login': None
        }
        
        self.save_users()
        
        # Create user-specific data directory
        user_dir = f"user_data/{username}"
        os.makedirs(user_dir, exist_ok=True)
        
        return True, "User registered successfully"
    
    def login_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user login"""
        if username not in self.users:
            return False, "User not found"
        
        stored_hash = self.users[username]['password_hash']
        
        if self.verify_password(password, stored_hash):
            self.users[username]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_users()
            return True, "Login successful"
        else:
            return False, "Invalid password"
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return username in self.users
    
    def get_user_stats(self, username: str) -> Dict:
        """Get user statistics"""
        if username not in self.users:
            return {}
        
        return {
            'created_at': self.users[username]['created_at'],
            'last_login': self.users[username]['last_login']
        }

class ExpenseTracker:
    def __init__(self, username: str):
        self.username = username
        self.data_file = f"user_data/{username}/expenses.json"
        self.expenses: List[Expense] = []
        self.budgets: Dict[str, Budget] = {}
        
        # Create user directory if it doesn't exist
        os.makedirs(f"user_data/{username}", exist_ok=True)
        
        self.load_data()
    
    def load_data(self):
        """Load expenses and budgets from user-specific JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.expenses = [Expense.from_dict(exp_data) for exp_data in data.get('expenses', [])]
                    self.budgets = {budget_data['id']: Budget.from_dict(budget_data) 
                                  for budget_data in data.get('budgets', [])}
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading data for {self.username}: {e}")
                self.expenses = []
                self.budgets = {}
    
    def save_data(self):
        """Save expenses and budgets to user-specific JSON file"""
        data = {
            'username': self.username,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'expenses': [expense.to_dict() for expense in self.expenses],
            'budgets': [budget.to_dict() for budget in self.budgets.values()]
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_expense(self, amount: float, category: ExpenseCategory, description: str, date: str = None) -> Tuple[bool, str]:
        """Add a new expense"""
        try:
            if amount <= 0:
                return False, "Amount must be positive"
                
            expense = Expense(amount, category, description, date)
            self.expenses.append(expense)
            self.save_data()
            return True, f"Expense added successfully (ID: {expense.id})"
        except Exception as e:
            return False, f"Error adding expense: {e}"
    
    def delete_expense(self, expense_id: str) -> Tuple[bool, str]:
        """Delete an expense by ID"""
        initial_length = len(self.expenses)
        self.expenses = [exp for exp in self.expenses if exp.id != expense_id]
        if len(self.expenses) < initial_length:
            self.save_data()
            return True, "Expense deleted successfully"
        return False, "Expense not found"
    
    def update_expense(self, expense_id: str, amount: float = None, category: ExpenseCategory = None, 
                      description: str = None, date: str = None) -> Tuple[bool, str]:
        """Update an existing expense"""
        for expense in self.expenses:
            if expense.id == expense_id:
                if amount is not None:
                    if amount <= 0:
                        return False, "Amount must be positive"
                    expense.amount = amount
                if category is not None:
                    expense.category = category
                if description is not None:
                    expense.description = description
                if date is not None:
                    expense.date = date
                
                self.save_data()
                return True, "Expense updated successfully"
        return False, "Expense not found"
    
    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """Get expense by ID"""
        for expense in self.expenses:
            if expense.id == expense_id:
                return expense
        return None
    
    def get_expenses_by_category(self, category: ExpenseCategory) -> List[Expense]:
        """Get all expenses for a specific category"""
        return [exp for exp in self.expenses if exp.category == category]
    
    def get_expenses_by_date_range(self, start_date: str, end_date: str) -> List[Expense]:
        """Get expenses within a date range"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            filtered_expenses = []
            for exp in self.expenses:
                exp_date = datetime.strptime(exp.date, "%Y-%m-%d")
                if start <= exp_date <= end:
                    filtered_expenses.append(exp)
            return filtered_expenses
        except ValueError:
            return []
    
    def get_total_spent(self, category: ExpenseCategory = None, start_date: str = None, end_date: str = None) -> float:
        """Get total amount spent, optionally filtered by category and date range"""
        expenses = self.expenses
        
        if category:
            expenses = [exp for exp in expenses if exp.category == category]
        
        if start_date and end_date:
            # Filter the already-selected expenses by date range so we don't drop a prior
            # category filter. Previously this reused get_expenses_by_date_range which
            # returned expenses across all categories and overwrote the category filter.
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                expenses = [exp for exp in expenses if start <= datetime.strptime(exp.date, "%Y-%m-%d") <= end]
            except ValueError:
                # If date parsing fails, fall back to no date filtering
                pass

        return sum(exp.amount for exp in expenses)
    
    def get_total_spent_by_category(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        """Get total spent for each category"""
        category_totals = {category.value: 0.0 for category in ExpenseCategory}
        
        expenses = self.expenses
        if start_date and end_date:
            expenses = self.get_expenses_by_date_range(start_date, end_date)
        
        for expense in expenses:
            category_totals[expense.category.value] += expense.amount
        
        return category_totals
    
    def set_budget(self, category: ExpenseCategory, amount: float, period: str = "monthly") -> Tuple[bool, str]:
        """Set or update budget for a category"""
        try:
            if amount < 0:
                return False, "Budget amount cannot be negative"
                
            budget = Budget(category, amount, period)
            self.budgets[budget.id] = budget
            self.save_data()
            return True, f"Budget set for {category.value}: ${amount} ({period})"
        except Exception as e:
            return False, f"Error setting budget: {e}"
    
    def delete_budget(self, category: ExpenseCategory, period: str = None) -> Tuple[bool, str]:
        """Delete budget for a category"""
        if period:
            budget_id = f"budget_{category.value}_{period}"
        else:
            # Delete all budgets for this category
            budget_ids = [bid for bid in self.budgets.keys() if bid.startswith(f"budget_{category.value}_")]
            if not budget_ids:
                return False, f"No budget found for {category.value}"
            
            for budget_id in budget_ids:
                del self.budgets[budget_id]
            self.save_data()
            return True, f"All budgets deleted for {category.value}"
        
        if budget_id in self.budgets:
            del self.budgets[budget_id]
            self.save_data()
            return True, f"Budget deleted for {category.value} ({period})"
        return False, f"No budget found for {category.value} ({period})"
    
    def get_budget_status(self, category: ExpenseCategory, period: str = "monthly") -> Dict:
        """Get budget status for a category and period"""
        budget_id = f"budget_{category.value}_{period}"
        if budget_id not in self.budgets:
            return {'has_budget': False}
        
        budget = self.budgets[budget_id]
        
        # Calculate spending for this category in the current period
        spent = self.get_total_spent_by_period(category, period)
        
        remaining = budget.amount - spent
        percentage_used = (spent / budget.amount) * 100 if budget.amount > 0 else 0
        
        return {
            'has_budget': True,
            'budget_amount': budget.amount,
            'spent': spent,
            'remaining': remaining,
            'percentage_used': round(percentage_used, 2),
            'is_over_budget': spent > budget.amount,
            'period': period
        }
    
    def get_total_spent_by_period(self, category: ExpenseCategory, period: str) -> float:
        """Get total spent for a category in the current period"""
        now = datetime.now()
        
        if period == "daily":
            start_date = now.strftime("%Y-%m-%d")
            end_date = start_date
        elif period == "weekly":
            start_date = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:  # monthly
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        
        # Get spending only for the specific category within the date range
        return self.get_total_spent(category, start_date, end_date)
    
    def get_all_budgets_with_status(self) -> List[Dict]:
        """Get all budgets with their current status"""
        budgets_with_status = []
        
        for budget in self.budgets.values():
            budget_status = self.get_budget_status(budget.category, budget.period)
            if budget_status['has_budget']:
                budgets_with_status.append({
                    'category': budget.category.value,
                    'period': budget.period,
                    'status': budget_status
                })
        
        return budgets_with_status
    
    def get_spending_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get spending summary by category"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get actual spending for each category
        category_totals = self.get_total_spent_by_category(start_date, end_date)
        total_spent = sum(category_totals.values())
        
        summary = {
            'total_spent': total_spent,
            'date_range': {'start': start_date, 'end': end_date},
            'categories': {}
        }
        
        # Add budget status for each category. Prefer a monthly budget if present;
        # otherwise use any existing budget period for that category so saved budgets
        # with weekly/daily periods are not ignored.
        for category in ExpenseCategory:
            category_value = category.value
            spent = category_totals[category_value]

            # Find budgets for this category
            matching_budgets = [b for b in self.budgets.values() if b.category == category]

            if not matching_budgets:
                budget_status = {'has_budget': False}
            else:
                # Prefer monthly if available
                preferred = next((b for b in matching_budgets if b.period == 'monthly'), matching_budgets[0])
                budget_status = self.get_budget_status(category, preferred.period)

            summary['categories'][category_value] = {
                'spent': spent,
                'budget_status': budget_status,
                'percentage_of_total': (spent / total_spent * 100) if total_spent > 0 else 0
            }
        
        return summary
    
    def get_financial_insights(self) -> Dict:
        """Generate financial insights and recommendations"""
        monthly_summary = self.get_spending_summary()
        categories_data = monthly_summary['categories']
        total_spent = monthly_summary['total_spent']
        
        # Find top spending category
        top_category = "No expenses"
        top_amount = 0
        for category_name, data in categories_data.items():
            if data['spent'] > top_amount:
                top_category = category_name
                top_amount = data['spent']
        
        insights = {
            'total_monthly_spending': total_spent,
            'top_category': top_category,
            'budget_alerts': [],
            'recommendations': [],
            'savings_tips': []
        }
        
        # Check for budget overruns across all periods
        for budget in self.budgets.values():
            budget_status = self.get_budget_status(budget.category, budget.period)
            if budget_status['has_budget'] and budget_status['is_over_budget']:
                insights['budget_alerts'].append(
                    f"🚨 Over {budget.period} budget in {budget.category.value}: "
                    f"${budget_status['spent']:.2f} / ${budget_status['budget_amount']:.2f}"
                )
        
        # Generate recommendations based on actual spending
        if total_spent > 0:
            food_spent = categories_data['Food']['spent']
            if food_spent > total_spent * 0.3:
                insights['recommendations'].append(
                    "🍽️  Consider meal planning to reduce food expenses (currently {:.1f}% of total spending)".format(
                        (food_spent / total_spent) * 100
                    )
                )
            
            entertainment_spent = categories_data['Entertainment']['spent']
            if entertainment_spent > total_spent * 0.2:
                insights['recommendations'].append(
                    "🎬 Look for free entertainment options to reduce costs ({:.1f}% of total spending)".format(
                        (entertainment_spent / total_spent) * 100
                    )
                )
            
            # Add recommendation if no budgets are set
            if len(self.budgets) == 0:
                insights['recommendations'].append(
                    "📊 Set up budgets for your main spending categories to better track your expenses"
                )
        
        # Add savings tips
        insights['savings_tips'].extend([
            "💡 Track every expense, no matter how small",
            "💡 Review your budgets monthly and adjust as needed",
            "💡 Set aside 10-20% of income for savings",
            "💡 Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings"
        ])
        
        return insights
    
    def get_all_expenses(self, sort_by: str = "date", reverse: bool = True) -> List[Expense]:
        """Get all expenses for the user with sorting options"""
        expenses = self.expenses.copy()
        
        if sort_by == "date":
            expenses.sort(key=lambda x: x.date, reverse=reverse)
        elif sort_by == "amount":
            expenses.sort(key=lambda x: x.amount, reverse=reverse)
        elif sort_by == "category":
            expenses.sort(key=lambda x: x.category.value, reverse=reverse)
        
        return expenses
    
    def clear_all_data(self) -> Tuple[bool, str]:
        """Clear all expenses and budgets for the user"""
        self.expenses = []
        self.budgets = {}
        self.save_data()
        return True, "All data cleared successfully"
    
    def get_user_statistics(self) -> Dict:
        """Get comprehensive user statistics"""
        total_expenses = len(self.expenses)
        total_spent = self.get_total_spent()
        avg_expense = total_spent / total_expenses if total_expenses > 0 else 0
        
        # Most used category by count
        category_counts = {}
        # Most spent category by amount
        category_amounts = {}
        
        for expense in self.expenses:
            cat = expense.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            category_amounts[cat] = category_amounts.get(cat, 0) + expense.amount
        
        most_used_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "None"
        most_spent_category = max(category_amounts.items(), key=lambda x: x[1])[0] if category_amounts else "None"
        
        return {
            'total_expenses': total_expenses,
            'total_amount_spent': round(total_spent, 2),
            'average_expense': round(avg_expense, 2),
            'most_used_category': most_used_category,
            'most_spent_category': most_spent_category,
            'active_budgets': len(self.budgets),
            'first_expense_date': min([exp.date for exp in self.expenses]) if self.expenses else "No expenses",
            'last_expense_date': max([exp.date for exp in self.expenses]) if self.expenses else "No expenses"
        }

class ExpenseTrackerApp:
    def __init__(self):
        self.user_manager = UserManager()
        self.current_user = None
        self.current_tracker = None
    
    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """Register a new user"""
        return self.user_manager.register_user(username, password)
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Login user and initialize their expense tracker"""
        success, message = self.user_manager.login_user(username, password)
        if success:
            self.current_user = username
            self.current_tracker = ExpenseTracker(username)
            return True, message
        return False, message
    
    def logout(self) -> str:
        """Logout current user"""
        self.current_user = None
        self.current_tracker = None
        return "Logged out successfully"
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self.current_user is not None and self.current_tracker is not None
    
    def get_current_user_info(self) -> Dict:
        """Get current user information"""
        if not self.is_logged_in():
            return {}
        
        stats = self.user_manager.get_user_stats(self.current_user)
        expense_stats = self.current_tracker.get_user_statistics()
        
        return {
            'username': self.current_user,
            'registration_date': stats.get('created_at', 'Unknown'),
            'last_login': stats.get('last_login', 'Never'),
            **expense_stats
        }

def main():
    app = ExpenseTrackerApp()
    
    while True:
        clear_console()
        print("=== Expense Tracker System ===")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            success, message = app.register(username, password)
            print(f"Result: {message}")
            pause()
            
        elif choice == "2":
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            success, message = app.login(username, password)
            print(f"Result: {message}")

            if success:
                user_menu(app)
            else:
                pause()
                
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def user_menu(app):
    """User menu after login"""
    tracker = app.current_tracker
    while True:
        clear_console()
        print("\n=== Expense Tracker Menu ===")
        print("1. Add Expense")
        print("2. Edit Expense")
        print("3. Delete Expense")
        print("4. View Expenses")
        print("5. Set Budget")
        print("6. View Budgets")
        print("7. Delete Budget")
        print("8. Spending Summary")
        print("9. Financial Insights")
        print("10. User Statistics")
        print("11. Logout")

        choice = input("\nChoose option (1-11): ").strip()

        if choice == "1":
            # Add expense
            try:
                amount = float(input("Enter amount: "))
                print("Categories: ", [cat.value for cat in ExpenseCategory])
                category_name = input("Enter category: ").strip()
                description = input("Enter description: ").strip()

                category = None
                for cat in ExpenseCategory:
                    if cat.value.lower() == category_name.lower():
                        category = cat
                        break

                if category is None:
                    print("Invalid category. Using 'Other'.")
                    category = ExpenseCategory.OTHER

                success, message = tracker.add_expense(amount, category, description)
                print(f"Result: {message}")
                pause()

            except ValueError:
                print("Invalid amount. Please enter a number.")

        elif choice == "2":
            # Edit expense (select by number or full ID)
            expenses = tracker.get_all_expenses()
            if not expenses:
                print("No expenses to edit.")
                continue

            print(f"\n{'#':<4} {'ID':<25} {'Date':<12} {'Category':<15} {'Amount':<10} {'Description':<20}")
            print("-" * 95)
            for i, exp in enumerate(expenses, start=1):
                print(f"{i:<4} {exp.id:<25} {exp.date:<12} {exp.category.value:<15} ${exp.amount:<9.2f} {exp.description:<20}")

            selection = input("Enter the number or full ID of the expense to edit: ").strip()
            exp_id = None
            if selection.isdigit():
                idx = int(selection) - 1
                if idx < 0 or idx >= len(expenses):
                    print("Invalid selection number.")
                    continue
                exp_id = expenses[idx].id
            else:
                exp_id = selection

            expense = tracker.get_expense(exp_id)
            if not expense:
                print("Expense not found.")
                continue

            print("Leave input blank to keep current value.")
            new_amount = input(f"Amount [{expense.amount}]: ").strip()
            new_category = input(f"Category [{expense.category.value}]: ").strip()
            new_description = input(f"Description [{expense.description}]: ").strip()
            new_date = input(f"Date (YYYY-MM-DD) [{expense.date}]: ").strip()

            amt = None
            cat = None
            desc = None
            dt = None

            if new_amount:
                try:
                    amt = float(new_amount)
                except ValueError:
                    print("Invalid amount entered. Skipping amount update.")

            if new_category:
                for c in ExpenseCategory:
                    if c.value.lower() == new_category.lower():
                        cat = c
                        break
                if cat is None:
                    print("Invalid category entered. Skipping category update.")

            if new_description:
                desc = new_description

            if new_date:
                # basic validation
                try:
                    datetime.strptime(new_date, "%Y-%m-%d")
                    dt = new_date
                except ValueError:
                    print("Invalid date format. Skipping date update.")

            success, message = tracker.update_expense(exp_id, amount=amt, category=cat, description=desc, date=dt)
            print(f"Result: {message}")
            pause()

        elif choice == "3":
            # Delete expense (select by number or full ID)
            expenses = tracker.get_all_expenses()
            if not expenses:
                print("No expenses to delete.")
                continue

            print(f"\n{'#':<4} {'ID':<25} {'Date':<12} {'Category':<15} {'Amount':<10} {'Description':<20}")
            print("-" * 95)
            for i, exp in enumerate(expenses, start=1):
                print(f"{i:<4} {exp.id:<25} {exp.date:<12} {exp.category.value:<15} ${exp.amount:<9.2f} {exp.description:<20}")

            selection = input("Enter the number or full ID of the expense to delete: ").strip()
            exp_id = None
            if selection.isdigit():
                idx = int(selection) - 1
                if idx < 0 or idx >= len(expenses):
                    print("Invalid selection number.")
                    continue
                exp_id = expenses[idx].id
            else:
                exp_id = selection

            confirm = input(f"Are you sure you want to delete expense {exp_id}? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Deletion cancelled.")
                continue

            success, message = tracker.delete_expense(exp_id)
            print(f"Result: {message}")
            pause()

        elif choice == "4":
            # View expenses
            print("\nSort by: (1) Date (2) Amount (3) Category")
            sort_choice = input("Choose sort option (1-3) [1]: ").strip() or "1"

            # Choose scope: current month, all, or custom date range
            print("\nView: (1) Current month (2) All (3) Date range")
            view_choice = input("Choose view option (1-3) [1]: ").strip() or "1"

            # Get sorted expenses first
            if sort_choice == "2":
                expenses = tracker.get_all_expenses(sort_by="amount")
            elif sort_choice == "3":
                expenses = tracker.get_all_expenses(sort_by="category")
            else:
                expenses = tracker.get_all_expenses(sort_by="date")

            # Apply view filter if needed
            if view_choice == "1":
                # current month
                now = datetime.now()
                start_date = now.replace(day=1).strftime("%Y-%m-%d")
                end_date = now.strftime("%Y-%m-%d")
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    expenses = [exp for exp in expenses if start_dt <= datetime.strptime(exp.date, "%Y-%m-%d") <= end_dt]
                except ValueError:
                    # fallback to all if parsing fails
                    pass
            elif view_choice == "3":
                # custom date range
                sd = input("Start date (YYYY-MM-DD): ").strip()
                ed = input("End date (YYYY-MM-DD): ").strip()
                try:
                    start_dt = datetime.strptime(sd, "%Y-%m-%d")
                    end_dt = datetime.strptime(ed, "%Y-%m-%d")
                    expenses = [exp for exp in expenses if start_dt <= datetime.strptime(exp.date, "%Y-%m-%d") <= end_dt]
                except ValueError:
                    print("Invalid date(s) entered. Showing all expenses.")

            if not expenses:
                print("No expenses found.")
            else:
                print(f"\n{'Date':<12} {'Category':<15} {'Amount':<10} {'Description':<20}")
                print("-" * 60)
                for expense in expenses:
                    print(f"{expense.date:<12} {expense.category.value:<15} ${expense.amount:<9.2f} {expense.description:<20}")
            pause()

        elif choice == "5":
            # Set budget
            try:
                print("Categories: ", [cat.value for cat in ExpenseCategory])
                category_name = input("Enter category: ").strip()
                amount = float(input("Enter budget amount: "))
                period = input("Enter period (daily/weekly/monthly) [monthly]: ").strip() or "monthly"

                if period not in ["daily", "weekly", "monthly"]:
                    print("Invalid period. Using 'monthly'.")
                    period = "monthly"

                category = None
                for cat in ExpenseCategory:
                    if cat.value.lower() == category_name.lower():
                        category = cat
                        break

                if category is None:
                    print("Invalid category.")
                    continue

                success, message = tracker.set_budget(category, amount, period)
                print(f"Result: {message}")

            except ValueError:
                print("Invalid amount. Please enter a number.")

        elif choice == "6":
            # View budgets
            print("\n=== Budget Status ===")
            budgets_with_status = tracker.get_all_budgets_with_status()

            if not budgets_with_status:
                print("No budgets set. Use option 5 to set budgets.")
            else:
                print(f"{'Category':<15} {'Period':<10} {'Spent':<10} {'Budget':<10} {'Remaining':<12} {'Used %':<10} {'Status':<10}")
                print("-" * 80)

                for budget_info in budgets_with_status:
                    category = budget_info['category']
                    period = budget_info['period']
                    status = budget_info['status']

                    symbol = "🔴" if status['is_over_budget'] else "🟢"
                    status_text = "OVER" if status['is_over_budget'] else "OK"
                    print(f"{category:<15} {period:<10} ${status['spent']:<9.2f} ${status['budget_amount']:<9.2f} "
                          f"${status['remaining']:<11.2f} {status['percentage_used']:<9.1f}% {symbol} {status_text}")
                pause()

        elif choice == "7":
            # Delete budget
            print("Categories: ", [cat.value for cat in ExpenseCategory])
            category_name = input("Enter category: ").strip()
            period = input("Enter period to delete (or leave blank for all): ").strip()

            category = None
            for cat in ExpenseCategory:
                if cat.value.lower() == category_name.lower():
                    category = cat
                    break

            if category is None:
                print("Invalid category.")
                continue

            success, message = tracker.delete_budget(category, period if period else None)
            print(f"Result: {message}")
            pause()

        elif choice == "8":
            # Spending summary
            summary = tracker.get_spending_summary()
            print(f"\n=== Spending Summary ({summary['date_range']['start']} to {summary['date_range']['end']}) ===")
            print(f"{'Category':<15} {'Spent':<10} {'% of Total':<12} {'Budget Status':<15}")
            print("-" * 60)

            for category_name, data in summary['categories'].items():
                spent = data['spent']
                percentage = data['percentage_of_total']
                budget_status = data['budget_status']

                if budget_status['has_budget']:
                    status_str = f"${spent:.2f}/${budget_status['budget_amount']:.2f} ({budget_status['period']})"
                    if budget_status['is_over_budget']:
                        status_str += " 🔴"
                    else:
                        status_str += " 🟢"
                else:
                    status_str = "No budget"

                print(f"{category_name:<15} ${spent:<9.2f} {percentage:<11.1f}% {status_str:<15}")

            print(f"\nTotal Spent: ${summary['total_spent']:.2f}")
            pause()

        elif choice == "9":
            # Financial insights
            insights = tracker.get_financial_insights()
            print("\n=== Financial Insights ===")
            print(f"Total Monthly Spending: ${insights['total_monthly_spending']:.2f}")
            print(f"Top Spending Category: {insights['top_category']}")

            if insights['budget_alerts']:
                print("\n🚨 Budget Alerts:")
                for alert in insights['budget_alerts']:
                    print(f"  {alert}")

            if insights['recommendations']:
                print("\n💡 Recommendations:")
                for rec in insights['recommendations']:
                    print(f"  {rec}")

            print("\n🌟 Savings Tips:")
            for tip in insights['savings_tips']:
                print(f"  {tip}")
            pause()

        elif choice == "10":
            # User statistics
            user_info = app.get_current_user_info()
            print("\n=== User Statistics ===")
            for key, value in user_info.items():
                if key not in ['username', 'registration_date', 'last_login']:
                    print(f"{key.replace('_', ' ').title()}: {value}")
            pause()

        elif choice == "11":
            # Logout
            print(app.logout())
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()