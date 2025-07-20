# Trade War Game Theory

A Python implementation of game theory algorithms for trade war scenarios, including Nash equilibrium calculations, mixed strategy analysis, and various game strategies.

## Features

- **Pure Strategy Analysis**: Dominant move detection and payoff calculations
- **Mixed Strategy Support**: Probability-based move selection and indifference calculations
- **Game Strategies**: Copy-cat, tit-for-tat, grim trigger, and mixed strategies
- **Nash Equilibrium**: Finding optimal strategies for both players
- **Security Level Responses**: Minimax strategy implementation
- **Full Game Simulation**: Complete game rounds with strategy evolution

## Installation

```bash
pip install numpy pytest
```

## Running Tests

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install pytest numpy
```

### Running All Tests

To run all tests in the project:

```bash
pytest
```

### Running Specific Test File

To run only the game theory tests:

```bash
pytest test_game_theory.py
```

### Running Specific Test Functions

To run a specific test function:

```bash
# Run dominant move tests
pytest test_game_theory.py::test_check_dominant_move_pure

# Run payoff calculation tests
pytest test_game_theory.py::test_calculate_payoff_pure

# Run Nash equilibrium tests
pytest test_game_theory.py::test_nash_equilibrium_strategy_pure

# Run full game simulation tests
pytest test_game_theory.py::test_play_full_game
```

### Running Tests with Verbose Output

To see detailed test output:

```bash
pytest -v test_game_theory.py
```

### Running Tests with Print Statements

To see print statements from tests:

```bash
pytest -s test_game_theory.py
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pip install pytest-cov
pytest --cov=game_theory test_game_theory.py
```

## Test Categories

The test suite includes comprehensive tests for:

### Core Game Theory Functions
- `test_check_dominant_move_pure`: Tests dominant move detection
- `test_is_the_move_with_the_better_payoff_pure`: Tests payoff comparisons
- `test_calculate_payoff_pure` / `test_calculate_payoff_mixed`: Tests payoff calculations

### Strategy Analysis
- `test_find_best_response_using_epsilon_greedy_pure` / `test_find_best_response_using_epsilon_greedy_mixed`: Tests epsilon-greedy best response
- `test_nash_equilibrium_strategy_pure`: Tests Nash equilibrium finding
- `test_solve_mixed_strategy_indifference_general`: Tests mixed strategy indifference

### Game Strategies
- `test_get_copy_cat_move`: Tests copy-cat strategy
- `test_get_security_level_response`: Tests security level responses
- `test_get_next_move_based_on_strategy_settings`: Tests various strategy implementations

### Game Simulation
- `test_play_game_round`: Tests individual game rounds
- `test_play_full_game`: Tests complete game simulations

## Test Data

The tests use predefined fixtures including:

- **Pure Strategy Moves**: Cooperative and defective moves with probability 1.0
- **Mixed Strategy Moves**: Moves with varying probabilities
- **Payoff Matrices**: Different game scenarios with user/computer payoffs
- **Strategy Settings**: Various strategy configurations for testing

## Example Test Output

```
============================= test session starts ==============================
platform darwin -- Python 3.x.x, pytest-x.x.x, pluggy-x.x.x
rootdir: /path/to/trade_war_core_game_logic
plugins: hypothesis-x.x.x, cov-x.x.x
collected 15 items

test_game_theory.py ................                                    [100%]

============================== 15 passed in 2.34s ==============================
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure `game_theory.py` is in the same directory as the test file
2. **Missing Dependencies**: Install required packages with `pip install pytest numpy`
3. **Test Failures**: Check that the game theory functions are properly implemented

### Debug Mode

To run tests in debug mode with more detailed output:

```bash
pytest -vvv --tb=long test_game_theory.py
```

## Contributing

When adding new features, please ensure:

1. Add corresponding tests in `test_game_theory.py`
2. Follow the existing test naming conventions
3. Include both positive and negative test cases
4. Test edge cases and error conditions
5. Run the full test suite before submitting changes

## License

[Add your license information here]
