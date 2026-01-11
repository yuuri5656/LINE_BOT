import sys
import os
sys.path.append(os.getcwd())

print("Importing stock_api...")
try:
    from apps.stock.api import stock_api
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
