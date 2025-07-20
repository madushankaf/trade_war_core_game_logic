import pytest
import numpy as np
from game_theory import check_dominant_move, is_the_move_with_the_better_payoff, calculate_payoff, find_best_response_using_epsilon_greedy, find_nash_equilibrium_strategy, solve_mixed_strategy_indifference_general, get_the_next_move_based_on_mixed_strartegy_probability_indifference, get_security_level_response, get_copy_cat_move, get_next_move_based_on_strategy_settings, play_game_round, play_full_game

# Test moves for pure strategies
@pytest.fixture
def test_moves_pure():
    return [
        {
            "type": "cooperative",
            "probability": 1.0,
            "name": "open_dialogue",
            'player': 'user'
            
        },
        {
            "type": "defective",
            "probability": 1.0,
            "name": "raise_tariffs",
            'player': 'user'

        },
        {
            "type": "cooperative",
            "probability": 1.0,
            "name": "wait_and_see",
            'player': 'user'
        },
        {
            "type": "defective",
            "probability": 1.0,
            "name": "sanction",
            'player': 'user'

        }
    ]

@pytest.fixture
def test_payoff_matrix_pure():
    return [
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 3, "computer": 3}
        },
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "sanction",
            "payoff": {"user": 0, "computer": 5}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 5, "computer": 0}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "sanction",
            "payoff": {"user": 1, "computer": 1}
        }
    ]

# Test moves for mixed strategies
@pytest.fixture
def test_moves_mixed():
    return [
        {
            "type": "mixed",
            "probability": 0.6,
            "name": "open_dialogue",
            'player': 'user'
        },
        {
            "type": "mixed",
            "probability": 0.4,
            "name": "wait_and_see",
            'player': 'user'
        },
        {
            "type": "mixed",
            "probability": 0.8,
            "name": "raise_tariffs",
            'player': 'user'
        },
        {
            "type": "mixed",
            "probability": 0.2,
            "name": "sanction",
            'player': 'user'
        },
        {
            "type": "mixed",
            "probability": 0.5,
            "name": "impose_quota",
            'player': 'user'
        },
        {
            "type": "mixed",
            "probability": 0.7,
            "name": "subsidize_export",
            'player': 'user'
        }
    ]

@pytest.fixture
def test_payoff_matrix_mixed():
    return [
        # open_dialogue combinations
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "open_dialogue",
            "payoff": {"user": 4, "computer": 4}
        },
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "raise_tariffs",
            "payoff": {"user": 0, "computer": 5}
        },
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 3, "computer": 3}
        },
        # raise_tariffs combinations
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "open_dialogue",
            "payoff": {"user": 5, "computer": 0}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "raise_tariffs",
            "payoff": {"user": 1, "computer": 1}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 5, "computer": 0}
        },
        # wait_and_see combinations
        {
            "user_move_name": "wait_and_see",
            "computer_move_name": "open_dialogue",
            "payoff": {"user": 3, "computer": 3}
        },
        {
            "user_move_name": "wait_and_see",
            "computer_move_name": "raise_tariffs",
            "payoff": {"user": 0, "computer": 5}
        },
        {
            "user_move_name": "wait_and_see",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 2, "computer": 2}
        }
    ]

def test_check_dominant_move_pure(test_moves_pure, test_payoff_matrix_pure):
    """Test dominant move detection with pure strategies"""
    # Test with a move that should be dominant
    opponent_move = {"name": "wait_and_see", "type": "cooperative", "probability": 1.0, 'player': 'user'}
    dominant = check_dominant_move(test_moves_pure, opponent_move, test_payoff_matrix_pure)
    assert dominant is not None
    assert dominant["name"] == "raise_tariffs"  # Raise tariffs should be dominant against wait_and_see

    # Test with sanction - raise_tariffs should be dominant
    opponent_move = {"name": "sanction", "type": "defective", "probability": 1.0, 'player': 'user'}
    dominant = check_dominant_move(test_moves_pure, opponent_move, test_payoff_matrix_pure)
    assert dominant is not None
    assert dominant["name"] == "raise_tariffs"  # Raise tariffs should be dominant against sanction

    # Test wish no dominant move (using a move not in payoff matrix)
    opponent_move = {"name": "unknown_move", "type": "cooperative", "probability": 1.0, 'player': 'user'}
    dominant = check_dominant_move(test_moves_pure, opponent_move, test_payoff_matrix_pure)
    assert dominant is None  # No dominant move against unknown move

def test_is_the_move_with_the_better_payoff_pure( test_payoff_matrix_pure):
    """Test payoff comparison between pure strategies"""
    move1 = {"name": "raise_tariffs", "type": "defective", "probability": 1.0, 'player': 'computer'}
    move2 = {"name": "open_dialogue", "type": "cooperative", "probability": 1.0, 'player': 'computer'}
    opponent_move = {"name": "wait_and_see", "type": "cooperative", "probability": 1.0, 'player': 'user'}
    
    # Raise tariffs should be better than open dialogue against wait_and_see
    assert not is_the_move_with_the_better_payoff(move1, move2, opponent_move, test_payoff_matrix_pure)
    
    # Open dialogue should not be better than raise tariffs against wait_and_see
    assert  is_the_move_with_the_better_payoff(move2, move1, opponent_move, test_payoff_matrix_pure)

def test_calculate_payoff_pure(test_payoff_matrix_pure):
    """Test payoff calculation with pure strategies"""
    # Test mutual cooperation (open dialogue vs wait_and_see)
    move = {"name": "open_dialogue", "type": "cooperative", "probability": 1.0, 'player': 'computer'}
    opponent_move = {"name": "wait_and_see", "type": "cooperative", "probability": 1.0, 'player': 'user'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_pure)
    print(payoff)
    assert payoff >= 0  # Should be positive for mutual cooperation
    
    # Test defection against cooperation (raise tariffs vs wait_and_see)
    move = {"name": "raise_tariffs", "type": "defective", "probability": 1.0, 'player': 'computer'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_pure)
    print(payoff)
    assert payoff >= 0  # Should be positive for defection against cooperation
    
    # Test cooperation against defection (open dialogue vs sanction)
    opponent_move = {"name": "sanction", "type": "defective", "probability": 1.0, 'player': 'user'}
    move = {"name": "open_dialogue", "type": "cooperative", "probability": 1.0, 'player': 'computer'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_pure)
    print(payoff)
    assert payoff > 0  # Should be non-negative 


def test_calculate_payoff_mixed(test_payoff_matrix_mixed):
    """Test payoff calculation with mixed strategies"""
    # Test mutual cooperation (open dialogue vs wait_and_see)
    move = {"name": "open_dialogue", "type": "cooperative", "probability": 0.5, 'player': 'computer'}
    opponent_move = {"name": "wait_and_see", "type": "cooperative", "probability": 0.3, 'player': 'user'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_mixed)
    print(payoff)
    assert payoff >= 0  # Should be positive for mutual cooperation
    
    # Test defection against cooperation (raise tariffs vs wait_and_see)
    move = {"name": "raise_tariffs", "type": "defective", "probability": 0.5, 'player': 'computer'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_mixed)
    print(payoff)
    assert  payoff >= 0  # Should be positive for defection against cooperation
    
    # Test cooperation against defection (open dialogue vs sanction)
    opponent_move = {"name": "sanction", "type": "defective", "probability": 0.3, 'player': 'user'}
    move = {"name": "open_dialogue", "type": "cooperative", "probability": 0.5, 'player': 'computer'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_mixed)
    print(payoff)
    assert payoff >= 0  # Should be positive for cooperation against defection
    
    # Test defection against cooperation (raise tariffs vs sanction)
    move = {"name": "raise_tariffs", "type": "defective", "probability": 0.5, 'player': 'computer'}
    payoff = calculate_payoff(move, opponent_move, test_payoff_matrix_mixed)
    print(payoff)
    assert payoff >= 0  # Should be positive for defection against cooperation

def test_find_best_response_using_epsilon_greedy_pure(test_moves_pure, test_payoff_matrix_pure):
    """Test best response using epsilon-greedy"""
    opponent_move = {"name": "wait_and_see", "type": "cooperative", "probability": 1.0, 'player': 'user'}
    epsilon = 0.1
    best_response = find_best_response_using_epsilon_greedy(test_moves_pure, opponent_move, epsilon, test_payoff_matrix_pure)
    print(best_response)
    assert best_response is not None
    assert best_response["name"] == "raise_tariffs"

    # Test with epsilon = 0.5
    epsilon = 0.5
    best_response = find_best_response_using_epsilon_greedy(test_moves_pure, opponent_move, epsilon, test_payoff_matrix_pure)
    print(best_response)
    assert best_response is not None


def test_find_best_response_using_epsilon_greedy_mixed(test_moves_mixed, test_payoff_matrix_mixed):
    """Test best response using epsilon-greedy"""
    opponent_move = {"name": "wait_and_see", "type": "cooperative", "probability": 0.7, 'player': 'user'}
    epsilon = 0.1
    best_response = find_best_response_using_epsilon_greedy(test_moves_mixed, opponent_move, epsilon, test_payoff_matrix_mixed)
    print(best_response)
    assert best_response is not None
    assert best_response["name"] == "raise_tariffs"

@pytest.fixture
def test_payoff_matrix_for_nash_equilibrium():
    return [
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 3, "computer": 3}
    },
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 0, "computer": 5}
    },
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 2, "computer": 2}
    },
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "sanction",
        "payoff": {"user": 0, "computer": 5}
    },
    {
        "user_move_name": "sanction",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 5, "computer": 0}
    },
    {
        "user_move_name": "sanction",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 1, "computer": 1}
    },
    {
        "user_move_name": "sanction",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 5, "computer": 0}
    },
    {
        "user_move_name": "sanction",
        "computer_move_name": "sanction",
        "payoff": {"user": 1, "computer": 1}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 5, "computer": 0}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 1, "computer": 1}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 5, "computer": 0}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "sanction",
        "payoff": {"user": 1, "computer": 1}
    },
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 4, "computer": 4}
    },
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 0, "computer": 5}
    },
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 3, "computer": 3}
    },
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "sanction",
        "payoff": {"user": 0, "computer": 5}    
    }
]

def test_nash_equilibrium_strategy_pure(test_moves_pure, test_payoff_matrix_for_nash_equilibrium):
    """Test Nash equilibrium strategy"""
    opponent_moves = [
        {"name": "wait_and_see", "type": "cooperative", "probability": 1.0, 'player': 'user'},
        {"name": "sanction", "type": "defective", "probability": 1.0, 'player': 'user'},
        {"name": "raise_tariffs", "type": "defective", "probability": 1.0, 'player': 'user'},
        {"name": "open_dialogue", "type": "cooperative", "probability": 1.0, 'player': 'user'}
    ]
    nash_equilibrium = find_nash_equilibrium_strategy(test_moves_pure, opponent_moves, test_payoff_matrix_for_nash_equilibrium)

    assert nash_equilibrium is not None
    assert nash_equilibrium['nash_equilibria_strategies'][0]["computer_strategy"]['name'] == "open_dialogue"

def test_solve_mixed_strategy_indifference_general(test_payoff_matrix_mixed):
    """Test solving for mixed strategies that make the opponent indifferent"""
    # Construct 4x4 payoff matrix using all four moves
    moves = ["open_dialogue", "raise_tariffs", "wait_and_see"]
    trade_payoffs = np.zeros((len(moves), len(moves)))
    
    for i, move1 in enumerate(moves):
        for j, move2 in enumerate(moves):
            payoff_entry = next(
                (entry for entry in test_payoff_matrix_mixed 
                 if entry['user_move_name'] == move1 
                 and entry['computer_move_name'] == move2),
                None
            )
            if payoff_entry:
                trade_payoffs[i, j] = payoff_entry['payoff']['user']
    print("Payoff Matrix:")
    print(trade_payoffs)
    
    # Test solving for row player's mixed strategy
    row_strategy = solve_mixed_strategy_indifference_general(trade_payoffs, player='row')
    assert row_strategy is  None

def test_get_the_next_move_based_on_mixed_strartegy_probability_indifference():
    """Test getting the next move based on mixed strategy probability indifference"""
    # Construct 3x3 payoff matrix using the same moves
    moves = [
        {
            "name": "open_dialogue",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'computer'
        },
        {
            "name": "raise_tariffs",
            "type": "defective",
            "probability": 1.0,
            'player': 'computer'
        },
        {
            "name": "wait_and_see",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'computer'
        }
    ]
    user_moves =   [
        {
            "name": "open_dialogue",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        },
        {
            "name": "raise_tariffs",
            "type": "defective",
            "probability": 1.0,
            'player': 'user'
        },
        {
            "name": "wait_and_see",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        }
    ]

    test_payoff_matrix_mixed = [
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 3, "computer": 1}
    },
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 1, "computer": 3}
    },
    {
        "user_move_name": "open_dialogue",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 2, "computer": 2}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 1, "computer": 3}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 3, "computer": 1}
    },
    {
        "user_move_name": "raise_tariffs",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 0, "computer": 4}
    },
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "open_dialogue",
        "payoff": {"user": 2, "computer": 2}
    },
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "raise_tariffs",
        "payoff": {"user": 4, "computer": 0}
    },
    {
        "user_move_name": "wait_and_see",
        "computer_move_name": "wait_and_see",
        "payoff": {"user": 1, "computer": 1}
    }
]
   
    state = {}
    state['equalizer_strategy'] = None
    state['round_idx'] = 2
    state['last_strategy_update'] = 0
    state['generated_mixed_moves_array'] = None
    next_move = get_the_next_move_based_on_mixed_strartegy_probability_indifference(
        computer_moves=moves,
        user_moves=user_moves,
        payoff_matrix=test_payoff_matrix_mixed,
        state=state
    )
    print("Next Move:")
    print(next_move)
    assert next_move is not None
    assert next_move['name'] in [move['name'] for move in moves]  # Next move should be one of our defined moves
 
def test_get_security_level_response():
    """Test getting security level response"""
    # Define computer moves
    moves = [
        {
            "name": "open_dialogue",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'computer'
        },
        {
            "name": "raise_tariffs",
            "type": "defective",
            "probability": 1.0,
            'player': 'computer'
        },
        {
            "name": "wait_and_see",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'computer'
        }
    ]

    # Define user moves
    user_moves = [
        {
            "name": "open_dialogue",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        },
        {
            "name": "raise_tariffs",
            "type": "defective",
            "probability": 1.0,
            'player': 'user'
        },
        {
            "name": "wait_and_see",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        }
    ]

    # Define payoff matrix
    test_payoff_matrix = [
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "open_dialogue",
            "payoff": {"user": 3, "computer": 1}
        },
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "raise_tariffs",
            "payoff": {"user": 1, "computer": 3}
        },
        {
            "user_move_name": "open_dialogue",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 2, "computer": 2}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "open_dialogue",
            "payoff": {"user": 1, "computer": 3}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "raise_tariffs",
            "payoff": {"user": 3, "computer": 1}
        },
        {
            "user_move_name": "raise_tariffs",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 0, "computer": 4}
        },
        {
            "user_move_name": "wait_and_see",
            "computer_move_name": "open_dialogue",
            "payoff": {"user": 2, "computer": 2}
        },
        {
            "user_move_name": "wait_and_see",
            "computer_move_name": "raise_tariffs",
            "payoff": {"user": 4, "computer": 0}
        },
        {
            "user_move_name": "wait_and_see",
            "computer_move_name": "wait_and_see",
            "payoff": {"user": 1, "computer": 1}
        }
    ]

 
    
    security_response = get_security_level_response(
        moves=moves,
        opponent_move={
            "name": "wait_and_see",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        },
        payoff_matrix=test_payoff_matrix
    )
    
    print("Security Level Response:")
    print(security_response)
    assert security_response is not None
    assert security_response['name'] in [move['name'] for move in user_moves]  # Response should be one of our defined moves
 
def test_get_copy_cat_move():
    """Test getting copy cat move"""
    # Define test moves
    moves = [
        {
            "name": "open_dialogue",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        },
        {
            "name": "raise_tariffs",
            "type": "defective",
            "probability": 1.0,
            'player': 'user'
        },
        {
            "name": "wait_and_see",
            "type": "cooperative",
            "probability": 1.0,
            'player': 'user'
        }
    ]

    # Test case 1: Last computer move exists in moves
    last_computer_move = {
        "name": "open_dialogue",
        "type": "cooperative",
        "probability": 1.0,
        'player': 'computer'
    }
    copy_cat_move = get_copy_cat_move(moves, last_computer_move)
    assert copy_cat_move is not None
    assert copy_cat_move['name'] == "open_dialogue"
    assert copy_cat_move['type'] == "cooperative"

    # Test case 2: Last computer move doesn't exist in moves
    last_computer_move = {
        "name": "non_existent_move",
        "type": "cooperative",
        "probability": 1.0,
        'player': 'computer'
    }
    copy_cat_move = get_copy_cat_move(moves, last_computer_move)
    assert copy_cat_move is not None
    assert copy_cat_move in moves  # Should return a random move from the list

    # Test case 3: Empty moves list
    empty_moves = []
    copy_cat_move = get_copy_cat_move(empty_moves, last_computer_move)
    assert copy_cat_move is None  # get_a_random_move returns None for empty list

def test_get_next_move_based_on_strategy_settings():
    """Test getting next move based on strategy settings"""
    # Build the game object
    game = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.6,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'user'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.1,
                'player': 'user'
            }
        ],
        'user_strategy_settings': {
            'strategy': 'copy_cat',  # or 'tit_for_tat'
            'first_move': 'open_dialogue',
            'cooperation_start': 2,
            'mixed_strategy_array': None
        }
    }

    # Test case 1: First round (round_idx = 0)
    last_computer_move = {
        "name": "wait_and_see",
        "type": "cooperative",
        "probability": 1.0,
        'player': 'computer'
    }
    next_move = get_next_move_based_on_strategy_settings(game, last_computer_move, 0)
    print("First round move:")
    print(next_move)
    assert next_move is not None
    assert next_move['name'] == 'open_dialogue'  # Should return first_move from settings

    # Test case 2: Later round with copy_cat strategy
    next_move = get_next_move_based_on_strategy_settings(game, last_computer_move, 1)
    print("Copy cat move:")
    print(next_move)
    assert next_move is not None
    assert next_move['name'] == 'wait_and_see'  # Should copy last computer move

    # # Test case 3: Later round with tit_for_tat strategy
    game['user_strategy_settings']['strategy'] = 'tit_for_tat'
    next_move = get_next_move_based_on_strategy_settings(game, last_computer_move, 3)
    print("Tit for tat move:")
    print(next_move)
    assert next_move is not None
    assert next_move['name'] == 'wait_and_see'  # Should copy last computer move

    # Test case 3: Later round with grim trigger strategy
    game['user_strategy_settings']['strategy'] = 'grim_trigger'
    next_move = get_next_move_based_on_strategy_settings(game, last_computer_move, 3)
    print("Grim trigger move:")
    print(next_move)
    assert next_move is not None
    assert next_move['name'] == 'raise_tariffs'  # Should copy last computer move

   # Test case 4: unknown_strategy - should raise ValueError
    game['user_strategy_settings']['strategy'] = 'unknown_strategy'
    with pytest.raises(ValueError):
        get_next_move_based_on_strategy_settings(game, last_computer_move, 1)
    
    # Test case 5: mixed strategy 
    game['user_strategy_settings']['strategy'] = 'mixed'
    next_move = get_next_move_based_on_strategy_settings(game, last_computer_move, 1)
    print("Mixed move:")
    print(next_move)
    assert next_move is not None
    assert next_move in game['user_moves']  

    # Test case 6: No strategy settings - should raise ValueError
    game['user_strategy_settings'] = None
    with pytest.raises(ValueError):
        get_next_move_based_on_strategy_settings(game, last_computer_move, 1)

    # Test case 7: No user moves - should raise ValueError
    game['user_moves'] = None
    with pytest.raises(ValueError):
        get_next_move_based_on_strategy_settings(game, last_computer_move, 1)

def test_play_game_round():
    """Test the play_game_round method with different game configurations"""
    
    # Test game object with copy_cat strategy
    test_game_copy_cat = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'user'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'computer'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 4}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 4, "computer": 1}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 3, "computer": 1}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 3}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'copy_cat',
            'first_move': 'open_dialogue',
            'cooperation_start': 2,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    # Test case 1: First round (round 0) with copy_cat strategy
    test_game_copy_cat['state']['round_idx'] = 0
    user_move, computer_move = play_game_round(test_game_copy_cat, 0)
    
    print(f"Round 0 - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    assert user_move['name'] in [move['name'] for move in test_game_copy_cat['user_moves']]
    assert computer_move['name'] in [move['name'] for move in test_game_copy_cat['computer_moves']]
    assert user_move['name'] == 'open_dialogue'  # Should return first_move from settings
    
    # Test case 2: Later round with copy_cat strategy
    test_game_copy_cat['state']['round_idx'] = 1
    user_move, computer_move = play_game_round(test_game_copy_cat, 1)
    
    print(f"Round 1 - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    assert user_move['name'] in [move['name'] for move in test_game_copy_cat['user_moves']]
    assert computer_move['name'] in [move['name'] for move in test_game_copy_cat['computer_moves']]
    
    # Test case 3: Phase 1 (Nash Equilibrium) - rounds 0-15
    test_game_copy_cat['state']['round_idx'] = 5
    user_move, computer_move = play_game_round(test_game_copy_cat, 5)
    
    print(f"Phase 1 (Round 5) - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    
    # Test case 4: Phase 2 (Greedy Response) - rounds 16-100
    test_game_copy_cat['state']['round_idx'] = 20
    user_move, computer_move = play_game_round(test_game_copy_cat, 20)
    
    print(f"Phase 2 (Round 20) - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    
    # Test case 5: Phase 3 (Mixed Strategy) - rounds 101-200
    test_game_copy_cat['state']['round_idx'] = 110
    user_move, computer_move = play_game_round(test_game_copy_cat, 110)
    
    print(f"Phase 3 (Round 110) - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    
    # Test case 6: Tit for tat strategy
    test_game_tit_for_tat = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.5,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.5,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 0, "computer": 5}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 5, "computer": 0}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'tit_for_tat',
            'first_move': 'open_dialogue',
            'cooperation_start': 3,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    # Test tit_for_tat before cooperation_start
    test_game_tit_for_tat['state']['round_idx'] = 1
    user_move, computer_move = play_game_round(test_game_tit_for_tat, 1)
    
    print(f"Tit for Tat (Round 1) - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    assert user_move['type'] == 'cooperative'  # Should be cooperative before cooperation_start
    
    # Test tit_for_tat after cooperation_start
    test_game_tit_for_tat['state']['round_idx'] = 5
    user_move, computer_move = play_game_round(test_game_tit_for_tat, 5)
    
    print(f"Tit for Tat (Round 5) - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    
    # Test case 7: Mixed strategy
    test_game_mixed = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'user'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'computer'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 4}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 4, "computer": 1}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 3, "computer": 1}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 3}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'mixed',
            'first_move': 'open_dialogue',
            'cooperation_start': 2,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    # Test mixed strategy
    test_game_mixed['state']['round_idx'] = 1
    user_move, computer_move = play_game_round(test_game_mixed, 1)
    
    print(f"Mixed Strategy (Round 1) - User move: {user_move['name']}, Computer move: {computer_move['name']}")
    
    assert user_move is not None
    assert computer_move is not None
    assert user_move['name'] in [move['name'] for move in test_game_mixed['user_moves']]
    assert computer_move['name'] in [move['name'] for move in test_game_mixed['computer_moves']]
    
    # Test case 8: Multiple rounds to test strategy evolution
    print("\nTesting multiple rounds with copy_cat strategy:")
    moves_history = []
    
    for round_idx in range(5):
        test_game_copy_cat['state']['round_idx'] = round_idx
        user_move, computer_move = play_game_round(test_game_copy_cat, round_idx)
        
        moves_history.append({
            'round': round_idx,
            'user_move': user_move['name'],
            'computer_move': computer_move['name']
        })
        
        print(f"Round {round_idx}: User={user_move['name']}, Computer={computer_move['name']}")
        
        assert user_move is not None
        assert computer_move is not None
    
    print(f"Move history: {moves_history}")
    assert len(moves_history) == 5
    
    print("\nAll play_game_round tests passed successfully!")

def test_play_full_game():
    """Test the play_full_game method with different game configurations"""
    
    # Test game object with copy_cat strategy
    test_game_copy_cat = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'user'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'computer'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 4}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 4, "computer": 1}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 3, "computer": 1}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 3}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'copy_cat',
            'first_move': 'open_dialogue',
            'cooperation_start': 2,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    # Test case 1: Play full game with copy_cat strategy
    print("\n=== Testing play_full_game with copy_cat strategy ===")
    result = play_full_game(test_game_copy_cat)
    final_payoff, iteration_moves = result
    print(f"Final user payoff: {final_payoff['final_user_payoff']}")
    print(f"Final computer payoff: {final_payoff['final_computer_payoff']}")
    
    assert 'final_user_payoff' in final_payoff
    assert 'final_computer_payoff' in final_payoff
    assert isinstance(final_payoff['final_user_payoff'], (int, float))
    assert isinstance(final_payoff['final_computer_payoff'], (int, float))
    assert final_payoff['final_user_payoff'] >= 0
    assert final_payoff['final_computer_payoff'] >= 0
    
    #Test case 2: Play full game with tit_for_tat strategy
    test_game_tit_for_tat = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.5,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.5,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 0, "computer": 5}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 5, "computer": 0}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'tit_for_tat',
            'first_move': 'open_dialogue',
            'cooperation_start': 3,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    print("\n=== Testing play_full_game with tit_for_tat strategy ===")
    result_tit_for_tat, iteration_moves = play_full_game(test_game_tit_for_tat)
    
    print(f"Final user payoff: {result_tit_for_tat['final_user_payoff']}")
    print(f"Final computer payoff: {result_tit_for_tat['final_computer_payoff']}")
    
    assert 'final_user_payoff' in result_tit_for_tat
    assert 'final_computer_payoff' in result_tit_for_tat
    assert isinstance(result_tit_for_tat['final_user_payoff'], (int, float))
    assert isinstance(result_tit_for_tat['final_computer_payoff'], (int, float))
    assert result_tit_for_tat['final_user_payoff'] >= 0
    assert result_tit_for_tat['final_computer_payoff'] >= 0
    
    # Test case 3: Play full game with mixed strategy
    test_game_mixed = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'user'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.4,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.3,
                'player': 'computer'
            },
            {
                "name": "wait_and_see",
                "type": "cooperative",
                "probability": 0.3,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 4}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 4, "computer": 1}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 3, "computer": 1}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 2, "computer": 2}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 3}
            },
            {
                "user_move_name": "wait_and_see",
                "computer_move_name": "wait_and_see",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'mixed',
            'first_move': 'open_dialogue',
            'cooperation_start': 2,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    print("\n=== Testing play_full_game with mixed strategy ===")
    result_mixed, iteration_moves = play_full_game(test_game_mixed)
    
    print(f"Final user payoff: {result_mixed['final_user_payoff']}")
    print(f"Final computer payoff: {result_mixed['final_computer_payoff']}") 
    
    assert 'final_user_payoff' in result_mixed
    assert 'final_computer_payoff' in result_mixed
    assert isinstance(result_mixed['final_user_payoff'], (int, float))
    assert isinstance(result_mixed['final_computer_payoff'], (int, float))
    assert result_mixed['final_user_payoff'] >= 0
    assert result_mixed['final_computer_payoff'] >= 0
    
    # Test case 4: Compare payoffs across different strategies
    print("\n=== Comparing payoffs across strategies ===")
    #print(f"Copy Cat - User: {result['final_user_payoff']:.2f}, Computer: {result['final_computer_payoff']:.2f}")
    #print(f"Tit for Tat - User: {result_tit_for_tat['final_user_payoff']:.2f}, Computer: {result_tit_for_tat['final_computer_payoff']:.2f}")
    #print(f"Mixed - User: {result_mixed['final_user_payoff']:.2f}, Computer: {result_mixed['final_computer_payoff']:.2f}")
    
    # Test case 5: Test with random strategy
    test_game_random = {
        'user_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                'player': 'user'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.5,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                'player': 'computer'
            },
            {
                "name": "raise_tariffs",
                "type": "defective",
                "probability": 0.5,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            },
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 0, "computer": 5}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 5, "computer": 0}
            },
            {
                "user_move_name": "raise_tariffs",
                "computer_move_name": "raise_tariffs",
                "payoff": {"user": 1, "computer": 1}
            }
        ],
        'user_strategy_settings': {
            'strategy': 'random',
            'first_move': 'open_dialogue',
            'cooperation_start': 3,
            'mixed_strategy_array': None
        },
        'state': {
            'equalizer_strategy': None,
            'round_idx': 0,
            'last_strategy_update': 0,
            'generated_mixed_moves_array': None,
            'last_computer_move': None
        }
    }
    
    print("\n=== Testing play_full_game with random strategy ===")
    result_random, iteration_moves = play_full_game(test_game_random)
    
    print(f"Final user payoff: {result_random['final_user_payoff']}")
    print(f"Final computer payoff: {result_random['final_computer_payoff']}")
    
    assert 'final_user_payoff' in result_random
    assert 'final_computer_payoff' in result_random
    assert isinstance(result_random['final_user_payoff'], (int, float))
    assert isinstance(result_random['final_computer_payoff'], (int, float))
    assert result_random['final_user_payoff'] >= 0
    assert result_random['final_computer_payoff'] >= 0
    
    print("\nAll play_full_game tests passed successfully!")

