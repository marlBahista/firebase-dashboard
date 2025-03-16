import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Initialize Firebase with credentials
cred = credentials.Certificate("D:/Printer-Controller/printer-vendo-firebase-adminsdk-fbsvc-893a19c6ba.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://printer-vendo-default-rtdb.firebaseio.com/"})

def update_firebase(coins, papers, transaction=None, ink_levels=None):
    """
    Updates Firebase with printer vending machine data.

    Args:
        coins (int): Number of coins inserted.
        papers (int): Remaining paper count.
        transaction (dict, optional): Dictionary with "pages" and "cost" details. Defaults to an empty dictionary.
        ink_levels (dict, optional): Dictionary containing ink levels.
    """
    ref = db.reference("printer_data")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    transaction_entry = {
        "date": now.split(" ")[0],
        "time": now.split(" ")[1],
        "pages": transaction.get("pages", 0) if transaction else 0,
        "cost": transaction.get("cost", 0) if transaction else 0
    }

    # Retrieve existing transaction history or initialize as an empty list
    transaction_history = ref.child("transaction_history").get() or []
    transaction_history.append(transaction_entry)

    # Construct data payload
    data = {
        "coins_inserted": coins,
        "papers_remaining": papers,
        "transaction_history": transaction_history
    }

    if ink_levels:
        data["ink_levels"] = ink_levels  # Add ink levels only if provided

    ref.update(data)
    print("🔥 Data uploaded to Firebase!")
