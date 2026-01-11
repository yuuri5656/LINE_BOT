
import sys
import os
from decimal import Decimal

sys.path.append(os.getcwd())
from apps.stock.models import SessionLocal, AITraderHolding, StockSymbol, AITrader

def verify_negative_quantity():
    db = SessionLocal()
    try:
        # Check if we can insert/update a negative quantity
        # Find a trader and a stock
        trader = db.query(AITrader).first()
        stock = db.query(StockSymbol).first()
        
        if not trader or not stock:
            print("No trader or stock found to test.")
            return

        print(f"Testing with Trader: {trader.name}, Stock: {stock.symbol_code}")

        # Check existing holding
        holding = db.query(AITraderHolding).filter_by(trader_id=trader.trader_id, symbol_id=stock.symbol_id).first()
        
        if holding:
            print(f"Existing holding: {holding.quantity}")
            # Update to negative
            holding.quantity = -10
        else:
            # Create negative
            holding = AITraderHolding(
                trader_id=trader.trader_id,
                symbol_id=stock.symbol_id,
                quantity=-10,
                average_price=Decimal("1000")
            )
            db.add(holding)
        
        db.commit()
        print("Successfully committed negative quantity!")
        
        # Verify read
        db.refresh(holding)
        print(f"Read quantity: {holding.quantity}")
        if holding.quantity == -10:
            print("Verification PASSED")
        else:
            print("Verification FAILED: Quantity mismatch")

        # Cleanup (restore to positive or 0 if it was new/changed, but for test just leaving it is fine or maybe revert)
        # Assuming this is a test env or acceptable to change one record.
        # Let's revert to 0 or delete if it was created
        
    except Exception as e:
        db.rollback()
        print(f"Verification FAILED with error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_negative_quantity()
