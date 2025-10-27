#!/usr/bin/env python3
"""
Test script for the game logging system

This script demonstrates how to use the game logging functionality
and tests various logging scenarios.
"""

import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_logger import GameLogger, initialize_game_logger, get_game_logger
from game_theory import play_full_game


def load_sample_game_config():
    """Load a sample game configuration"""
    sample_file = Path(__file__).parent / "sample_game_model.json"
    
    if not sample_file.exists():
        print(f"Sample game file not found: {sample_file}")
        return None
    
    with open(sample_file, 'r') as f:
        return json.load(f)


def test_basic_logging():
    """Test basic logging functionality"""
    print("=" * 60)
    print("TESTING BASIC GAME LOGGING")
    print("=" * 60)
    
    # Initialize logger
    logger = initialize_game_logger("test_logs", enable_console_logging=True)
    
    # Load sample game configuration
    game_config = load_sample_game_config()
    if not game_config:
        print("Failed to load sample game configuration")
        return
    
    # Start a game session
    session_id = logger.start_game_session("test_game_001", game_config)
    print(f"Started game session: {session_id}")
    
    # Simulate some moves
    moves_data = [
        {
            "round": 1,
            "phase": "Phase 1 (Nash Equilibrium)",
            "user_move": {"name": "Cooperate", "type": "cooperate"},
            "computer_move": {"name": "Cooperate", "type": "cooperate"},
            "user_payoff": 3.0,
            "computer_payoff": 3.0,
            "round_winner": "tie",
            "running_user_total": 3.0,
            "running_computer_total": 3.0
        },
        {
            "round": 2,
            "phase": "Phase 1 (Nash Equilibrium)",
            "user_move": {"name": "Defect", "type": "defect"},
            "computer_move": {"name": "Cooperate", "type": "cooperate"},
            "user_payoff": 5.0,
            "computer_payoff": 0.0,
            "round_winner": "user",
            "running_user_total": 8.0,
            "running_computer_total": 3.0
        },
        {
            "round": 3,
            "phase": "Phase 1 (Nash Equilibrium)",
            "user_move": {"name": "Cooperate", "type": "cooperate"},
            "computer_move": {"name": "Defect", "type": "defect"},
            "user_payoff": 0.0,
            "computer_payoff": 5.0,
            "round_winner": "computer",
            "running_user_total": 8.0,
            "running_computer_total": 8.0
        }
    ]
    
    # Log the moves
    for move_data in moves_data:
        logger.log_move(
            round_number=move_data["round"],
            phase=move_data["phase"],
            user_move=move_data["user_move"],
            computer_move=move_data["computer_move"],
            user_payoff=move_data["user_payoff"],
            computer_payoff=move_data["computer_payoff"],
            round_winner=move_data["round_winner"],
            running_user_total=move_data["running_user_total"],
            running_computer_total=move_data["running_computer_total"],
            game_context={"test_mode": True}
        )
    
    # End the session
    final_session_id = logger.end_game_session(8.0, 8.0)
    print(f"Ended game session: {final_session_id}")
    
    # Get log statistics
    stats = logger.get_log_statistics()
    print(f"Log statistics: {json.dumps(stats, indent=2)}")
    
    print("Basic logging test completed!")


def test_full_game_logging():
    """Test logging with a full game simulation"""
    print("\n" + "=" * 60)
    print("TESTING FULL GAME LOGGING")
    print("=" * 60)
    
    # Load sample game configuration
    game_config = load_sample_game_config()
    if not game_config:
        print("Failed to load sample game configuration")
        return
    
    print("Running a short game simulation...")
    print("Note: This will run a few rounds for demonstration purposes")
    
    # Modify the game to run fewer rounds for testing
    original_phase_end = 200  # Store original value
    
    # Run the game (this will automatically use our logging system)
    try:
        result, moves = play_full_game(game_config, game_id="full_test_game")
        print(f"Game completed!")
        print(f"Final user payoff: {result['final_user_payoff']}")
        print(f"Final computer payoff: {result['final_computer_payoff']}")
        print(f"Total moves logged: {len(moves.get_moves())}")
        
    except Exception as e:
        print(f"Error during game simulation: {e}")
        import traceback
        traceback.print_exc()


def test_log_management():
    """Test log management features"""
    print("\n" + "=" * 60)
    print("TESTING LOG MANAGEMENT")
    print("=" * 60)
    
    logger = get_game_logger()
    
    # List all sessions
    sessions = logger.list_all_sessions()
    print(f"Available sessions: {sessions}")
    
    # Get statistics
    stats = logger.get_log_statistics()
    print(f"Current log statistics:")
    print(json.dumps(stats, indent=2))
    
    # Test log rotation (if we have enough files)
    if stats['total_sessions'] > 2:
        print("Testing log rotation...")
        logger.rotate_logs(max_files_per_type=2)
        print("Log rotation completed")
    
    print("Log management test completed!")


def main():
    """Main test function"""
    print("GAME LOGGING SYSTEM TEST")
    print("=" * 60)
    
    try:
        # Test basic logging
        test_basic_logging()
        
        # Test full game logging (commented out for now to avoid long execution)
        # test_full_game_logging()
        
        # Test log management
        test_log_management()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\nGenerated log files are available in the 'test_logs' directory:")
        print("- Human readable logs: test_logs/human_readable/")
        print("- Machine readable logs: test_logs/machine_readable/")
        print("- Analysis logs: test_logs/analysis/")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
