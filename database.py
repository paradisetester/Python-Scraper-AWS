import os
import json
import requests
from datetime import datetime

# WordPress REST API configuration
WORDPRESS_URL = "https://online-app-flex-cars.com"  
API_BASE = f"{WORDPRESS_URL}/wp-json/cars-scraper/v1"

FIELDS = [
    'id', 'title', 'price', 'mileage', 'exterior_color', 'interior_color',
    'engine', 'transmission', 'drivetrain', 'fuel_type', 'mpg', 'vin',
    'stock_', 'features_exterior', 'features_seating', 'features_safety',
    'features_convenience', 'features_entertainment',
    'additional_popular_features', 'all_features', 'images',
    'start_payment', 'payment_breakdown', 'status_flag',
    'make', 'model', 'status', 'year',
    'bodystyle', 'location'
]

def get_wordpress_nonce():
    """Get WordPress nonce for authentication"""
    try:
        return "test_nonce"
    except Exception:
        return None

def update_wordpress_database(car_data_list):
    """Update WordPress database via REST API"""
    try:
        # Remove 'last_updated' from each record so MySQL can auto-update it
        for car in car_data_list:
            car.pop('last_updated', None)
        
        # Send data to WordPress REST API endpoint
        username = "Puneet"
        app_password = "MgMD pIbf hRkM EJq6 NJut n0cn"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        def sanitize_car(car):
            return {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in car.items() if k in FIELDS}
        
        payload = {
            'cars_data': [sanitize_car(car) for car in car_data_list],
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{API_BASE}/update-cars-data",
            json=payload,
            headers=headers,
            auth=(username, app_password),
            timeout=30
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"Database update error: {e}")
        return False

def get_cars_data_from_wordpress(limit=100):
    """Get cars data from WordPress via REST API"""
    try:
        response = requests.get(f"{API_BASE}/get-cars-data?limit={limit}", timeout=10)
        if response.status_code == 200:
            return response.json().get('cars_data', [])
        else:
            return []
    except Exception as e:
        print(f"Database fetch error: {e}")
        return []

def dynamic_insert_or_update(conn, car_data):
    """Legacy function - now just updates WordPress via REST API"""
    car_data_list = [car_data]
    return update_wordpress_database(car_data_list)

def create_connection():
    """Legacy function - returns None since we're not using direct database connections"""
    return None