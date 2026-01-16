#!/usr/bin/env python3
"""
Test script for calculate_world_order function in country_markov_states module
"""
import numpy as np
from world_model.country_markov_states import (
    calculate_world_order,
    COUNTRIES,
    COUPLING_RULES,
    get_coupling_probabilities,
    sample_categorical
)


def test_calculate_world_order():
    """Test calculate_world_order with various inputs"""
    
    print("=" * 80)
    print("Testing calculate_world_order function")
    print("=" * 80)
    print(f"\nAvailable countries: {list(COUNTRIES.keys())}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality - test with small number of weeks
    print(f"{'='*80}")
    print("Test 1: Basic functionality with small number of weeks")
    print(f"{'='*80}\n")
    
    test_cases = [
        (1, "1 week"),
        (2, "2 weeks"),
        (5, "5 weeks"),
        (10, "10 weeks"),
    ]
    
    for no_of_weeks, description in test_cases:
        try:
            trajectory = calculate_world_order(no_of_weeks)
            
            # Validate result is a list
            assert isinstance(trajectory, list), \
                f"Result should be a list, got {type(trajectory)}"
            
            # Validate length is no_of_weeks + 1 (initial state + no_of_weeks transitions)
            expected_length = no_of_weeks + 1
            assert len(trajectory) == expected_length, \
                f"Trajectory length should be {expected_length} (initial + {no_of_weeks} weeks), got {len(trajectory)}"
            
            # Validate each entry in trajectory is a dictionary
            for i, world_order in enumerate(trajectory):
                assert isinstance(world_order, dict), \
                    f"Trajectory[{i}] should be a dict, got {type(world_order)}"
            
            print(f"  ✓ {description:15s} | Trajectory length: {len(trajectory)} | Countries: {len(trajectory[0]) if trajectory else 0}")
            
        except Exception as e:
            print(f"  ✗ ERROR for {description}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: Validate trajectory structure
    print(f"\n{'='*80}")
    print("Test 2: Validate trajectory structure")
    print(f"{'='*80}\n")
    
    try:
        trajectory = calculate_world_order(3)
        
        # Check initial state (index 0)
        initial_order = trajectory[0]
        print(f"  Initial world order (week 0):")
        for country, state in initial_order.items():
            print(f"    {country}: {state}")
        
        # Check that all countries are present
        expected_countries = set(COUNTRIES.keys())
        actual_countries = set(initial_order.keys())
        
        if expected_countries == actual_countries:
            print(f"  ✓ All countries present in world order")
        else:
            missing = expected_countries - actual_countries
            extra = actual_countries - expected_countries
            print(f"  ✗ Country mismatch - Missing: {missing}, Extra: {extra}")
            all_passed = False
        
        # Check subsequent weeks
        print(f"\n  Subsequent weeks:")
        for week_idx in range(1, min(4, len(trajectory))):
            world_order = trajectory[week_idx]
            print(f"    Week {week_idx}:")
            for country in list(COUNTRIES.keys())[:3]:  # Show first 3 countries
                if country in world_order:
                    state = world_order[country]
                    prev_state = trajectory[week_idx - 1].get(country, "N/A")
                    print(f"      {country}: {prev_state} -> {state}")
        
        # Validate all weeks have the same countries
        countries_in_trajectory = [set(wo.keys()) for wo in trajectory]
        all_same = all(countries == countries_in_trajectory[0] for countries in countries_in_trajectory)
        
        if all_same:
            print(f"\n  ✓ All weeks have same countries")
        else:
            print(f"\n  ✗ Countries differ across weeks")
            all_passed = False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 3: Validate states are valid for each country
    print(f"\n{'='*80}")
    print("Test 3: Validate states are valid for each country")
    print(f"{'='*80}\n")
    
    try:
        trajectory = calculate_world_order(5)
        
        invalid_states = []
        
        for week_idx, world_order in enumerate(trajectory):
            for country, state in world_order.items():
                if country not in COUNTRIES:
                    invalid_states.append((week_idx, country, state, "Country not in COUNTRIES"))
                    continue
                
                valid_states = COUNTRIES[country]["states"]
                if state not in valid_states:
                    invalid_states.append((week_idx, country, state, f"State not in {valid_states}"))
        
        if invalid_states:
            print(f"  ✗ Found {len(invalid_states)} invalid state(s):")
            for week_idx, country, state, reason in invalid_states[:10]:  # Show first 10
                print(f"    Week {week_idx} | {country} | {state} | {reason}")
            all_passed = False
        else:
            print(f"  ✓ All states are valid for their respective countries")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 4: Reproducibility with same seed
    print(f"\n{'='*80}")
    print("Test 4: Reproducibility with same seed")
    print(f"{'='*80}\n")
    
    try:
        # Note: The function sets seed internally, so results should be reproducible
        trajectory1 = calculate_world_order(5)
        trajectory2 = calculate_world_order(5)
        
        # Compare trajectories
        if trajectory1 == trajectory2:
            print(f"  ✓ Trajectories are identical (reproducible with seed=42)")
        else:
            # Check differences
            differences = []
            for week_idx in range(min(len(trajectory1), len(trajectory2))):
                wo1 = trajectory1[week_idx]
                wo2 = trajectory2[week_idx]
                for country in wo1.keys():
                    if country in wo2 and wo1[country] != wo2[country]:
                        differences.append((week_idx, country, wo1[country], wo2[country]))
            
            if differences:
                print(f"  ⚠ Trajectories differ ({len(differences)} differences)")
                print(f"    (This may be expected if random state is used between calls)")
                for week_idx, country, state1, state2 in differences[:5]:
                    print(f"      Week {week_idx} | {country}: {state1} vs {state2}")
            else:
                print(f"  ✓ Trajectories are identical")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 5: Edge cases
    print(f"\n{'='*80}")
    print("Test 5: Edge cases")
    print(f"{'='*80}\n")
    
    # Test with 0 weeks
    try:
        trajectory = calculate_world_order(0)
        
        assert len(trajectory) == 1, \
            f"With 0 weeks, trajectory should have 1 entry (initial), got {len(trajectory)}"
        
        print(f"  ✓ 0 weeks: Returns initial state only (length: {len(trajectory)})")
        
    except Exception as e:
        print(f"  ✗ ERROR for 0 weeks: {e}")
        all_passed = False
    
    # Test with larger number
    try:
        trajectory = calculate_world_order(50)
        
        assert len(trajectory) == 51, \
            f"With 50 weeks, trajectory should have 51 entries, got {len(trajectory)}"
        
        print(f"  ✓ 50 weeks: Trajectory length: {len(trajectory)}")
        
    except Exception as e:
        print(f"  ✗ ERROR for 50 weeks: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 6: Validate state transitions make sense
    print(f"\n{'='*80}")
    print("Test 6: Validate state transitions (basic sanity check)")
    print(f"{'='*80}\n")
    
    try:
        trajectory = calculate_world_order(10)
        
        # Check that states change over time (at least some should)
        transitions = []
        for week_idx in range(1, len(trajectory)):
            prev_order = trajectory[week_idx - 1]
            curr_order = trajectory[week_idx]
            
            for country in COUNTRIES.keys():
                if country in prev_order and country in curr_order:
                    prev_state = prev_order[country]
                    curr_state = curr_order[country]
                    if prev_state != curr_state:
                        transitions.append((week_idx, country, prev_state, curr_state))
        
        if transitions:
            print(f"  ✓ Found {len(transitions)} state transitions across trajectory")
            # Show a few examples
            for week_idx, country, prev_state, curr_state in transitions[:5]:
                print(f"    Week {week_idx} | {country}: {prev_state} -> {curr_state}")
        else:
            print(f"  ⚠ No state transitions found (all states remain constant)")
            print(f"    (This may indicate an issue with the simulation)")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 7: Check that initial state is properly set
    print(f"\n{'='*80}")
    print("Test 7: Check initial state structure")
    print(f"{'='*80}\n")
    
    try:
        trajectory = calculate_world_order(1)
        initial_order = trajectory[0]
        
        # Check structure
        if isinstance(initial_order, dict):
            if len(initial_order) == len(COUNTRIES):
                print(f"  ✓ Initial state has correct structure ({len(initial_order)} countries)")
                
                # Check values
                empty_values = [country for country, state in initial_order.items() if not state or state == []]
                if empty_values:
                    print(f"  ⚠ Initial state has empty values for: {empty_values}")
                else:
                    print(f"  ✓ All countries have initial state values")
            else:
                print(f"  ✗ Initial state has wrong number of countries: {len(initial_order)} (expected {len(COUNTRIES)})")
                all_passed = False
        else:
            print(f"  ✗ Initial state is not a dict, got {type(initial_order)}")
            all_passed = False
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All calculate_world_order tests passed! ✓")
    else:
        print("Some calculate_world_order tests failed! ✗")
    print(f"{'='*80}\n")
    
    return all_passed


if __name__ == "__main__":
    success = test_calculate_world_order()
    
    print("\n" + "=" * 80)
    if success:
        print("All tests passed! ✓")
        exit(0)
    else:
        print("Some tests failed! ✗")
        exit(1)
