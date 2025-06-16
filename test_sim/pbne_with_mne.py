"""
Sequential USA-China tariff game (3 USA tariffs × 3 China responses)
-------------------------------------------------------------------
• USA moves first, type ∈ {Aggressive (A), Opportunist (O)}
• China observes the tariff, then responds, type ∈ {Isolationist (I), Opportunist (O)}
• This script

  1. stores *type–action* pay-offs for **both** players
  2. derives a mixed strategy for Aggressive-USA that makes
     Isolationist-China indifferent between R and S
  3. builds the full behavioural strategy σ
  4. provides a posterior-belief helper
"""

import numpy as np
from   scipy.optimize import linprog

# ------------------------------------------------------------------
# 1. PRIORS
pi_USA   = {'A': 0.40, 'O': 0.60}
pi_China = {'I': 0.50, 'O': 0.50}

# ------------------------------------------------------------------
# 2. PAY-OFF TABLE  (china_type, usa_type, usa_action, china_action) → u_China
#    Numbers are illustrative; tweak to taste.
uC = {}
# --- Isolationist China facing Aggressive USA
uC.update({
 ('I','A','H','R'): 3, ('I','A','H','S'): 0, ('I','A','H','D'):-1,
 ('I','A','L','R'): 2, ('I','A','L','S'): 1, ('I','A','L','D'):-1,
})
# --- Isolationist China facing Opportunist USA
uC.update({
 ('I','O','H','R'): 2, ('I','O','H','S'): 1, ('I','O','H','D'): 0,
 ('I','O','L','R'): 1, ('I','O','L','S'): 2, ('I','O','L','D'): 0,
})
# --- Opportunist China facing Aggressive USA
uC.update({
 ('O','A','H','R'): 0, ('O','A','H','S'): 1, ('O','A','H','D'): 2,
 ('O','A','L','R'): 0, ('O','A','L','S'): 1, ('O','A','L','D'): 2,
})
# --- Opportunist China facing Opportunist USA
uC.update({
 ('O','O','H','R'): 1, ('O','O','H','S'): 2, ('O','O','H','D'): 3,
 ('O','O','L','R'): 1, ('O','O','L','S'): 2, ('O','O','L','D'): 3,
})

# ------------------------------------------------------------------
# 3.  HELPER – solve for probability vector that makes the OTHER player indifferent
def solve_indifference(payoffs, player='row'):
    """
    payoffs : 2-D numpy array
        If player='row' we find a mixed strategy for the COLUMNS
        that leaves all ROW pay-offs equal (and vice-versa).
    """
    A = payoffs.copy()
    m, n = A.shape
    if player == 'row':                      # solve for column mix  p  (length n)
        eqs   = A[1:] - A[0:1]              # (m-1) indifference rows
        A_eq  = np.vstack([eqs, np.ones((1, n))])
        b_eq  = np.zeros(m);  b_eq[-1] = 1
        bounds, c = [(0,1)]*n, np.zeros(n)
    else:                                    # solve for row mix  q  (length m)
        eqs   = (A[:,1:] - A[:,0:1]).T
        A_eq  = np.vstack([eqs, np.ones((1, m))])
        b_eq  = np.zeros(n);  b_eq[-1] = 1
        bounds, c = [(0,1)]*m, np.zeros(m)

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    return res.x if res.success and np.isclose(res.x.sum(),1) else None

# ------------------------------------------------------------------
# 4.  derive Aggressive-USA mix  (Isolationist China is the player we keep indifferent)
#     Pay-off matrix rows = {R,S}, columns = {H,L}
pay_I_vs_A = np.array([
    [uC[('I','A','H','R')], uC[('I','A','L','R')]],   # China plays R
    [uC[('I','A','H','S')], uC[('I','A','L','S')]],   # China plays S
])
mix_A = solve_indifference(pay_I_vs_A, player='row')  # row player = China, so solve for USA columns

# ------------------------------------------------------------------
# 5.  BUILD BEHAVIOURAL STRATEGY σ  (fallback to pure if no mix exists)
sigma = {
    'A': {'H': 1.0, 'M': 0.0, 'L': 0.0},   # default pure
    'O': {'H': 0.0, 'M': 0.0, 'L': 1.0},   # opportunist USA stays Low
}
if mix_A is not None:
    sigma['A']['H'], sigma['A']['L'] = float(mix_A[0]), float(mix_A[1])

# ------------------------------------------------------------------
# 6.  POSTERIOR BELIEF FUNCTION  (China’s belief USA=A | action)
def posterior(action: str):
    num_A = sigma['A'][action] * pi_USA['A']
    num_O = sigma['O'][action] * pi_USA['O']
    denom = num_A + num_O
    if np.isclose(denom, 0):
        return {'A': 'free choice', 'O': 'free choice'}
    return {'A': num_A/denom, 'O': num_O/denom}

# ------------------------------------------------------------------
# 7.  QUICK DEMO
if __name__ == "__main__":
    print("Behavioural strategy σ:")
    for t, probs in sigma.items():
        print(f"  USA-type {t}: {probs}")

    for act in ['H','M','L']:
        print(f"\nPosterior if China sees {act}: {posterior(act)}")
