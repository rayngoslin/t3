import sqlite3
import os
from datetime import date

DB_FILE = "shop.db"

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        print(f"Successfully connected to database: {DB_FILE}")
    except sqlite3.Error as e:
        print(e)
    return conn

def setup_database(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            order_date DATE NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """)
        conn.commit()
        print("Database setup complete. Tables are ready.")
    except sqlite3.Error as e:
        print(f"Error during setup: {e}")
        conn.rollback()

def execute_and_print(conn, query, params=None):
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        if not results:
            print("Query executed, but no results were returned.")
            return

        headers = [description[0] for description in cursor.description]
        print("\n--- Query Results ---")
        print(f"{' | '.join(headers)}")
        print("-" * (sum(len(h) for h in headers) + len(headers) * 3))

        for row in results:
            print(f"{' | '.join(map(str, row))}")
        print("---------------------\n")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

def add_products(conn):
    products_to_add = [
        ('iPhone 15 Pro', 'smartphones', 1199.99),
        ('Samsung Galaxy S25', 'smartphones', 1099.99),
        ('MacBook Air M4', 'laptops', 1299.00),
        ('Dell XPS 15', 'laptops', 1899.50),
        ('iPad Pro', 'tablets', 999.00),
        ('Samsung Galaxy Tab S10', 'tablets', 750.00)
    ]
    query = "INSERT INTO products (name, category, price) VALUES (?, ?, ?);"
    cursor = conn.cursor()
    cursor.executemany(query, products_to_add)
    print(f"{cursor.rowcount} products added.")

def add_customers(conn):
    customers_to_add = [
        ('John', 'Doe', 'john.doe@example.com'),
        ('Jane', 'Smith', 'jane.smith@example.com'),
        ('Peter', 'Jones', 'peter.jones@example.com')
    ]
    query = "INSERT INTO customers (first_name, last_name, email) VALUES (?, ?, ?);"
    cursor = conn.cursor()
    cursor.executemany(query, customers_to_add)
    print(f"{cursor.rowcount} customers added.")

def add_orders(conn):
    orders_to_add = [
        (1, 1, 1, date.today()),
        (1, 3, 1, date.today()),
        (2, 2, 2, date.today()),
        (3, 5, 1, date.today()), 
        (2, 1, 1, date.today())
    ]
    query = "INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (?, ?, ?, ?);"
    cursor = conn.cursor()
    cursor.executemany(query, orders_to_add)
    print(f"{cursor.rowcount} orders added.")

def get_total_sales(conn):
    query = """
    SELECT SUM(p.price * o.quantity) AS total_sales
    FROM orders o
    JOIN products p ON o.product_id = p.id;
    """
    execute_and_print(conn, query)

def get_orders_per_customer(conn):
    query = """
    SELECT c.first_name, c.last_name, COUNT(o.id) AS order_count
    FROM customers c
    INNER JOIN orders o ON c.id = o.customer_id
    GROUP BY c.id;
    """
    execute_and_print(conn, query)

def get_average_order_value(conn):
    query = """
    SELECT AVG(order_total) AS average_order_value
    FROM (
        SELECT SUM(p.price * o.quantity) AS order_total
        FROM orders o
        JOIN products p ON o.product_id = p.id
        GROUP BY o.id
    );
    """
    execute_and_print(conn, query)

def get_most_popular_category(conn):
    query = """
    SELECT p.category, COUNT(o.id) AS orders_in_category
    FROM products p
    JOIN orders o ON p.id = o.product_id
    GROUP BY p.category
    ORDER BY orders_in_category DESC
    LIMIT 1;
    """
    execute_and_print(conn, query)

def get_products_per_category(conn):
    query = """
    SELECT category, COUNT(id) AS product_count
    FROM products
    GROUP BY category;
    """
    execute_and_print(conn, query)

def update_smartphone_prices(conn):
    query = """
    UPDATE products
    SET price = price * 1.10
    WHERE category = 'smartphones';
    """
    cursor = conn.cursor()
    cursor.execute(query)
    print(f"{cursor.rowcount} smartphone prices updated by 10%.")

def main_menu():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed old database file: {DB_FILE}")

    conn = create_connection()
    if not conn:
        return

    setup_database(conn)

    actions = {
        '1': ('Add products', add_products),
        '2': ('Add customers', add_customers),
        '3': ('Add orders', add_orders),
        '4': ('Show total sales', get_total_sales),
        '5': ('Show orders per customer', get_orders_per_customer),
        '6': ('Show average order value', get_average_order_value),
        '7': ('Show most popular category', get_most_popular_category),
        '8': ('Show products per category', get_products_per_category),
        '9': ('Update smartphone prices by 10%', update_smartphone_prices),
    }

    while True:
        print("\n--- SQL Database Manager ---")
        for key, (desc, _) in actions.items():
            print(f"{key}. {desc}")
        print("0. Exit")
        
        choice = input("Enter your choice: ")

        if choice == '0':
            break
        
        action_tuple = actions.get(choice)
        if action_tuple:
            description, func = action_tuple
            print(f"\nExecuting: {description}...")
            
            is_modification = choice in ['1', '2', '3', '9']
            
            try:
                func(conn)
                if is_modification:
                    save_choice = input("Save changes to the database? (y/n): ").lower()
                    if save_choice == 'y':
                        conn.commit()
                        print("Changes saved.")
                    else:
                        conn.rollback()
                        print("Changes rolled back.")
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
                conn.rollback()
        else:
            print("Invalid choice, please try again.")

    conn.close()
    print("Database connection closed.")

if __name__ == '__main__':
    main_menu()