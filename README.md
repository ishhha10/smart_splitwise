# Smart Splitwise 💸

Smart Splitwise is a premium, web-based group expense sharing and debt simplification application. It utilizes the **Min-Cash Flow (Greedy/Graph) Algorithm** to optimize transactions and integrates **UPI Deep Linking + QR Codes** to make settling up quick and painless.

## Features

1. **Member Management**: Add group members with their optional UPI IDs.
2. **Expense & Split Manager**: Log expenses with detailed descriptions and select who participated. Split is automatically calculated equally among the active participants.
3. **Running Ledger**: A historical ledger allows tracking transactions and deleting errors, updating group stats and individual balances instantly.
4. **Min-Cash Flow Debt Simplification**: Shows a visual comparison of debts "Before" (bilateral netting) and "After" (optimized) simplification, with an interactive network graph visualizer.
5. **Integrated UPI Payments**: For every simplified transaction:
   - Mobile users can click the **Pay via UPI** button to directly launch GPay, PhonePe, Paytm, or BHIM.
   - Desktop users can scan the dynamically generated **UPI QR Code** using their phone camera/UPI apps to settle up instantly.

---

## Technical Stack

- **Backend**: Python 3.14 + SQLite (with foreign keys cascading)
- **Frontend**: Streamlit + Custom CSS styling (glassmorphism cards, responsive grids, gradient highlights)
- **Algorithms**: NetworkX (for graph analysis and visualization), Matplotlib
- **Integrations**: `qrcode` + PIL (for dynamic QR codes)

---

## File Structure

```
smart_splitwise/
├── .streamlit/
│   └── config.toml       # Custom dark theme configuration
├── app.py                # Main Streamlit web application
├── database.py           # SQLite persistence layer and schemas
├── debt_simplifier.py    # Math & Min-Cash Flow Algorithm implementation
├── requirements.txt      # Python dependencies
├── test_algorithm.py    # Unit tests for algorithm correctness
├── README.md             # This file
└── run.bat               # One-click Windows runner
```

---

## How to Run

Since a virtual environment `.venv` is already configured in the parent directory, you can run the app with one click:

### Windows (Recommended)
1. Double-click the `run.bat` file in this directory.
2. This script will automatically check and install all dependencies in `requirements.txt` into the virtual environment and start the Streamlit server.
3. Once running, your web browser should open automatically to:
   [http://localhost:8501](http://localhost:8501)

### Manual Command Line (PowerShell/CMD)
From the root workspace directory, run:
```powershell
# Navigate to the smart_splitwise folder
cd smart_splitwise

# Install requirements
..\.venv\bin\pip.exe install -r requirements.txt

# Start Streamlit
..\.venv\bin\streamlit.exe run app.py
```

---

## Understanding the Algorithm (Min-Cash Flow)

The goal is to settle all group debts using the minimum number of cash transfers.

1. **Calculate Net Balance**: For each member, we calculate their total amount paid minus their total share of all expenses.
   $$\text{Balance}_i = \text{Paid}_i - \text{Share}_i$$
   The sum of all balances in the group is always zero.
2. **Classify**: Members are categorized into **Debtors** (negative balance) and **Creditors** (positive balance).
3. **Greedy Matching**:
   - Locate the largest debtor (most negative balance) and the largest creditor (most positive balance).
   - Compute the transfer amount:
     $$\text{Amount} = \min(-\text{Debtor Balance}, \text{Creditor Balance})$$
   - Create a transfer transaction from Debtor to Creditor.
   - Update both balances by this amount.
   - Repeat until all balances are zero (~0).
