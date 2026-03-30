#!/usr/bin/env python3
"""
Local Test Script for Data Generation
Run this to test the data generation logic before uploading to Databricks
"""

import uuid
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

# Configuration
CONFIG = {
    "seed": int(datetime.now().strftime("%Y%m%d")),
    "null_rate": 0.02,
    "duplicate_rate": 0.005,
    "sla_breach_rate": 0.12,
    "refund_rate": 0.08,
}

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"]

np.random.seed(CONFIG["seed"])

print("="*60)
print("LOCAL TEST - Data Generation")
print("="*60)

# Test 1: Generate Restaurants
print("\n1. Testing restaurant generation...")
cuisines = ["Biryani", "Chinese", "South Indian", "North Indian", "Fast Food", "Pizza", "Desserts", "Continental"]
ratings = ["Excellent", "Good", "Average", "Poor"]

restaurants = []
for i in range(10):  # Small sample
    restaurants.append({
        "restaurant_id": f"REST-{i+1:05d}",
        "city": np.random.choice(CITIES),
        "cuisine_type": np.random.choice(cuisines),
        "rating_band": np.random.choice(ratings, p=[0.1, 0.4, 0.35, 0.15]),
        "onboarding_date": (date.today() - timedelta(days=np.random.randint(30, 365))).isoformat()
    })

restaurants_df = pd.DataFrame(restaurants)
print(f"✓ Generated {len(restaurants_df)} restaurants")
print(restaurants_df.head(3))

# Test 2: Build restaurant lookup (the fixed version)
print("\n2. Testing restaurant lookup by city...")
restaurant_by_city = {}
for city in CITIES:
    city_df = restaurants_df[restaurants_df["city"] == city]
    restaurant_by_city[city] = city_df.to_dict("records")

print(f"✓ Built lookup for {len(restaurant_by_city)} cities")
for city, rests in restaurant_by_city.items():
    if rests:
        print(f"  {city}: {len(rests)} restaurants")

# Test 3: Generate sample orders
print("\n3. Testing order generation...")
HOUR_WEIGHTS = [1,2,3,8,10,6, 3,3,4,7,10,8, 6,4,2,1]
STATUS_WEIGHTS = {"delivered": 0.85, "cancelled": 0.10, "in_progress": 0.05}
PAYMENT_MODES = {"UPI": 0.55, "Card": 0.20, "COD": 0.15, "Wallet": 0.10}

target_date = date.today()
orders = []

for _ in range(5):  # Small sample
    hours = list(range(8, 24))
    weights = np.array(HOUR_WEIGHTS) / sum(HOUR_WEIGHTS)
    hour = int(np.random.choice(hours, p=weights))
    minute = np.random.randint(0, 60)
    order_ts = datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0)
    
    city = np.random.choice(CITIES)
    city_restaurants = restaurant_by_city.get(city, [])
    restaurant = np.random.choice(city_restaurants) if city_restaurants else restaurants_df.sample(1).to_dict("records")[0]
    
    sla_minutes = np.random.randint(30, 45)
    promised_ts = order_ts + timedelta(minutes=sla_minutes)
    
    status = np.random.choice(list(STATUS_WEIGHTS.keys()), p=list(STATUS_WEIGHTS.values()))
    order_value = round(np.random.lognormal(5.5, 0.6), 2)
    order_value = max(50, min(order_value, 5000))
    payment_mode = np.random.choice(list(PAYMENT_MODES.keys()), p=list(PAYMENT_MODES.values()))
    
    orders.append({
        "order_id": f"ORD-{uuid.uuid4().hex[:12].upper()}",
        "customer_id": f"CUST-{np.random.randint(10000, 99999)}",
        "restaurant_id": restaurant["restaurant_id"],
        "city": city,
        "order_ts": order_ts.isoformat(),
        "promised_delivery_ts": promised_ts.isoformat(),
        "status": status,
        "order_value": order_value,
        "payment_mode": payment_mode,
    })

orders_df = pd.DataFrame(orders)
print(f"✓ Generated {len(orders_df)} orders")
print(orders_df[["order_id", "city", "status", "order_value"]].head())

# Test 4: Generate delivery events
print("\n4. Testing delivery event generation...")
EVENT_SEQUENCE = ["order_confirmed", "restaurant_accepted", "food_ready", "rider_assigned", "delivered"]

events = []
for _, order in orders_df.iterrows():
    current_ts = pd.to_datetime(order["order_ts"])
    for event_type in EVENT_SEQUENCE:
        current_ts += timedelta(minutes=np.random.randint(5, 15))
        events.append({
            "order_id": order["order_id"],
            "event_type": event_type,
            "event_ts": current_ts.isoformat(),
        })

events_df = pd.DataFrame(events)
print(f"✓ Generated {len(events_df)} delivery events")
print(events_df.head(3))

print("\n" + "="*60)
print("ALL TESTS PASSED ✓")
print("="*60)
print("\nYou can now upload the notebooks to Databricks!")
print("\nNext steps:")
print("1. Upload all 5 .ipynb files to Databricks")
print("2. Run them in order: 01 → 02 → 03 → 04")
print("3. Check the tables with: spark.catalog.listTables()")
