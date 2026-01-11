import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
try:
    from apps.stock.models import engine
except ImportError:
    # Fallback or try simpler import if needed, but this should work in this project structure
    from apps.banking.main_bank_system import engine

def apply_sql(sql_file):
    print(f"Applying {sql_file}...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    with engine.connect() as conn:
        # Split by ; for simple statements if needed, but text() might handle it if supported.
        # SQLAlchemy text() with execution_options(autocommit=True) usually works for scripts.
        # However, for multiple statements, it depends on driver. 
        # Let's split strictly.
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        trans = conn.begin()
        try:
            for s in statements:
                conn.execute(text(s))
            trans.commit()
            print("Success.")
        except Exception as e:
            trans.rollback()
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_sql.py <sql_file>")
        sys.exit(1)
    apply_sql(sys.argv[1])
