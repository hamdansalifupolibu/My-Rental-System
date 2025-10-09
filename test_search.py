#!/usr/bin/env python3
"""
Test script to debug the search functionality
Run this to test your search implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import get_db_connection

def test_search_functionality():
    """Test the search functionality with different parameters"""
    
    print("🔍 Testing Search Functionality")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            'name': 'Search by text',
            'params': {'search': 'apartment'},
            'description': 'Searching for "apartment" in title/description'
        },
        {
            'name': 'Filter by region',
            'params': {'region': '1'},
            'description': 'Filtering by region ID 1'
        },
        {
            'name': 'Filter by property type',
            'params': {'property_type': 'single_room'},
            'description': 'Filtering by single room property type'
        },
        {
            'name': 'Price range filter',
            'params': {'min_price': '1000', 'max_price': '5000'},
            'description': 'Filtering by price range 1000-5000'
        },
        {
            'name': 'Combined filters',
            'params': {'search': 'room', 'property_type': 'single_room', 'min_price': '500'},
            'description': 'Combined search with multiple filters'
        }
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # First, let's see what data we have
        print("\n📊 Current Database State:")
        cursor.execute("SELECT COUNT(*) as total FROM houses")
        total_houses = cursor.fetchone()['total']
        print(f"Total houses in database: {total_houses}")
        
        if total_houses > 0:
            cursor.execute("SELECT id, title, property_type, price FROM houses LIMIT 3")
            sample_houses = cursor.fetchall()
            print("Sample houses:")
            for house in sample_houses:
                print(f"  - ID: {house['id']}, Title: {house['title']}, Type: {house['property_type']}, Price: {house['price']}")
        
        # Test regions
        cursor.execute("SELECT id, name FROM regions LIMIT 5")
        regions = cursor.fetchall()
        print(f"\nAvailable regions: {[f\"{r['id']}: {r['name']}\" for r in regions]}")
        
        # Test each search case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print(f"Description: {test_case['description']}")
            print(f"Parameters: {test_case['params']}")
            
            # Build query similar to the route
            query = """
                SELECT h.*, r.name as region_name, n.name as neighborhood_name
                FROM houses h
                LEFT JOIN regions r ON h.region_id = r.id
                LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
                WHERE 1=1
            """
            params = []
            
            # Apply filters (same logic as in the route)
            search_filter = test_case['params'].get('search', '')
            if search_filter and search_filter != '':
                query += " AND (h.title LIKE %s OR h.description LIKE %s)"
                params.extend([f'%{search_filter}%', f'%{search_filter}%'])
            
            region_filter = test_case['params'].get('region', '')
            if region_filter and region_filter.strip() and region_filter.isdigit():
                query += " AND h.region_id = %s"
                params.append(int(region_filter))
            
            property_type_filter = test_case['params'].get('property_type', '')
            if property_type_filter and property_type_filter != '':
                query += " AND h.property_type = %s"
                params.append(property_type_filter)
            
            min_price = test_case['params'].get('min_price', '')
            if min_price and min_price.strip() and min_price.replace('.', '').isdigit():
                query += " AND h.price >= %s"
                params.append(float(min_price))
            
            max_price = test_case['params'].get('max_price', '')
            if max_price and max_price.strip() and max_price.replace('.', '').isdigit():
                query += " AND h.price <= %s"
                params.append(float(max_price))
            
            query += " ORDER BY h.created_at DESC"
            
            try:
                print(f"Executing query: {query}")
                print(f"With parameters: {params}")
                cursor.execute(query, params)
                results = cursor.fetchall()
                print(f"✅ Results: {len(results)} houses found")
                
                if results:
                    for house in results[:3]:  # Show first 3 results
                        print(f"  - {house['title']} ({house['property_type']}) - GHS {house['price']}")
                else:
                    print("  No results found")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                print(f"Query: {query}")
                print(f"Params: {params}")
    
    except Exception as e:
        print(f"❌ Database connection error: {e}")
    
    finally:
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 50)
    print("✅ Search functionality test completed!")

if __name__ == "__main__":
    test_search_functionality()
