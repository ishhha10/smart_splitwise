def calculate_net_balances(members, expenses, all_splits):
    """
    Computes the net balance for each member.
    Net Balance = (Total Amount Paid) - (Total Split Share)
    Returns: dict of {member_id: net_balance}
    """
    balances = {m['id']: 0.0 for m in members}
    
    # Group splits by expense_id
    splits_by_expense = {}
    for s in all_splits:
        e_id = s['expense_id']
        if e_id not in splits_by_expense:
            splits_by_expense[e_id] = []
        splits_by_expense[e_id].append(s['member_id'])
        
    for exp in expenses:
        exp_id = exp['id']
        payer_id = exp['payer_id']
        amount = exp['amount']
        
        # Members involved in the split
        involved_members = splits_by_expense.get(exp_id, [])
        if not involved_members:
            continue
            
        # Payer is credited the full amount
        if payer_id in balances:
            balances[payer_id] += amount
            
        # Split share per involved member
        share = amount / len(involved_members)
        
        # Each involved member is debited their share
        for m_id in involved_members:
            if m_id in balances:
                balances[m_id] -= share
                
    # Round to 2 decimal places to avoid floating point issues
    return {k: round(v, 2) for k, v in balances.items()}


def get_bilateral_debts(members, expenses, all_splits):
    """
    Calculates direct debts before simplification, netted bilaterally.
    If A owes B 50 and B owes A 20, then A owes B 30.
    Returns: list of dicts [{'debtor_id': u, 'creditor_id': v, 'amount': amt}]
    """
    # Group splits by expense_id
    splits_by_expense = {}
    for s in all_splits:
        e_id = s['expense_id']
        if e_id not in splits_by_expense:
            splits_by_expense[e_id] = []
        splits_by_expense[e_id].append(s['member_id'])
        
    # Accumulate all raw direct debts
    # raw_debts[debtor][creditor] = amount
    member_ids = [m['id'] for m in members]
    raw_debts = {d_id: {c_id: 0.0 for c_id in member_ids} for d_id in member_ids}
    
    for exp in expenses:
        exp_id = exp['id']
        payer_id = exp['payer_id']
        amount = exp['amount']
        
        involved_members = splits_by_expense.get(exp_id, [])
        if not involved_members:
            continue
            
        share = amount / len(involved_members)
        for debtor_id in involved_members:
            if debtor_id != payer_id:
                raw_debts[debtor_id][payer_id] += share
                
    # Perform bilateral netting
    net_debts = []
    for i in range(len(member_ids)):
        for j in range(i + 1, len(member_ids)):
            u = member_ids[i]
            v = member_ids[j]
            
            u_to_v = raw_debts[u][v]
            v_to_u = raw_debts[v][u]
            
            if u_to_v > v_to_u:
                diff = u_to_v - v_to_u
                if diff > 0.01:
                    net_debts.append({
                        'debtor_id': u,
                        'creditor_id': v,
                        'amount': round(diff, 2)
                    })
            elif v_to_u > u_to_v:
                diff = v_to_u - u_to_v
                if diff > 0.01:
                    net_debts.append({
                        'debtor_id': v,
                        'creditor_id': u,
                        'amount': round(diff, 2)
                    })
                    
    return net_debts


def min_cash_flow(net_balances):
    """
    Implements the greedy Min-Cash Flow algorithm to simplify debts.
    Returns: list of dicts [{'debtor_id': u, 'creditor_id': v, 'amount': amt}]
    """
    # Create a working copy of balances filtering out negligible balances
    balances = {k: v for k, v in net_balances.items() if abs(v) > 0.01}
    
    transactions = []
    
    # Loop until all balances are settled
    # At most N-1 transactions are generated
    while len(balances) > 1:
        # Find maximum debtor (most negative balance) and maximum creditor (most positive balance)
        max_debtor_id = min(balances, key=balances.get)
        max_creditor_id = max(balances, key=balances.get)
        
        max_debt = balances[max_debtor_id]
        max_credit = balances[max_creditor_id]
        
        if abs(max_debt) < 0.01 or abs(max_credit) < 0.01:
            break
            
        # Settle the minimum of the debt and credit
        settle_amount = min(-max_debt, max_credit)
        
        transactions.append({
            'debtor_id': max_debtor_id,
            'creditor_id': max_creditor_id,
            'amount': round(settle_amount, 2)
        })
        
        # Update balances
        balances[max_debtor_id] += settle_amount
        balances[max_creditor_id] -= settle_amount
        
        # Remove settled members from considerations to prevent floating point inaccuracies
        if abs(balances[max_debtor_id]) < 0.01:
            del balances[max_debtor_id]
        if max_creditor_id in balances and abs(balances[max_creditor_id]) < 0.01:
            del balances[max_creditor_id]
            
    return transactions
