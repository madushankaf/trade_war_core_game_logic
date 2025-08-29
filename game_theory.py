from typing import Dict, List, Optional, Tuple
import numpy as np
from game_moves import GameMoves
import nashpy as nash
from scipy.optimize import linprog

# Phase boundaries
PHASE_1_START = 0
PHASE_1_END = 15
PHASE_2_START = 16
PHASE_2_END = 100
PHASE_3_START = 101
PHASE_3_END = 200

def check_dominant_move(moves: List[dict], opponent_move: dict, payoff_matrix: List[dict]) -> Optional[dict]:
    """
    Check if there's a dominant move among the given moves against a specific opponent move.
    Returns the dominant move if found, None otherwise.
    
    Args:
        moves: List of possible moves to check
        opponent_move: The opponent's move to evaluate against
        payoff_matrix: List of payoff entries
        
    Returns:
        Optional[dict]: The dominant move if found, None otherwise
    """
    print(f"\nChecking for dominant move against opponent move: {opponent_move['name']}")
    
    if not moves:
        print("No moves to check")
        return None
    
    if len(moves) == 1:
        return moves[0]
    
    #guard rail for unknown opponent move
    payoff_entry = next(
        (entry for entry in payoff_matrix 
         if entry['computer_move_name'] == opponent_move['name'] 
         ),
        None
    )

    if payoff_entry is None:
        return None
    
    
    # For each move, check if it's dominant
    for move in moves:
        print(f"\nChecking if {move['name']} is dominant")
        is_dominant = True
        
        for other_move in moves:
            if move == other_move:
                continue
                
            print(f"Comparing {move['name']} vs {other_move['name']}")
            is_better = is_the_move_with_the_better_payoff(move, other_move, opponent_move, payoff_matrix)
            if is_better is None:
                break
            if not is_better:
                print(f"{move['name']} is not better than {other_move['name']}")
                is_dominant = False
                break
        
        if is_dominant:
            print(f"Found dominant move: {move['name']}")
            return move
    
    print("No dominant move found")
    return None

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
    # Get payoffs for each move against the opponent
    payoff1 = calculate_payoff(move1, opponent_move, payoff_matrix)
    payoff2 = calculate_payoff(move2, opponent_move, payoff_matrix)
    
    print(f"Payoff comparison: {move1['name']}({payoff1}) vs {move2['name']}({payoff2})")
    
    # Move1 is better if it has a higher payoff
    return payoff1 > payoff2

def calculate_payoff(move: dict, opponent_move: dict, payoff_matrix: List[dict], is_noise_added: bool = False) -> float:
    """
    Calculate the expected payoff for a move against a specific opponent move.
    
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
        float: The expected payoff (never negative)
    """
    print(f"\nCalculating payoff for move: {move['name']} (type: {move['type']}, probability: {move['probability']})")
    print(f"Against opponent move: {opponent_move['name']} (type: {opponent_move['type']}, probability: {opponent_move['probability']})")
    
    # Extract move parameters
    move_name = move.get('name', '')
    move_prob = move.get('probability', 1.0)
    opp_name = opponent_move.get('name', '')
    opp_prob = opponent_move.get('probability', 1.0)
    player = move.get('player', None)
    if player is None:
        raise ValueError(f"Move {move['name']} has no player")
    
    # if player == 'user':
    #     payoff_entry = next((e for e in payoff_matrix
    #                          if e['user_move_name'] == move_name and e['computer_move_name'] == opp_name), None)
    # elif player == 'computer':
    #     payoff_entry = next((e for e in payoff_matrix
    #                          if e['user_move_name'] == opp_name and e['computer_move_name'] == move_name), None)
    # else:
    #     raise ValueError("player must be 'user' or 'computer'")

    # if not payoff_entry:
    #     return 0.0
    
    # Find matching payoff in the matrix
    payoff_entry = next(
        (entry for entry in payoff_matrix 
         if entry['user_move_name'] == move_name 
         and entry['computer_move_name'] == opp_name),
        None
    )
    
    if payoff_entry:
        # Get base payoff and adjust for probabilities
        base_payoff = payoff_entry['payoff'][player]  # For user's perspective
        move_payoff = base_payoff * move_prob * opp_prob
        
        print(f"Found payoff entry: {payoff_entry}")
        print(f"Base payoff: {base_payoff}")
        print(f"Adjusted payoff (with probabilities): {move_payoff}")
    else:
        print(f"No payoff entry found for move combination: {move_name} vs {opp_name}")
        move_payoff = 0.0
        
    noise = 0.0
    #Always add noise, but ensure final payoff is never negative
    if is_noise_added:
        noise = np.random.normal(0, 0.1)  # Small random noise
    print(f"\nTotal payoff before noise: {move_payoff}")
    print(f"Generated noise: {noise}")
    
    if move_payoff == 0:
        # For zero payoffs, only add positive noise
        final_payoff = max(0, noise)
        print(f"Zero base payoff - only adding positive noise")
    else:
        # For non-zero payoffs, add noise but ensure result is not negative
        final_payoff = max(0, move_payoff + noise)
        print(f"Added noise to non-zero payoff")
    
    print(f"Final payoff: {final_payoff}")
    return final_payoff

def get_security_level_response(moves: List[dict], opponent_move: dict, payoff_matrix: List[dict]) -> Optional[dict]:
    """
    Get the security-level (min-max) response to an opponent's strategy.
    """


    all_payoffs = {}
    for move in moves:
        payoff = calculate_payoff(move, opponent_move, payoff_matrix)
        print(f"Payoff for {move.get('name', '')}: {payoff}")
        all_payoffs[move.get('name', '')] = payoff
    
    print(f"All Payoffs: {all_payoffs}")
    
    # Find the worst payoff
    worst_payoff = min(all_payoffs.values())   
    print(f"Worst Payoff: {worst_payoff}")
    worst_case_threshold = worst_payoff + 1
    worst_case_moves = {
        move: payoff for move, payoff in all_payoffs.items()
        if payoff <= worst_case_threshold
   }
    
    worst_case_move = max(worst_case_moves, key=worst_case_moves.get)
    for move in moves:
        if move['name'] == worst_case_move:
            return move

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
        state: dict) -> dict:
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

        computer_payoff_matrix = np.array([[calculate_payoff(cs, us, payoff_matrix) for us in user_moves] for cs in computer_moves])
        user_payoff_matrix = np.array([[calculate_payoff(us, cs, payoff_matrix) for cs in computer_moves] for us in user_moves])   

        print(f"Computer Payoff Matrix: {computer_payoff_matrix}")
        print(f"User Payoff Matrix: {user_payoff_matrix}")

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

        state['generated_mixed_moves_array'] = np.random.choice(mixed_strategies, size= (PHASE_3_END - PHASE_2_START), p=[move['probability'] for move in mixed_strategies])
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
        payoff = calculate_payoff(move, opponenet_move, payoff_matrix)
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

def get_copy_cat_move(moves: List[dict], last_computer_move: dict) -> Optional[dict]:
    """
    Get the copy cat move from the available strategies.
    """
    if last_computer_move is None:
        return get_a_random_move(moves)
    
    last_computer_move_name = last_computer_move['name']
    matching_move = next((move for move in moves if move['name'] == last_computer_move_name), None)
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
        if user_strategy_settings['mixed_strategy_array'] is None:            
            user_strategy_settings['mixed_strategy_array'] = np.random.choice(user_moves, size = (PHASE_3_END - PHASE_1_START), p=[move['probability'] for move in user_moves])

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
            if round_idx < user_strategy_settings['cooperation_start']:
                return get_a_random_move(cooperative_moves)
            if last_computer_move is None:
                return get_a_random_move(cooperative_moves)
            if is_cooperative(last_computer_move):
                return get_a_random_move(defective_moves)
            else:
                return get_a_random_move(cooperative_moves)
        elif user_strategy_settings['strategy'] == 'random':
            return get_a_random_move(user_moves)
        elif user_strategy_settings['strategy'] == 'mixed':
            shift = round_idx * 0.2
            indices = np.arange(len(user_strategy_settings['mixed_strategy_array'])) - shift
            probabilities = np.exp(-np.maximum(0, indices) * 0.5) 
            probabilities = probabilities / probabilities.sum()
            return np.random.choice(user_strategy_settings['mixed_strategy_array'], p=probabilities)
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
    row_player_payoffs = np.array([[calculate_payoff(s, os, payoff_matrix) for os in opponent_moves] for s in moves])
    col_player_payoffs = np.array([[calculate_payoff(os, s, payoff_matrix) for s in moves] for os in opponent_moves])
    
    game = nash.Game(row_player_payoffs, col_player_payoffs)
    nash_equilibria = {}
    nash_equilibria['nash_equilibria_strategies'] = []
    for eq in game.support_enumeration():
        print(f"Eq: {eq}")
        row_strategy, col_strategy = eq
        print(f"Row Strategy: {row_strategy}, Column Strategy: {col_strategy}")
        #strategies.append((row_strategy, col_strategy))
        print(moves)
        for nash_eq_prob in row_strategy:
            i = 0
            if  nash_eq_prob > 0:
                nash_equilibria['nash_equilibria_strategies'].append({
                            'computer_strategy': {
                                'name':moves[i].get('name'),
                                'nash_eq_probability':nash_eq_prob
                            }
                        })
            i += 1

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
        if m['name'] == move['computer_strategy']['name']:
            m['nash_eq_probability'] = move['computer_strategy']['nash_eq_probability']
            m['probability'] = move['computer_strategy']['nash_eq_probability']
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

def play_game_round(game: dict, round_idx: int) -> Tuple[dict, dict]:
    """
    Play a single round of the game.
    Returns the user move and computer move for the round.
    """
    if round_idx == 0:
        game['state']['last_computer_move'] = None
        game['state']['round_idx'] = 0
        game['state']['last_strategy_update'] = 0
        game['state']['generated_mixed_moves_array'] = None
        game['state']['equalizer_strategy'] = None

        
    user_move = get_next_move_based_on_strategy_settings(game, game['state']['last_computer_move'], round_idx)
    if user_move is None:
        user_move = get_a_random_move(game['user_moves'])

    # Check if current user_move is a dominant strategy
    #computer_dominant = check_dominant_strategy(game['computer_moves'], game['user_moves'], user_move)
    user_dominant = check_dominant_move(game['user_moves'], user_move, game['payoff_matrix'])

    
    if user_dominant and user_move == user_dominant:
        computer_move = get_security_level_response(game['computer_moves'], user_move, game['payoff_matrix'])
        if computer_move is None:
            computer_move = get_a_random_move(game['computer_moves'])
        game['state']['last_computer_move'] = computer_move
        game['state']['round_idx'] = round_idx
        return user_move, computer_move

    if PHASE_1_START <= round_idx <= PHASE_1_END:  # Phase 1: Nash Equilibrium
        computer_dominant = check_dominant_move(game['computer_moves'], user_move, game['payoff_matrix'])
        computer_move = computer_dominant if computer_dominant else get_a_random_move_from_nash_equilibrium_strategy(
            find_nash_equilibrium_strategy(
                game['computer_moves'], game['user_moves'], game['payoff_matrix']),
            game['computer_moves'])
        if computer_move is None:
            computer_move = find_best_response_using_epsilon_greedy(game['computer_moves'], user_move, game['payoff_matrix'])
        if computer_move is None:
            computer_move = get_a_random_move(game['computer_moves'])

    elif PHASE_2_START <= round_idx <= PHASE_2_END:  # Phase 2: Greedy Response
        computer_dominant = check_dominant_move(game['computer_moves'], user_move, game['payoff_matrix'])
        computer_move = computer_dominant if computer_dominant else find_best_response_using_epsilon_greedy(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
        if computer_move is None:
            computer_move = get_a_random_move(game['computer_moves'])

    else:  # Phase 3: Mixed Strategy
        computer_dominant = check_dominant_move(game['computer_moves'], user_move, game['payoff_matrix'])
        computer_move = computer_dominant if computer_dominant else get_the_next_move_based_on_mixed_strartegy_probability_indifference(
                game['computer_moves'],
                game['user_moves'],
                game['payoff_matrix'],
                game['state'],
                user_support=None        # plug in your support rule
            )
        if computer_move is None:
            computer_move = get_a_random_move(game['computer_moves'])

    game['state']['last_computer_move'] = computer_move
    game['state']['round_idx'] = round_idx
    return user_move, computer_move

def play_full_game(game: dict) -> dict:
    """
    Play a complete game and return the moves history and dominant strategies.
    """
    iteration_moves = GameMoves()
    
    for i in range(PHASE_3_END):
        user_move, computer_move = play_game_round(game, i)
        if user_move is None:
            continue
        if computer_move is None:
            continue
        iteration_moves.add_moves(user_move, computer_move)
    
    final_user_payoff = 0
    final_computer_payoff = 0
    for user_move, computer_move in iteration_moves.get_moves():
        user_payoff = calculate_payoff(user_move, computer_move, game['payoff_matrix'], is_noise_added=True)
        computer_payoff = calculate_payoff(computer_move, user_move, game['payoff_matrix'], is_noise_added=True)
        final_user_payoff += user_payoff
        final_computer_payoff += computer_payoff

    return {
        'final_user_payoff': final_user_payoff,
        'final_computer_payoff': final_computer_payoff
    },iteration_moves 