import os
from agent.tools import search_store_products

print("Search for 'لابتوب':")
print(search_store_products.invoke({"query": "لابتوب"}))

print("\nSearch for 'لابتوبات':")
print(search_store_products.invoke({"query": "لابتوبات"}))
