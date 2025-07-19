"""
Sample game object dictionary for testing the play_game_round method.

This file contains a complete game object that can be used to test the play_game_round function
from game_theory.py. The game object includes all required fields and sample data.
"""

import numpy as np

# Sample game object for testing play_game_round method
sample_game = {
    # User moves - strategies available to the user
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
    
    # Computer moves - strategies available to the computer
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
    
    # Payoff matrix - defines payoffs for all move combinations
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
    
    # User strategy settings - controls how the user selects moves
    'user_strategy_settings': {
        'strategy': 'copy_cat',  # Options: 'copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed'
        'first_move': 'open_dialogue',  # First move for the user
        'cooperation_start': 2,  # Round when cooperation starts (for tit_for_tat and grim_trigger)
        'mixed_strategy_array': None  # Will be populated for mixed strategy
    },
    
    # Game state - tracks internal state for mixed strategies
    'state': {
        'equalizer_strategy': None,
        'round_idx': 0,
        'last_strategy_update': 0,
        'generated_mixed_moves_array': None,
        'last_computer_move': None
    }
}

# Alternative game object with different strategy settings
sample_game_tit_for_tat = {
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

# Game object for testing mixed strategy
sample_game_mixed = {
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

def print_game_object(game_obj, name="Game Object"):
    """Helper function to print a game object in a readable format"""
    print(f"\n=== {name} ===")
    print(f"User Moves: {len(game_obj['user_moves'])} moves")
    for move in game_obj['user_moves']:
        print(f"  - {move['name']} ({move['type']}, prob: {move['probability']})")
    
    print(f"\nComputer Moves: {len(game_obj['computer_moves'])} moves")
    for move in game_obj['computer_moves']:
        print(f"  - {move['name']} ({move['type']}, prob: {move['probability']})")
    
    print(f"\nPayoff Matrix: {len(game_obj['payoff_matrix'])} entries")
    for entry in game_obj['payoff_matrix']:
        print(f"  - {entry['user_move_name']} vs {entry['computer_move_name']}: "
              f"user={entry['payoff']['user']}, computer={entry['payoff']['computer']}")
    
    print(f"\nStrategy Settings:")
    print(f"  - Strategy: {game_obj['user_strategy_settings']['strategy']}")
    print(f"  - First Move: {game_obj['user_strategy_settings']['first_move']}")
    print(f"  - Cooperation Start: {game_obj['user_strategy_settings']['cooperation_start']}")

if __name__ == "__main__":
    # Print all sample game objects
    print_game_object(sample_game, "Sample Game (Copy Cat)")
    print_game_object(sample_game_tit_for_tat, "Sample Game (Tit for Tat)")
    print_game_object(sample_game_mixed, "Sample Game (Mixed Strategy)")
    
    print("\n=== Usage Example ===")
    print("from game_theory import play_game_round")
    print("from sample_game_object import sample_game")
    print("")
    print("# Test a single round")
    print("user_move, computer_move = play_game_round(sample_game, 0)")
    print("print(f'User move: {user_move[\"name\"]}')")
    print("print(f'Computer move: {computer_move[\"name\"]}')") 