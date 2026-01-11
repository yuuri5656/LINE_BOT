import sys
import os
import time
from decimal import Decimal
from datetime import datetime

sys.path.append(os.getcwd())

from apps.stock.api import stock_api
from apps.stock.models import SessionLocal, StockSymbol, StockAccount, UserStockShortPosition
from apps.stock.price_service import price_service
from apps.banking.api import banking_api
from apps.banking.main_bank_system import Account, SessionLocal as BankingSessionLocal

USER_ID = "test_user_short"
SYMBOL_CODE = "7203"  # Assuming Toyota or similar exists
QUANTITY = 100

def setup_test_environment():
    print("Setting up test environment...")
    
    # 1. Ensure Customer & Account
    db = BankingSessionLocal()
    from apps.banking.main_bank_system import Customer, Branch
    
    # Create Customer if not exists
    customer = db.query(Customer).filter_by(user_id=USER_ID).first()
    if not customer:
        customer = Customer(
            full_name="Test Short User",
            date_of_birth=datetime.now(),
            user_id=USER_ID
        )
        db.add(customer)
        db.commit()
    
    bank_account = db.query(Account).filter_by(user_id=USER_ID).first()
    if not bank_account:
        print("Creating User Bank Account...")
        
        branch = db.query(Branch).first()
        if not branch:
             branch = Branch(code="001", name="Test Branch")
             db.add(branch)
             db.commit()
             
        bank_account = Account(
            customer_id=customer.customer_id,
            account_number="999888111",
            branch_id=branch.branch_id, 
            balance=10000000, # 10M JPY
            currency='JPY',
            user_id=USER_ID
        )
        db.add(bank_account)
        db.commit()
    else:
        bank_account.balance = 10000000 # Reset balance
        db.commit()
    
    bank_account_id = bank_account.account_id
    db.close()

    # 2. Ensure Reserve Account
    db = BankingSessionLocal()
    reserve = db.query(Account).filter_by(account_number='7777777').first()
    if not reserve:
        print("Creating Reserve Account...")
        # Create System Customer
        sys_customer = db.query(Customer).filter_by(user_id='system_reserve').first()
        if not sys_customer:
            sys_customer = Customer(
                full_name="Stock System Reserve",
                date_of_birth=datetime.now(),
                user_id="system_reserve"
            )
            db.add(sys_customer)
            db.commit()

        branch = db.query(Branch).first()

        reserve = Account(
            customer_id=sys_customer.customer_id,
            account_number='7777777',
            branch_id=branch.branch_id,
            balance=100000000,
            currency='JPY',
            user_id="system_reserve"
        )
        db.add(reserve)
        db.commit()
    db.close()

    # 3. Ensure Stock Account
    stock_account = stock_api.get_stock_account(USER_ID)
    if not stock_account:
        print("Creating Stock Account...")
        stock_api.create_stock_account(USER_ID, bank_account_id)
    
    # 4. Cleanup existing short positions for test user
    db = SessionLocal()
    existing_shorts = db.query(UserStockShortPosition).filter_by(user_id=USER_ID).all()
    if existing_shorts:
        print(f"Cleaning up {len(existing_shorts)} existing short positions...")
        for s in existing_shorts:
            db.delete(s)
        db.commit()
    
    # 5. Ensure Stock Symbol
    stock = stock_api.get_stock_by_code(SYMBOL_CODE)
    if not stock:
        # Create dummy stock if not exists
        stock = StockSymbol(
            symbol_code=SYMBOL_CODE,
            name="Test Motor",
            sector="Automotive",
            initial_price=2000,
            current_price=2000,
            volatility=0.02,
            dividend_yield=2.5
        )
        db.add(stock)
        db.commit()
    else:
        # Reset price
        stock = db.query(StockSymbol).filter_by(symbol_code=SYMBOL_CODE).first()
        stock.current_price = 2000
        db.commit()
        
    db.close()

def test_short_selling():
    print("\n--- Testing Short Selling ---")
    
    # Sell Short
    print(f"Selling Short {QUANTITY} of {SYMBOL_CODE}...")
    success, msg, result = stock_api.sell_short(USER_ID, SYMBOL_CODE, QUANTITY)
    if not success:
        print(f"FAILED: {msg}")
        return
    print(f"SUCCESS: {msg}")
    print(f"Result: {result}")
    
    # Verify Result has due_date
    assert 'due_date' in result, "Result should contain due_date"
    print(f"Due Date in Result: {result['due_date']}")

    # Verify Position
    shorts = stock_api.get_short_positions(USER_ID)
    print(f"Short Positions: {len(shorts)}")
    if len(shorts) == 0:
        print("FAILED: No short position found.")
        return 
    
    pos = shorts[0]
    print(f"Position: {pos}")
    assert pos['quantity'] == QUANTITY
    assert pos['symbol_code'] == SYMBOL_CODE
    assert 'due_date' in pos, "Position should contain due_date"
    print(f"Due Date in Position: {pos['due_date']}")

    # Verify Margin Deposit
    account = stock_api.get_stock_account(USER_ID)
    print(f"Stock Account Margin: {account['margin_deposit']}")
    # Margin req = 2000 * 100 * 0.5 = 100,000
    expected_margin = float(pos['average_sell_price']) * QUANTITY * 0.5
    assert float(account['margin_deposit']) == expected_margin
    
    # Simulate Interest Accrual
    print("\n--- Testing Interest Accrual ---")
    # lending_fee_rate default 0.001 (0.1%)
    # Fee = 2000 * 100 * 0.001 = 200
    price_service.accrue_short_interest()
    
    shorts = stock_api.get_short_positions(USER_ID)
    pos = shorts[0]
    print(f"Accrued Interest: {pos['accrued_interest']}")
    assert float(pos['accrued_interest']) > 0

    # Test Buy to Cover
    print("\n--- Testing Buy to Cover ---")
    # First, let's lower the price to make profit
    db = SessionLocal()
    stock = db.query(StockSymbol).filter_by(symbol_code=SYMBOL_CODE).first()
    stock.current_price = 1800 # 200 profit per share
    db.commit()
    db.close()
    
    success, msg, result = stock_api.buy_to_cover(USER_ID, SYMBOL_CODE, QUANTITY)
    if not success:
        print(f"FAILED: {msg}")
        return
    print(f"SUCCESS: {msg}")
    print(f"Result: {result}")
    
    # Verify Profit
    print(f"Profit: {result['profit']}")
    
    # Verify Position Gone
    shorts = stock_api.get_short_positions(USER_ID)
    print(f"Remaining Shorts: {len(shorts)}")
    assert len(shorts) == 0

    print("\n--- ALL TESTS PASSED ---")

if __name__ == "__main__":
    setup_test_environment()
    test_short_selling()
