# Extended simulation including Medium Tariff (M) and deviation checks for Step 6

# Step 1: Define types, priors, actions, and payoffs
usa_priors = {'A': 0.4, 'O': 0.6}
china_priors = {'I': 0.5, 'O': 0.5}

usa_actions = ['H', 'M', 'L']
china_actions = ['R', 'S', 'D']

# Base payoffs for China at H and L
payoffs_China = {
    ('I','H','R'): 2, ('I','H','S'): 1, ('I','H','D'): 0,
    ('I','L','R'): 1, ('I','L','S'): 2, ('I','L','D'): 0,
    ('O','H','R'): 1, ('O','H','S'): 2, ('O','H','D'): 3,
    ('O','L','R'): 1, ('O','L','S'): 2, ('O','L','D'): 3,
}

# Base payoffs for USA at H and L
payoffs_USA = {
    ('A','H','R','I'): -1, ('A','H','R','O'): -1,
    ('A','H','S','I'):  3, ('A','H','S','O'):  3,
    ('A','H','D','I'):  1, ('A','H','D','O'):  1,
    ('A','L','R','I'):  0, ('A','L','R','O'):  0,
    ('A','L','S','I'):  1, ('A','L','S','O'):  1,
    ('A','L','D','I'):  1, ('A','L','D','O'):  1,

    ('O','H','R','I'): -2, ('O','H','R','O'): -2,
    ('O','H','S','I'):  1, ('O','H','S','O'):  1,
    ('O','H','D','I'):  2, ('O','H','D','O'):  2,
    ('O','L','R','I'):  0, ('O','L','R','O'):  0,
    ('O','L','S','I'):  1, ('O','L','S','O'):  1,
    ('O','L','D','I'):  2, ('O','L','D','O'):  3,
}

# Step 2: Extend payoffs for 'M' as the average of 'H' and 'L'
for ctype in china_priors:
    for action in china_actions:
        payoffs_China[(ctype, 'M', action)] = (
            payoffs_China[(ctype, 'H', action)] + payoffs_China[(ctype, 'L', action)]
        ) / 2

for utype in ['A', 'O']:
    for ctype in china_priors:
        for caction in china_actions:
            payoffs_USA[(utype, 'M', caction, ctype)] = (
                payoffs_USA[(utype, 'H', caction, ctype)] + payoffs_USA[(utype, 'L', caction, ctype)]
            ) / 2

# Step 3: Compute beliefs via Bayes (on-path for H and L)
beliefs_on = {
    'H': {'A': 1.0, 'O': 0.0},
    'L': {'A': 0.0, 'O': 1.0},
}

# Step 4: Best response for China at each observation
best_response = {}
for ctype in china_priors:
    for observed in ['H', 'L', 'M']:
        if observed in ['H', 'L']:
            # use on-path beliefs
            belief = beliefs_on[observed]
            # degenerate belief: pick payoff against the certain type
            best_action = max(
                china_actions,
                key=lambda a: payoffs_China[(ctype, observed, a)]
            )
        else:
            # off-path: use prior beliefs
            best_action = max(
                china_actions,
                key=lambda a: sum(china_priors[ct] * payoffs_China[(ctype, observed, a)] for ct in china_priors)
            )
        best_response[(ctype, observed)] = best_action

# Step 5: USA’s expected payoffs anticipating China’s best response
usa_expected = {utype: {} for utype in usa_priors}
for utype in usa_priors:
    for ua in usa_actions:
        usa_expected[utype][ua] = sum(
            china_priors[ctype] * payoffs_USA[(utype, ua, best_response[(ctype, ua)], ctype)]
            for ctype in china_priors
        )

# Step 6: Deviation checks for USA
deviation_results = {}
for utype in usa_priors:
    # find best action given expected payoffs
    best_act = max(usa_expected[utype], key=lambda a: usa_expected[utype][a])
    deviation_results[utype] = {
        'equilibrium_action': 'L',
        'best_action': best_act,
        'equilibrium_payoff': usa_expected[utype]['L'],
        'best_payoff': usa_expected[utype][best_act],
        'is_deviation_profitable': usa_expected[utype][best_act] > usa_expected[utype]['L']
    }

# Display results
print("=== Best Responses for China ===")
for (ctype, obs), act in best_response.items():
    print(f"China type {ctype} after observing {obs}: {act}")

print("\n=== USA Expected Payoffs ===")
for utype, payoffs in usa_expected.items():
    print(f"USA type {utype}:")
    for act, val in payoffs.items():
        print(f"  {act} → {val:.2f}")

print("\n=== USA Deviation Checks (Step 6) ===")
for utype, res in deviation_results.items():
    print(f"USA type {utype}: equilibrium L payoff = {res['equilibrium_payoff']:.2f}, "
          f"best action = {res['best_action']} (payoff {res['best_payoff']:.2f}), "
          f"profitable deviation? {'Yes' if res['is_deviation_profitable'] else 'No'}")

