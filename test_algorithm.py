import os
import unittest
from database import init_db, add_member, add_expense, get_members, get_expenses_with_payer, get_all_splits, DB_PATH
from debt_simplifier import calculate_net_balances, get_bilateral_debts, min_cash_flow

class TestSmartSplitwise(unittest.TestCase):
    def setUp(self):
        # Remove any existing test DB
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass
        init_db()

    def tearDown(self):
        # Clean up database after tests
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass

    def test_database_and_algorithm(self):
        # 1. Add members
        a_id = add_member("Alice", "alice@upi")
        b_id = add_member("Bob", "bob@upi")
        c_id = add_member("Charlie", "charlie@upi")
        d_id = add_member("David", "david@upi")
        
        members = get_members()
        self.assertEqual(len(members), 4)
        
        # 2. Add Expenses
        # Alice paid 300, split between Alice, Bob, Charlie (100 each)
        add_expense("Lunch", 300, a_id, [a_id, b_id, c_id])
        
        # Bob paid 200, split between Bob, Charlie (100 each)
        add_expense("Drinks", 200, b_id, [b_id, c_id])
        
        # Charlie paid 100, split between Alice, David (50 each)
        add_expense("Snacks", 100, c_id, [a_id, d_id])
        
        expenses = get_expenses_with_payer()
        splits = get_all_splits()
        
        self.assertEqual(len(expenses), 3)
        self.assertEqual(len(splits), 3 + 2 + 2)
        
        # 3. Calculate Net Balances
        # Let's trace Alice:
        # Paid 300. Share in Lunch = -100. Share in Drinks = 0. Share in Snacks = -50.
        # Net Alice = +300 - 100 - 50 = +150
        # Let's trace Bob:
        # Paid 200. Share in Lunch = -100. Share in Drinks = -100. Share in Snacks = 0.
        # Net Bob = +200 - 100 - 100 = 0
        # Let's trace Charlie:
        # Paid 100. Share in Lunch = -100. Share in Drinks = -100. Share in Snacks = 0.
        # Net Charlie = +100 - 100 - 100 = -100
        # Let's trace David:
        # Paid 0. Share in Lunch = 0. Share in Drinks = 0. Share in Snacks = -50.
        # Net David = 0 - 50 = -50
        
        balances = calculate_net_balances(members, expenses, splits)
        self.assertEqual(balances[a_id], 150.0)
        self.assertEqual(balances[b_id], 0.0)
        self.assertEqual(balances[c_id], -100.0)
        self.assertEqual(balances[d_id], -50.0)
        self.assertEqual(sum(balances.values()), 0.0)
        
        # 4. Before Simplification (Bilateral Net Debts)
        # Alice paid Lunch (300): Bob owes Alice 100, Charlie owes Alice 100.
        # Bob paid Drinks (200): Charlie owes Bob 100.
        # Charlie paid Snacks (100): Alice owes Charlie 50, David owes Charlie 50.
        #
        # Netting bilaterally:
        # Charlie owes Alice 100 & Alice owes Charlie 50 -> Charlie owes Alice 50.
        # Bob owes Alice 100.
        # Charlie owes Bob 100.
        # David owes Charlie 50.
        #
        # Bilateral debts should match:
        # - Bob owes Alice 100
        # - Charlie owes Alice 50
        # - Charlie owes Bob 100
        # - David owes Charlie 50
        # Total transactions = 4
        bilateral_debts = get_bilateral_debts(members, expenses, splits)
        self.assertEqual(len(bilateral_debts), 4)
        
        # 5. After Simplification (Min-Cash Flow)
        # Net Balances: Alice = +150, Bob = 0, Charlie = -100, David = -50.
        # Debtors: Charlie (-100), David (-50)
        # Creditors: Alice (+150)
        # Iteration 1: Max debtor = Charlie (-100), Max creditor = Alice (+150)
        # Settle: Charlie pays Alice 100.
        # Balances updated: Charlie = 0, Alice = +50.
        # Iteration 2: Max debtor = David (-50), Max creditor = Alice (+50)
        # Settle: David pays Alice 50.
        # Balances updated: David = 0, Alice = 0.
        # Total transactions = 2
        
        simplified_debts = min_cash_flow(balances)
        self.assertEqual(len(simplified_debts), 2)
        
        # Transaction 1: Charlie pays Alice 100
        # Transaction 2: David pays Alice 50
        t1 = next(t for t in simplified_debts if t['debtor_id'] == c_id)
        self.assertEqual(t1['creditor_id'], a_id)
        self.assertEqual(t1['amount'], 100.0)
        
        t2 = next(t for t in simplified_debts if t['debtor_id'] == d_id)
        self.assertEqual(t2['creditor_id'], a_id)
        self.assertEqual(t2['amount'], 50.0)
        
        print("Algorithm and Database test PASSED successfully!")

if __name__ == '__main__':
    unittest.main()
