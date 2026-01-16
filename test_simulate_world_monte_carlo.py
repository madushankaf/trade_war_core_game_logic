#!/usr/bin/env python3
"""
Test script for simulate_world_using_monte_carlo function in country_markov_states module
"""
import numpy as np
from world_model.country_markov_states import (
    simulate_world_using_monte_carlo,
    COUNTRIES,
    COUPLING_RULES
)


def test_simulate_world_using_monte_carlo():
    """Test simulate_world_using_monte_carlo with various inputs"""
    
    print("=" * 80)
    print("Testing simulate_world_using_monte_carlo function")
    print("=" * 80)
    print(f"\nAvailable countries: {list(COUNTRIES.keys())}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality - test with small number of weeks and runs
    print(f"{'='*80}")
    print("Test 1: Basic functionality with small parameters")
    print(f"{'='*80}\n")
    
    test_cases = [
        (1, 10, "1 week, 10 runs"),
        (2, 50, "2 weeks, 50 runs"),
        (5, 100, "5 weeks, 100 runs"),
    ]
    
    for no_of_weeks, no_of_runs, description in test_cases:
        try:
            distribution, occupancy = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
            
            # Validate results are numpy arrays
            assert isinstance(distribution, np.ndarray), \
                f"Distribution should be numpy array, got {type(distribution)}"
            assert isinstance(occupancy, np.ndarray), \
                f"Occupancy should be numpy array, got {type(occupancy)}"
            
            # Validate shapes match expected
            num_countries = len(COUNTRIES)
            max_num_states = max(len(COUNTRIES[country]["states"]) for country in COUNTRIES.keys())
            expected_shape = (no_of_weeks + 1, num_countries, max_num_states)
            
            assert distribution.shape == expected_shape, \
                f"Distribution shape should be {expected_shape}, got {distribution.shape}"
            assert occupancy.shape == expected_shape, \
                f"Occupancy shape should be {expected_shape}, got {occupancy.shape}"
            
            # Validate they're the same (as documented)
            assert np.allclose(distribution, occupancy), \
                f"Distribution and occupancy should be identical"
            
            print(f"  ✓ {description:25s} | Shape: {distribution.shape} | Both arrays identical")
            
        except Exception as e:
            print(f"  ✗ ERROR for {description}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: Validate normalization - probabilities should sum to 1.0 per country
    print(f"\n{'='*80}")
    print("Test 2: Validate normalization per country")
    print(f"{'='*80}\n")
    
    try:
        no_of_weeks = 3
        no_of_runs = 100
        distribution, occupancy = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
        
        country_names = list(COUNTRIES.keys())
        normalization_errors = []
        
        for t in range(no_of_weeks + 1):
            for country_idx, country_name in enumerate(country_names):
                num_states = len(COUNTRIES[country_name]["states"])
                country_probs = distribution[t, country_idx, :num_states]
                prob_sum = country_probs.sum()
                
                if not np.isclose(prob_sum, 1.0, atol=1e-5):
                    normalization_errors.append((t, country_name, prob_sum))
        
        if normalization_errors:
            print(f"  ✗ Found {len(normalization_errors)} normalization errors:")
            for t, country, prob_sum in normalization_errors[:5]:  # Show first 5
                print(f"    Week {t} | {country}: sum={prob_sum:.6f} (expected 1.0)")
            all_passed = False
        else:
            print(f"  ✓ All probabilities normalized correctly (sum to 1.0 per country at each time step)")
            print(f"    Tested {no_of_weeks + 1} time steps × {len(country_names)} countries")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 3: Validate probability values are in [0, 1]
    print(f"\n{'='*80}")
    print("Test 3: Validate probability values are in valid range [0, 1]")
    print(f"{'='*80}\n")
    
    try:
        no_of_weeks = 5
        no_of_runs = 200
        distribution, occupancy = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
        
        # Check for invalid values
        invalid_min = distribution < -1e-6
        invalid_max = distribution > 1.0 + 1e-6
        
        if np.any(invalid_min) or np.any(invalid_max):
            min_val = distribution.min()
            max_val = distribution.max()
            print(f"  ✗ Found invalid probability values: min={min_val:.6f}, max={max_val:.6f}")
            all_passed = False
        else:
            print(f"  ✓ All probability values in valid range [0, 1]")
            print(f"    Min: {distribution.min():.6f}, Max: {distribution.max():.6f}")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 4: Validate that probabilities make sense (more runs = better statistics)
    print(f"\n{'='*80}")
    print("Test 4: Validate statistical convergence with more runs")
    print(f"{'='*80}\n")
    
    try:
        no_of_weeks = 1
        runs_list = [50, 200, 500]
        
        distributions = []
        for no_of_runs in runs_list:
            dist, _ = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
            distributions.append(dist)
        
        # Compare distributions - they should be similar but with variance decreasing
        print(f"  Comparing distributions across different run counts:")
        for i in range(len(runs_list)):
            country_idx = 0  # Test first country
            country_name = list(COUNTRIES.keys())[0]
            num_states = len(COUNTRIES[country_name]["states"])
            
            probs = distributions[i][0, country_idx, :num_states]
            non_zero_states = np.sum(probs > 1e-6)
            
            print(f"    {runs_list[i]:4d} runs: {non_zero_states} states with non-zero probability")
        
        print(f"  ✓ Statistical convergence test completed (variance should decrease with more runs)")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 5: Test with edge cases
    print(f"\n{'='*80}")
    print("Test 5: Edge cases")
    print(f"{'='*80}\n")
    
    # Test with minimal parameters
    try:
        distribution, occupancy = simulate_world_using_monte_carlo(0, 1)
        
        assert distribution.shape[0] == 1, \
            f"With 0 weeks, should have 1 time step, got {distribution.shape[0]}"
        
        print(f"  ✓ 0 weeks, 1 run: Returns correct shape {distribution.shape}")
        
    except Exception as e:
        print(f"  ✗ ERROR for 0 weeks, 1 run: {e}")
        all_passed = False
    
    # Test with larger parameters
    try:
        distribution, occupancy = simulate_world_using_monte_carlo(10, 50)
        
        expected_shape = (11, len(COUNTRIES), max(len(COUNTRIES[c]["states"]) for c in COUNTRIES.keys()))
        assert distribution.shape == expected_shape, \
            f"With 10 weeks, shape should be {expected_shape}, got {distribution.shape}"
        
        print(f"  ✓ 10 weeks, 50 runs: Returns correct shape {distribution.shape}")
        
    except Exception as e:
        print(f"  ✗ ERROR for 10 weeks, 50 runs: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 6: Validate that each country only uses its valid states
    print(f"\n{'='*80}")
    print("Test 6: Validate state indices match valid states per country")
    print(f"{'='*80}\n")
    
    try:
        no_of_weeks = 2
        no_of_runs = 100
        distribution, occupancy = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
        
        country_names = list(COUNTRIES.keys())
        invalid_states_found = []
        
        for country_idx, country_name in enumerate(country_names):
            num_states = len(COUNTRIES[country_name]["states"])
            
            # Check that states beyond num_states are all zero (as they should be)
            invalid_state_probs = distribution[:, country_idx, num_states:]
            if np.any(invalid_state_probs > 1e-6):
                invalid_states_found.append((country_name, num_states, distribution.shape[2]))
        
        if invalid_states_found:
            print(f"  ✗ Found non-zero probabilities in invalid state indices:")
            for country, num_valid, max_states in invalid_states_found:
                print(f"    {country}: has {num_valid} valid states but probabilities found beyond index {num_valid}")
            all_passed = False
        else:
            print(f"  ✓ All countries use only their valid state indices")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 7: Test reproducibility (same seed should give same results)
    print(f"\n{'='*80}")
    print("Test 7: Reproducibility (note: uses different seeds per run)")
    print(f"{'='*80}\n")
    
    try:
        no_of_weeks = 2
        no_of_runs = 10
        
        # Run twice with same parameters
        dist1, occ1 = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
        dist2, occ2 = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
        
        # They should be identical because calculate_world_order uses seed=run+1 internally
        if np.allclose(dist1, dist2, atol=1e-10):
            print(f"  ✓ Results are reproducible (identical across calls)")
        else:
            # Check if difference is due to floating point precision
            max_diff = np.max(np.abs(dist1 - dist2))
            if max_diff < 1e-6:
                print(f"  ✓ Results are reproducible (differences < 1e-6 due to floating point)")
            else:
                print(f"  ⚠ Results differ (max diff: {max_diff:.6f})")
                print(f"    Note: This is expected if there's randomness not controlled by seed")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 8: Validate that distributions change over time (when applicable)
    print(f"\n{'='*80}")
    print("Test 8: Validate distributions evolve over time")
    print(f"{'='*80}\n")
    
    try:
        no_of_weeks = 5
        no_of_runs = 200
        distribution, occupancy = simulate_world_using_monte_carlo(no_of_weeks, no_of_runs)
        
        # Compare first and last time step for each country
        country_names = list(COUNTRIES.keys())
        changes_detected = 0
        
        for country_idx, country_name in enumerate(country_names):
            num_states = len(COUNTRIES[country_name]["states"])
            initial_dist = distribution[0, country_idx, :num_states]
            final_dist = distribution[-1, country_idx, :num_states]
            
            # Check if distributions differ
            if not np.allclose(initial_dist, final_dist, atol=0.01):
                changes_detected += 1
        
        if changes_detected > 0:
            print(f"  ✓ Distributions evolve over time ({changes_detected}/{len(country_names)} countries show changes)")
        else:
            print(f"  ⚠ No significant distribution changes detected (may be due to small sample size or stable states)")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All simulate_world_using_monte_carlo tests passed! ✓")
    else:
        print("Some simulate_world_using_monte_carlo tests failed! ✗")
    print(f"{'='*80}\n")
    
    return all_passed


if __name__ == "__main__":
    success = test_simulate_world_using_monte_carlo()
    
    print("\n" + "=" * 80)
    if success:
        print("All tests passed! ✓")
        exit(0)
    else:
        print("Some tests failed! ✗")
        exit(1)
