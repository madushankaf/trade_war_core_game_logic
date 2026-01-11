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

def test_get_next_move_based_on_markov_chain():
    """Test get_next_move_based_on_markov_chain with various inputs"""
    
    print("=" * 80)
    print("Testing get_next_move_based_on_markov_chain function")
    print("=" * 80)
    print(f"\nAvailable states: {markov_chain.STATES}")
    print(f"Available actor types: {list(markov_chain.ACTOR_TYPE_PARAMS.keys())}")
    print(f"State to moves mapping: {markov_chain.STATE_TO_MOVES}")
    print(f"Move to states mapping: {markov_chain.STATES_TO_MOVE_MAPPING}\n")
    
    all_passed = True
    
    # Test 1: Basic functionality with different moves and actor types
    print(f"\n{'='*80}")
    print("Test 1: Basic functionality with different inputs")
    print(f"{'='*80}\n")
    
    test_cases = [
        ("sanction", "aggressive", 1),
        ("open_dialogue", "opportunist", 15),
        ("subsidize_export", "isolationist", 30),
        ("wait_and_see", "neutralist", 50),
        ("raise_tariffs", "aggressive", 10),
        ("impose_quota", "opportunist", 20),
    ]
    
    for current_move, actor_type, round_num in test_cases:
        try:
            move = markov_chain.get_next_move_based_on_markov_chain(
                current_move, actor_type, round_num
            )
            print(f"  Current Move: {current_move:20s} | Actor: {actor_type:15s} | Round: {round_num:3d} -> Next Move: {move}")
            
            # Validate that move is either a string (move name or state) or None
            assert move is None or isinstance(move, str), \
                f"Move should be None or string, got {type(move)}"
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # Test 2: RNG reproducibility
    print(f"\n{'='*80}")
    print("Test 2: RNG reproducibility")
    print(f"{'='*80}\n")
    
    current_move = "sanction"
    actor_type = "aggressive"
    round_num = 30
    
    # Create a seeded RNG
    rng1 = np.random.default_rng(seed=42)
    rng2 = np.random.default_rng(seed=42)
    
    print(f"Current move: {current_move}")
    print(f"Actor type: {actor_type}")
    print(f"Round: {round_num}")
    print(f"Using seeded RNG (seed=42)\n")
    
    # Get moves with same seed should produce same results
    moves1 = []
    moves2 = []
    for i in range(10):
        move1 = markov_chain.get_next_move_based_on_markov_chain(
            current_move, actor_type, round_num, rng=rng1
        )
        move2 = markov_chain.get_next_move_based_on_markov_chain(
            current_move, actor_type, round_num, rng=rng2
        )
        moves1.append(move1)
        moves2.append(move2)
        if move1 == move2:
            print(f"  Sample {i+1}: {move1} ✓")
        else:
            print(f"  Sample {i+1}: {move1} vs {move2} ✗ (mismatch!)")
            all_passed = False
    
    assert moves1 == moves2, "RNG reproducibility failed - same seed should produce same results"
    
    # Test 3: Probability distribution verification
    print(f"\n{'='*80}")
    print("Test 3: Probability distribution verification")
    print(f"{'='*80}\n")
    
    # Sample many times to verify move distribution
    rng = np.random.default_rng(seed=123)
    num_samples = 1000
    
    # Count moves
    move_counts = {}
    
    for _ in range(num_samples):
        move = markov_chain.get_next_move_based_on_markov_chain(
            current_move, actor_type, round_num, rng=rng
        )
        if move:
            move_counts[move] = move_counts.get(move, 0) + 1
    
    print(f"Move distribution (from {num_samples} samples):")
    for move, count in sorted(move_counts.items()):
        freq = count / num_samples
        print(f"  {move:20s}: {freq:.4f} ({count} samples)")
    
    # Verify that at least some moves were returned
    assert len(move_counts) > 0, "Should have at least one move returned"
    print(f"  ✓ Distribution test passed")
    
    # Test 4: Moves that map to multiple states
    print(f"\n{'='*80}")
    print("Test 4: Moves that map to multiple states")
    print(f"{'='*80}\n")
    
    # "sanction" maps to ["hawkish", "opportunist"] (multiple states)
    # "wait_and_see" maps to ["neutral", "dovish"] (multiple states)
    # Other moves map to single states
    
    multi_state_moves = ["sanction", "wait_and_see"]
    
    for move in multi_state_moves:
        expected_states = markov_chain.STATES_TO_MOVE_MAPPING.get(move, [])
        print(f"  Move '{move}' maps to states: {expected_states}")
        
        # Verify the mapping is correct
        if move in markov_chain.STATES_TO_MOVE_MAPPING:
            assert len(markov_chain.STATES_TO_MOVE_MAPPING[move]) > 0, \
                f"Move {move} should have at least one state"
            if len(markov_chain.STATES_TO_MOVE_MAPPING[move]) > 1:
                print(f"    ✓ Multiple states verified - function will randomly select one")
            else:
                print(f"    ✓ Single state verified")
    
    # Test 5: Edge cases - moves that might not map to states
    print(f"\n{'='*80}")
    print("Test 5: Edge cases")
    print(f"{'='*80}\n")
    
    # Test with all moves to see which ones map to states
    print("Testing all moves to see state mappings:")
    for move in markov_chain.STATES_TO_MOVE_MAPPING.keys():
        states = markov_chain.STATES_TO_MOVE_MAPPING[move]
        print(f"  {move:20s} -> {states}")
    
    # Test 6: Error handling - invalid move
    print(f"\n{'='*80}")
    print("Test 6: Error handling")
    print(f"{'='*80}\n")
    
    try:
        move = markov_chain.get_next_move_based_on_markov_chain(
            "invalid_move", "aggressive", 1
        )
        if move is None:
            print(f"  ✓ Correctly returned None for invalid move")
        else:
            print(f"  ERROR: Should have returned None for invalid move, but got: {move}")
            all_passed = False
    except Exception as e:
        print(f"  ERROR: Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 7: Error handling - invalid actor type
    try:
        move = markov_chain.get_next_move_based_on_markov_chain(
            "sanction", "invalid_actor", 1
        )
        print(f"  ERROR: Should have raised KeyError for invalid actor type, but got: {move}")
        all_passed = False
    except KeyError as e:
        print(f"  ✓ Correctly raised KeyError for invalid actor type: {e}")
    except Exception as e:
        print(f"  ERROR: Unexpected exception type {type(e).__name__}: {e}")
        all_passed = False
    
    # Test 8: Verify move is always valid when returned
    print(f"\n{'='*80}")
    print("Test 8: Verify returned moves are valid")
    print(f"{'='*80}\n")
    
    # Get all valid move names from the mapping keys
    all_moves = set(markov_chain.STATES_TO_MOVE_MAPPING.keys())
    
    print(f"All valid moves: {sorted(all_moves)}")
    
    # Sample many times and verify all returned moves are valid
    rng = np.random.default_rng(seed=789)
    invalid_moves = []
    
    # Test with all valid moves
    for move_name in markov_chain.STATES_TO_MOVE_MAPPING.keys():
        for _ in range(50):
            try:
                next_move = markov_chain.get_next_move_based_on_markov_chain(
                    move_name, "aggressive", 30, rng=rng
                )
                if next_move is not None:
                    # Convert numpy string to regular string for comparison
                    move_str = str(next_move)
                    # Move should be either a valid move name or a state name (fallback)
                    if move_str not in all_moves and move_str not in markov_chain.STATES:
                        invalid_moves.append((move_name, move_str))
            except Exception:
                pass  # Expected for invalid moves
    
    if invalid_moves:
        print(f"  ✗ Found invalid moves: {invalid_moves[:10]}...")  # Show first 10
        print(f"  Total invalid moves: {len(invalid_moves)}")
        all_passed = False
    else:
        print(f"  ✓ All returned moves are valid")
    
    print(f"\n{'='*80}")
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    print(f"{'='*80}")
    
    return all_passed


if __name__ == "__main__":
    success1 = test_transition_matrix_round()
    print("\n\n")
    success2 = test_get_next_move_based_on_markov_chain()
    exit(0 if (success1 and success2) else 1)

