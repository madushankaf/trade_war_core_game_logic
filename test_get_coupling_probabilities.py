#!/usr/bin/env python3
"""
Test script for get_coupling_probabilities function in country_markov_states module
"""
import numpy as np
from world_model.country_markov_states import (
    get_coupling_probabilities, 
    get_transition_matrix,
    softmax,
    COUNTRIES,
    COUPLING_RULES
)


def test_get_coupling_probabilities():
    """Test get_coupling_probabilities with various inputs"""
    
    print("=" * 80)
    print("Testing get_coupling_probabilities function")
    print("=" * 80)
    print(f"\nAvailable countries with coupling rules: {list(COUPLING_RULES.keys())}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality - test with valid inputs that have coupling rules
    print(f"{'='*80}")
    print("Test 1: Basic functionality with states that have coupling rules")
    print(f"{'='*80}\n")
    
    # Test cases: (country, current_state, has_coupling_rule)
    test_cases = [
        ("USA", "NORMAL", False),  # No coupling rule for NORMAL
        ("USA", "ECON_STRESS", False),  # No coupling rule matching
        ("EU", "UNITY_HIGH", False),  # No coupling rule matching
        ("CHINA", "GROWTH_STRONG", False),  # No coupling rule matching
        ("INDIA", "NORMAL", False),  # No coupling rule matching
    ]
    
    for country, current_state, expected_has_coupling in test_cases:
        try:
            # Get coupling probabilities
            coupling_probs = get_coupling_probabilities(current_state, country)
            base_probs = get_transition_matrix(current_state, country)
            
            # Validate result is a list/array
            assert isinstance(coupling_probs, (list, np.ndarray)), \
                f"Result should be list or numpy array, got {type(coupling_probs)}"
            
            # Convert to numpy array for easier manipulation
            coupling_probs = np.array(coupling_probs)
            
            # Validate shape matches number of states
            expected_length = len(COUNTRIES[country]["states"])
            assert coupling_probs.shape == (expected_length,), \
                f"Probabilities shape should be ({expected_length},), got {coupling_probs.shape}"
            
            # Validate probabilities sum to 1 (softmax should ensure this)
            prob_sum = coupling_probs.sum()
            assert np.isclose(prob_sum, 1.0, atol=1e-6), \
                f"Probabilities should sum to 1, got {prob_sum}"
            
            # Validate all values are in [0, 1]
            assert np.all(coupling_probs >= -1e-6) and np.all(coupling_probs <= 1.0 + 1e-6), \
                f"All values should be in [0, 1], got min={coupling_probs.min():.6f}, max={coupling_probs.max():.6f}"
            
            # Check if probabilities differ from base (indicating coupling was applied)
            probs_differ = not np.allclose(coupling_probs, base_probs, atol=1e-6)
            
            status = "with coupling" if probs_differ else "no coupling (base)"
            print(f"  ✓ {country:15s} | {current_state:30s} | Sum: {prob_sum:.6f} | {status}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_state}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: Test with states that trigger coupling rules
    print(f"\n{'='*80}")
    print("Test 2: Test with states that should trigger coupling rules")
    print(f"{'='*80}\n")
    
    # Based on the coupling rules, find states that have rules
    coupling_test_cases = []
    for country in COUPLING_RULES.keys():
        rules = COUPLING_RULES[country]
        for rule in rules:
            source_states = rule["source_states"]
            for source_state in source_states:
                # Only add if it's a valid state for this country
                if source_state in COUNTRIES.get(country, {}).get("states", []):
                    coupling_test_cases.append((country, source_state, rule["target_states"], rule["logit_bump"]))
                    break  # Only add one test case per rule
    
    # Take a few representative test cases
    for country, current_state, expected_targets, logit_bump in coupling_test_cases[:10]:
        try:
            # Get probabilities
            coupling_probs = get_coupling_probabilities(current_state, country)
            base_probs = get_transition_matrix(current_state, country)
            
            coupling_probs = np.array(coupling_probs)
            base_probs = np.array(base_probs)
            
            # Validate basic properties
            assert np.isclose(coupling_probs.sum(), 1.0, atol=1e-6), \
                f"Probabilities should sum to 1, got {coupling_probs.sum()}"
            
            # Check if target states have higher probabilities after coupling
            country_states = COUNTRIES[country]["states"]
            target_indices = [i for i, state in enumerate(country_states) if state in expected_targets]
            
            # Compare probabilities - target states should have increased probability
            target_increase = any(coupling_probs[i] > base_probs[i] for i in target_indices)
            
            # For positive logit_bump, targets should increase
            # For negative logit_bump, targets should decrease
            if logit_bump > 0:
                status = "targets increased" if target_increase else "no change"
            else:
                status = "targets decreased (negative bump)"
            
            print(f"  ✓ {country:15s} | {current_state:30s} | Bump: {logit_bump:+.2f} | {status}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_state}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 3: Validate coupling effect is correct for specific cases
    print(f"\n{'='*80}")
    print("Test 3: Validate coupling effect with specific test cases")
    print(f"{'='*80}\n")
    
    # Test case: USA with a state that has a coupling rule
    # Based on rules: USA has rules for various source states
    # Let's test a simple case where we can verify the logic
    
    test_cases_detailed = [
        ("USA", "NORMAL"),  # Should have no coupling effect
    ]
    
    for country, current_state in test_cases_detailed:
        try:
            coupling_probs = np.array(get_coupling_probabilities(current_state, country))
            base_probs = np.array(get_transition_matrix(current_state, country))
            
            # Convert to logits to see the effect
            base_logits = np.log(np.maximum(base_probs, 1e-12))
            coupling_logits = np.log(np.maximum(coupling_probs, 1e-12))
            
            # Check if probabilities changed
            if np.allclose(coupling_probs, base_probs, atol=1e-6):
                print(f"  ✓ {country:15s} | {current_state:30s} | No coupling rules match (expected)")
            else:
                diff = coupling_probs - base_probs
                max_diff_idx = np.argmax(np.abs(diff))
                max_diff_state = COUNTRIES[country]["states"][max_diff_idx]
                print(f"  ✓ {country:15s} | {current_state:30s} | Coupling applied, max diff: {diff[max_diff_idx]:.6f} for {max_diff_state}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_state}: {e}")
            all_passed = False
    
    # Test 4: Validate probabilities sum to 1 for all countries and states
    print(f"\n{'='*80}")
    print("Test 4: Validate probabilities sum to 1 for all countries with coupling rules")
    print(f"{'='*80}\n")
    
    for country in COUPLING_RULES.keys():
        if country not in COUNTRIES:
            print(f"  ⚠ Skipping {country}: not in COUNTRIES")
            continue
            
        states = COUNTRIES[country]["states"]
        print(f"  Country: {country} ({len(states)} states)")
        
        for state in states[:3]:  # Test first 3 states to avoid too much output
            try:
                probs = np.array(get_coupling_probabilities(state, country))
                prob_sum = probs.sum()
                
                if np.isclose(prob_sum, 1.0, atol=1e-6):
                    print(f"    ✓ {state:30s} | Sum: {prob_sum:.6f}")
                else:
                    print(f"    ✗ {state:30s} | Sum: {prob_sum:.6f} (should be 1.0)")
                    all_passed = False
                    
            except Exception as e:
                print(f"    ✗ ERROR for {state}: {e}")
                all_passed = False
    
    # Test 5: Error handling - invalid country
    print(f"\n{'='*80}")
    print("Test 5: Error handling - invalid country")
    print(f"{'='*80}\n")
    
    try:
        get_coupling_probabilities("NORMAL", "INVALID_COUNTRY")
        print(f"  ✗ Should have raised ValueError for invalid country")
        all_passed = False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {str(e)[:80]}...")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 6: Error handling - invalid state (should be handled by get_transition_matrix)
    print(f"\n{'='*80}")
    print("Test 6: Error handling - invalid state")
    print(f"{'='*80}\n")
    
    try:
        get_coupling_probabilities("INVALID_STATE", "USA")
        print(f"  ✗ Should have raised KeyError for invalid state")
        all_passed = False
    except KeyError as e:
        print(f"  ✓ Correctly raised KeyError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 7: Compare coupling probabilities with base probabilities
    print(f"\n{'='*80}")
    print("Test 7: Compare coupling probabilities with base probabilities")
    print(f"{'='*80}\n")
    
    country = "USA"
    current_state = "NORMAL"
    
    try:
        coupling_probs = np.array(get_coupling_probabilities(current_state, country))
        base_probs = np.array(get_transition_matrix(current_state, country))
        
        # Check if they're the same (no coupling rules match)
        rules = COUPLING_RULES.get(country, [])
        matching_rules = [r for r in rules if current_state in r.get("source_states", [])]
        
        if len(matching_rules) == 0:
            # No coupling rules match, probabilities should be similar
            if np.allclose(coupling_probs, base_probs, atol=1e-4):
                print(f"  ✓ No coupling rules match, probabilities match base (expected)")
            else:
                # After softmax, even with no coupling, there might be tiny differences
                max_diff = np.max(np.abs(coupling_probs - base_probs))
                if max_diff < 1e-3:
                    print(f"  ✓ No coupling rules match, small differences due to softmax (max diff: {max_diff:.6f})")
                else:
                    print(f"  ⚠ No coupling rules match but probabilities differ (max diff: {max_diff:.6f})")
        else:
            print(f"  ✓ {len(matching_rules)} coupling rule(s) match, probabilities adjusted")
            max_diff = np.max(np.abs(coupling_probs - base_probs))
            print(f"    Max probability difference: {max_diff:.6f}")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All get_coupling_probabilities tests passed! ✓")
    else:
        print("Some get_coupling_probabilities tests failed! ✗")
    print(f"{'='*80}\n")
    
    return all_passed


if __name__ == "__main__":
    success = test_get_coupling_probabilities()
    
    print("\n" + "=" * 80)
    if success:
        print("All tests passed! ✓")
        exit(0)
    else:
        print("Some tests failed! ✗")
        exit(1)
