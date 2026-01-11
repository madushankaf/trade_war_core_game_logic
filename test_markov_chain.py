#!/usr/bin/env python3
"""
Test script for transition_matrix_round function
"""
import numpy as np
import markov_chain

def test_transition_matrix_round():
    """Test transition_matrix_round with various inputs"""
    
    # Available actor types from the JSON
    actor_types = ["aggressive", "opportunist", "isolationist", "neutralist"]
    
    # Test with different round numbers (including some random values)
    test_rounds = [1, 5, 10, 15, 20, 25, 30, 50, 100]
    
    print("=" * 80)
    print("Testing transition_matrix_round function")
    print("=" * 80)
    print(f"\nAvailable actor types: {actor_types}")
    print(f"States: {markov_chain.STATES}\n")
    
    all_passed = True
    
    for actor_type in actor_types:
        print(f"\n{'='*80}")
        print(f"Actor Type: {actor_type}")
        print(f"{'='*80}")
        
        for round_num in test_rounds:
            try:
                # Call the function
                Pt = markov_chain.transition_matrix_round(round_num, actor_type)
                
                # Validate the result
                assert Pt.shape == (len(markov_chain.STATES), len(markov_chain.STATES)), \
                    f"Matrix shape should be ({len(markov_chain.STATES)}, {len(markov_chain.STATES)})"
                
                # Check that rows sum to 1 (stochastic matrix)
                row_sums = Pt.sum(axis=1)
                assert np.allclose(row_sums, 1.0, atol=1e-6), f"Rows should sum to 1, got {row_sums}"
                
                # Check that all values are in [0, 1]
                assert np.all(Pt >= -1e-6) and np.all(Pt <= 1.0 + 1e-6), \
                    f"All values should be in [0, 1], got min={Pt.min():.6f}, max={Pt.max():.6f}"
                
                # Print results for round 1, 30, and 100 as examples
                if round_num in [1, 30, 100]:
                    print(f"\n  Round {round_num}:")
                    print(f"  Matrix shape: {Pt.shape}")
                    print(f"  Row sums: {row_sums}")
                    print(f"  Matrix (rows=from_state, cols=to_state):")
                    print(f"  States: {markov_chain.STATES}")
                    for i, from_state in enumerate(markov_chain.STATES):
                        print(f"    {from_state:15s}: {Pt[i]}")
                else:
                    print(f"  Round {round_num:3d}: OK (row sums: {row_sums})")
                    
            except Exception as e:
                print(f"  ERROR at round {round_num}: {e}")
                import traceback
                traceback.print_exc()
                all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    print(f"{'='*80}")
    
    return all_passed

if __name__ == "__main__":
    success = test_transition_matrix_round()
    exit(0 if success else 1)

