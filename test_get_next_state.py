#!/usr/bin/env python3
"""
Test script for get_next_state function
"""
import markov_chain
import numpy as np

def test_get_next_state():
    """Test get_next_state with various inputs"""
    
    print("=" * 80)
    print("Testing get_next_state function")
    print("=" * 80)
    print(f"\nAvailable states: {markov_chain.STATES}")
    print(f"Available actor types: {list(markov_chain.ACTOR_TYPE_PARAMS.keys())}\n")
    
    # Test with different combinations
    test_cases = [
        ("hawkish", "aggressive", 1),
        ("dovish", "opportunist", 15),
        ("opportunistic", "isolationist", 30),
        ("neutral", "neutralist", 50),
    ]
    
    print("Testing single state transitions:\n")
    for current_state, actor_type, round_num in test_cases:
        print(f"  Current: {current_state:15s} | Actor: {actor_type:15s} | Round: {round_num:3d}")
        try:
            next_state = markov_chain.get_next_state(current_state, actor_type, round_num)
            print(f"    -> Next state: {next_state}")
        except Exception as e:
            print(f"    ERROR: {e}")
    
    # Test with RNG for reproducibility
    print(f"\n{'='*80}")
    print("Testing with RNG (reproducible results):")
    print(f"{'='*80}\n")
    
    current_state = "hawkish"
    actor_type = "aggressive"
    round_num = 30
    
    # Create a seeded RNG
    rng = np.random.default_rng(seed=42)
    
    print(f"Current state: {current_state}")
    print(f"Actor type: {actor_type}")
    print(f"Round: {round_num}")
    print(f"Using seeded RNG (seed=42)\n")
    
    # Sample a few states with the RNG
    print("First 10 samples with seeded RNG:")
    for i in range(10):
        next_state = markov_chain.get_next_state(current_state, actor_type, round_num, rng=rng)
        print(f"  Sample {i+1}: {next_state}")
    
    # Test multiple samples to show probability distribution
    print(f"\n{'='*80}")
    print("Testing probability distribution (1000 samples with RNG):")
    print(f"{'='*80}\n")
    
    # Get the transition matrix to compare
    Pt = markov_chain.transition_matrix_round(round_num, actor_type)
    current_idx = markov_chain.STATE_TO_IDX[current_state]
    expected_probs = Pt[current_idx, :]
    
    print(f"Current state: {current_state}")
    print(f"Actor type: {actor_type}")
    print(f"Round: {round_num}\n")
    print("Expected probabilities (from matrix):")
    for state, prob in zip(markov_chain.STATES, expected_probs):
        print(f"  {state:15s}: {prob:.4f}")
    
    # Sample 1000 times with RNG
    rng = np.random.default_rng(seed=123)  # Reset RNG for consistent test
    samples = {}
    for state in markov_chain.STATES:
        samples[state] = 0
    
    num_samples = 1000
    for _ in range(num_samples):
        next_state = markov_chain.get_next_state(current_state, actor_type, round_num, rng=rng)
        samples[next_state] += 1
    
    print(f"\nObserved frequencies (from {num_samples} samples with RNG):")
    for state in markov_chain.STATES:
        freq = samples[state] / num_samples
        expected = expected_probs[markov_chain.STATE_TO_IDX[state]]
        diff = abs(freq - expected)
        print(f"  {state:15s}: {freq:.4f} (expected: {expected:.4f}, diff: {diff:.4f})")
    
    print(f"\n{'='*80}")
    print("Test completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_get_next_state()

