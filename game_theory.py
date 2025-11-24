from typing import Dict, List, Optional, Tuple
import numpy as np
import time
from game_moves import GameMoves
import nashpy as nash
from scipy.optimize import linprog
from game_logger import get_game_logger
import random

# Phase boundaries (deprecated - now calculated from percentages)
# Kept for backward compatibility
PHASE_1_START = 0
PHASE_1_END = 15
PHASE_2_START = 16
PHASE_2_END = 100
PHASE_3_START = 101
PHASE_3_END = 200

def calculate_phase_boundaries(num_rounds: int, phase_percentages: Dict[str, float]) -> Dict[str, List[int]]:
    """
    Calculate phase boundaries from total rounds and phase percentages.
    
    Args:
        num_rounds: Total number of game rounds
        phase_percentages: Dictionary with phase percentages, e.g. {'p1': 0.20, 'p2': 0.50, 'p3': 0.30}
        
    Returns:
        Dictionary with phase boundaries, e.g. {'p1': [0, 19], 'p2': [20, 99], 'p3': [100, 199]}
    """
    # Validate percentages sum to 1.0 (with small tolerance for floating point)
    total_percentage = sum(phase_percentages.values())
    if abs(total_percentage - 1.0) > 0.01:
        raise ValueError(f"Phase percentages must sum to 1.0, got {total_percentage}")
    
    # Calculate phase boundaries
    phases = {}
    current_start = 0
    
    # Calculate each phase
    for phase_key in ['p1', 'p2', 'p3']:
        if phase_key not in phase_percentages:
            raise ValueError(f"Missing phase percentage for {phase_key}")
        
        percentage = phase_percentages[phase_key]
        phase_size = int(num_rounds * percentage)
        
        # Ensure we don't exceed total rounds
        phase_end = min(current_start + phase_size - 1, num_rounds - 1)
        
        phases[phase_key] = [current_start, phase_end]
        current_start = phase_end + 1
    
    # Ensure last phase ends at num_rounds - 1
    phases['p3'][1] = num_rounds - 1
    
    return phases

def check_dominant_move(my_moves: List[dict], possible_opponent_moves: List[dict], payoff_matrix: List[dict]) -> Optional[dict]:
    """
    Check if there is a dominant move (strategy) that is strictly better than 
    all other available moves, regardless of what the opponent plays.
    
    Args:
        my_moves: List of the player's available moves (e.g., game['computer_moves'])
        possible_opponent_moves: List of ALL moves the opponent could play (e.g., game['user_moves'])
        payoff_matrix: List of payoff entries
        
    Returns:
        Optional[dict]: The dominant move if found, None otherwise
    """
    print(f"\nChecking for True Dominant Strategy...")
    
    if not my_moves or not possible_opponent_moves:
        return None
    
    # If there's only one move, it is trivially dominant
    if len(my_moves) == 1:
        return my_moves[0]

    # Iterate through each of my potential moves (Candidate)
    for candidate_move in my_moves:
        is_strictly_dominant = True
        
        # Compare the Candidate against every other move I could make (Alternative)
        for alternative_move in my_moves:
            if candidate_move['name'] == alternative_move['name']:
                continue
            
            # Check against EVERY possible move the opponent has
            for opp_move in possible_opponent_moves:
                
                # IMPORTANT: Use deterministic expected payoff for theoretical calculations
                payoff_candidate = get_expected_payoff(candidate_move, opp_move, payoff_matrix)
                payoff_alternative = get_expected_payoff(alternative_move, opp_move, payoff_matrix)
                
                # If the candidate is NOT better in even one scenario, it is not dominant.
                # Use <= for Strict Dominance (must be strictly better)
                # Use < for Weak Dominance (can be equal)
                if payoff_candidate <= payoff_alternative:
                    is_strictly_dominant = False
                    break 
            
            if not is_strictly_dominant:
                break
        
        # If the candidate survived all comparisons against all opponent moves
        if is_strictly_dominant:
            print(f"Found dominant strategy: {candidate_move['name']}")
            return candidate_move

    print("No dominant strategy found.")
    return None

# def check_dominant_move(moves: List[dict], opponent_move: dict, payoff_matrix: List[dict]) -> Optional[dict]:
#     """
#     Check if there's a dominant move among the given moves against a specific opponent move.
#     Returns the dominant move if found, None otherwise.
    
#     Args:
#         moves: List of possible moves to check
#         opponent_move: The opponent's move to evaluate against
#         payoff_matrix: List of payoff entries
        
#     Returns:
#         Optional[dict]: The dominant move if found, None otherwise
#     """
#     print(f"\nChecking for dominant move against opponent move: {opponent_move['name']}")
    
#     if not moves:
#         print("No moves to check")
#         return None
    
#     if len(moves) == 1:
#         return moves[0]
    
#     #guard rail for unknown opponent move
#     payoff_entry = next(
#         (entry for entry in payoff_matrix 
#          if entry['computer_move_name'] == opponent_move['name'] 
#          ),
#         None
#     )

#     if payoff_entry is None:
#         return None
    
    
#     # For each move, check if it's dominant
#     for move in moves:
#         print(f"\nChecking if {move['name']} is dominant")
#         is_dominant = True
        
#         for other_move in moves:
#             if move == other_move:
#                 continue
                
#             print(f"Comparing {move['name']} vs {other_move['name']}")
#             is_better = is_the_move_with_the_better_payoff(move, other_move, opponent_move, payoff_matrix)
#             if is_better is None:
#                 break
#             if not is_better:
#                 print(f"{move['name']} is not better than {other_move['name']}")
#                 is_dominant = False
#                 break
        
#         if is_dominant:
#             print(f"Found dominant move: {move['name']}")
#             return move
    
#     print("No dominant move found")
#     return None

def is_the_move_with_the_better_payoff(move1: dict, move2: dict, opponent_move: dict, payoff_matrix: List[dict]) -> bool:
    """
    Compare payoffs between two moves against an opponent move.
    Returns True if move1 has better payoff than move2.
    
    Args:
        move1: First move to compare
        move2: Second move to compare
        opponent_move: Opponent's move to evaluate against
        payoff_matrix: List of payoff entries
        
    Returns:
        bool: True if move1 has better payoff than move2 against opponent_move
    """
    # Get payoffs for each move against the opponent (deterministic for comparison)
    payoff1 = get_expected_payoff(move1, opponent_move, payoff_matrix)
    payoff2 = get_expected_payoff(move2, opponent_move, payoff_matrix)
    
    print(f"Payoff comparison: {move1['name']}({payoff1}) vs {move2['name']}({payoff2})")
    
    # Move1 is better if it has a higher payoff
    return payoff1 > payoff2

def get_expected_payoff(move: dict, opponent_move: dict, payoff_matrix: List[dict]) -> float:
    """
    Calculate the expected (deterministic) payoff for a move against a specific opponent move.
    This function is used by solvers (Nash equilibrium, linear programming, etc.) and should
    NEVER include random noise to ensure stable, reproducible results.
    
    Args:
        move: The move to evaluate
        opponent_move: The opponent's move to evaluate against
        payoff_matrix: List of payoff entries with structure:
            [
                {
                    "user_move_name": str,
                    "computer_move_name": str,
                    "payoff": {"user": float, "computer": float}
                },
                ...
            ]
        
    Returns:
        float: The expected payoff (deterministic, no noise)
    """
    print(f"\nCalculating expected payoff for move: {move['name']} (type: {move['type']}, probability: {move['probability']})")
    print(f"Against opponent move: {opponent_move['name']} (type: {opponent_move['type']}, probability: {opponent_move['probability']})")
    
    # Extract move parameters
    move_name = move.get('name', '')
    move_prob = move.get('probability', 1.0)
    opp_name = opponent_move.get('name', '')
    opp_prob = opponent_move.get('probability', 1.0)
    player = move.get('player', None)
    if player is None:
        raise ValueError(f"Move {move['name']} has no player")
    
    # Find matching payoff in the matrix based on player perspective
    if player == 'user':
        payoff_entry = next(
            (entry for entry in payoff_matrix
             if entry['user_move_name'] == move_name 
             and entry['computer_move_name'] == opp_name), 
            None
        )
    elif player == 'computer':
        payoff_entry = next(
            (entry for entry in payoff_matrix
             if entry['user_move_name'] == opp_name 
             and entry['computer_move_name'] == move_name), 
            None
        )
    else:
        raise ValueError("player must be 'user' or 'computer'")

    if not payoff_entry:
        print(f"No payoff entry found for move combination: {move_name} vs {opp_name}")
        return 0.0
    
    # Get base payoff and adjust for probabilities
    # Convert enum to string value for dictionary access
    player_key = player.value if hasattr(player, 'value') else str(player)
    base_payoff = payoff_entry['payoff'][player_key]
    expected_payoff = base_payoff * move_prob * opp_prob
    
    print(f"Found payoff entry: {payoff_entry}")
    print(f"Base payoff: {base_payoff}")
    print(f"Expected payoff (with probabilities): {expected_payoff}")
    
    return expected_payoff

def get_realized_payoff(move: dict, opponent_move: dict, payoff_matrix: List[dict]) -> float:
    """
    Calculate the realized payoff for a move against a specific opponent move, including random noise.
    This function is used for actual scoring of game rounds, where noise represents real-world uncertainty.
    
    Args:
        move: The move to evaluate
        opponent_move: The opponent's move to evaluate against
        payoff_matrix: List of payoff entries with structure:
            [
                {
                    "user_move_name": str,
                    "computer_move_name": str,
                    "payoff": {"user": float, "computer": float}
                },
                ...
            ]
        
    Returns:
        float: The realized payoff (with noise, never negative)
    """
    # Get deterministic expected payoff
    expected_payoff = get_expected_payoff(move, opponent_move, payoff_matrix)
    
    # Add random noise to simulate real-world uncertainty
    noise = np.random.normal(0, 0.1)  # Small random noise
    print(f"\nTotal payoff before noise: {expected_payoff}")
    print(f"Generated noise: {noise}")
    
    if expected_payoff == 0:
        # For zero payoffs, only add positive noise
        final_payoff = max(0, noise)
        print(f"Zero base payoff - only adding positive noise")
    else:
        final_payoff = expected_payoff + noise
        print(f"Added noise to non-zero payoff")
    
    print(f"Final realized payoff: {final_payoff}")
    return final_payoff

def calculate_payoff(move: dict, opponent_move: dict, payoff_matrix: List[dict], is_noise_added: bool = False) -> float:
    """
    [DEPRECATED] Calculate payoff - kept for backward compatibility.
    
    Use get_expected_payoff() for solver calculations (deterministic).
    Use get_realized_payoff() for actual game scoring (with noise).
    
    Args:
        move: The move to evaluate
        opponent_move: The opponent's move to evaluate against
        payoff_matrix: List of payoff entries
        is_noise_added: Whether to add noise (deprecated - use get_realized_payoff instead)
        
    Returns:
        float: The payoff
    """
    if is_noise_added:
        return get_realized_payoff(move, opponent_move, payoff_matrix)
    else:
        return get_expected_payoff(move, opponent_move, payoff_matrix)

# def get_security_level_response(moves: List[dict], opponent_move: dict, payoff_matrix: List[dict]) -> Optional[dict]:
#     """
#     Get the security-level (min-max) response to an opponent's strategy.
#     """

#     print(f"Getting security-level response for moves: {moves} against opponent move: {opponent_move}")

#     all_payoffs = {}
#     for move in moves:
#         payoff = get_expected_payoff(move, opponent_move, payoff_matrix)
#         print(f"Payoff for {move.get('name', '')}: {payoff}")
#         all_payoffs[move.get('name', '')] = payoff
    
#     print(f"All Payoffs: {all_payoffs}")
    
#     # Find the worst payoff
#     worst_payoff = min(all_payoffs.values())   
#     print(f"Worst Payoff: {worst_payoff}")
#     worst_case_threshold = worst_payoff + 1
#     worst_case_moves = {
#         move: payoff for move, payoff in all_payoffs.items()
#         if payoff <= worst_case_threshold
#    }
    
#     worst_case_move = max(worst_case_moves, key=worst_case_moves.get)
#     print(f"Worst case move: {worst_case_move}")
#     for move in moves:
#         if move['name'] == worst_case_move:
#             print(f"Returning worst case move: {move}")
#             return move

def get_security_level_strategy(my_moves: List[dict], possible_opponent_moves: List[dict], payoff_matrix: List[dict]) -> Optional[dict]:
    """
    Calculates the Maximin strategy (Security Level).
    1. For each of my moves, find the worst possible payoff (Minimum).
    2. Pick the move where that worst payoff is the highest (Maximum).
    """
    print(f"\nCalculating Security Level (Maximin) Strategy...")
    
    if not my_moves or not possible_opponent_moves:
        return None

    maximin_value = -float('inf')
    maximin_move = None

    # Step 1: Loop through all my possible moves
    for my_move in my_moves:
        
        # Find the worst case scenario for THIS move
        worst_payoff_for_this_move = float('inf')
        
        for opp_move in possible_opponent_moves:
            # Use deterministic expected payoff for theoretical calculations
            payoff = get_expected_payoff(my_move, opp_move, payoff_matrix)
            
            if payoff < worst_payoff_for_this_move:
                worst_payoff_for_this_move = payoff
        
        print(f"Worst case for {my_move['name']} is {worst_payoff_for_this_move}")

        # Step 2: Maximize the Minimum
        if worst_payoff_for_this_move > maximin_value:
            maximin_value = worst_payoff_for_this_move
            maximin_move = my_move

    if maximin_move:
        print(f"Security Level Move: {maximin_move['name']} (Guaranteed Payoff: {maximin_value})")
    else:
        print("No security level strategy found")
    return maximin_move

def solve_mixed_strategy_indifference_general(payoffs, player='row', tolerance=0.1):
    """
    Solves for a mixed strategy for one player that makes the other player indifferent between all their pure strategies.

    Arguments:
        payoffs: numpy array of shape (m, n) representing the payoff matrix for the player whose strategies are being solved.
        player: 'row' to solve for the column player's mixed strategy (making the row player indifferent),
                'col' to solve for the row player's mixed strategy (making the column player indifferent).

    Returns:
        A numpy array representing the mixed strategy for the specified player, or np.nan array if no valid solution exists.
    """
    A = payoffs
    m, n = A.shape

    if player == 'row':
        if m < 2:
            raise ValueError("Need at least two strategies for the row player.")
        # Create (m-1) indifference equations: (A[i] - A[0]) · p = 0
        equations = A[1:] - A[0:1]
        lhs_eq = np.vstack([equations, np.ones((1, n))])
        rhs_eq = np.zeros(m)
        rhs_eq[-1] = 1  # The sum constraint
        bounds = [(0, 1)] * n
        c = np.zeros(n)
    elif player == 'col':
        if n < 2:
            raise ValueError("Need at least two strategies for the column player.")
        # Create (n-1) indifference equations: (A[:, i] - A[:, 0]) · p = 0
        equations = A[:, 1:] - A[:, 0:1]
        lhs_eq = np.vstack([equations.T, np.ones((1, m))])
        rhs_eq = np.zeros(n)
        rhs_eq[-1] = 1  # The sum constraint
        bounds = [(0, 1)] * m
        c = np.zeros(m)
    else:
        raise ValueError("Player must be 'row' or 'col'.")

    # Solve using linear programming to enforce p >= 0
    res = linprog(
        c=c,
        A_eq=lhs_eq,
        b_eq=rhs_eq,
        bounds=bounds,
        method='highs'
    )

    if res.success and np.isclose(np.sum(res.x), 1, atol=tolerance):
        return res.x
    else:
        return None

def get_the_next_move_based_on_mixed_strartegy_probability_indifference(
        computer_moves: List[dict],
        user_moves: List[dict],
        payoff_matrix: List[dict],
        state: dict,
        user_support: Optional[np.ndarray] = None,
        num_rounds: int = 200) -> dict:
    """
    Implements a mixed strategy based on probability indifference principle,
    where the strategy makes the opponent indifferent between their pure strategies.

    `state` should carry:
        - state.equalizer_strategy    (current equalizer strategy or None)
        - state.last_strategy_update  (last round index when strategy was updated)
        - state.round_idx            (current round index)
        - state.generated_mixed_moves_array

    Returns:
        np.ndarray: A pure strategy sampled from the current equalizer strategy distribution
    """
    if state['generated_mixed_moves_array'] is None or state['equalizer_strategy'] is None or ( state['round_idx'] - state['last_strategy_update'] > 10):

        computer_payoff_matrix = np.array([[get_expected_payoff(cs, us, payoff_matrix) for us in user_moves] for cs in computer_moves])
        user_payoff_matrix = np.array([[get_expected_payoff(us, cs, payoff_matrix) for cs in computer_moves] for us in user_moves])   


        strategy = refresh_equaliser_if_needed_using_indifference_principles(
            computer_payoff_matrix,
            user_payoff_matrix,
            user_support=None      # or your chosen support rule
        )
        state['equalizer_strategy'] = strategy

        print(f"Strategy: {strategy}")

        if strategy is None:
            return None
        # if strategy is None:
        #     strategy = np.full(len(computer_moves), 1/len(computer_moves))
        i = 0
        for probability in strategy:
            if probability is None:
                continue
            computer_moves[i]['probability'] = probability
            i += 1
            
        state['last_strategy_update'] = state['round_idx']

        mixed_strategies = [move for move in computer_moves if move['probability'] is not None and move['probability'] > 0]

        # Calculate array size from phase boundaries (phase 2 + phase 3)
        # Use num_rounds parameter passed to function
        array_size = num_rounds  # Use full game length for mixed strategy array
        state['generated_mixed_moves_array'] = np.random.choice(mixed_strategies, size=array_size, p=[move['probability'] for move in mixed_strategies])
        if len(state['generated_mixed_moves_array']) == 0 or state['generated_mixed_moves_array'] is None:
            raise ValueError("No mixed strategies found")
    
    shift = state['round_idx'] * 0.2
    indices = np.arange(len(state['generated_mixed_moves_array'])) - shift 
    probabilities = np.exp(-np.maximum(0, indices) * 0.5)  # adjust 0.5 to control decay rate
    probabilities = probabilities / probabilities.sum()

    return np.random.choice(state['generated_mixed_moves_array'], p=probabilities)

    # Fallback handled inside refresh_equaliser_if_needed

def calculate_loss(strategy1: dict, strategy2: dict) -> float:
    """
    Calculate the loss (negative payoff) for strategy1 against strategy2.
    """
    # TODO: Implement loss calculation based on your game's payoff matrix
    return 0.0

def find_best_response_using_epsilon_greedy(moves: List[dict], opponenet_move: dict, epsilon: float = 0.1, payoff_matrix: List[dict] = None) -> Optional[dict]:
    """
    Find the best response using epsilon-greedy approach.
    
    Args:
        moves: moves of player 1
        opponenet_move: move of player 2
        epsilon: Probability of exploration (default: 0.1)
        
    Returns:
        Optional[dict]: The selected strategy or None if no valid strategies
    """
    # Generate random number between 0 and 1
    random_value = np.random.random()
    
    # If random value is less than epsilon, explore (random strategy)
    if random_value < epsilon:
        return get_a_random_move(moves)
    best_responses = []
    highest_payoff = -float('inf')
    for move in moves:
        payoff = get_expected_payoff(move, opponenet_move, payoff_matrix)
        if payoff > highest_payoff:
            highest_payoff = payoff
            best_responses = [move]
        elif payoff == highest_payoff:
            best_responses.append(move)

    if len(best_responses) == 1:
        return best_responses[0]
    else:
        return np.random.choice(best_responses)
    

def get_a_random_move(moves: List[dict]) -> Optional[dict]:
    """
    Get a random move from the available strategies.
    """
    if not moves:
        return None
    return np.random.choice(moves)

def get_copy_cat_move(moves: List[dict], opp_move: dict) -> Optional[dict]:
    """
    Get the copy cat move from the available strategies.
    """
    if opp_move is None:
        return get_a_random_move(moves)
    
    opp_move_name = opp_move['name']
    matching_move = next((move for move in moves if move['name'] == opp_move_name), None)
    if matching_move:
        return matching_move
    else:
        return get_a_random_move(moves)

def get_next_move_based_on_strategy_settings(game: dict, last_computer_move: dict, round_idx: int) -> Optional[dict]:
    """
    Get the next move based on strategy settings.
    """
    if game['user_strategy_settings'] is None:
        raise ValueError("User strategy settings are not set")
    
    user_strategy_settings = game['user_strategy_settings']
    user_moves = game['user_moves']
    if user_moves is None:
        raise ValueError("User moves are not set")
    if len(user_moves) == 0:
        raise ValueError("User moves are empty")
    cooperative_moves = [move for move in user_moves if move['type'] == 'cooperative']
    defective_moves = [move for move in user_moves if move['type'] == 'defective']
    if user_strategy_settings['cooperation_start'] is None:
        user_strategy_settings['cooperation_start'] = 0

    if user_strategy_settings['strategy'] == 'mixed':
        # Check if mixed_strategy_array is None or contains strings (from frontend) instead of dicts
        needs_recreation = False
        if user_strategy_settings['mixed_strategy_array'] is None:
            needs_recreation = True
        elif len(user_strategy_settings['mixed_strategy_array']) > 0:
            # Check if first element is a string (frontend sends strings, backend needs dicts)
            first_element = user_strategy_settings['mixed_strategy_array'][0]
            if isinstance(first_element, str):
                needs_recreation = True
        
        if needs_recreation:
            # Calculate array size from game's num_rounds (stored in game state or use default)
            num_rounds = game.get('num_rounds', 200)
            array_size = num_rounds  # Use full game length for mixed strategy array
            user_strategy_settings['mixed_strategy_array'] = np.random.choice(user_moves, size=array_size, p=[move['probability'] for move in user_moves])

    if round_idx == 0:
        first_move_name = user_strategy_settings['first_move']
        if first_move_name is not None:
            matching_move = next((move for move in user_moves if move['name'] == first_move_name), None)
            if matching_move:
                for move in user_moves:
                    if move['name'] == first_move_name:
                        return move
            else:
                return None
        return None
          
    else:
        if user_strategy_settings['strategy'] == 'copy_cat':
            return get_copy_cat_move(user_moves, last_computer_move)
        elif user_strategy_settings['strategy'] == 'tit_for_tat':
            if round_idx < user_strategy_settings['cooperation_start']:
                return get_a_random_move(cooperative_moves)
            else:
                return get_copy_cat_move(user_moves, last_computer_move)
        elif user_strategy_settings['strategy'] == 'grim_trigger':
            # Before the cooperation start round, just play cooperative
            if round_idx < user_strategy_settings['cooperation_start']:
                return get_a_random_move(cooperative_moves)

            # If we were ever betrayed in the past, punish forever
            if game['state'].get('grim_triggered', False):
                return get_a_random_move(defective_moves)

            # No previous move -> start cooperatively
            if last_computer_move is None:
                return get_a_random_move(cooperative_moves)

            # If opponent defected now, set trigger and punish
            if not is_cooperative(last_computer_move):
                game['state']['grim_triggered'] = True
                return get_a_random_move(defective_moves)

            # Otherwise continue cooperating
            return get_a_random_move(cooperative_moves)
        elif user_strategy_settings['strategy'] == 'random':
            return get_a_random_move(user_moves)
        elif user_strategy_settings['strategy'] == 'mixed':
            shift = round_idx * 0.2
            indices = np.arange(len(user_strategy_settings['mixed_strategy_array'])) - shift
            probabilities = np.exp(-np.maximum(0, indices) * 0.5) 
            probabilities = probabilities / probabilities.sum()
            next_mixed_move = np.random.choice(
                user_strategy_settings['mixed_strategy_array'],
                p=probabilities
            )
            print(f"Next mixed move: {next_mixed_move}")
            
            # Handle numpy scalar wrapper if present
            if hasattr(next_mixed_move, 'item'):
                next_mixed_move = next_mixed_move.item()
            
            # mixed_strategy_array should now always contain dicts (converted from strings if needed)
            # But add safety check just in case
            if isinstance(next_mixed_move, dict):
                for mixed_move in user_moves:
                    # mixed_strategy_array contains move dicts, so compare by name
                    if mixed_move['name'] == next_mixed_move.get('name'):
                        print(f"Returning mixed move: {mixed_move}")
                        return mixed_move
            else:
                # This shouldn't happen after the fix, but handle it defensively
                raise ValueError(f"Expected dict from mixed_strategy_array, got {type(next_mixed_move)}: {next_mixed_move}")
        else:
            raise ValueError(f"Unknown strategy or strategy is not set: {user_strategy_settings['strategy']}")

def is_cooperative(move: dict) -> bool:
    """
    Check if the move is cooperative.
    """
    print(f"Checking if move {move['name']} is cooperative")
    print(f"Move type: {move['type']}")
    return move['type'] == 'cooperative'

def find_nash_equilibrium_strategy(moves: List[dict], opponent_moves: List[dict], payoff_matrix: List[dict]) -> dict:
    """
    Find the Nash equilibrium strategy for the computer.
    
    Args:
        moves: List of computer's available moves
        opponent_movess: List of user's available moves
        
    Returns:
        List[Tuple[np.ndarray, np.ndarray]]: List of Nash equilibrium moves
    """
    # Convert strategies to payoff matrices
    # Row player (computer) payoffs: computer move vs user move
    row_player_payoffs = np.array([[get_expected_payoff(s, os, payoff_matrix) for os in opponent_moves] for s in moves])
    # Column player (user) payoffs: user move vs computer move (flipped indexing)
    col_player_payoffs = np.array([[get_expected_payoff(os, s, payoff_matrix) for s in moves] for os in opponent_moves])
    
    game = nash.Game(row_player_payoffs, col_player_payoffs)
    nash_equilibria = {}
    nash_equilibria['nash_equilibria_strategies'] = []
    for eq in game.support_enumeration():
        print(f"Eq: {eq}")
        row_strategy, col_strategy = eq
        print(f"Row Strategy: {row_strategy}, Column Strategy: {col_strategy}")
        print(moves)
        for i, nash_eq_prob in enumerate(row_strategy):
            if nash_eq_prob > 0:
                nash_equilibria['nash_equilibria_strategies'].append({
                    'nash_eq_strategy': {
                        'name': moves[i]['name'],
                        'nash_eq_probability': float(nash_eq_prob),
                    }
                })

    print(nash_equilibria)

    if len(nash_equilibria['nash_equilibria_strategies']) == 0:
        return None
    
    return nash_equilibria

def get_a_random_move_from_nash_equilibrium_strategy(nash_equilibria: dict, moves: List[dict]) -> dict:

    if not nash_equilibria:
        return None

    if len(nash_equilibria['nash_equilibria_strategies']) == 0:
        return None
    
    move = np.random.choice(nash_equilibria['nash_equilibria_strategies'])

    for m in moves:
        if m['name'] == move['nash_eq_strategy']['name']:
            m['nash_eq_probability'] = move['nash_eq_strategy']['nash_eq_probability']
            m['probability'] = move['nash_eq_strategy']['nash_eq_probability']
            return m

def refresh_equaliser_if_needed_using_indifference_principles(computer_payoff_matrix: np.ndarray, user_payoff_matrix: np.ndarray, 
                              user_support: Optional[np.ndarray] = None) -> Tuple[np.ndarray, int]:
    """
    Refresh the equalizer strategy if needed based on current round and state.
    The equalizer strategy is a mixed strategy that makes the opponent indifferent between their pure strategies.

    Args:
      
        computer_payoff_matrix: Payoff matrix for computer player
        user_payoff_matrix: Payoff matrix for user player
        user_support: Optional support set for user's strategies

    Returns:
        Tuple[np.ndarray, int]: 
            - Updated equalizer strategy distribution (mixed strategy that makes opponent indifferent)
    """
    q_eq = solve_mixed_strategy_indifference_general(computer_payoff_matrix, player='col')
    if q_eq is None:
        return None
    return q_eq

def calculate_epsilon(computer_profile: dict, round_idx: int) -> float:
    """
    Calculate epsilon value based on the computer profile's epsilon schedule.
    
    Args:
        computer_profile: Computer profile dictionary
        round_idx: Current round index
        
    Returns:
        Epsilon value for the current round
    """
    epsilon_config = computer_profile['epsilon_schedule']
    schedule_type = epsilon_config['type']
    
    if schedule_type == 'constant':
        return epsilon_config['value']
    
    elif schedule_type == 'linear':
        start = epsilon_config['start']
        end = epsilon_config['end']
        end_round = epsilon_config['end_round']
        
        if round_idx >= end_round:
            return end
        else:
            # Linear interpolation
            progress = round_idx / end_round
            return start + (end - start) * progress
    
    elif schedule_type == 'decay':
        base = epsilon_config['base']
        floor = epsilon_config['floor']
        tau = epsilon_config['tau']
        
        # Exponential decay: epsilon = floor + (base - floor) * exp(-round_idx / tau)
        import math
        return floor + (base - floor) * math.exp(-round_idx / tau)
    
    elif schedule_type == 'piecewise':
        values = epsilon_config['values']
        switch_round = epsilon_config['switch_round']
        
        if round_idx < switch_round:
            return values['early']
        else:
            return values['late']
    
    elif schedule_type == 'linear_decay':
        start = epsilon_config['start']
        end = epsilon_config['end']
        end_round = epsilon_config['end_round']
        
        if round_idx >= end_round:
            return end
        else:
            # Linear decay (opposite of linear growth)
            progress = round_idx / end_round
            return start - (start - end) * progress
    
    else:
        # Fallback to constant value
        return 0.1


def play_game_round(game: dict, round_idx: int) -> Tuple[dict, dict]:
    """
    Play a single round of the game.
    Returns the user move and computer move for the round.
    """
    computer_profile = game['computer_profile']
    if computer_profile is None:
        raise ValueError("Computer profile is not set")
    
    if round_idx == 0:
        game['state']['last_computer_move'] = None
        game['state']['round_idx'] = 0
        game['state']['last_strategy_update'] = 0
        game['state']['generated_mixed_moves_array'] = None
        game['state']['equalizer_strategy'] = None
        # Reset grim trigger state at the start of a new game
        game['state']['grim_triggered'] = False

        
    user_move = get_next_move_based_on_strategy_settings(game, game['state']['last_computer_move'], round_idx)
    if user_move is None:
        print(f"User move is None, getting a random move")
        user_move = get_a_random_move(game['user_moves'])


    if computer_profile['phases']['p1'][0] <= round_idx <= computer_profile['phases']['p1'][1]:  # Phase 1: Nash Equilibrium
        computer_dominant = check_dominant_move(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
        # Play dominant move randomly (50% chance) instead of always
        if computer_dominant and random.random() < computer_profile['dominant_probabilities']['p1']:
            computer_move = computer_dominant
        else:
            computer_move = get_a_random_move_from_nash_equilibrium_strategy(
                find_nash_equilibrium_strategy(
                    game['computer_moves'], game['user_moves'], game['payoff_matrix']),
                game['computer_moves'])
            if computer_move is None:
                epsilon = calculate_epsilon(computer_profile, round_idx)
                computer_move = find_best_response_using_epsilon_greedy(game['computer_moves'], user_move, epsilon, game['payoff_matrix'])
            if computer_move is None:
                computer_move = get_a_random_move(game['computer_moves'])

    elif computer_profile['phases']['p2'][0] <= round_idx <= computer_profile['phases']['p2'][1]:  # Phase 2: Greedy Best Response
        computer_dominant = check_dominant_move(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
        # Play dominant move randomly (40% chance) instead of always
        if computer_dominant and random.random() < computer_profile['dominant_probabilities']['p2']:
            computer_move = computer_dominant
        else:
            epsilon = calculate_epsilon(computer_profile, round_idx)
            computer_move = find_best_response_using_epsilon_greedy(game['computer_moves'], user_move, epsilon, game['payoff_matrix'])
            if computer_move is None:
                computer_move = get_a_random_move(game['computer_moves'])

    elif computer_profile['phases']['p3'][0] <= round_idx <= computer_profile['phases']['p3'][1]:  # Phase 3: Mixed Strategy
        computer_dominant = check_dominant_move(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
        # Play dominant move randomly (30% chance) instead of always
        if computer_dominant and random.random() < computer_profile['dominant_probabilities']['p3']:
            computer_move = computer_dominant
        else:
            computer_move = get_the_next_move_based_on_mixed_strartegy_probability_indifference(
                    game['computer_moves'],
                    game['user_moves'],
                    game['payoff_matrix'],
                    game['state'],
                    user_support=None,        # plug in your support rule
                    num_rounds=game.get('num_rounds', 200)
                )
            if computer_move is None:
                computer_move = get_a_random_move(game['computer_moves'])

    game['state']['last_computer_move'] = computer_move
    game['state']['round_idx'] = round_idx

    # Respond to user's dominant move with mixed strategy:
    # - 60% of the time: play best response
    # - 20% of the time: play security level strategy (safe/defensive)
    # - 20% of the time: play normal (keep original move)
    user_dominant = check_dominant_move(game['user_moves'], game['computer_moves'], game['payoff_matrix'])
    if user_dominant and user_move == user_dominant:
        rand = random.random()
        if rand < 0.6:  # 60% - play best response
            best_response = find_best_response_using_epsilon_greedy(game['computer_moves'], user_move, epsilon=0.0, payoff_matrix=game['payoff_matrix'])
            computer_move = best_response if best_response else computer_move
            game['state']['last_computer_move'] = computer_move
        elif rand < 0.8:  # 20% - play security level strategy (0.6 to 0.8 = 20%)
            security_level_response = get_security_level_strategy(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
            computer_move = security_level_response if security_level_response else computer_move
            game['state']['last_computer_move'] = computer_move
        # else: 20% - play normal (keep original computer_move, already set above)

    return user_move, computer_move

def play_full_game(game: dict, socketio=None, game_id=None, round_delay: float = 0.5) -> dict:
    """
    Play a complete game and return the moves history and dominant strategies.
    
    Args:
        game: Game configuration dictionary
        socketio: Optional Flask-SocketIO instance for real-time updates
        game_id: Optional game ID for WebSocket room targeting
        round_delay: Delay in seconds between rounds (default: 0.5s)
    """

    computer_profile = game['computer_profile']
    if computer_profile is None:
        raise ValueError("Computer profile is not set")
    
    # Get num_rounds from profile, default to 200 for backward compatibility
    num_rounds = computer_profile.get('num_rounds', 200)
    
    iteration_moves = GameMoves()
    final_user_payoff = 0
    final_computer_payoff = 0
    
    # Initialize game logger
    logger = get_game_logger()
    session_id = logger.start_game_session(game_id or "unknown_game", game)
    
    # Store num_rounds in game state for use in other functions
    game['num_rounds'] = num_rounds
    
    for i in range(num_rounds):
        user_move, computer_move = play_game_round(game, i)
        if user_move is None:
            continue
        if computer_move is None:
            continue
        
        # Add moves to history
        iteration_moves.add_moves(user_move, computer_move)
        
        # Calculate payoffs immediately (with noise for actual scoring)
        user_payoff = get_realized_payoff(user_move, computer_move, game['payoff_matrix'])
        computer_payoff = get_realized_payoff(computer_move, user_move, game['payoff_matrix'])
        
        # Debug: Check if payoffs are the expected type
        print(f"Debug: user_payoff type: {type(user_payoff)}, value: {user_payoff}")
        print(f"Debug: computer_payoff type: {type(computer_payoff)}, value: {computer_payoff}")
        
        # Ensure payoffs are floats
        if isinstance(user_payoff, list):
            user_payoff = float(user_payoff[0]) if user_payoff else 0.0
        if isinstance(computer_payoff, list):
            computer_payoff = float(computer_payoff[0]) if computer_payoff else 0.0
        final_user_payoff += user_payoff
        final_computer_payoff += computer_payoff

        print(f"User payoff: {final_user_payoff}, Computer payoff: {final_computer_payoff}")
        
        # Determine round winner and phase
        round_winner = "tie"
        if user_payoff > computer_payoff:
            round_winner = "user"
        elif computer_payoff > user_payoff:
            round_winner = "computer"
        
        # Determine current phase
        if computer_profile['phases']['p1'][0] <= i <= computer_profile['phases']['p1'][1]:
            phase = "Phase 1 (Nash Equilibrium)"
        elif computer_profile['phases']['p2'][0] <= i <= computer_profile['phases']['p2'][1]:
            phase = "Phase 2 (Greedy Response)"
        elif computer_profile['phases']['p3'][0] <= i <= computer_profile['phases']['p3'][1]:
            phase = "Phase 3 (Mixed Strategy)"
        else:
            phase = "Unknown Phase"
        
        # Log the move
        # Convert numpy types to Python types for JSON serialization
        user_payoff_python = float(user_payoff) if hasattr(user_payoff, 'item') else user_payoff
        computer_payoff_python = float(computer_payoff) if hasattr(computer_payoff, 'item') else computer_payoff
        final_user_payoff_python = float(final_user_payoff) if hasattr(final_user_payoff, 'item') else final_user_payoff
        final_computer_payoff_python = float(final_computer_payoff) if hasattr(final_computer_payoff, 'item') else final_computer_payoff
        
        logger.log_move(
            round_number=i + 1,
            phase=phase,
            user_move=user_move,
            computer_move=computer_move,
            user_payoff=user_payoff_python,
            computer_payoff=computer_payoff_python,
            round_winner=round_winner,
            running_user_total=final_user_payoff_python,
            running_computer_total=final_computer_payoff_python,
            game_context={
                "game_id": game_id,
                "strategy_settings": game.get('user_strategy_settings', {}),
                "last_computer_move": game['state'].get('last_computer_move', {}).get('name', 'None')
            }
        )
        
        # Emit real-time update via WebSocket if available
        if socketio and game_id:
            print(f"User won the round" if round_winner == "user" else f"Computer won the round" if round_winner == "computer" else "Round was a tie")
            print(f"Round winner: {round_winner}")
            update_data = {
                "type": "round_update",
                "round": i + 1,
                "user_move": {
                    "name": user_move['name'],
                    "type": user_move['type']
                },
                "computer_move": {
                    "name": computer_move['name'],
                    "type": computer_move['type']
                },
                "user_payoff": round(user_payoff, 2),
                "computer_payoff": round(computer_payoff, 2),
                "round_winner": round_winner,
                "running_totals": {
                    "user_total": round(final_user_payoff, 2),
                    "computer_total": round(final_computer_payoff, 2)
                },
                "game_status": "in_progress" if i < num_rounds - 1 else "completed"
            }
            
            socketio.emit('game_update', update_data, room=game_id)
            
            # Add delay between rounds for better real-time experience
            if round_delay > 0:
                time.sleep(round_delay)

    # End the game session and save logs
    # Convert numpy types to Python types for JSON serialization
    final_user_payoff_python = float(final_user_payoff) if hasattr(final_user_payoff, 'item') else final_user_payoff
    final_computer_payoff_python = float(final_computer_payoff) if hasattr(final_computer_payoff, 'item') else final_computer_payoff
    logger.end_game_session(final_user_payoff_python, final_computer_payoff_python)

    return {
        'final_user_payoff': final_user_payoff,
        'final_computer_payoff': final_computer_payoff
    },iteration_moves 