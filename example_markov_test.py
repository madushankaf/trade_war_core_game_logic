#!/usr/bin/env python3
"""
Simple example showing how to use transition_matrix_round function
"""
import markov_chain
import numpy as np

# Example usage with random values
print("Testing transition_matrix_round with different inputs:\n")

# Test with different actor types and round numbers
test_cases = [
    ("aggressive", 1),
    ("aggressive", 30),
    ("opportunist", 15),
    ("isolationist", 50),
    ("neutralist", 100),
]

for actor_type, round_num in test_cases:
    print(f"{'='*60}")
    print(f"Actor Type: {actor_type}, Round: {round_num}")
    print(f"{'='*60}")
    
    # Call the function
    Pt = markov_chain.transition_matrix_round(round_num, actor_type)
    
    # Display results
    print(f"\nTransition Matrix ({Pt.shape[0]}x{Pt.shape[1]}):")
    print(f"States: {markov_chain.STATES}\n")
    
    # Print matrix with state labels
    print("From\\To    ", end="")
    for state in markov_chain.STATES:
        print(f"{state:12s}", end="")
    print()
    
    for i, from_state in enumerate(markov_chain.STATES):
        print(f"{from_state:12s}", end="")
        for j in range(len(markov_chain.STATES)):
            print(f"{Pt[i, j]:12.6f}", end="")
        print(f"  (sum: {Pt[i].sum():.6f})")
    
    print(f"\nValidation:")
    print(f"  - All values in [0, 1]: {np.all((Pt >= 0) & (Pt <= 1))}")
    print(f"  - Rows sum to 1: {np.allclose(Pt.sum(axis=1), 1.0)}")
    print()

