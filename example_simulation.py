"""
Example script demonstrating how to use the game simulation module.

This script shows how to run simulations of different user strategies
against the computer's core game logic.
"""

from game_simulation import (
    run_single_simulation,
    run_simulation_suite,
    run_multi_profile_simulation,
    create_default_game_config
)
from profile_manager import ProfileManager

# Initialize profile manager
profile_manager = ProfileManager()


def example_single_simulation():
    """Example: Run a single simulation"""
    print("=" * 60)
    print("Example 1: Single Simulation")
    print("=" * 60)
    
    # Create a base game configuration
    base_config = create_default_game_config(
        move_names=['open_dialogue', 'raise_tariffs', 'wait_and_see'],
        move_types={
            'open_dialogue': 'cooperative',
            'raise_tariffs': 'defective',
            'wait_and_see': 'cooperative'
        }
    )
    
    # Run a single simulation: tit_for_tat strategy vs Hawkish profile
    result = run_single_simulation(
        base_game_config=base_config,
        user_strategy='tit_for_tat',
        computer_profile_name='Hawkish',
        profile_manager=profile_manager,
        num_rounds=100  # Override default 200 rounds
    )
    
    print(f"\nSimulation Result:")
    print(f"  Strategy: {result['user_strategy']}")
    print(f"  Computer Profile: {result['computer_profile']}")
    print(f"  Rounds: {result['num_rounds']}")
    print(f"  User Payoff: {result['final_user_payoff']:.2f}")
    print(f"  Computer Payoff: {result['final_computer_payoff']:.2f}")
    print(f"  Payoff Difference: {result['payoff_difference']:.2f}")
    print(f"  User Won: {'Yes' if result['user_won'] else 'No'}")
    print()


def example_simulation_suite():
    """Example: Run multiple strategies against one computer profile"""
    print("=" * 60)
    print("Example 2: Simulation Suite (Multiple Strategies)")
    print("=" * 60)
    
    # Create a base game configuration
    base_config = create_default_game_config(
        move_names=['open_dialogue', 'raise_tariffs'],
        move_types={
            'open_dialogue': 'cooperative',
            'raise_tariffs': 'defective'
        }
    )
    
    # Test multiple strategies
    strategies = ['copy_cat', 'tit_for_tat', 'grim_trigger', 'random']
    
    suite_results = run_simulation_suite(
        base_game_config=base_config,
        user_strategies=strategies,
        computer_profile_name='Dovish',
        profile_manager=profile_manager,
        num_simulations=100,  # Reduced for example (default is 5000)
        rounds_mean=50,
        rounds_std=15,
        rounds_min=20,
        rounds_max=100
    )
    
    print(f"\nSimulation Suite Results:")
    print(f"  Computer Profile: {suite_results['computer_profile']}")
    print(f"  Simulations per strategy: {suite_results['num_simulations']}")
    print(f"  Rounds statistics: {suite_results['rounds_statistics']}")
    print(f"\n  Strategy Results:")
    
    for result in suite_results['results']:
        print(f"    {result['user_strategy']}:")
        print(f"      Avg User Payoff: {result['average_user_payoff']:.2f} (std: {result['std_user_payoff']:.2f})")
        print(f"      Avg Computer Payoff: {result['average_computer_payoff']:.2f} (std: {result['std_computer_payoff']:.2f})")
        print(f"      Win Rate: {result['win_rate']:.1f}%")
        print(f"      Successful simulations: {result['num_successful_simulations']}")
    
    print(f"\n  Summary:")
    print(f"    Best Strategy (by avg payoff): {suite_results['summary']['best_strategy']}")
    print(f"    Worst Strategy: {suite_results['summary']['worst_strategy']}")
    print(f"    Most Wins: {suite_results['summary']['most_wins']}")
    print()


def example_multi_profile_simulation():
    """Example: Run strategies against multiple computer profiles"""
    print("=" * 60)
    print("Example 3: Multi-Profile Simulation")
    print("=" * 60)
    
    # Create a base game configuration
    base_config = create_default_game_config(
        move_names=['open_dialogue', 'raise_tariffs', 'wait_and_see'],
        move_types={
            'open_dialogue': 'cooperative',
            'raise_tariffs': 'defective',
            'wait_and_see': 'cooperative'
        }
    )
    
    # Test strategies against multiple profiles
    strategies = ['tit_for_tat', 'grim_trigger', 'random']
    profiles = ['Hawkish', 'Dovish', 'Opportunist']
    
    multi_results = run_multi_profile_simulation(
        base_game_config=base_config,
        user_strategies=strategies,
        computer_profiles=profiles,
        profile_manager=profile_manager,
        num_simulations=50,  # Reduced for example (default is 5000)
        rounds_mean=100,
        rounds_std=30,
        rounds_min=50,
        rounds_max=200
    )
    
    print(f"\nMulti-Profile Simulation Results:")
    print(f"  Profiles tested: {', '.join(profiles)}")
    print(f"  Strategies tested: {', '.join(strategies)}")
    
    print(f"\n  Results by Profile:")
    for profile_name, suite_results in multi_results['profiles'].items():
        print(f"\n    {profile_name}:")
        for result in suite_results['results']:
            print(f"      {result['user_strategy']}: "
                  f"Avg Payoff = {result['average_user_payoff']:.2f}, "
                  f"Win Rate = {result['win_rate']:.1f}%")
    
    print(f"\n  Cross-Profile Summary:")
    print(f"    Best Strategy Overall: {multi_results['cross_profile_summary']['best_strategy_overall']}")
    print(f"    Strategy Averages Across All Profiles:")
    for strategy, avg_payoff in multi_results['cross_profile_summary']['strategy_averages'].items():
        print(f"      {strategy}: {avg_payoff:.2f}")
    print()


def example_custom_game_config():
    """Example: Using a custom game configuration"""
    print("=" * 60)
    print("Example 4: Custom Game Configuration")
    print("=" * 60)
    
    # Create a custom game configuration with specific payoff matrix
    custom_config = {
        'user_moves': [
            {
                'name': 'cooperate',
                'type': 'cooperative',
                'probability': 0.5,
                'player': 'user'
            },
            {
                'name': 'defect',
                'type': 'defective',
                'probability': 0.5,
                'player': 'user'
            }
        ],
        'computer_moves': [
            {
                'name': 'cooperate',
                'type': 'cooperative',
                'probability': 0.5,
                'player': 'computer'
            },
            {
                'name': 'defect',
                'type': 'defective',
                'probability': 0.5,
                'player': 'computer'
            }
        ],
        'payoff_matrix': [
            {
                'user_move_name': 'cooperate',
                'computer_move_name': 'cooperate',
                'payoff': {'user': 3, 'computer': 3}
            },
            {
                'user_move_name': 'cooperate',
                'computer_move_name': 'defect',
                'payoff': {'user': 0, 'computer': 5}
            },
            {
                'user_move_name': 'defect',
                'computer_move_name': 'cooperate',
                'payoff': {'user': 5, 'computer': 0}
            },
            {
                'user_move_name': 'defect',
                'computer_move_name': 'defect',
                'payoff': {'user': 1, 'computer': 1}
            }
        ]
    }
    
    # Run simulation with custom config
    result = run_single_simulation(
        base_game_config=custom_config,
        user_strategy='copy_cat',
        computer_profile_name='TitForTatPlus',
        profile_manager=profile_manager,
        num_rounds=200
    )
    
    print(f"\nCustom Config Simulation Result:")
    print(f"  Strategy: {result['user_strategy']}")
    print(f"  Computer Profile: {result['computer_profile']}")
    print(f"  Final User Payoff: {result['final_user_payoff']:.2f}")
    print(f"  Final Computer Payoff: {result['final_computer_payoff']:.2f}")
    print(f"  User Won: {'Yes' if result['user_won'] else 'No'}")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Game Simulation Examples")
    print("=" * 60 + "\n")
    
    try:
        # Run examples
        example_single_simulation()
        example_simulation_suite()
        example_multi_profile_simulation()
        example_custom_game_config()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()

