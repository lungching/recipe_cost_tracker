import unittest
import os
import tempfile
from datetime import datetime, date
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Import the GroceryTracker class from the main module
from grocery_tracker import GroceryTracker


class TestGroceryTracker(unittest.TestCase):
    """Test suite for GroceryTracker class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.tracker = GroceryTracker(self.db_path)
        
    def tearDown(self):
        """Clean up after each test method."""
        self.tracker.close()
        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_initialization(self):
        """Test that tracker initializes correctly."""
        self.assertIsNotNone(self.tracker.conn)
        self.assertEqual(self.tracker.db_path, self.db_path)
        
        # Verify table exists
        result = self.tracker.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='grocery_items'"
        ).fetchall()
        self.assertTrue(len(result) > 0 or self.tracker.get_all_items() is not None)
    
    def test_add_item_basic(self):
        """Test adding a basic item."""
        self.tracker.add_item("Milk", 3.99)
        
        df = self.tracker.get_all_items()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['item_name'], "Milk")
        self.assertEqual(float(df.iloc[0]['price']), 3.99)
    
    def test_add_item_with_store(self):
        """Test adding an item with store information."""
        self.tracker.add_item("Bread", 2.49, store="Walmart")
        
        df = self.tracker.get_all_items()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['store'], "Walmart")
    
    def test_add_item_with_date(self):
        """Test adding an item with a specific date."""
        test_date = date(2024, 1, 15)
        self.tracker.add_item("Eggs", 4.99, purchase_date=test_date)
        
        df = self.tracker.get_all_items()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['purchase_date'], test_date)
    
    def test_add_multiple_items(self):
        """Test adding multiple items."""
        self.tracker.add_item("Milk", 3.99)
        self.tracker.add_item("Bread", 2.49)
        self.tracker.add_item("Eggs", 4.99)
        
        df = self.tracker.get_all_items()
        self.assertEqual(len(df), 3)
    
    def test_get_all_items_empty(self):
        """Test getting all items when database is empty."""
        df = self.tracker.get_all_items()
        self.assertTrue(df.empty)
    
    def test_get_all_items_ordering(self):
        """Test that items are returned in descending date order."""
        self.tracker.add_item("Item1", 1.00, purchase_date=date(2024, 1, 1))
        self.tracker.add_item("Item2", 2.00, purchase_date=date(2024, 1, 15))
        self.tracker.add_item("Item3", 3.00, purchase_date=date(2024, 1, 10))
        
        df = self.tracker.get_all_items()
        dates = df['purchase_date'].tolist()
        self.assertEqual(dates[0], date(2024, 1, 15))
        self.assertEqual(dates[1], date(2024, 1, 10))
        self.assertEqual(dates[2], date(2024, 1, 1))
    
    def test_get_item_history(self):
        """Test getting history for a specific item."""
        self.tracker.add_item("Milk", 3.99, purchase_date=date(2024, 1, 1))
        self.tracker.add_item("Milk", 4.29, purchase_date=date(2024, 1, 15))
        self.tracker.add_item("Bread", 2.49, purchase_date=date(2024, 1, 10))
        
        milk_history = self.tracker.get_item_history("Milk")
        self.assertEqual(len(milk_history), 2)
        self.assertTrue(all(milk_history['item_name'] == "Milk"))
    
    def test_get_item_history_case_insensitive(self):
        """Test that item history search is case-insensitive."""
        self.tracker.add_item("Milk", 3.99)
        self.tracker.add_item("MILK", 4.29)
        
        history = self.tracker.get_item_history("milk")
        self.assertEqual(len(history), 2)
    
    def test_get_item_history_nonexistent(self):
        """Test getting history for a non-existent item."""
        self.tracker.add_item("Milk", 3.99)
        
        history = self.tracker.get_item_history("Orange Juice")
        self.assertTrue(history.empty)
    
    def test_get_price_summary(self):
        """Test getting price summary statistics."""
        self.tracker.add_item("Milk", 3.99, purchase_date=date(2024, 1, 1))
        self.tracker.add_item("Milk", 4.29, purchase_date=date(2024, 1, 15))
        self.tracker.add_item("Milk", 3.89, purchase_date=date(2024, 2, 1))
        
        summary = self.tracker.get_price_summary()
        self.assertEqual(len(summary), 1)
        
        milk_summary = summary.iloc[0]
        self.assertEqual(milk_summary['item_name'], "Milk")
        self.assertEqual(milk_summary['purchase_count'], 3)
        self.assertEqual(float(milk_summary['min_price']), 3.89)
        self.assertEqual(float(milk_summary['max_price']), 4.29)
        self.assertAlmostEqual(float(milk_summary['avg_price']), 4.056667, places=2)
    
    def test_get_price_summary_multiple_items(self):
        """Test price summary with multiple items."""
        self.tracker.add_item("Milk", 3.99)
        self.tracker.add_item("Milk", 4.29)
        self.tracker.add_item("Bread", 2.49)
        self.tracker.add_item("Eggs", 4.99)
        
        summary = self.tracker.get_price_summary()
        self.assertEqual(len(summary), 3)
        self.assertEqual(set(summary['item_name']), {"Milk", "Bread", "Eggs"})
    
    def test_delete_item(self):
        """Test deleting an item."""
        self.tracker.add_item("Milk", 3.99)
        df = self.tracker.get_all_items()
        item_id = df.iloc[0]['id']
        
        self.tracker.delete_item(item_id)
        df_after = self.tracker.get_all_items()
        self.assertTrue(df_after.empty)
    
    def test_delete_item_multiple(self):
        """Test deleting one item from multiple items."""
        self.tracker.add_item("Milk", 3.99)
        self.tracker.add_item("Bread", 2.49)
        self.tracker.add_item("Eggs", 4.99)
        
        df = self.tracker.get_all_items()
        item_id = df.iloc[0]['id']
        
        self.tracker.delete_item(item_id)
        df_after = self.tracker.get_all_items()
        self.assertEqual(len(df_after), 2)
    
    def test_plot_price_trends_single_item(self):
        """Test plotting price trends for a single item."""
        self.tracker.add_item("Milk", 3.99, purchase_date=date(2024, 1, 1))
        self.tracker.add_item("Milk", 4.29, purchase_date=date(2024, 1, 15))
        
        # Test that plot doesn't raise an error
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            try:
                self.tracker.plot_price_trends(item_name="Milk", save_path=tmp.name)
                self.assertTrue(os.path.exists(tmp.name))
                self.assertGreater(os.path.getsize(tmp.name), 0)
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)
    
    def test_plot_price_trends_all_items(self):
        """Test plotting price trends for all items."""
        self.tracker.add_item("Milk", 3.99, purchase_date=date(2024, 1, 1))
        self.tracker.add_item("Bread", 2.49, purchase_date=date(2024, 1, 1))
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            try:
                self.tracker.plot_price_trends(save_path=tmp.name)
                self.assertTrue(os.path.exists(tmp.name))
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)
    
    def test_plot_price_trends_empty_data(self):
        """Test plotting with empty data."""
        # Should handle empty data gracefully
        self.tracker.plot_price_trends(item_name="Milk")
        # If no exception raised, test passes
    
    def test_plot_price_distribution(self):
        """Test plotting price distribution."""
        self.tracker.add_item("Milk", 3.99)
        self.tracker.add_item("Milk", 4.29)
        self.tracker.add_item("Bread", 2.49)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            try:
                self.tracker.plot_price_distribution(save_path=tmp.name)
                self.assertTrue(os.path.exists(tmp.name))
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)
    
    def test_plot_store_comparison(self):
        """Test plotting store comparison."""
        self.tracker.add_item("Milk", 3.99, store="Walmart")
        self.tracker.add_item("Milk", 4.29, store="Target")
        self.tracker.add_item("Bread", 2.49, store="Walmart")
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            try:
                self.tracker.plot_store_comparison(save_path=tmp.name)
                self.assertTrue(os.path.exists(tmp.name))
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)
    
    def test_plot_store_comparison_no_store_data(self):
        """Test store comparison plot with no store data."""
        self.tracker.add_item("Milk", 3.99)
        # Should handle gracefully
        self.tracker.plot_store_comparison()
    
    def test_database_persistence(self):
        """Test that data persists after closing and reopening connection."""
        self.tracker.add_item("Milk", 3.99)
        self.tracker.close()
        
        # Reopen with same database
        tracker2 = GroceryTracker(self.db_path)
        df = tracker2.get_all_items()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['item_name'], "Milk")
        tracker2.close()
    
    def test_sequence_increments(self):
        """Test that IDs increment properly."""
        self.tracker.add_item("Item1", 1.00)
        self.tracker.add_item("Item2", 2.00)
        self.tracker.add_item("Item3", 3.00)
        
        df = self.tracker.get_all_items()
        ids = sorted(df['id'].tolist())
        
        # IDs should be sequential
        self.assertEqual(len(set(ids)), 3)  # All unique
        self.assertEqual(ids[2] - ids[0], 2)  # Sequential increment


class TestGroceryTrackerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.tracker = GroceryTracker(self.db_path)
    
    def tearDown(self):
        """Clean up."""
        self.tracker.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_add_item_with_special_characters(self):
        """Test adding items with special characters in name."""
        self.tracker.add_item("Ben & Jerry's Ice Cream", 5.99)
        df = self.tracker.get_all_items()
        self.assertEqual(df.iloc[0]['item_name'], "Ben & Jerry's Ice Cream")
    
    def test_add_item_with_very_long_name(self):
        """Test adding an item with a very long name."""
        long_name = "A" * 500
        self.tracker.add_item(long_name, 1.99)
        df = self.tracker.get_all_items()
        self.assertEqual(df.iloc[0]['item_name'], long_name)
    
    def test_add_item_with_zero_price(self):
        """Test adding an item with zero price."""
        self.tracker.add_item("Free Sample", 0.00)
        df = self.tracker.get_all_items()
        self.assertEqual(float(df.iloc[0]['price']), 0.00)
    
    def test_add_item_with_high_precision_price(self):
        """Test adding an item with high precision price."""
        self.tracker.add_item("Gas", 3.459)
        df = self.tracker.get_all_items()
        # Price should be stored with appropriate precision
        self.assertAlmostEqual(float(df.iloc[0]['price']), 3.46, places=2)
    
    def test_delete_nonexistent_item(self):
        """Test deleting an item that doesn't exist."""
        # Should not raise an error
        self.tracker.delete_item(99999)
        df = self.tracker.get_all_items()
        self.assertTrue(df.empty)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)