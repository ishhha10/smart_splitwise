import os
from flask import Flask, request, jsonify, render_template
from database import (
    init_db, add_member, get_members, delete_member,
    add_expense, get_expenses_with_payer, delete_expense,
    get_splits_for_expense, get_all_splits
)
from debt_simplifier import (
    calculate_net_balances, get_bilateral_debts, min_cash_flow
)

app = Flask(__name__)

# Initialize database on startup
init_db()

@app.route('/')
def home():
    """Serve the SPA frontend."""
    return render_template('index.html')

# --- API Endpoints ---

@app.route('/api/members', methods=['GET'])
def api_get_members():
    """Fetch all group members."""
    try:
        members = get_members()
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/members', methods=['POST'])
def api_add_member():
    """Add a new member."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    name = data.get('name')
    upi_id = data.get('upi_id', '')
    
    try:
        member_id = add_member(name, upi_id)
        return jsonify({
            'status': 'success',
            'member_id': member_id,
            'message': f'Member {name} added successfully.'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def api_delete_member(member_id):
    """Delete a member."""
    try:
        delete_member(member_id)
        return jsonify({'status': 'success', 'message': 'Member deleted successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['GET'])
def api_get_expenses():
    """Fetch all expenses with details of their splits."""
    try:
        expenses = get_expenses_with_payer()
        result = []
        for e in expenses:
            splits = get_splits_for_expense(e['id'])
            result.append({
                'id': e['id'],
                'description': e['description'],
                'amount': e['amount'],
                'payer_id': e['payer_id'],
                'payer_name': e['payer_name'],
                'created_at': e['created_at'],
                'splits': splits
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def api_add_expense():
    """Add a new expense and split it among selected members."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400
        
    description = data.get('description')
    amount = data.get('amount')
    payer_id = data.get('payer_id')
    split_member_ids = data.get('split_member_ids') # list of ints
    
    if not all([description, amount, payer_id, split_member_ids]):
        return jsonify({'error': 'Missing required fields: description, amount, payer_id, split_member_ids'}), 400
        
    try:
        expense_id = add_expense(description, amount, payer_id, split_member_ids)
        return jsonify({
            'status': 'success',
            'expense_id': expense_id,
            'message': f'Expense "{description}" of amount {amount} added.'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def api_delete_expense(expense_id):
    """Delete an expense."""
    try:
        delete_expense(expense_id)
        return jsonify({'status': 'success', 'message': 'Expense deleted successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debts', methods=['GET'])
def api_calculate_debts():
    """Compute net balances, direct debts (before), and simplified debts (after)."""
    try:
        members = get_members()
        expenses = get_expenses_with_payer()
        all_splits = get_all_splits()
        
        if not members:
            return jsonify({
                'net_balances': {},
                'before_debts': [],
                'after_debts': []
            })
            
        net_balances = calculate_net_balances(members, expenses, all_splits)
        before_debts = get_bilateral_debts(members, expenses, all_splits)
        after_debts = min_cash_flow(net_balances)
        
        # Format the balances and debts for easier client consumption
        # Include names in the debts lists
        members_map = {m['id']: m for m in members}
        
        formatted_balances = []
        for m_id, bal in net_balances.items():
            member = members_map.get(m_id)
            formatted_balances.append({
                'member_id': m_id,
                'name': member['name'] if member else 'Unknown',
                'upi_id': member['upi_id'] if member else '',
                'balance': bal
            })
            
        formatted_before = []
        for debt in before_debts:
            d_mem = members_map.get(debt['debtor_id'])
            c_mem = members_map.get(debt['creditor_id'])
            formatted_before.append({
                'debtor_id': debt['debtor_id'],
                'debtor_name': d_mem['name'] if d_mem else 'Unknown',
                'creditor_id': debt['creditor_id'],
                'creditor_name': c_mem['name'] if c_mem else 'Unknown',
                'amount': debt['amount']
            })
            
        formatted_after = []
        for debt in after_debts:
            d_mem = members_map.get(debt['debtor_id'])
            c_mem = members_map.get(debt['creditor_id'])
            formatted_after.append({
                'debtor_id': debt['debtor_id'],
                'debtor_name': d_mem['name'] if d_mem else 'Unknown',
                'creditor_id': debt['creditor_id'],
                'creditor_name': c_mem['name'] if c_mem else 'Unknown',
                'creditor_upi': c_mem['upi_id'] if c_mem else '',
                'amount': debt['amount']
            })
            
        return jsonify({
            'net_balances': formatted_balances,
            'before_debts': formatted_before,
            'after_debts': formatted_after
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    # Render dynamic port deta hai, isliye os.environ use karenge
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
