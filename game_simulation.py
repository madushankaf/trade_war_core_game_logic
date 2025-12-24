"""
Game Simulation Module

This module provides functionality to run automated simulations of games
where different user strategies are tested against the computer's core game logic.
"""

from typing import Dict, List, Optional, Tuple, Any
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
        first_move_name: Name of the first move (if None, uses first cooperative move or first move)
        cooperation_start: Round when cooperation starts (for tit_for_tat, grim_trigger)
        mixed_strategy_array: Array of move names for mixed strategy (if None, uses all moves)
        
    Returns:
        UserStrategySettings object
    """
    # Determine first move if not specified
    if first_move_name is None:
        # Try to find a cooperative move, otherwise use first move
        cooperative_moves = [move for move in user_moves if move.type == MoveType.COOPERATIVE]
        if cooperative_moves:
            first_move_name = cooperative_moves[0].name
        else:
            first_move_name = user_moves[0].name if user_moves else None
    
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
    simulation_id: Optional[str] = None
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
            'payoff_difference': float
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
        result, iteration_moves = play_full_game(game_dict, socketio=None, game_id=simulation_id, round_delay=0.0, enable_logging=False)
        
        final_user_payoff = result.get('final_user_payoff', 0.0)
        final_computer_payoff = result.get('final_computer_payoff', 0.0)
        
        # Determine winner
        user_won = final_user_payoff > final_computer_payoff
        payoff_difference = final_user_payoff - final_computer_payoff
        
        return {
            'simulation_id': simulation_id,
            'user_strategy': user_strategy,
            'computer_profile': computer_profile_name,
            'final_user_payoff': float(final_user_payoff),
            'final_computer_payoff': float(final_computer_payoff),
            'num_rounds': actual_num_rounds,
            'user_won': user_won,
            'payoff_difference': float(payoff_difference)
        }
    except Exception as e:
        logger.error(f"Error in simulation {simulation_id}: {str(e)}")
        raise


def run_simulation_suite(
    base_game_config: Dict[str, Any],
    user_strategies: List[str],
    computer_profile_name: str,
    profile_manager: ProfileManager,
    num_simulations: int = 5000,
    rounds_mean: Optional[int] = None,
    rounds_std: Optional[float] = None,
    rounds_min: int = 50,
    rounds_max: int = 500
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
                    'std_computer_payoff': float  # Standard deviation of computer payoffs
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
    
    for strategy in user_strategies:
        logger.info(f"Running {num_simulations} simulations for strategy: {strategy}")
        strategy_results = []
        
        # Sample random number of rounds for each simulation using normal distribution
        # Clip to ensure values are within [rounds_min, rounds_max] range
        sampled_rounds = np.random.normal(loc=rounds_mean, scale=rounds_std, size=num_simulations)
        sampled_rounds = np.clip(sampled_rounds, rounds_min, rounds_max).astype(int)
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
                    simulation_id=simulation_id
                )
                strategy_results.append(result)
            except Exception as e:
                logger.warning(f"Simulation {simulation_id} failed: {str(e)}")
                # Continue with other simulations even if one fails
                continue
            
            # Log progress for long-running simulations
            if (sim_num + 1) % 500 == 0:
                logger.info(f"  Progress: {sim_num + 1}/{num_simulations} simulations completed for {strategy}")
        
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
            
            all_results.append({
                'user_strategy': strategy,
                'simulations': strategy_results,  # Note: contains all simulation results (may be large)
                'average_user_payoff': avg_user_payoff,
                'average_computer_payoff': avg_computer_payoff,
                'average_payoff_difference': avg_payoff_difference,
                'win_rate': win_rate,
                'std_user_payoff': std_user_payoff,
                'std_computer_payoff': std_computer_payoff,
                'num_successful_simulations': len(strategy_results)
            })
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
                'num_successful_simulations': 0
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

