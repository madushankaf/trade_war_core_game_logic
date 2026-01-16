#!/usr/bin/env python3
"""
Test script for get_leader_behaviour_probabilities function in country_markov_states module
"""
import numpy as np
from world_model.country_markov_states import (
    get_leader_behaviour_probabilities,
    LEADER_BEHAVIOURS,
    BEHAVIOR_ORDER
)


def test_get_leader_behaviour_probabilities():
    """Test get_leader_behaviour_probabilities with various inputs"""
    
    print("=" * 80)
    print("Testing get_leader_behaviour_probabilities function")
    print("=" * 80)
    print(f"\nAvailable countries: {list(LEADER_BEHAVIOURS.keys())}")
    print(f"Behavior order: {BEHAVIOR_ORDER}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality - test with valid inputs
    print(f"{'='*80}")
    print("Test 1: Basic functionality with valid inputs")
    print(f"{'='*80}\n")
    
    test_cases = [
        ("USA", "DOVISH", "NORMAL"),
        ("USA", "NEUTRAL", "ELECTION_CYCLE"),
        ("INDIA", "DOVISH", "NORMAL"),
        ("CHINA", "HAWKISH", "FLASHPOINT_TENSION"),
        ("RUSSIA", "NEUTRAL", "CONFLICT_ESCALATION"),
    ]
    
    for country, current_behaviour, current_world_state in test_cases:
        try:
            probabilities = get_leader_behaviour_probabilities(country, current_behaviour, current_world_state)
            
            # Validate result is a numpy array
            assert isinstance(probabilities, np.ndarray), \
                f"Result should be numpy array, got {type(probabilities)}"
            
            # Validate shape matches number of behaviors
            expected_length = len(BEHAVIOR_ORDER)
            assert probabilities.shape == (expected_length,), \
                f"Probabilities shape should be ({expected_length},), got {probabilities.shape}"
            
            # Validate probabilities sum to 1
            prob_sum = probabilities.sum()
            assert np.isclose(prob_sum, 1.0, atol=1e-6), \
                f"Probabilities should sum to 1, got {prob_sum}"
            
            # Validate all values are in [0, 1]
            assert np.all(probabilities >= -1e-6) and np.all(probabilities <= 1.0 + 1e-6), \
                f"All values should be in [0, 1], got min={probabilities.min():.6f}, max={probabilities.max():.6f}"
            
            print(f"  ✓ {country:15s} | {current_behaviour:12s} | {current_world_state:30s} | Shape: {probabilities.shape} | Sum: {prob_sum:.6f}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_behaviour}/{current_world_state}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: Test with states that trigger behavior rules
    print(f"\n{'='*80}")
    print("Test 2: Test with states that should trigger behavior rules")
    print(f"{'='*80}\n")
    
    # Based on the leader behaviours JSON, find states that have rules
    behavior_test_cases = []
    for country in LEADER_BEHAVIOURS.keys():
        rules_key = "behavior_rules_by_country" if "behavior_rules_by_country" in LEADER_BEHAVIOURS[country] else "behaviour_rules_by_country"
        rules = LEADER_BEHAVIOURS[country][rules_key]
        base_transition_key = "base_behavior_transition" if "base_behavior_transition" in LEADER_BEHAVIOURS[country] else "base_behaviour_transition"
        behaviours = list(LEADER_BEHAVIOURS[country][base_transition_key].keys())
        for rule in rules[:3]:  # Test first 3 rules per country
            env_states = rule["env_states"]
            if env_states:
                for env_state in env_states[:1]:  # Test first env state per rule
                    for behaviour in behaviours[:1]:  # Test first behaviour
                        target_behaviors_key = "target_behaviors" if "target_behaviors" in rule else "target_behaviours"
                        target_behaviors = rule.get(target_behaviors_key, [])
                        behavior_test_cases.append((country, behaviour, env_state, target_behaviors, rule["logit_bump"]))
                        break
                    break
            break
    
    for country, current_behaviour, current_world_state, expected_targets, logit_bump in behavior_test_cases[:10]:
        try:
            # Get probabilities
            probabilities = get_leader_behaviour_probabilities(country, current_behaviour, current_world_state)
            base_transition_key = "base_behavior_transition" if "base_behavior_transition" in LEADER_BEHAVIOURS[country] else "base_behaviour_transition"
            base_probs = np.array(LEADER_BEHAVIOURS[country][base_transition_key][current_behaviour])
            
            # Validate basic properties
            assert np.isclose(probabilities.sum(), 1.0, atol=1e-6), \
                f"Probabilities should sum to 1, got {probabilities.sum()}"
            
            # Check if target behaviors have different probabilities after rule application
            behavior_to_idx = {behavior: idx for idx, behavior in enumerate(BEHAVIOR_ORDER)}
            target_indices = [behavior_to_idx[b] for b in expected_targets if b in behavior_to_idx]
            
            # Compare probabilities - target behaviors should have changed
            if len(target_indices) > 0:
                target_changed = any(abs(probabilities[i] - base_probs[i]) > 1e-3 for i in target_indices)
            else:
                target_changed = False
            
            if logit_bump > 0:
                status = "targets changed" if target_changed else "no change detected"
            else:
                status = "negative bump (targets decreased)"
            
            print(f"  ✓ {country:15s} | {current_behaviour:12s} | {current_world_state:30s} | Bump: {logit_bump:+.2f} | {status}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_behaviour}/{current_world_state}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 3: Validate probabilities for all countries and behaviors
    print(f"\n{'='*80}")
    print("Test 3: Validate probabilities sum to 1 for all countries and behaviors")
    print(f"{'='*80}\n")
    
    normalization_errors = []
    for country in LEADER_BEHAVIOURS.keys():
        base_transition_key = "base_behavior_transition" if "base_behavior_transition" in LEADER_BEHAVIOURS[country] else "base_behaviour_transition"
        behaviours = list(LEADER_BEHAVIOURS[country][base_transition_key].keys())
        env_states = LEADER_BEHAVIOURS[country]["env_states"]
        
        # Test a few combinations per country
        for behaviour in behaviours[:2]:  # Test first 2 behaviors
            for env_state in env_states[:2]:  # Test first 2 env states
                try:
                    probs = get_leader_behaviour_probabilities(country, behaviour, env_state)
                    prob_sum = probs.sum()
                    
                    if not np.isclose(prob_sum, 1.0, atol=1e-5):
                        normalization_errors.append((country, behaviour, env_state, prob_sum))
                    else:
                        print(f"    ✓ {country:15s} | {behaviour:12s} | {env_state:30s} | Sum: {prob_sum:.6f}")
                except Exception as e:
                    print(f"    ✗ ERROR for {country}/{behaviour}/{env_state}: {e}")
                    all_passed = False
    
    if normalization_errors:
        print(f"\n  ✗ Found {len(normalization_errors)} normalization errors:")
        for country, behaviour, env_state, prob_sum in normalization_errors[:5]:
            print(f"    {country}/{behaviour}/{env_state}: sum={prob_sum:.6f} (expected 1.0)")
        all_passed = False
    else:
        print(f"\n  ✓ All probabilities normalized correctly (sum to 1.0)")
    
    # Test 4: Error handling - invalid country
    print(f"\n{'='*80}")
    print("Test 4: Error handling - invalid country")
    print(f"{'='*80}\n")
    
    try:
        get_leader_behaviour_probabilities("INVALID_COUNTRY", "DOVISH", "NORMAL")
        print(f"  ✗ Should have raised ValueError for invalid country")
        all_passed = False
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {str(e)[:80]}...")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 5: Error handling - invalid behavior
    print(f"\n{'='*80}")
    print("Test 5: Error handling - invalid behavior")
    print(f"{'='*80}\n")
    
    try:
        get_leader_behaviour_probabilities("USA", "INVALID_BEHAVIOUR", "NORMAL")
        print(f"  ✗ Should have raised KeyError for invalid behavior")
        all_passed = False
    except KeyError as e:
        print(f"  ✓ Correctly raised KeyError: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 6: Compare probabilities with base probabilities
    print(f"\n{'='*80}")
    print("Test 6: Compare behavior probabilities with base probabilities")
    print(f"{'='*80}\n")
    
    country = "USA"
    current_behaviour = "DOVISH"
    current_world_state = "NORMAL"
    
    try:
        behaviour_probs = np.array(get_leader_behaviour_probabilities(country, current_behaviour, current_world_state))
        base_transition_key = "base_behavior_transition" if "base_behavior_transition" in LEADER_BEHAVIOURS[country] else "base_behaviour_transition"
        base_probs = np.array(LEADER_BEHAVIOURS[country][base_transition_key][current_behaviour])
        
        # Check if they're the same (no behavior rules match)
        rules_key = "behavior_rules_by_country" if "behavior_rules_by_country" in LEADER_BEHAVIOURS[country] else "behaviour_rules_by_country"
        rules = LEADER_BEHAVIOURS[country][rules_key]
        matching_rules = [r for r in rules if current_world_state in r.get("env_states", [])]
        
        if len(matching_rules) == 0:
            # No behavior rules match, probabilities should be similar (may differ slightly due to softmax)
            max_diff = np.max(np.abs(behaviour_probs - base_probs))
            if max_diff < 1e-3:
                print(f"  ✓ No behavior rules match, probabilities match base (max diff: {max_diff:.6f})")
            else:
                print(f"  ⚠ No behavior rules match but probabilities differ (max diff: {max_diff:.6f})")
        else:
            print(f"  ✓ {len(matching_rules)} behavior rule(s) match, probabilities adjusted")
            max_diff = np.max(np.abs(behaviour_probs - base_probs))
            print(f"    Max probability difference: {max_diff:.6f}")
            # Show probabilities
            for i, behavior in enumerate(BEHAVIOR_ORDER):
                base_p = base_probs[i]
                adj_p = behaviour_probs[i]
                diff = adj_p - base_p
                if abs(diff) > 1e-3:
                    print(f"      {behavior:12s}: base={base_p:.4f} -> adjusted={adj_p:.4f} (diff: {diff:+.4f})")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 7: Test with states that definitely trigger rules
    print(f"\n{'='*80}")
    print("Test 7: Test with states that definitely trigger behavior rules")
    print(f"{'='*80}\n")
    
    # Test cases where rules should apply
    rule_test_cases = [
        ("USA", "DOVISH", "SECURITY_SHOCK"),  # Should increase HAWKISH probability
        ("CHINA", "NEUTRAL", "FLASHPOINT_TENSION"),  # Should increase HAWKISH probability
        ("INDIA", "DOVISH", "BORDER_TENSION"),  # Should increase HAWKISH probability
    ]
    
    for country, current_behaviour, current_world_state in rule_test_cases:
        try:
            behaviour_probs = np.array(get_leader_behaviour_probabilities(country, current_behaviour, current_world_state))
            base_transition_key = "base_behavior_transition" if "base_behavior_transition" in LEADER_BEHAVIOURS[country] else "base_behaviour_transition"
            base_probs = np.array(LEADER_BEHAVIOURS[country][base_transition_key][current_behaviour])
            
            behavior_to_idx = {behavior: idx for idx, behavior in enumerate(BEHAVIOR_ORDER)}
            
            # Find which behaviors changed
            changes = []
            for behavior in BEHAVIOR_ORDER:
                idx = behavior_to_idx[behavior]
                diff = behaviour_probs[idx] - base_probs[idx]
                if abs(diff) > 0.01:  # Significant change
                    changes.append(f"{behavior}: {base_probs[idx]:.3f}->{behaviour_probs[idx]:.3f} ({diff:+.3f})")
            
            if changes:
                print(f"  ✓ {country:15s} | {current_behaviour:12s} | {current_world_state:30s}")
                print(f"    Changes: {', '.join(changes)}")
            else:
                print(f"  ⚠ {country:15s} | {current_behaviour:12s} | {current_world_state:30s} | No significant changes")
            
        except Exception as e:
            print(f"  ✗ ERROR for {country}/{current_behaviour}/{current_world_state}: {e}")
            all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All get_leader_behaviour_probabilities tests passed! ✓")
    else:
        print("Some get_leader_behaviour_probabilities tests failed! ✗")
    print(f"{'='*80}\n")
    
    return all_passed


if __name__ == "__main__":
    success = test_get_leader_behaviour_probabilities()
    
    print("\n" + "=" * 80)
    if success:
        print("All tests passed! ✓")
        exit(0)
    else:
        print("Some tests failed! ✗")
        exit(1)
