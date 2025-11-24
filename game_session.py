"""
Game Session Manager

Handles game state management, round-by-round gameplay, and game lifecycle.
Separates game logic from REST API interface.
"""
import logging
from typing import Dict, Optional, Tuple
import random
from game_model import GameModel
from profile_manager import ProfileManager
from game_theory import (
    play_game_round, get_realized_payoff,
    check_dominant_move, find_nash_equilibrium_strategy,
    get_a_random_move_from_nash_equilibrium_strategy,
    find_best_response_using_epsilon_greedy, get_a_random_move,
    get_the_next_move_based_on_mixed_strartegy_probability_indifference,
    get_security_level_strategy, calculate_epsilon,
    calculate_phase_boundaries
)
from profile_manager import PhaseConfig

logger = logging.getLogger(__name__)


class GameSessionManager:
    """Manages game sessions and round-by-round gameplay"""
    
    def __init__(self, profile_manager: ProfileManager):
        self.games: Dict[str, dict] = {}
        self.profile_manager = profile_manager
    
    def initialize_game(self, game_id: str, game_data: dict) -> dict:
        """
        Initialize a new game session.
        
        Args:
            game_id: Unique game identifier
            game_data: Game configuration dictionary
            
        Returns:
            Initialized game dictionary
            
        Raises:
            ValueError: If game data is invalid or profile not found
        """
        # Validate the game data using GameModel
        try:
            game_model = GameModel.from_dict(game_data)
            game = game_model.to_dict()
        except Exception as validation_error:
            logger.error(f"Game data validation error: {str(validation_error)}")
            raise ValueError(f'Invalid game data: {str(validation_error)}')

        # Get computer profile
        computer_profile_name = game_data.get('computer_profile_name')
        if not computer_profile_name:
            raise ValueError('Computer profile name is required')

        computer_profile = self.profile_manager.get_profile(computer_profile_name)
        if not computer_profile:
            raise ValueError(f'Computer profile not found: {computer_profile_name}')

        # Override num_rounds if provided in request
        num_rounds_override = game_data.get('num_rounds')
        if num_rounds_override:
            # Recalculate phases if phase_percentages exist
            if computer_profile.phase_percentages:
                phases = calculate_phase_boundaries(num_rounds_override, computer_profile.phase_percentages)
                # Update the profile's phases
                computer_profile.phases = PhaseConfig(
                    p1_start=phases['p1'][0],
                    p1_end=phases['p1'][1],
                    p2_start=phases['p2'][0],
                    p2_end=phases['p2'][1],
                    p3_start=phases['p3'][0],
                    p3_end=phases['p3'][1]
                )
            computer_profile.num_rounds = num_rounds_override

        game['computer_profile_name'] = computer_profile_name
        game['computer_profile'] = computer_profile.to_dict()
        # For step-by-step games, default to 20 rounds
        # If num_rounds is explicitly provided, use it; otherwise, set to 20 for step-by-step
        game['num_rounds'] = game_data.get('num_rounds') if game_data.get('num_rounds') else 20
        
        # Initialize game state
        game['state'] = game.get('state', {})
        game['state']['round_idx'] = 0
        game['state']['last_computer_move'] = None
        game['state']['last_strategy_update'] = 0
        game['state']['generated_mixed_moves_array'] = None
        game['state']['equalizer_strategy'] = None
        game['state']['grim_triggered'] = False
        
        # Initialize running totals
        game['running_totals'] = {
            'user_total': 0.0,
            'computer_total': 0.0
        }
        
        # Store game
        self.games[game_id] = game
        logger.info(f"Initialized game {game_id}")
        
        return game
    
    def get_game(self, game_id: str) -> Optional[dict]:
        """Get game by ID"""
        return self.games.get(game_id)
    
    def delete_game(self, game_id: str) -> bool:
        """Delete a game from memory"""
        if game_id in self.games:
            del self.games[game_id]
            logger.info(f"Deleted game {game_id}")
            return True
        return False
    
    def _calculate_computer_move(self, game: dict, user_move: dict, round_idx: int) -> dict:
        """
        Calculate computer move based on user move and current game phase.
        This is used when user provides a specific move override.
        """
        computer_profile = game['computer_profile']
        
        # Initialize state if first round
        if round_idx == 0:
            game['state']['last_computer_move'] = None
            game['state']['round_idx'] = 0
            game['state']['last_strategy_update'] = 0
            game['state']['generated_mixed_moves_array'] = None
            game['state']['equalizer_strategy'] = None
            game['state']['grim_triggered'] = False
        
        computer_move = None
        
        # Determine computer move based on phase
        if computer_profile['phases']['p1'][0] <= round_idx <= computer_profile['phases']['p1'][1]:  # Phase 1: Nash Equilibrium
            computer_dominant = check_dominant_move(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
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
            if computer_dominant and random.random() < computer_profile['dominant_probabilities']['p2']:
                computer_move = computer_dominant
            else:
                epsilon = calculate_epsilon(computer_profile, round_idx)
                computer_move = find_best_response_using_epsilon_greedy(game['computer_moves'], user_move, epsilon, game['payoff_matrix'])
                if computer_move is None:
                    computer_move = get_a_random_move(game['computer_moves'])

        elif computer_profile['phases']['p3'][0] <= round_idx <= computer_profile['phases']['p3'][1]:  # Phase 3: Mixed Strategy
            computer_dominant = check_dominant_move(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
            if computer_dominant and random.random() < computer_profile['dominant_probabilities']['p3']:
                computer_move = computer_dominant
            else:
                computer_move = get_the_next_move_based_on_mixed_strartegy_probability_indifference(
                    game['computer_moves'],
                    game['user_moves'],
                    game['payoff_matrix'],
                    game['state'],
                    user_support=None,
                    num_rounds=game.get('num_rounds', 200)
                )
                if computer_move is None:
                    computer_move = get_a_random_move(game['computer_moves'])
        
        # Update game state
        game['state']['last_computer_move'] = computer_move
        game['state']['round_idx'] = round_idx
        
        # Respond to user's dominant move with mixed strategy
        user_dominant = check_dominant_move(game['user_moves'], game['computer_moves'], game['payoff_matrix'])
        if user_dominant and user_move == user_dominant:
            rand = random.random()
            if rand < 0.6:  # 60% - play best response
                epsilon = calculate_epsilon(computer_profile, round_idx)
                best_response = find_best_response_using_epsilon_greedy(game['computer_moves'], user_move, epsilon=0.0, payoff_matrix=game['payoff_matrix'])
                computer_move = best_response if best_response else computer_move
                game['state']['last_computer_move'] = computer_move
            elif rand < 0.8:  # 20% - play security level strategy
                security_level_response = get_security_level_strategy(game['computer_moves'], game['user_moves'], game['payoff_matrix'])
                computer_move = security_level_response if security_level_response else computer_move
                game['state']['last_computer_move'] = computer_move
        
        return computer_move
    
    def play_round(self, game_id: str, user_move_override: Optional[dict] = None) -> dict:
        """
        Play a single round of the game.
        
        Args:
            game_id: Unique game identifier
            user_move_override: Optional user move to override strategy (dict with 'name' field or string)
            
        Returns:
            Dictionary with round results including moves, payoffs, and game state
            
        Raises:
            ValueError: If game not found, game completed, or invalid move
        """
        game = self.get_game(game_id)
        if not game:
            raise ValueError('Game not found')
        
        # Get current round index
        current_round = game['state'].get('round_idx', 0)
        num_rounds = game.get('num_rounds')
        
        # Check if game is already completed (only if num_rounds is set)
        if num_rounds is not None and current_round >= num_rounds:
            raise ValueError('Game already completed')
        
        # Determine user move
        if user_move_override:
            # Find the move in user_moves by name
            user_move_name = user_move_override.get('name') if isinstance(user_move_override, dict) else user_move_override
            user_move = next((move for move in game['user_moves'] if move['name'] == user_move_name), None)
            if not user_move:
                raise ValueError(f'Invalid user move: {user_move_name}')
            
            # Calculate computer move based on user's chosen move
            computer_move = self._calculate_computer_move(game, user_move, current_round)
        else:
            # Use strategy to determine user move (normal flow)
            user_move, computer_move = play_game_round(game, current_round)
        
        if user_move is None or computer_move is None:
            raise ValueError('Failed to generate moves for this round')
        
        # Calculate payoffs
        user_payoff = get_realized_payoff(user_move, computer_move, game['payoff_matrix'])
        computer_payoff = get_realized_payoff(computer_move, user_move, game['payoff_matrix'])
        
        # Ensure payoffs are floats
        if isinstance(user_payoff, list):
            user_payoff = float(user_payoff[0]) if user_payoff else 0.0
        if isinstance(computer_payoff, list):
            computer_payoff = float(computer_payoff[0]) if computer_payoff else 0.0
        
        # Update running totals
        game['running_totals']['user_total'] += user_payoff
        game['running_totals']['computer_total'] += computer_payoff
        
        # Determine round winner
        round_winner = "tie"
        if user_payoff > computer_payoff:
            round_winner = "user"
        elif computer_payoff > user_payoff:
            round_winner = "computer"
        
        # Determine current phase
        computer_profile = game['computer_profile']
        if computer_profile['phases']['p1'][0] <= current_round <= computer_profile['phases']['p1'][1]:
            phase = "Phase 1 (Nash Equilibrium)"
        elif computer_profile['phases']['p2'][0] <= current_round <= computer_profile['phases']['p2'][1]:
            phase = "Phase 2 (Greedy Response)"
        elif computer_profile['phases']['p3'][0] <= current_round <= computer_profile['phases']['p3'][1]:
            phase = "Phase 3 (Mixed Strategy)"
        else:
            phase = "Unknown Phase"
        
        # Increment round index
        game['state']['round_idx'] = current_round + 1
        # Game is only completed if num_rounds is set and we've reached it
        is_game_completed = num_rounds is not None and game['state']['round_idx'] >= num_rounds
        
        # Prepare response
        response_data = {
            'round': current_round + 1,
            'user_move': {
                'name': user_move['name'],
                'type': user_move['type']
            },
            'computer_move': {
                'name': computer_move['name'],
                'type': computer_move['type']
            },
            'user_payoff': round(user_payoff, 2),
            'computer_payoff': round(computer_payoff, 2),
            'round_winner': round_winner,
            'phase': phase,
            'running_totals': {
                'user_total': round(game['running_totals']['user_total'], 2),
                'computer_total': round(game['running_totals']['computer_total'], 2)
            },
            'game_status': 'completed' if is_game_completed else 'in_progress',
            'current_round': game['state']['round_idx'],
            'total_rounds': num_rounds  # None for unlimited rounds
        }
        
        return response_data
    
    def get_game_state(self, game_id: str) -> dict:
        """
        Get the current state of a game.
        
        Args:
            game_id: Unique game identifier
            
        Returns:
            Dictionary with game state information
            
        Raises:
            ValueError: If game not found
        """
        game = self.get_game(game_id)
        if not game:
            raise ValueError('Game not found')
        
        current_round = game['state'].get('round_idx', 0)
        num_rounds = game.get('num_rounds')
        
        last_computer_move = game['state'].get('last_computer_move')
        last_computer_move_name = None
        if isinstance(last_computer_move, dict):
            last_computer_move_name = last_computer_move.get('name')
        elif last_computer_move:
            last_computer_move_name = last_computer_move
        
        # Determine game status
        if num_rounds is None:
            game_status = 'in_progress'  # Unlimited rounds
        elif current_round >= num_rounds:
            game_status = 'completed'
        else:
            game_status = 'in_progress'
        
        return {
            'game_id': game_id,
            'current_round': current_round,
            'total_rounds': num_rounds,  # None for unlimited
            'running_totals': game.get('running_totals', {
                'user_total': 0.0,
                'computer_total': 0.0
            }),
            'game_status': game_status,
            'last_computer_move': last_computer_move_name
        }

