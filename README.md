# Grocery Price Tracker

A data-focused application to track grocery prices, analyze trends, and generate comprehensive reports.

## Features

- 📝 Track grocery items with price, quantity, unit, store, and date
- 📊 Visualize price trends over time using Seaborn
- 🏪 Compare prices across different stores
- 📈 Analyze price distributions and averages
- 📄 Generate detailed reports with insights
- 💾 DuckDB backend for efficient data storage

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management.

1. Install uv:
```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
   git clone <your-repo-url>
   cd grocery-tracker
```

3. Create virtual environment and install dependencies:
```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
```

## Usage

### Run the Streamlit App
```bash
streamlit run src/app.py
```

### Use as a Python Library
```python
from grocery_tracker import GroceryTracker

tracker = GroceryTracker('data/grocery_tracker.db')
tracker.add_item("Milk", 3.99, quantity=1, unit="gallon", store="Walmart")
summary = tracker.get_price_summary()
tracker.plot_price_trends()
```

## Testing

Run tests with:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Development

The project uses:
- `uv` for dependency management
- `pytest` for testing (configured in `pyproject.toml`)
- `src/` layout for clean imports
- DuckDB for database storage
- Claude Code

## Project Structure
```
grocery-tracker/
├── pyproject.toml         # Project configuration
├── src/                   # Source code
│   ├── grocery_tracker.py # Core tracking class
│   └── app.py            # Streamlit application
├── tests/                # Unit tests
├── data/                 # Database storage
├── docs/                 # Documentation
├── reports/              # Generated reports
└── examples/             # Example scripts
```

## License

MIT License