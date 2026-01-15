"""
Game Simulation Module

This module provides functionality to run automated simulations of games
where different user strategies are tested against the computer's core game logic.
"""

from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import uuid
import numpy as np
from game_model import GameModel, Move, MoveType, PlayerType, StrategyType, UserStrategySettings, GameState, PayoffEntry
from game_theory import play_full_game
from profile_manager import ProfileManager
import logging
import sys

# Configure logging for simulation module
# Check if root logger is configured, if not configure it
root_logger = logging.getLogger()
if not root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _async_emit(socketio_instance, event, data, room=None):
    """
    Emit a WebSocket message asynchronously using background tasks.
    This prevents blocking the calling thread while sending messages.
    
    Args:
        socketio_instance: The SocketIO instance to use for emitting
        event: The event name to emit
        data: The data to send
        room: Optional room to target (if None, broadcasts to all)
    """
    if socketio_instance is None:
        return
    
    def _emit():
        try:
            if room:
                socketio_instance.emit(event, data, room=room)
            else:
                socketio_instance.emit(event, data)
        except Exception as e:
            logger.error(f"Error emitting WebSocket event {event}: {str(e)}")
    
    # Use start_background_task for async execution
    socketio_instance.start_background_task(_emit)


def calculate_move_statistics(simulation_results: List[Dict[str, Any]], payoff_matrix: List[PayoffEntry]) -> Dict[str, Any]:
    """
    Calculate move-level statistics from simulation results.
    
    Args:
        simulation_results: List of simulation result dictionaries, each containing 'move_history' and 'user_won'
        payoff_matrix: Payoff matrix for calculating move payoffs
        
    Returns:
        Dictionary with move statistics:
        {
            'user_moves': {
                'move_name': {
                    'frequency': int,
                    'frequency_percentage': float,
                    'average_payoff': float,
                    'win_rate': float,  # Percentage of simulations where user won when this move was used
                    'usage_count': int
                }
            },
            'computer_moves': {
                'move_name': {
                    'frequency': int,
                    'frequency_percentage': float,
                    'average_payoff': float,
                    'win_rate': float,  # Percentage of simulations where computer won when this move was used
                    'usage_count': int
                }
            },
            'move_combinations': {
                '(user_move, computer_move)': {
                    'frequency': int,
                    'frequency_percentage': float,
                    'average_user_payoff': float,
                    'average_computer_payoff': float
                }
            }
        }
    """
    user_move_stats = defaultdict(lambda: {'count': 0, 'total_payoff': 0.0, 'wins': 0, 'simulations_with_move': set()})
    computer_move_stats = defaultdict(lambda: {'count': 0, 'total_payoff': 0.0, 'wins': 0, 'simulations_with_move': set()})
    move_combination_stats = defaultdict(lambda: {'count': 0, 'total_user_payoff': 0.0, 'total_computer_payoff': 0.0})
    
    total_moves = 0
    total_combinations = 0
    
    # Process each simulation
    all_computer_moves_seen = set()
    for sim_result in simulation_results:
        move_history = sim_result.get('move_history', [])
        user_won = sim_result.get('user_won', False)
        sim_id = sim_result.get('simulation_id', '')
        
        # Track which simulations used which moves (for win rate calculation)
        user_moves_in_sim = set()
        computer_moves_in_sim = set()
        
        for move_round in move_history:
            user_move_name = move_round.get('user_move_name', 'unknown')
            computer_move_name = move_round.get('computer_move_name', 'unknown')
            
            # Track all unique computer moves seen
            all_computer_moves_seen.add(computer_move_name)
            
            # Update user move statistics
            user_move_stats[user_move_name]['count'] += 1
            user_moves_in_sim.add(user_move_name)
            
            # Update computer move statistics
            computer_move_stats[computer_move_name]['count'] += 1
            computer_moves_in_sim.add(computer_move_name)
            
            # Update move combination statistics
            combo_key = f"({user_move_name}, {computer_move_name})"
            move_combination_stats[combo_key]['count'] += 1
            total_combinations += 1
            
            total_moves += 1
        
        # Update win rates: track wins per move
        # For user moves: if user won the simulation, count as a win for user moves
        # For computer moves: if computer won (user lost), count as a win for computer moves
        if user_won:
            for move_name in user_moves_in_sim:
                user_move_stats[move_name]['wins'] += 1
        else:
            # User lost, so computer won - count as wins for computer moves
            for move_name in computer_moves_in_sim:
                computer_move_stats[move_name]['wins'] += 1
        
        # Track which simulations used each move
        for move_name in user_moves_in_sim:
            user_move_stats[move_name]['simulations_with_move'].add(sim_id)
        for move_name in computer_moves_in_sim:
            computer_move_stats[move_name]['simulations_with_move'].add(sim_id)
    
    # Calculate payoffs for each move (approximate using payoff matrix)
    # For more accurate payoffs, we'd need round-by-round payoff data
    # For now, we'll calculate average payoffs based on move combinations
    for combo_key, combo_data in move_combination_stats.items():
        # Extract move names from combo_key (format: "(user_move, computer_move)")
        try:
            moves = combo_key.strip('()').split(', ')
            if len(moves) == 2:
                user_move_name = moves[0]
                computer_move_name = moves[1]
                
                # Find payoff from matrix
                for entry in payoff_matrix:
                    # Handle both dict and PayoffEntry object
                    entry_user_move = entry.get('user_move_name') if isinstance(entry, dict) else getattr(entry, 'user_move_name', None)
                    entry_computer_move = entry.get('computer_move_name') if isinstance(entry, dict) else getattr(entry, 'computer_move_name', None)
                    
                    if entry_user_move == user_move_name and entry_computer_move == computer_move_name:
                        payoff = entry.get('payoff', {}) if isinstance(entry, dict) else getattr(entry, 'payoff', {})
                        if isinstance(payoff, dict):
                            combo_data['total_user_payoff'] += payoff.get('user', 0.0) * combo_data['count']
                            combo_data['total_computer_payoff'] += payoff.get('computer', 0.0) * combo_data['count']
                        break
        except Exception:
            pass
    
    # Aggregate user move payoffs from combinations
    for combo_key, combo_data in move_combination_stats.items():
        try:
            moves = combo_key.strip('()').split(', ')
            if len(moves) == 2:
                user_move_name = moves[0]
                if combo_data['count'] > 0:
                    avg_payoff = combo_data['total_user_payoff'] / combo_data['count']
                    user_move_stats[user_move_name]['total_payoff'] += avg_payoff * combo_data['count']
        except Exception:
            pass
    
    # Aggregate computer move payoffs from combinations
    for combo_key, combo_data in move_combination_stats.items():
        try:
            moves = combo_key.strip('()').split(', ')
            if len(moves) == 2:
                computer_move_name = moves[1]
                if combo_data['count'] > 0:
                    avg_payoff = combo_data['total_computer_payoff'] / combo_data['count']
                    computer_move_stats[computer_move_name]['total_payoff'] += avg_payoff * combo_data['count']
        except Exception:
            pass
    
    # Build final statistics
    user_moves_result = {}
    for move_name, stats in user_move_stats.items():
        count = stats['count']
        num_sims_with_move = len(stats['simulations_with_move'])
        user_moves_result[move_name] = {
            'frequency': count,
            'frequency_percentage': (count / total_moves * 100) if total_moves > 0 else 0.0,
            'average_payoff': (stats['total_payoff'] / count) if count > 0 else 0.0,
            'win_rate': (stats['wins'] / num_sims_with_move * 100) if num_sims_with_move > 0 else 0.0,
            'usage_count': num_sims_with_move  # Number of simulations that used this move
        }
    
    # Debug logging: log all computer moves found
    logger.info(f"calculate_move_statistics: Found {len(computer_move_stats)} unique computer moves: {list(computer_move_stats.keys())}")
    logger.info(f"calculate_move_statistics: All computer moves seen in move_history: {sorted(all_computer_moves_seen)}")
    logger.info(f"calculate_move_statistics: Total moves analyzed: {total_moves}")
    
    computer_moves_result = {}
    for move_name, stats in computer_move_stats.items():
        count = stats['count']
        num_sims_with_move = len(stats['simulations_with_move'])
        computer_moves_result[move_name] = {
            'frequency': count,
            'frequency_percentage': (count / total_moves * 100) if total_moves > 0 else 0.0,
            'average_payoff': (stats['total_payoff'] / count) if count > 0 else 0.0,
            'win_rate': (stats['wins'] / num_sims_with_move * 100) if num_sims_with_move > 0 else 0.0,
            'usage_count': num_sims_with_move
        }
        logger.debug(f"Computer move '{move_name}': frequency={count}, win_rate={computer_moves_result[move_name]['win_rate']:.2f}%")
    
    move_combinations_result = {}
    for combo_key, combo_data in move_combination_stats.items():
        count = combo_data['count']
        move_combinations_result[combo_key] = {
            'frequency': count,
            'frequency_percentage': (count / total_combinations * 100) if total_combinations > 0 else 0.0,
            'average_user_payoff': (combo_data['total_user_payoff'] / count) if count > 0 else 0.0,
            'average_computer_payoff': (combo_data['total_computer_payoff'] / count) if count > 0 else 0.0
        }
    
    return {
        'user_moves': user_moves_result,
        'computer_moves': computer_moves_result,
        'move_combinations': move_combinations_result,
        'total_moves_analyzed': total_moves,
        'total_combinations_analyzed': total_combinations
    }


def create_strategy_settings(
    strategy_type: str,
    user_moves: List[Move],
    first_move_name: Optional[str] = None,
    cooperation_start: int = 2,
    mixed_strategy_array: Optional[List[str]] = None
) -> UserStrategySettings:
    """
    Create user strategy settings for a given strategy type.
    
    Args:
        strategy_type: Type of strategy ('copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed')
        user_moves: List of available user moves
        first_move_name: Name of the first move (if None, randomly selects from cooperative moves or all moves)
        cooperation_start: Round when cooperation starts (for tit_for_tat, grim_trigger)
        mixed_strategy_array: Array of move names for mixed strategy (if None, uses all moves)
        
    Returns:
        UserStrategySettings object
    """
    # Determine first move if not specified
    if first_move_name is None:
        # Randomly select from cooperative moves if available, otherwise randomly select from all moves
        # This adds variation to simulations while maintaining preference for cooperative starts
        cooperative_moves = [move for move in user_moves if move.type == MoveType.COOPERATIVE]
        if cooperative_moves:
            # Randomly select from cooperative moves
            selected_move = np.random.choice(cooperative_moves)
            first_move_name = selected_move.name
        else:
            # No cooperative moves available, randomly select from all moves
            if user_moves:
                selected_move = np.random.choice(user_moves)
                first_move_name = selected_move.name
            else:
                first_move_name = None
    
    # For mixed strategy, use all moves if array not provided
    if strategy_type == 'mixed' and mixed_strategy_array is None:
        mixed_strategy_array = [move.name for move in user_moves]
    
    return UserStrategySettings(
        strategy=StrategyType(strategy_type),
        first_move=first_move_name,
        cooperation_start=cooperation_start if strategy_type in ['tit_for_tat', 'grim_trigger'] else None,
        mixed_strategy_array=mixed_strategy_array
    )


def run_single_simulation(
    base_game_config: Dict[str, Any],
    user_strategy: str,
    computer_profile_name: str,
    profile_manager: ProfileManager,
    num_rounds: Optional[int] = None,
    simulation_id: Optional[str] = None,
    socketio=None,
    suite_simulation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a single simulation: one user strategy against the computer profile.
    
    Args:
        base_game_config: Base game configuration dictionary with:
            - user_moves: List[Dict] - User moves
            - computer_moves: List[Dict] - Computer moves  
            - payoff_matrix: List[Dict] - Payoff matrix entries
            Optionally can include other fields, but strategy settings will be overridden
        user_strategy: User strategy type ('copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed')
        computer_profile_name: Name of the computer profile to use
        profile_manager: ProfileManager instance
        num_rounds: Optional number of rounds (overrides profile default)
        simulation_id: Optional simulation ID for logging
        
    Returns:
        Dictionary with simulation results:
        {
            'simulation_id': str,
            'user_strategy': str,
            'computer_profile': str,
            'final_user_payoff': float,
            'final_computer_payoff': float,
            'num_rounds': int,
            'user_won': bool,
            'payoff_difference': float,
            'move_history': List[Dict]  # List of moves played in each round for move-level analysis
        }
    """
    if simulation_id is None:
        simulation_id = str(uuid.uuid4())
    
    # Validate strategy
    valid_strategies = ['copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed']
    if user_strategy not in valid_strategies:
        raise ValueError(f"Invalid strategy: {user_strategy}. Must be one of {valid_strategies}")
    
    # Get computer profile
    computer_profile = profile_manager.get_profile(computer_profile_name)
    if not computer_profile:
        raise ValueError(f"Computer profile not found: {computer_profile_name}")
    
    # Create game model from base config
    # Convert moves to Move objects if they're dicts
    user_moves = []
    for move_dict in base_game_config['user_moves']:
        if isinstance(move_dict, dict):
            user_moves.append(Move(**move_dict))
        else:
            user_moves.append(move_dict)
    
    computer_moves = []
    for move_dict in base_game_config['computer_moves']:
        if isinstance(move_dict, dict):
            computer_moves.append(Move(**move_dict))
        else:
            computer_moves.append(move_dict)
    
    # Convert payoff matrix entries to PayoffEntry objects if they're dicts
    payoff_matrix = []
    for entry in base_game_config['payoff_matrix']:
        if isinstance(entry, dict):
            payoff_matrix.append(PayoffEntry(**entry))
        else:
            payoff_matrix.append(entry)
    
    # Create strategy settings
    strategy_settings = create_strategy_settings(
        strategy_type=user_strategy,
        user_moves=user_moves
    )
    
    # Create game state
    game_state = GameState(
        equalizer_strategy=None,
        round_idx=0,
        last_strategy_update=0,
        generated_mixed_moves_array=None,
        last_computer_move=None,
        grim_triggered=False
    )
    
    # Override num_rounds if provided
    actual_num_rounds = num_rounds if num_rounds is not None else computer_profile.num_rounds
    
    # Create game model
    game_model = GameModel(
        user_moves=user_moves,
        computer_moves=computer_moves,
        payoff_matrix=payoff_matrix,
        user_strategy_settings=strategy_settings,
        state=game_state,
        computer_profile_name=computer_profile_name,
        computer_profile={'name': computer_profile_name, 'settings': {}}
    )
    
    # Convert to dict for game_theory functions
    game_dict = game_model.to_dict()
    computer_profile_dict = computer_profile.to_dict()
    # Override num_rounds in profile if provided
    computer_profile_dict['num_rounds'] = actual_num_rounds
    game_dict['computer_profile'] = computer_profile_dict
    game_dict['num_rounds'] = actual_num_rounds
    
    # Run the game (disable logging for simulations to improve performance and reduce log size)
    logger.info(f"Running simulation {simulation_id}: {user_strategy} vs {computer_profile_name}")
    try:
        # Pass socketio if available for real-time updates during simulation
        # Use suite_simulation_id as the room ID so all updates go to the suite room
        result, iteration_moves = play_full_game(
            game_dict, 
            socketio=socketio, 
            game_id=suite_simulation_id or simulation_id, 
            round_delay=0.0, 
            enable_logging=False
        )
        
        final_user_payoff = result.get('final_user_payoff', 0.0)
        final_computer_payoff = result.get('final_computer_payoff', 0.0)
        
        # Determine winner - explicitly convert to Python bool to ensure JSON serializability
        user_won = bool(final_user_payoff > final_computer_payoff)
        payoff_difference = final_user_payoff - final_computer_payoff
        
        # Extract move history for move-level analysis
        move_history = []
        computer_moves_in_history = set()
        if iteration_moves:
            all_moves = iteration_moves.get_moves()
            # We need to get payoffs per round, but we don't have that in iteration_moves
            # So we'll just track move names for frequency analysis
            # For payoff analysis, we'd need to recalculate or store during game play
            for user_move, computer_move in all_moves:
                # Extract move names with proper handling
                if isinstance(computer_move, dict):
                    computer_move_name = computer_move.get('name', 'unknown')
                else:
                    computer_move_name = getattr(computer_move, 'name', 'unknown')
                
                if isinstance(user_move, dict):
                    user_move_name = user_move.get('name', 'unknown')
                else:
                    user_move_name = getattr(user_move, 'name', 'unknown')
                
                computer_moves_in_history.add(computer_move_name)
                
                move_history.append({
                    'user_move_name': user_move_name,
                    'user_move_type': user_move.get('type', 'unknown') if isinstance(user_move, dict) else getattr(user_move, 'type', 'unknown'),
                    'computer_move_name': computer_move_name,
                    'computer_move_type': computer_move.get('type', 'unknown') if isinstance(computer_move, dict) else getattr(computer_move, 'type', 'unknown')
                })
        
        # Debug logging for move extraction
        if computer_moves_in_history:
            logger.debug(f"Simulation {simulation_id}: Found {len(computer_moves_in_history)} unique computer moves in move_history: {sorted(computer_moves_in_history)}")
        
        # Emit per-simulation completion event for real-time updates
        if socketio and suite_simulation_id:
            _async_emit(socketio, 'simulation_single_complete', {
                'simulation_id': suite_simulation_id,
                'single_simulation_id': simulation_id,
                'user_strategy': user_strategy,
                'computer_profile': computer_profile_name,
                'final_user_payoff': float(final_user_payoff),
                'final_computer_payoff': float(final_computer_payoff),
                'num_rounds': actual_num_rounds,
                'user_won': user_won,
                'payoff_difference': float(payoff_difference)
            }, room=suite_simulation_id)
        
        return {
            'simulation_id': simulation_id,
            'user_strategy': user_strategy,
            'computer_profile': computer_profile_name,
            'final_user_payoff': float(final_user_payoff),
            'final_computer_payoff': float(final_computer_payoff),
            'num_rounds': actual_num_rounds,
            'user_won': user_won,
            'payoff_difference': float(payoff_difference),
            'move_history': move_history  # Add move history for analysis
        }
    except Exception as e:
        logger.error(f"Error in simulation {simulation_id}: {str(e)}")
        raise


def sample_discrete_weibull(q: float, beta: float, max_rounds: int = 1000) -> int:
    """
    Sample from a Discrete Weibull distribution.
    
    The Discrete Weibull distribution models the number of rounds until an event
    (e.g., trade war resolution) with a hazard-based approach.
    
    Survival function: S(k) = q^(k^beta) for k = 0, 1, 2, ...
    - For beta > 1: increasing hazard (fatigue - conflicts get harder to resolve)
    - For beta < 1: decreasing hazard (entrenchment - conflicts stabilize)
    - For beta = 1: constant hazard (exponential/geometric)
    
    Args:
        q: Scale parameter (0 < q < 1), controls base survival probability
        beta: Shape parameter (beta > 0), controls hazard behavior
        max_rounds: Maximum rounds to consider (safety limit)
        
    Returns:
        Positive integer number of rounds
    """
    # Generate uniform random variable
    u = np.random.uniform(0, 1)
    
    # Find k such that S(k) <= u < S(k-1)
    # S(k) = q^(k^beta), so we need q^(k^beta) <= u
    # Taking logs: k^beta * ln(q) <= ln(u)
    # Since ln(q) < 0, we have: k^beta >= ln(u) / ln(q)
    # Therefore: k >= (ln(u) / ln(q))^(1/beta)
    
    if u >= 1.0 or q <= 0 or q >= 1:
        return 1  # Safety fallback
    
    if beta <= 0:
        return 1  # Safety fallback
    
    # Calculate the minimum k that satisfies the condition
    # We solve: q^(k^beta) <= u
    # k^beta >= ln(u) / ln(q)
    # k >= (ln(u) / ln(q))^(1/beta)
    
    log_u = np.log(u)
    log_q = np.log(q)
    
    if log_q == 0:
        return 1
    
    # Calculate k using the inverse survival function
    k_power = log_u / log_q
    
    if k_power <= 0:
        return 1
    
    k = int(np.ceil(k_power ** (1.0 / beta)))
    
    # Ensure positive integer and within bounds
    k = max(1, min(k, max_rounds))
    
    return k


def sample_trade_war_rounds(
    rounds_mean: float,
    rounds_min: int = 1,
    rounds_max: int = 1000,
    num_samples: int = 1,
    normal_regime_prob: float = 0.8,
    normal_beta: float = 1.5,
    entrenched_beta: float = 0.7
) -> np.ndarray:
    """
    Sample trade war durations using a mixture model of two regimes.
    
    Model:
    - 80% normal/negotiable trade wars: increasing hazard (fatigue)
      * Conflicts get harder to resolve over time
      * Uses Discrete Weibull with beta > 1
    - 20% entrenched trade wars: decreasing hazard (entrenchment)
      * Conflicts stabilize and become persistent
      * Uses Discrete Weibull with beta < 1
    
    The q parameter is calibrated to match the desired rounds_mean.
    
    Args:
        rounds_mean: Target mean number of rounds
        rounds_min: Minimum number of rounds (default: 1)
        rounds_max: Hard cap on maximum rounds
        num_samples: Number of samples to generate
        normal_regime_prob: Probability of normal regime (default: 0.8)
        normal_beta: Beta parameter for normal regime (default: 1.5, increasing hazard)
        entrenched_beta: Beta parameter for entrenched regime (default: 0.7, decreasing hazard)
        
    Returns:
        Array of positive integers representing number of rounds, clamped to [rounds_min, rounds_max]
    """
    def calibrate_q(target_mean: float, beta: float, max_iter: int = 50) -> float:
        """
        Calibrate q to achieve target mean using binary search.
        
        For Discrete Weibull, lower q values produce longer durations.
        We use binary search to find q that gives the desired mean.
        Note: The calibration accounts for the rounds_min constraint by adjusting
        the target mean to be relative to the valid range.
        """
        q_low, q_high = 0.01, 0.99
        
        for _ in range(max_iter):
            q_mid = (q_low + q_high) / 2
            
            # Estimate mean by sampling (use smaller sample for speed)
            test_samples = [sample_discrete_weibull(q_mid, beta, rounds_max) for _ in range(500)]
            # Clamp samples to respect rounds_min
            test_samples = [max(rounds_min, min(s, rounds_max)) for s in test_samples]
            test_mean = np.mean(test_samples)
            
            if abs(test_mean - target_mean) < 0.5:
                return q_mid
            
            if test_mean < target_mean:
                q_high = q_mid  # Lower q means longer durations, need to decrease q
            else:
                q_low = q_mid
        
        return (q_low + q_high) / 2
    
    # Calibrate q for normal regime (target mean around rounds_mean)
    normal_q = calibrate_q(rounds_mean, normal_beta)
    
    # Calibrate q for entrenched regime (target mean slightly higher, but more variable)
    entrenched_q = calibrate_q(rounds_mean * 1.2, entrenched_beta)
    
    # Sample from mixture using vectorized approach where possible
    regime_choices = np.random.uniform(0, 1, size=num_samples)
    samples = []
    
    for i in range(num_samples):
        if regime_choices[i] < normal_regime_prob:
            # Normal regime: increasing hazard (fatigue)
            rounds = sample_discrete_weibull(normal_q, normal_beta, rounds_max)
        else:
            # Entrenched regime: decreasing hazard (stabilization)
            rounds = sample_discrete_weibull(entrenched_q, entrenched_beta, rounds_max)
        
        # Apply hard cap and ensure within [rounds_min, rounds_max] range
        rounds = max(rounds_min, min(rounds, rounds_max))
        samples.append(rounds)
    
    return np.array(samples, dtype=int)


def run_simulation_suite(
    base_game_config: Dict[str, Any],
    user_strategies: List[str],
    computer_profile_name: str,
    profile_manager: ProfileManager,
    num_simulations: int = 5000,
    rounds_mean: Optional[int] = None,
    rounds_std: Optional[float] = None,
    rounds_min: int = 50,
    rounds_max: int = 500,
    socketio=None,
    simulation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a Monte Carlo simulation suite: multiple user strategies against the computer profile.
    
    Uses a Monte Carlo approach where each simulation runs for a randomly sampled number of rounds,
    ensuring variability across runs and better stochastic coverage of outcomes.
    
    Args:
        base_game_config: Base game configuration dictionary (see run_single_simulation)
        user_strategies: List of user strategy types to test
        computer_profile_name: Name of the computer profile to use
        profile_manager: ProfileManager instance
        num_simulations: Number of simulations per strategy (default: 5000)
        rounds_mean: Mean number of rounds for random sampling (default: uses profile default or 200)
        rounds_std: Standard deviation for rounds distribution (default: 50)
        rounds_min: Minimum number of rounds (default: 50)
        rounds_max: Maximum number of rounds (default: 500)
        
    Returns:
        Dictionary with simulation suite results:
        {
            'computer_profile': str,
            'num_simulations': int,
            'rounds_statistics': {
                'mean': float,
                'std': float,
                'min': int,
                'max': int
            },
            'results': [
                {
                    'user_strategy': str,
                    'simulations': [result1, result2, ...],  # Note: large list
                    'average_user_payoff': float,
                    'average_computer_payoff': float,
                    'average_payoff_difference': float,
                    'win_rate': float,  # Percentage of simulations where user won
                    'std_user_payoff': float,  # Standard deviation of user payoffs
                    'std_computer_payoff': float,  # Standard deviation of computer payoffs
                    'move_statistics': {
                        'user_moves': {move_name: {frequency, frequency_percentage, average_payoff, win_rate, usage_count}},
                        'computer_moves': {move_name: {frequency, frequency_percentage, average_payoff, win_rate, usage_count}},
                        'move_combinations': {combo_key: {frequency, frequency_percentage, average_user_payoff, average_computer_payoff}}
                    }  # Move-level statistics for histograms
                },
                ...
            ],
            'summary': {
                'best_strategy': str,  # Strategy with highest average payoff
                'worst_strategy': str,  # Strategy with lowest average payoff
                'most_wins': str  # Strategy with highest win rate
            }
        }
    """
    # Get default rounds_mean from profile if not provided
    if rounds_mean is None:
        computer_profile = profile_manager.get_profile(computer_profile_name)
        if computer_profile:
            rounds_mean = computer_profile.num_rounds
        else:
            rounds_mean = 200  # Default fallback
    
    if rounds_std is None:
        rounds_std = 50.0  # Default standard deviation
    
    logger.info(f"Starting Monte Carlo simulation suite: {len(user_strategies)} strategies vs {computer_profile_name}")
    logger.info(f"Running {num_simulations} simulations per strategy")
    logger.info(f"Rounds distribution: mean={rounds_mean}, std={rounds_std}, range=[{rounds_min}, {rounds_max}]")
    
    all_results = []
    all_sampled_rounds = []
    total_strategies = len(user_strategies)
    total_simulations = total_strategies * num_simulations
    
    for strategy_idx, strategy in enumerate(user_strategies):
        logger.info(f"Running {num_simulations} simulations for strategy: {strategy}")
        
        # Emit strategy start progress
        if socketio and simulation_id:
            _async_emit(socketio, 'simulation_progress', {
                'simulation_id': simulation_id,
                'status': 'running',
                'current_strategy': strategy,
                'strategy_index': strategy_idx + 1,
                'total_strategies': total_strategies,
                'message': f'Running simulations for {strategy}...'
            }, room=simulation_id)
        
        strategy_results = []
        failed_simulations = []  # Track failed simulations with error details
        
        # Sample random number of rounds
        # If rounds_std is explicitly provided, use normal distribution (respects user's min/max/mean/std)
        # Otherwise, use mixture model of Discrete Weibull distributions for more realistic trade war durations
        if rounds_std is not None and rounds_std > 0:
            # Use normal distribution when user explicitly provides std (gives precise control)
            sampled_rounds = np.random.normal(loc=rounds_mean, scale=rounds_std, size=num_simulations)
            sampled_rounds = np.clip(sampled_rounds, rounds_min, rounds_max).astype(int)
        else:
            # Use mixture model of Discrete Weibull distributions:
            # - 80% normal/negotiable trade wars: increasing hazard (fatigue over time)
            # - 20% entrenched trade wars: decreasing hazard (stabilization/entrenchment)
            # The model better captures the stochastic nature of trade war durations
            sampled_rounds = sample_trade_war_rounds(
                rounds_mean=rounds_mean,
                rounds_min=rounds_min,
                rounds_max=rounds_max,
                num_samples=num_simulations,
                normal_regime_prob=0.8,  # 80% normal, 20% entrenched
                normal_beta=1.5,         # Increasing hazard (fatigue)
                entrenched_beta=0.7      # Decreasing hazard (entrenchment)
            )
        
        all_sampled_rounds.extend(sampled_rounds)
        
        # Run simulations independently for this strategy
        for sim_num in range(num_simulations):
            simulation_id = f"{strategy}_{computer_profile_name}_sim_{sim_num + 1}"
            random_num_rounds = int(sampled_rounds[sim_num])
            
            try:
                result = run_single_simulation(
                    base_game_config=base_game_config,
                    user_strategy=strategy,
                    computer_profile_name=computer_profile_name,
                    profile_manager=profile_manager,
                    num_rounds=random_num_rounds,
                    simulation_id=simulation_id,
                    socketio=socketio,
                    suite_simulation_id=simulation_id  # Pass suite ID for WebSocket room
                )
                strategy_results.append(result)
            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                error_details = {
                    'simulation_number': sim_num + 1,
                    'simulation_id': simulation_id,
                    'strategy': strategy,
                    'computer_profile': computer_profile_name,
                    'num_rounds': random_num_rounds,
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                    'traceback': error_traceback
                }
                failed_simulations.append(error_details)
                logger.warning(f"Simulation {simulation_id} failed: {str(e)}")
                logger.debug(f"Full traceback for {simulation_id}:\n{error_traceback}")
                # Continue with other simulations even if one fails
                continue
            
            # Log progress for long-running simulations and emit via WebSocket
            # Emit updates more frequently for real-time feedback (every 50-100 sims depending on total)
            progress_interval = max(50, min(100, num_simulations // 20))  # Adaptive interval
            if (sim_num + 1) % progress_interval == 0 or (sim_num + 1) == num_simulations:
                logger.info(f"  Progress: {sim_num + 1}/{num_simulations} simulations completed for {strategy}")
                if socketio and simulation_id:
                    completed_sims = strategy_idx * num_simulations + (sim_num + 1)
                    _async_emit(socketio, 'simulation_progress', {
                        'simulation_id': simulation_id,
                        'status': 'running',
                        'current_strategy': strategy,
                        'strategy_index': strategy_idx + 1,
                        'total_strategies': total_strategies,
                        'simulations_completed_for_strategy': sim_num + 1,
                        'total_simulations_for_strategy': num_simulations,
                        'total_completed': completed_sims,
                        'total_simulations': total_simulations,
                        'progress_percentage': (completed_sims / total_simulations * 100) if total_simulations > 0 else 0,
                        'message': f'Completed {sim_num + 1}/{num_simulations} simulations for {strategy}'
                    }, room=simulation_id)
        
        # Calculate statistics for this strategy
        if strategy_results:
            user_payoffs = np.array([r['final_user_payoff'] for r in strategy_results])
            computer_payoffs = np.array([r['final_computer_payoff'] for r in strategy_results])
            payoff_differences = np.array([r['payoff_difference'] for r in strategy_results])
            wins = np.array([r['user_won'] for r in strategy_results])
            
            avg_user_payoff = float(np.mean(user_payoffs))
            avg_computer_payoff = float(np.mean(computer_payoffs))
            avg_payoff_difference = float(np.mean(payoff_differences))
            std_user_payoff = float(np.std(user_payoffs))
            std_computer_payoff = float(np.std(computer_payoffs))
            win_rate = float(np.mean(wins) * 100)
            
            # Calculate move-level statistics for histograms
            move_stats = calculate_move_statistics(strategy_results, base_game_config['payoff_matrix'])
            
            strategy_result = {
                'user_strategy': strategy,
                'simulations': strategy_results,  # Note: contains all simulation results (may be large)
                'average_user_payoff': avg_user_payoff,
                'average_computer_payoff': avg_computer_payoff,
                'average_payoff_difference': avg_payoff_difference,
                'win_rate': win_rate,
                'std_user_payoff': std_user_payoff,
                'std_computer_payoff': std_computer_payoff,
                'num_successful_simulations': len(strategy_results),
                'num_failed_simulations': len(failed_simulations),
                'failed_simulations': failed_simulations,  # Include error details
                'move_statistics': move_stats  # Add move-level statistics for histograms
            }
            all_results.append(strategy_result)
            
            # Emit strategy completion progress and partial results
            if socketio and simulation_id:
                completed_sims = (strategy_idx + 1) * num_simulations
                _async_emit(socketio, 'simulation_progress', {
                    'simulation_id': simulation_id,
                    'status': 'running',
                    'current_strategy': strategy,
                    'strategy_index': strategy_idx + 1,
                    'total_strategies': total_strategies,
                    'strategy_completed': True,
                    'total_completed': completed_sims,
                    'total_simulations': total_simulations,
                    'progress_percentage': (completed_sims / total_simulations * 100) if total_simulations > 0 else 0,
                    'message': f'Completed all simulations for {strategy}'
                }, room=simulation_id)
                
                # Emit partial results for this strategy (so UI can show incremental results)
                _async_emit(socketio, 'simulation_strategy_result', {
                    'simulation_id': simulation_id,
                    'strategy_result': strategy_result,
                    'strategy_index': strategy_idx + 1,
                    'total_strategies': total_strategies
                }, room=simulation_id)
        else:
            logger.error(f"No successful simulations for strategy: {strategy}")
            all_results.append({
                'user_strategy': strategy,
                'simulations': [],
                'average_user_payoff': 0.0,
                'average_computer_payoff': 0.0,
                'average_payoff_difference': 0.0,
                'win_rate': 0.0,
                'std_user_payoff': 0.0,
                'std_computer_payoff': 0.0,
                'num_successful_simulations': 0,
                'num_failed_simulations': len(failed_simulations),
                'failed_simulations': failed_simulations  # Include error details even if all failed
            })
    
    # Create summary
    valid_results = [r for r in all_results if r['num_successful_simulations'] > 0]
    if valid_results:
        best_strategy = max(valid_results, key=lambda x: x['average_user_payoff'])['user_strategy']
        worst_strategy = min(valid_results, key=lambda x: x['average_user_payoff'])['user_strategy']
        most_wins = max(valid_results, key=lambda x: x['win_rate'])['user_strategy']
    else:
        best_strategy = worst_strategy = most_wins = None
    
    # Calculate rounds statistics
    rounds_stats = {
        'mean': float(np.mean(all_sampled_rounds)) if all_sampled_rounds else rounds_mean,
        'std': float(np.std(all_sampled_rounds)) if all_sampled_rounds else rounds_std,
        'min': int(np.min(all_sampled_rounds)) if all_sampled_rounds else rounds_min,
        'max': int(np.max(all_sampled_rounds)) if all_sampled_rounds else rounds_max
    }
    
    return {
        'computer_profile': computer_profile_name,
        'num_simulations': num_simulations,
        'rounds_statistics': rounds_stats,
        'results': all_results,
        'summary': {
            'best_strategy': best_strategy,
            'worst_strategy': worst_strategy,
            'most_wins': most_wins
        }
    }


def run_multi_profile_simulation(
    base_game_config: Dict[str, Any],
    user_strategies: List[str],
    computer_profiles: List[str],
    profile_manager: ProfileManager,
    num_simulations: int = 5000,
    rounds_mean: Optional[int] = None,
    rounds_std: Optional[float] = None,
    rounds_min: int = 50,
    rounds_max: int = 500
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulations across multiple computer profiles.
    
    Args:
        base_game_config: Base game configuration dictionary
        user_strategies: List of user strategy types to test
        computer_profiles: List of computer profile names to test against
        profile_manager: ProfileManager instance
        num_simulations: Number of simulations per strategy (default: 5000)
        rounds_mean: Mean number of rounds for random sampling (default: uses profile default or 200)
        rounds_std: Standard deviation for rounds distribution (default: 50)
        rounds_min: Minimum number of rounds (default: 50)
        rounds_max: Maximum number of rounds (default: 500)
        
    Returns:
        Dictionary with results organized by profile:
        {
            'profiles': {
                'profile_name_1': {suite_results},
                'profile_name_2': {suite_results},
                ...
            },
            'cross_profile_summary': {
                'best_strategy_overall': str,
                'strategy_averages': {strategy: avg_payoff}
            }
        }
    """
    logger.info(f"Starting multi-profile Monte Carlo simulation: {len(user_strategies)} strategies vs {len(computer_profiles)} profiles")
    
    profile_results = {}
    
    for profile_name in computer_profiles:
        suite_results = run_simulation_suite(
            base_game_config=base_game_config,
            user_strategies=user_strategies,
            computer_profile_name=profile_name,
            profile_manager=profile_manager,
            num_simulations=num_simulations,
            rounds_mean=rounds_mean,
            rounds_std=rounds_std,
            rounds_min=rounds_min,
            rounds_max=rounds_max
        )
        profile_results[profile_name] = suite_results
    
    # Cross-profile analysis
    strategy_totals = {strategy: [] for strategy in user_strategies}
    
    for profile_name, suite_results in profile_results.items():
        for strategy_result in suite_results['results']:
            strategy = strategy_result['user_strategy']
            strategy_totals[strategy].append(strategy_result['average_user_payoff'])
    
    # Find best strategy overall (highest average across all profiles)
    strategy_averages = {
        strategy: sum(payoffs) / len(payoffs) if payoffs else 0.0
        for strategy, payoffs in strategy_totals.items()
    }
    
    best_strategy_overall = max(strategy_averages, key=strategy_averages.get) if strategy_averages else None
    
    return {
        'profiles': profile_results,
        'cross_profile_summary': {
            'best_strategy_overall': best_strategy_overall,
            'strategy_averages': strategy_averages
        }
    }


# Convenience function to create a default game config from moves
def create_default_game_config(
    move_names: List[str],
    move_types: Optional[Dict[str, str]] = None,
    payoff_matrix: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a default game configuration from move names.
    
    Args:
        move_names: List of move names (assumed available for both user and computer)
        move_types: Optional dict mapping move names to types ('cooperative', 'defective', 'mixed')
        payoff_matrix: Optional custom payoff matrix. If None, creates a simple default matrix.
        
    Returns:
        Base game configuration dictionary
    """
    # Default move types (Prisoner's Dilemma-like)
    if move_types is None:
        move_types = {}
        for move in move_names:
            if 'cooperat' in move.lower() or 'dialogue' in move.lower() or 'wait' in move.lower():
                move_types[move] = 'cooperative'
            elif 'tariff' in move.lower() or 'defect' in move.lower() or 'attack' in move.lower():
                move_types[move] = 'defective'
            else:
                move_types[move] = 'cooperative'  # Default to cooperative
    
    # Create moves
    user_moves = [
        {
            'name': name,
            'type': move_types.get(name, 'cooperative'),
            'probability': 1.0 / len(move_names),
            'player': 'user'
        }
        for name in move_names
    ]
    
    computer_moves = [
        {
            'name': name,
            'type': move_types.get(name, 'cooperative'),
            'probability': 1.0 / len(move_names),
            'player': 'computer'
        }
        for name in move_names
    ]
    
    # Create default payoff matrix if not provided
    if payoff_matrix is None:
        payoff_matrix = []
        # Simple default: mutual cooperation = 3,3; mutual defection = 1,1; 
        # one cooperates other defects = 0,5 or 5,0
        for user_move in move_names:
            for computer_move in move_names:
                user_type = move_types.get(user_move, 'cooperative')
                comp_type = move_types.get(computer_move, 'cooperative')
                
                if user_type == 'cooperative' and comp_type == 'cooperative':
                    payoff = {'user': 3, 'computer': 3}
                elif user_type == 'cooperative' and comp_type == 'defective':
                    payoff = {'user': 0, 'computer': 5}
                elif user_type == 'defective' and comp_type == 'cooperative':
                    payoff = {'user': 5, 'computer': 0}
                else:  # both defective
                    payoff = {'user': 1, 'computer': 1}
                
                payoff_matrix.append({
                    'user_move_name': user_move,
                    'computer_move_name': computer_move,
                    'payoff': payoff
                })
    
    return {
        'user_moves': user_moves,
        'computer_moves': computer_moves,
        'payoff_matrix': payoff_matrix
    }

