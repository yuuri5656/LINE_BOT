import sys
import os
sys.path.append(os.getcwd())

from apps.stock.models import engine
from apps.gacha.models import Base as GachaBase, CardMaster, GachaMaster, GachaItem
from apps.inventory.models import Base as InventoryBase
from apps.trade.models import Base as TradeBase
from apps.banking.main_bank_system import Base as BankingBase
from apps.stock.models import SessionLocal

def init_db():
    print("Creating tables...")
    # Be careful not to drop existing banking/stock tables if they share Base.
    # The new models import Base from banking.main_bank_system, so metadata is shared.
    # create_all checks for existence, so it's safe.
    
    GachaBase.metadata.create_all(bind=engine)
    InventoryBase.metadata.create_all(bind=engine)
    TradeBase.metadata.create_all(bind=engine)
    
    print("Tables created.")

def seed_data():
    db = SessionLocal()
    try:
        # Check if data exists
        if db.query(CardMaster).count() > 0:
            print("Data already exists. Skipping seed.")
            return

        print("Seeding data...")
        
        # 1. Create Cards
        cards = [
            CardMaster(name="塩爺 (Normal)", type="character", rarity="N", image_url="https://via.placeholder.com/150?text=Shiojii+N", description="普通の塩爺。"),
            CardMaster(name="塩爺 (SSR メスガキ)", type="character", rarity="SSR", image_url="https://via.placeholder.com/150/FF00FF/FFFFFF?text=Mesugaki", description="メスガキ化した塩爺。「ざぁこ♡」", attributes={"style": "mesugaki"}),
            CardMaster(name="株式手数料カット (Normal)", type="skill", rarity="N", image_url="https://via.placeholder.com/150?text=Fee-1%", description="株売却手数料 -1%", effects=[{"target": "stock_sell_fee_reduction", "value": 0.01}]),
            CardMaster(name="株式手数料カット (SSR)", type="skill", rarity="SSR", image_url="https://via.placeholder.com/150/Gold?text=Fee-50%", description="株売却手数料 -50%", effects=[{"target": "stock_sell_fee_reduction", "value": 0.50}]),
            CardMaster(name="塩爺の杖", type="skin", rarity="R", image_url="https://via.placeholder.com/150?text=Cane", description="ただの杖。"),
        ]
        db.add_all(cards)
        db.flush() # populate IDs

        # 2. Create Gacha Banner
        gacha = GachaMaster(
            name="塩爺プレミアムガチャ",
            description="メスガキ塩爺が出るかも！？",
            cost_amount=3000,
            currency_type="JPY",
            banner_image_url="https://via.placeholder.com/300x150?text=Premium+Gacha"
        )
        db.add(gacha)
        db.flush()

        # 3. Add Items to Gacha
        items = [
            GachaItem(gacha_id=gacha.gacha_id, card_id=cards[0].card_id, weight=50), # N Shiojii
            GachaItem(gacha_id=gacha.gacha_id, card_id=cards[1].card_id, weight=5),  # SSR Mesugaki
            GachaItem(gacha_id=gacha.gacha_id, card_id=cards[2].card_id, weight=30), # N Skill
            GachaItem(gacha_id=gacha.gacha_id, card_id=cards[3].card_id, weight=2),  # SSR Skill
            GachaItem(gacha_id=gacha.gacha_id, card_id=cards[4].card_id, weight=13), # R Skin
        ]
        db.add_all(items)
        db.commit()
        print("Seeding completed.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_data()
