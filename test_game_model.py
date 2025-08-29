import pytest
from game_model import GameModel, Move, MoveType, PlayerType, PayoffEntry, UserStrategySettings, StrategyType, GameState
from game_theory import play_full_game


def test_game_model_with_play_full_game():
    """Test that GameModel works correctly with play_full_game function"""
    
    # Create a simple game model
    game_model = GameModel(
        user_moves=[
            Move(
                name="open_dialogue",
                type=MoveType.COOPERATIVE,
                probability=0.5,
                player=PlayerType.USER
            ),
            Move(
                name="raise_tariffs",
                type=MoveType.DEFECTIVE,
                probability=0.5,
                player=PlayerType.USER
            )
        ],
        computer_moves=[
            Move(
                name="open_dialogue",
                type=MoveType.COOPERATIVE,
                probability=0.5,
                player=PlayerType.COMPUTER
            ),
            Move(
                name="raise_tariffs",
                type=MoveType.DEFECTIVE,
                probability=0.5,
                player=PlayerType.COMPUTER
            )
        ],
        payoff_matrix=[
            PayoffEntry(
                user_move_name="open_dialogue",
                computer_move_name="open_dialogue",
                payoff={"user": 3, "computer": 3}
            ),
            PayoffEntry(
                user_move_name="open_dialogue",
                computer_move_name="raise_tariffs",
                payoff={"user": 0, "computer": 5}
            ),
            PayoffEntry(
                user_move_name="raise_tariffs",
                computer_move_name="open_dialogue",
                payoff={"user": 5, "computer": 0}
            ),
            PayoffEntry(
                user_move_name="raise_tariffs",
                computer_move_name="raise_tariffs",
                payoff={"user": 1, "computer": 1}
            )
        ],
        user_strategy_settings=UserStrategySettings(
            strategy=StrategyType.COPY_CAT,
            first_move="open_dialogue",
            cooperation_start=2,
            mixed_strategy_array=None
        ),
        state=GameState(
            equalizer_strategy=None,
            round_idx=0,
            last_strategy_update=0,
            generated_mixed_moves_array=None,
            last_computer_move=None
        )
    )
    
    # Test that the model was created successfully
    assert len(game_model.user_moves) == 2
    assert len(game_model.computer_moves) == 2
    assert len(game_model.payoff_matrix) == 4
    assert game_model.user_strategy_settings.strategy == StrategyType.COPY_CAT
    
    # Convert to dict and test with play_full_game
    game_dict = game_model.to_dict()
    
    # Test that play_full_game runs without errors
    payoff_outcome, iteration_moves = play_full_game(game_dict)
    
    # Test that we get expected results
    assert 'final_user_payoff' in payoff_outcome
    assert 'final_computer_payoff' in payoff_outcome
    assert isinstance(payoff_outcome['final_user_payoff'], (int, float))
    assert isinstance(payoff_outcome['final_computer_payoff'], (int, float))
    assert payoff_outcome['final_user_payoff'] >= 0
    assert payoff_outcome['final_computer_payoff'] >= 0
    
    print(f"Test passed! Final payoffs - User: {payoff_outcome['final_user_payoff']:.2f}, Computer: {payoff_outcome['final_computer_payoff']:.2f}")


def test_game_model_validation():
    """Test that GameModel validation works correctly"""
    
    # Test with invalid data - should raise validation error
    with pytest.raises(ValueError):
        GameModel(
            user_moves=[
                Move(
                    name="open_dialogue",
                    type=MoveType.COOPERATIVE,
                    probability=1.5,  # Invalid probability > 1
                    player=PlayerType.USER
                )
            ],
            computer_moves=[
                Move(
                    name="open_dialogue",
                    type=MoveType.COOPERATIVE,
                    probability=0.5,
                    player=PlayerType.COMPUTER
                )
            ],
            payoff_matrix=[
                PayoffEntry(
                    user_move_name="open_dialogue",
                    computer_move_name="open_dialogue",
                    payoff={"user": 3, "computer": 3}
                )
            ],
            user_strategy_settings=UserStrategySettings(
                strategy=StrategyType.COPY_CAT,
                first_move="open_dialogue",
                cooperation_start=2,
                mixed_strategy_array=None
            )
        )


def test_game_model_from_dict():
    """Test creating GameModel from dictionary"""
    
    game_data = {
        "user_moves": [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                "player": "user"
            }
        ],
        "computer_moves": [
            {
                "name": "open_dialogue",
                "type": "cooperative",
                "probability": 0.5,
                "player": "computer"
            }
        ],
        "payoff_matrix": [
            {
                "user_move_name": "open_dialogue",
                "computer_move_name": "open_dialogue",
                "payoff": {"user": 3, "computer": 3}
            }
        ],
        "user_strategy_settings": {
            "strategy": "copy_cat",
            "first_move": "open_dialogue",
            "cooperation_start": 2,
            "mixed_strategy_array": None
        },
        "state": {
            "equalizer_strategy": None,
            "round_idx": 0,
            "last_strategy_update": 0,
            "generated_mixed_moves_array": None,
            "last_computer_move": None
        }
    }
    
    # Test creating from dict
    game_model = GameModel.from_dict(game_data)
    assert game_model.user_moves[0].name == "open_dialogue"
    assert game_model.computer_moves[0].name == "open_dialogue"
    assert game_model.user_strategy_settings.strategy == StrategyType.COPY_CAT
    
    # Test converting back to dict
    game_dict = game_model.to_dict()
    assert game_dict["user_moves"][0]["name"] == "open_dialogue"
    assert game_dict["computer_moves"][0]["name"] == "open_dialogue"


if __name__ == "__main__":
    # Run the tests
    print("Running GameModel tests...")
    
    test_game_model_with_play_full_game()
    print("✓ GameModel with play_full_game test passed")
    
    test_game_model_validation()
    print("✓ GameModel validation test passed")
    
    test_game_model_from_dict()
    print("✓ GameModel from_dict test passed")
    
    print("\nAll tests passed! 🎉") 