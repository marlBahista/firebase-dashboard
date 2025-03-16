import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Load Firebase credentials
cred = credentials.Certificate("D:/Printer-Controller/printer-vendo-firebase-adminsdk-fbsvc-893a19c6ba.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://printer-vendo-default-rtdb.firebaseio.com/"})

def update_firebase(coins, papers, transaction):
    ref = db.reference("printer_data")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    transaction_entry = {
        "date": now.split(" ")[0],
        "time": now.split(" ")[1],
        "pages": transaction.get("pages", 0),
        "cost": transaction.get("cost", 0)  # Store as integer
    }

    # Fetch existing transactions
    transaction_history = ref.child("transaction_history").get() or []
    if not isinstance(transaction_history, list):
        transaction_history = []  # Ensure it's a list

    transaction_history.append(transaction_entry)  # Add new transaction

    # Compute total coins inserted from all transactions
    total_coins_inserted = sum(int(tx["cost"]) for tx in transaction_history if isinstance(tx.get("cost"), (int, float)))

    ref.update({
        "coins_inserted": total_coins_inserted,
        "papers_remaining": papers,
        "transaction_history": transaction_history
    })

    print("🔥 Data uploaded to Firebase!")
