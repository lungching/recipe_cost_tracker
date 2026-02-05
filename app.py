import streamlit as st
import pandas as pd
from datetime import datetime, date
from grocery_tracker import GroceryTracker
import matplotlib.pyplot as plt
import seaborn as sns

# Page configuration
st.set_page_config(
    page_title="Grocery Price Tracker",
    page_icon="🛒",
    layout="wide"
)

# Initialize the tracker
@st.cache_resource
def get_tracker():
    return GroceryTracker('grocery_tracker.db')

tracker = get_tracker()

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🛒 Grocery Price Tracker")
st.markdown("Track your grocery prices and generate insightful reports")
st.divider()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Add Item", 
    "📋 View Items", 
    "📊 Summary", 
    "📈 Visualizations",
    "📄 Report"
])

# Tab 1: Add Item
with tab1:
    st.header("Add New Item")
    
    col1, col2 = st.columns(2)
    
    with col1:
        item_name = st.text_input("Item Name *", key="item_name")
        price = st.number_input("Price ($) *", min_value=0.0, step=0.01, format="%.2f", key="price")
        quantity = st.number_input("Quantity", min_value=0.0, step=0.01, format="%.2f", value=None, key="quantity")
    
    with col2:
        unit = st.selectbox("Unit", [
            "",
            "oz (ounces)",
            "lb (pounds)",
            "g (grams)",
            "kg (kilograms)",
            "ml (milliliters)",
            "l (liters)",
            "gallon",
            "quart",
            "pint",
            "count",
            "each"
        ], key="unit")
        
        store = st.text_input("Store", key="store")
        purchase_date = st.date_input("Purchase Date", value=date.today(), key="purchase_date")
    
    if st.button("Add Item", type="primary"):
        if item_name and price is not None:
            try:
                # Clean up unit string
                unit_value = unit.split(" ")[0] if unit else None
                
                tracker.add_item(
                    item_name=item_name,
                    price=price,
                    quantity=quantity if quantity else None,
                    unit=unit_value,
                    store=store if store else None,
                    purchase_date=purchase_date
                )
                st.success(f"✅ Added: {item_name} - ${price:.2f}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding item: {str(e)}")
        else:
            st.warning("Please fill in required fields (Item Name and Price)")

# Tab 2: View Items
with tab2:
    st.header("All Items")
    
    df = tracker.get_all_items()
    
    if not df.empty:
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_item = st.multiselect(
                "Filter by Item",
                options=df['item_name'].unique(),
                default=None
            )
        
        with col2:
            filter_store = st.multiselect(
                "Filter by Store",
                options=df[df['store'].notna()]['store'].unique(),
                default=None
            )
        
        with col3:
            date_range = st.date_input(
                "Filter by Date Range",
                value=None,
                key="date_range"
            )
        
        # Apply filters
        filtered_df = df.copy()
        if filter_item:
            filtered_df = filtered_df[filtered_df['item_name'].isin(filter_item)]
        if filter_store:
            filtered_df = filtered_df[filtered_df['store'].isin(filter_store)]
        if date_range:
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (pd.to_datetime(filtered_df['purchase_date']).dt.date >= start_date) &
                    (pd.to_datetime(filtered_df['purchase_date']).dt.date <= end_date)
                ]
        
        st.write(f"Showing {len(filtered_df)} of {len(df)} items")
        
        # Display dataframe with delete functionality
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1.5, 1.5, 1])
            
            with col1:
                st.write(f"**{row['item_name']}**")
            with col2:
                st.write(f"${row['price']:.2f}")
            with col3:
                qty_str = f"{row['quantity']:.2f}" if pd.notna(row['quantity']) else "-"
                st.write(qty_str)
            with col4:
                st.write(row['unit'] if pd.notna(row['unit']) else "-")
            with col5:
                st.write(row['store'] if pd.notna(row['store']) else "-")
            with col6:
                st.write(str(row['purchase_date']))
            with col7:
                if st.button("🗑️", key=f"delete_{row['id']}"):
                    tracker.delete_item(int(row['id']))
                    st.success("Item deleted!")
                    st.rerun()
        
        # Download option
        st.divider()
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"grocery_items_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No items found. Start by adding your first grocery item!")

# Tab 3: Summary
with tab3:
    st.header("Summary Statistics")
    
    df = tracker.get_all_items()
    summary = tracker.get_price_summary()
    
    if not df.empty:
        # Overall statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Purchases", len(df))
        with col2:
            st.metric("Unique Items", len(summary))
        with col3:
            st.metric("Total Spent", f"${df['price'].sum():.2f}")
        with col4:
            st.metric("Average Price", f"${df['price'].mean():.2f}")
        
        st.divider()
        
        # Item-level statistics
        st.subheader("Price Summary by Item")
        
        # Format the summary dataframe for display
        display_summary = summary.copy()
        display_summary['min_price'] = display_summary['min_price'].apply(lambda x: f"${x:.2f}")
        display_summary['max_price'] = display_summary['max_price'].apply(lambda x: f"${x:.2f}")
        display_summary['avg_price'] = display_summary['avg_price'].apply(lambda x: f"${x:.2f}")
        display_summary['avg_price_per_unit'] = display_summary['avg_price_per_unit'].apply(
            lambda x: f"${x:.4f}" if pd.notna(x) else "-"
        )
        
        st.dataframe(
            display_summary,
            column_config={
                "item_name": "Item",
                "purchase_count": "Purchases",
                "min_price": "Min Price",
                "max_price": "Max Price",
                "avg_price": "Avg Price",
                "avg_price_per_unit": "Avg Price/Unit",
                "last_purchase": "Last Purchase"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No data to summarize yet.")

# Tab 4: Visualizations
with tab4:
    st.header("Data Visualizations")
    
    df = tracker.get_all_items()
    
    if not df.empty:
        # Select item for trend analysis
        st.subheader("Price Trends Over Time")
        
        selected_item = st.selectbox(
            "Select an item to view trends",
            options=["All Items"] + list(df['item_name'].unique())
        )
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.set_style("whitegrid")
        
        if selected_item == "All Items":
            for item in df['item_name'].unique():
                item_df = df[df['item_name'] == item]
                sns.lineplot(data=item_df, x='purchase_date', y='price', 
                           marker='o', label=item, linewidth=2, ax=ax)
            ax.set_title('Price Trends: All Items', fontsize=16, fontweight='bold')
        else:
            item_df = tracker.get_item_history(selected_item)
            sns.lineplot(data=item_df, x='purchase_date', y='price', 
                       marker='o', linewidth=2.5, ax=ax)
            ax.set_title(f'Price Trend: {selected_item}', fontsize=16, fontweight='bold')
        
        ax.set_xlabel('Purchase Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        st.pyplot(fig)
        
        st.divider()
        
        # Price distribution
        st.subheader("Price Distribution Analysis")
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        sns.set_style("whitegrid")
        
        # Box plot
        sns.boxplot(data=df, y='item_name', x='price', ax=axes[0])
        axes[0].set_title('Price Distribution by Item', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Price ($)', fontsize=11)
        axes[0].set_ylabel('Item', fontsize=11)
        
        # Bar plot of average prices
        summary = tracker.get_price_summary()
        sns.barplot(data=summary, y='item_name', x='avg_price', ax=axes[1])
        axes[1].set_title('Average Price by Item', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Average Price ($)', fontsize=11)
        axes[1].set_ylabel('Item', fontsize=11)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        st.divider()
        
        # Store comparison
        if df['store'].notna().any():
            st.subheader("Price Comparison by Store")
            
            store_df = df[df['store'].notna()]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.set_style("whitegrid")
            
            sns.boxplot(data=store_df, x='store', y='price', hue='item_name', ax=ax)
            ax.set_title('Price Comparison by Store', fontsize=16, fontweight='bold')
            ax.set_xlabel('Store', fontsize=12)
            ax.set_ylabel('Price ($)', fontsize=12)
            plt.xticks(rotation=45)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            
            st.pyplot(fig)
    else:
        st.info("No data to visualize yet. Add some items first!")

# Tab 5: Report Generation
with tab5:
    st.header("Generate Report")
    
    df = tracker.get_all_items()
    
    if not df.empty:
        st.subheader("Report Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_items = st.multiselect(
                "Select items to include",
                options=df['item_name'].unique(),
                default=df['item_name'].unique()
            )
        
        with col2:
            report_date_range = st.date_input(
                "Date range for report",
                value=(df['purchase_date'].min(), df['purchase_date'].max()),
                key="report_date_range"
            )
        
        include_plots = st.checkbox("Include visualizations in report", value=True)
        
        if st.button("Generate Report", type="primary"):
            # Filter data for report
            report_df = df[df['item_name'].isin(report_items)].copy()
            
            if isinstance(report_date_range, tuple) and len(report_date_range) == 2:
                start_date, end_date = report_date_range
                report_df = report_df[
                    (pd.to_datetime(report_df['purchase_date']).dt.date >= start_date) &
                    (pd.to_datetime(report_df['purchase_date']).dt.date <= end_date)
                ]
            
            st.divider()
            st.subheader("📄 Grocery Price Report")
            st.write(f"**Report Period:** {report_date_range[0]} to {report_date_range[1]}")
            st.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Executive Summary
            st.subheader("Executive Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Purchases", len(report_df))
            with col2:
                st.metric("Total Spent", f"${report_df['price'].sum():.2f}")
            with col3:
                st.metric("Average Purchase", f"${report_df['price'].mean():.2f}")
            
            # Detailed breakdown
            st.subheader("Item Breakdown")
            
            for item in report_items:
                item_df = report_df[report_df['item_name'] == item]
                if not item_df.empty:
                    with st.expander(f"**{item}** - {len(item_df)} purchases"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Min Price", f"${item_df['price'].min():.2f}")
                        with col2:
                            st.metric("Max Price", f"${item_df['price'].max():.2f}")
                        with col3:
                            st.metric("Avg Price", f"${item_df['price'].mean():.2f}")
                        with col4:
                            st.metric("Total Spent", f"${item_df['price'].sum():.2f}")
                        
                        st.dataframe(item_df[['purchase_date', 'price', 'quantity', 'unit', 'store']], 
                                   hide_index=True, use_container_width=True)
            
            # Visualizations
            if include_plots:
                st.subheader("Visual Analysis")
                
                # Price trends
                fig, ax = plt.subplots(figsize=(12, 6))
                for item in report_items:
                    item_df = report_df[report_df['item_name'] == item]
                    if not item_df.empty:
                        sns.lineplot(data=item_df, x='purchase_date', y='price', 
                                   marker='o', label=item, linewidth=2, ax=ax)
                ax.set_title('Price Trends', fontsize=16, fontweight='bold')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Price ($)', fontsize=12)
                plt.xticks(rotation=45)
                plt.legend()
                plt.tight_layout()
                st.pyplot(fig)
            
            # Recommendations
            st.subheader("Insights & Recommendations")
            
            for item in report_items:
                item_df = report_df[report_df['item_name'] == item]
                if len(item_df) > 1:
                    price_change = ((item_df['price'].iloc[0] - item_df['price'].iloc[-1]) / 
                                  item_df['price'].iloc[-1] * 100)
                    
                    if abs(price_change) > 5:
                        direction = "increased" if price_change > 0 else "decreased"
                        st.write(f"- **{item}**: Price has {direction} by {abs(price_change):.1f}% over the report period")
                    
                    if item_df['store'].notna().any():
                        best_store = item_df.groupby('store')['price'].mean().idxmin()
                        best_price = item_df.groupby('store')['price'].mean().min()
                        st.write(f"- **{item}**: Best average price at {best_store} (${best_price:.2f})")
    else:
        st.info("No data available for report generation. Add some items first!")

# Footer
st.divider()
st.markdown("*Grocery Price Tracker - Track, Analyze, Save*")