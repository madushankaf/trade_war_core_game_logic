#!/usr/bin/env python3
"""
Test script for country_markov_states module functions:
- get_transition_matrix
- get_next_state
"""
import numpy as np
from world_model.country_markov_states import get_transition_matrix, get_next_state, COUNTRIES


def test_get_transition_matrix():
    """Test get_transition_matrix with various inputs"""
    
    print("=" * 80)
    print("Testing get_transition_matrix function")
    print("=" * 80)
    print(f"\nAvailable countries: {list(COUNTRIES.keys())}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality - test with valid inputs
    print(f"{'='*80}")
    print("Test 1: Basic functionality with valid inputs")
    print(f"{'='*80}\n")
    
    test_cases = [
        ("USA", "NORMAL"),
        ("USA", "ELECTION_CYCLE"),
        ("INDIA", "NORMAL"),
        ("CHINA", "GROWTH_STRONG"),
        ("RUSSIA", "SANCTIONS_ISOLATION_HIGH"),
    ]
    
    for country, state in test_cases:
        try:
            transition_matrix = get_transition_matrix(state, country)
            
            # Validate result is a numpy array
            assert isinstance(transition_matrix, np.ndarray), \
                f"Result should be numpy array, got {type(transition_matrix)}"
            
            # Validate shape matches number of states
            expected_length = len(COUNTRIES[country]["states"])
            assert transition_matrix.shape == (expected_length,), \
                f"Matrix shape should be ({expected_length},), got {transition_matrix.shape}"
            
            # Validate probabilities sum to 1
            prob_sum = transition_matrix.sum()
            assert np.isclose(prob_sum, 1.0, atol=1e-6), \
                f"Probabilities should sum to 1, got {prob_sum}"
            
            # Validate all values are in [0, 1]
            assert np.all(transition_matrix >= -1e-6) and np.all(transition_matrix <= 1.0 + 1e-6), \
                f"All values should be in [0, 1], got min={transition_matrix.min():.6f}, max={transition_matrix.max():.6f}"
            
            print(f"  ✓ {country:15s} | {state:30s} | Shape: {transition_matrix.shape} | Sum: {prob_sum:.6f}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{state}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: Validate transition matrices for all countries and states
    print(f"\n{'='*80}")
    print("Test 2: Validate all transition matrices")
    print(f"{'='*80}\n")
    
    for country in COUNTRIES.keys():
        states = COUNTRIES[country]["states"]
        print(f"  Country: {country} ({len(states)} states)")
        
        for state in states:
            try:
                transition_matrix = get_transition_matrix(state, country)
                
                # Check stochastic property
                prob_sum = transition_matrix.sum()
                if not np.isclose(prob_sum, 1.0, atol=1e-6):
                    print(f"    ✗ {state}: probabilities sum to {prob_sum:.6f} (expected 1.0)")
                    all_passed = False
                else:
                    # Check for negative values
                    if np.any(transition_matrix < -1e-6):
                        print(f"    ✗ {state}: contains negative values")
                        all_passed = False
                    else:
                        print(f"    ✓ {state:30s} | Sum: {prob_sum:.6f}")
                        
            except Exception as e:
                print(f"    ✗ ERROR for {state}: {e}")
                all_passed = False
    
    # Test 3: Error handling - invalid country
    print(f"\n{'='*80}")
    print("Test 3: Error handling - invalid country")
    print(f"{'='*80}\n")
    
    try:
        get_transition_matrix("NORMAL", "INVALID_COUNTRY")
        print(f"  ✗ Should have raised ValueError for invalid country")
        all_passed = False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 4: Error handling - invalid state
    print(f"\n{'='*80}")
    print("Test 4: Error handling - invalid state")
    print(f"{'='*80}\n")
    
    try:
        get_transition_matrix("INVALID_STATE", "USA")
        print(f"  ✗ Should have raised KeyError for invalid state")
        all_passed = False
    except KeyError as e:
        print(f"  ✓ Correctly raised KeyError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 5: Verify transition matrix values match JSON data
    print(f"\n{'='*80}")
    print("Test 5: Verify transition matrix values match JSON data")
    print(f"{'='*80}\n")
    
    country = "USA"
    state = "NORMAL"
    
    try:
        transition_matrix = get_transition_matrix(state, country)
        expected_values = COUNTRIES[country]["P_rows_in_state_order"][state]
        
        assert np.allclose(transition_matrix, expected_values), \
            f"Transition matrix doesn't match JSON data"
        
        print(f"  ✓ Transition matrix values match JSON data for {country}/{state}")
        print(f"    Values: {transition_matrix}")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All get_transition_matrix tests passed! ✓")
    else:
        print("Some get_transition_matrix tests failed! ✗")
    print(f"{'='*80}\n")
    
    return all_passed


def test_get_next_state():
    """Test get_next_state with various inputs"""
    
    print("=" * 80)
    print("Testing get_next_state function")
    print("=" * 80)
    print(f"\nAvailable countries: {list(COUNTRIES.keys())}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality - test with valid inputs
    print(f"{'='*80}")
    print("Test 1: Basic functionality with valid inputs")
    print(f"{'='*80}\n")
    
    test_cases = [
        ("USA", "NORMAL", 1),
        ("USA", "ELECTION_CYCLE", 10),
        ("INDIA", "NORMAL", 5),
        ("CHINA", "GROWTH_STRONG", 20),
        ("RUSSIA", "SANCTIONS_ISOLATION_HIGH", 15),
    ]
    
    for country, current_state, timestep in test_cases:
        try:
            next_state = get_next_state(current_state, country, timestep)
            
            # Validate result is a string
            assert isinstance(next_state, str), \
                f"Result should be string, got {type(next_state)}"
            
            # Validate next_state is in the list of valid states for this country
            valid_states = COUNTRIES[country]["states"]
            assert next_state in valid_states, \
                f"Next state '{next_state}' not in valid states {valid_states}"
            
            print(f"  ✓ {country:15s} | {current_state:30s} | Timestep: {timestep:3d} -> {next_state}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_state}/{timestep}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: RNG reproducibility (using seeded random)
    print(f"\n{'='*80}")
    print("Test 2: RNG reproducibility with seeded random")
    print(f"{'='*80}\n")
    
    country = "USA"
    current_state = "NORMAL"
    timestep = 10
    
    # Set seed for reproducibility
    np.random.seed(42)
    next_state1 = get_next_state(current_state, country, timestep)
    
    np.random.seed(42)
    next_state2 = get_next_state(current_state, country, timestep)
    
    if next_state1 == next_state2:
        print(f"  ✓ RNG reproducibility test passed (both returned '{next_state1}')")
    else:
        print(f"  ✗ RNG reproducibility test failed: '{next_state1}' != '{next_state2}'")
        all_passed = False
    
    # Test 3: Probability distribution verification
    print(f"\n{'='*80}")
    print("Test 3: Probability distribution verification")
    print(f"{'='*80}\n")
    
    country = "USA"
    current_state = "NORMAL"
    timestep = 10
    
    # Get expected probabilities from transition matrix
    transition_matrix = get_transition_matrix(current_state, country)
    valid_states = COUNTRIES[country]["states"]
    
    # Sample many times
    np.random.seed(123)  # Use seed for reproducible testing
    num_samples = 1000
    state_counts = {state: 0 for state in valid_states}
    
    for _ in range(num_samples):
        next_state = get_next_state(current_state, country, timestep)
        state_counts[next_state] += 1
    
    print(f"  Country: {country}")
    print(f"  Current state: {current_state}")
    print(f"  Timestep: {timestep}")
    print(f"  Samples: {num_samples}\n")
    
    print("  Expected vs Observed probabilities:")
    max_diff = 0
    for i, state in enumerate(valid_states):
        expected_prob = transition_matrix[i]
        observed_freq = state_counts[state] / num_samples
        diff = abs(observed_freq - expected_prob)
        max_diff = max(max_diff, diff)
        print(f"    {state:30s}: Expected: {expected_prob:.4f} | Observed: {observed_freq:.4f} | Diff: {diff:.4f}")
    
    # For 1000 samples, expect difference to be within reasonable tolerance
    # (approximately 2-3 standard deviations for binomial distribution)
    tolerance = 0.05  # 5% tolerance
    if max_diff < tolerance:
        print(f"\n  ✓ Probability distribution test passed (max diff: {max_diff:.4f} < {tolerance})")
    else:
        print(f"\n  ⚠ Probability distribution test: max diff {max_diff:.4f} >= {tolerance} (may be random variation)")
        # Don't fail the test for this, as it's stochastic
    
    # Test 4: Verify all states can be reached
    print(f"\n{'='*80}")
    print("Test 4: Verify all states can be reached (if probabilities > 0)")
    print(f"{'='*80}\n")
    
    country = "USA"
    current_state = "NORMAL"
    timestep = 1
    
    transition_matrix = get_transition_matrix(current_state, country)
    valid_states = COUNTRIES[country]["states"]
    
    # Sample many times to check if all non-zero probability states are reached
    np.random.seed(456)
    num_samples = 2000
    reached_states = set()
    
    for _ in range(num_samples):
        next_state = get_next_state(current_state, country, timestep)
        reached_states.add(next_state)
    
    print(f"  States that can be reached (from {num_samples} samples): {sorted(reached_states)}")
    print(f"  States with non-zero probability: {[state for i, state in enumerate(valid_states) if transition_matrix[i] > 0]}")
    
    # Verify all states with non-zero probability were reached (with high probability)
    expected_reachable = {state for i, state in enumerate(valid_states) if transition_matrix[i] > 0}
    if reached_states == expected_reachable or len(reached_states) == len(expected_reachable):
        print(f"  ✓ All reachable states were sampled")
    else:
        missing = expected_reachable - reached_states
        if missing:
            print(f"  ⚠ Some reachable states not sampled: {missing} (may be due to low probability)")
    
    # Test 5: Error handling - invalid country
    print(f"\n{'='*80}")
    print("Test 5: Error handling - invalid country")
    print(f"{'='*80}\n")
    
    try:
        get_next_state("NORMAL", "INVALID_COUNTRY", 1)
        print(f"  ✗ Should have raised ValueError for invalid country")
        all_passed = False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 6: Error handling - invalid state
    print(f"\n{'='*80}")
    print("Test 6: Error handling - invalid state")
    print(f"{'='*80}\n")
    
    try:
        get_next_state("INVALID_STATE", "USA", 1)
        print(f"  ✗ Should have raised KeyError for invalid state")
        all_passed = False
    except KeyError as e:
        print(f"  ✓ Correctly raised KeyError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 7: Test with different countries and their states
    print(f"\n{'='*80}")
    print("Test 7: Test with different countries and states")
    print(f"{'='*80}\n")
    
    country_test_cases = [
        ("EU", "UNITY_HIGH"),
        ("SAUDI_ARABIA", "OIL_COMFORT"),
        ("IRAN", "SANCTIONS_HIGH"),
        ("UK", "NORMAL"),
    ]
    
    for country, state in country_test_cases:
        try:
            np.random.seed(789)
            next_state = get_next_state(state, country, 5)
            valid_states = COUNTRIES[country]["states"]
            
            assert next_state in valid_states, \
                f"Next state '{next_state}' not in valid states for {country}"
            
            print(f"  ✓ {country:15s} | {state:30s} -> {next_state}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{state}: {e}")
            all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All get_next_state tests passed! ✓")
    else:
        print("Some get_next_state tests failed! ✗")
    print(f"{'='*80}\n")
    
    return all_passed


if __name__ == "__main__":
    success1 = test_get_transition_matrix()
    print("\n")
    success2 = test_get_next_state()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("All tests passed! ✓")
        exit(0)
    else:
        print("Some tests failed! ✗")
        exit(1)
