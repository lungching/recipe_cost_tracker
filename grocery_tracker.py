import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

class GroceryTracker:
    def __init__(self, db_path='grocery_tracker.db'):
        """Initialize the grocery tracker with a DuckDB database."""
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._create_table()
        
    def _create_table(self):
        """Create the grocery items table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS grocery_items (
                id INTEGER PRIMARY KEY,
                item_name VARCHAR NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                quantity DECIMAL(10, 2),
                unit VARCHAR,
                store VARCHAR,
                purchase_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS item_id_seq START 1
        """)
    
    def add_item(self, item_name, price, quantity=None, unit=None, store=None, purchase_date=None):
        """Add a new grocery item to the database."""
        if purchase_date is None:
            purchase_date = datetime.now().date()
        
        self.conn.execute("""
            INSERT INTO grocery_items (id, item_name, price, quantity, unit, store, purchase_date)
            VALUES (nextval('item_id_seq'), ?, ?, ?, ?, ?, ?)
        """, [item_name, price, quantity, unit, store, purchase_date])
        
        quantity_str = f" ({quantity} {unit})" if quantity and unit else ""
        print(f"✓ Added: {item_name}{quantity_str} - ${price:.2f}")
    
    def get_all_items(self):
        """Get all items from the database."""
        return self.conn.execute("""
            SELECT * FROM grocery_items
            ORDER BY purchase_date DESC
        """).df()
    
    def get_item_history(self, item_name):
        """Get purchase history for a specific item."""
        return self.conn.execute("""
            SELECT * FROM grocery_items
            WHERE LOWER(item_name) = LOWER(?)
            ORDER BY purchase_date DESC
        """, [item_name]).df()
    
    def get_price_summary(self):
        """Get summary statistics for each item."""
        return self.conn.execute("""
            SELECT 
                item_name,
                COUNT(*) as purchase_count,
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(price) as avg_price,
                ROUND(AVG(price / NULLIF(quantity, 0)), 4) as avg_price_per_unit,
                MAX(purchase_date) as last_purchase
            FROM grocery_items
            GROUP BY item_name
            ORDER BY last_purchase DESC
        """).df()
    
    def delete_item(self, item_id):
        """Delete an item by ID."""
        self.conn.execute("DELETE FROM grocery_items WHERE id = ?", [item_id])
        print(f"✓ Deleted item ID: {item_id}")
    
    def plot_price_trends(self, item_name=None, save_path=None):
        """Plot price trends over time."""
        if item_name:
            df = self.get_item_history(item_name)
            title = f'Price Trend: {item_name}'
        else:
            df = self.get_all_items()
            title = 'Price Trends: All Items'
        
        if df.empty:
            print("No data to plot.")
            return
        
        plt.figure(figsize=(12, 6))
        sns.set_style("whitegrid")
        
        if item_name:
            sns.lineplot(data=df, x='purchase_date', y='price', marker='o', linewidth=2.5)
        else:
            for item in df['item_name'].unique():
                item_df = df[df['item_name'] == item]
                sns.lineplot(data=item_df, x='purchase_date', y='price', 
                           marker='o', label=item, linewidth=2)
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('Purchase Date', fontsize=12)
        plt.ylabel('Price ($)', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Plot saved to: {save_path}")
        else:
            plt.show()
    
    def plot_price_distribution(self, save_path=None):
        """Plot price distribution across all items."""
        df = self.get_all_items()
        
        if df.empty:
            print("No data to plot.")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        sns.set_style("whitegrid")
        
        # Box plot
        sns.boxplot(data=df, y='item_name', x='price', ax=axes[0])
        axes[0].set_title('Price Distribution by Item', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Price ($)', fontsize=11)
        axes[0].set_ylabel('Item', fontsize=11)
        
        # Bar plot of average prices
        summary = self.get_price_summary()
        sns.barplot(data=summary, y='item_name', x='avg_price', ax=axes[1])
        axes[1].set_title('Average Price by Item', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Average Price ($)', fontsize=11)
        axes[1].set_ylabel('Item', fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Plot saved to: {save_path}")
        else:
            plt.show()
    
    def plot_store_comparison(self, save_path=None):
        """Compare prices across different stores."""
        df = self.get_all_items()
        df = df[df['store'].notna()]
        
        if df.empty:
            print("No store data to plot.")
            return
        
        plt.figure(figsize=(12, 6))
        sns.set_style("whitegrid")
        
        sns.boxplot(data=df, x='store', y='price', hue='item_name')
        plt.title('Price Comparison by Store', fontsize=16, fontweight='bold')
        plt.xlabel('Store', fontsize=12)
        plt.ylabel('Price ($)', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Plot saved to: {save_path}")
        else:
            plt.show()
    
    def close(self):
        """Close the database connection."""
        self.conn.close()


# Example usage
if __name__ == "__main__":
    # Initialize tracker
    tracker = GroceryTracker()
    
    # Add some sample items
    tracker.add_item("Milk", 3.99, quantity=1, unit="gallon", store="Walmart", purchase_date="2024-01-01")
    tracker.add_item("Milk", 4.29, quantity=1, unit="gallon", store="Target", purchase_date="2024-01-15")
    tracker.add_item("Milk", 3.89, quantity=1, unit="gallon", store="Walmart", purchase_date="2024-02-01")
    tracker.add_item("Bread", 2.49, quantity=24, unit="oz", store="Walmart", purchase_date="2024-01-01")
    tracker.add_item("Bread", 2.99, quantity=24, unit="oz", store="Target", purchase_date="2024-01-15")
    tracker.add_item("Eggs", 4.99, quantity=12, unit="count", store="Walmart", purchase_date="2024-01-01")
    tracker.add_item("Eggs", 5.49, quantity=12, unit="count", store="Target", purchase_date="2024-01-15")
    
    # Display summary
    print("\n=== Price Summary ===")
    print(tracker.get_price_summary())
    
    # Display all items
    print("\n=== All Items ===")
    print(tracker.get_all_items())
    
    # Generate plots
    print("\n=== Generating Plots ===")
    tracker.plot_price_trends(item_name="Milk")
    tracker.plot_price_distribution()
    tracker.plot_store_comparison()
    
    # Close connection
    tracker.close()