# Game Logging System Documentation

## Overview

The Trade War Game Theory simulation now includes a comprehensive logging system that captures all player moves, strategies, and outcomes in both human-readable and machine-readable formats. This system enables detailed analysis of game scenarios and player interactions.

## Features

### 🎯 **Comprehensive Logging**
- **Move-by-move tracking** with timestamps and context
- **Phase-based analysis** (Nash Equilibrium, Greedy Response, Mixed Strategy)
- **Payoff calculations** and running totals
- **Game session management** with unique identifiers

### 📊 **Multiple Output Formats**
- **Human-readable logs** (.txt) for easy reading and debugging
- **Machine-readable logs** (.json) for programmatic analysis
- **Analysis logs** (.csv) for statistical analysis and data science

### 🔧 **Advanced Features**
- **Log rotation** to prevent disk space issues
- **Automatic cleanup** of old log files
- **Thread-safe logging** for concurrent games
- **Statistics tracking** and session management

## File Structure

```
game_logs/
├── human_readable/          # Human-readable game logs
│   ├── session_id_human.txt
│   └── ...
├── machine_readable/        # JSON format for analysis
│   ├── session_id_machine.json
│   └── ...
├── analysis/               # CSV format for data science
│   ├── session_id_analysis.csv
│   └── ...
└── game_log_YYYYMMDD.log   # Daily consolidated logs
```

## Usage Examples

### Basic Usage

The logging system is automatically integrated into the game flow. When you run a game, logs are automatically generated:

```python
from game_theory import play_full_game
from game_logger import get_game_logger

# Run a game - logging happens automatically
result, moves = play_full_game(game_config, game_id="my_game")

# Access the logger for additional operations
logger = get_game_logger()
sessions = logger.list_all_sessions()
print(f"Available sessions: {sessions}")
```

### Manual Logging

You can also use the logging system manually:

```python
from game_logger import initialize_game_logger

# Initialize logger
logger = initialize_game_logger("my_logs", enable_console_logging=True)

# Start a session
session_id = logger.start_game_session("game_001", game_config)

# Log individual moves
logger.log_move(
    round_number=1,
    phase="Phase 1 (Nash Equilibrium)",
    user_move={"name": "Cooperate", "type": "cooperate"},
    computer_move={"name": "Defect", "type": "defect"},
    user_payoff=0.0,
    computer_payoff=5.0,
    round_winner="computer",
    running_user_total=0.0,
    running_computer_total=5.0,
    game_context={"strategy": "copy_cat"}
)

# End the session
logger.end_game_session(final_user_payoff=100.0, final_computer_payoff=95.0)
```

### Log Analysis

Use the analysis tools to examine logged data:

```python
from analyze_game_logs import GameLogAnalyzer

# Initialize analyzer
analyzer = GameLogAnalyzer("game_logs")

# Generate analysis report
analyzer.generate_analysis_report("my_analysis.txt")

# Export to CSV for further analysis
analyzer.export_to_csv("game_data.csv")

# Load specific session data
session_data = analyzer.load_session_data("session_id")
analysis = analyzer.analyze_move_patterns(session_data)
```

## Log File Formats

### Human-Readable Format (.txt)

```
================================================================================
TRADE WAR GAME THEORY SIMULATION - GAME SESSION LOG
================================================================================

Session ID: game_001_20251024_164010
Start Time: 2025-10-24T16:40:10.714021
End Time: 2025-10-24T16:40:10.714468
Total Rounds: 200
Final User Payoff: 850.50
Final Computer Payoff: 820.25

GAME ANALYSIS:
----------------------------------------
User Wins: 95
Computer Wins: 89
Ties: 16
Average User Payoff per Round: 4.25
Average Computer Payoff per Round: 4.10

MOVE-BY-MOVE LOG:
----------------------------------------
Round 1 (Phase 1 (Nash Equilibrium)) - 2025-10-24T16:40:10.714203
  User Move: Cooperate (cooperate) - Payoff: 3.00
  Computer Move: Cooperate (cooperate) - Payoff: 3.00
  Round Winner: tie
  Running Totals - User: 3.00, Computer: 3.00
```

### Machine-Readable Format (.json)

```json
{
  "session_id": "game_001_20251024_164010",
  "start_time": "2025-10-24T16:40:10.714021",
  "end_time": "2025-10-24T16:40:10.714468",
  "total_rounds": 200,
  "final_user_payoff": 850.50,
  "final_computer_payoff": 820.25,
  "game_config": { ... },
  "moves": [
    {
      "timestamp": "2025-10-24T16:40:10.714203",
      "round_number": 1,
      "phase": "Phase 1 (Nash Equilibrium)",
      "user_move": {"name": "Cooperate", "type": "cooperate"},
      "computer_move": {"name": "Cooperate", "type": "cooperate"},
      "user_payoff": 3.0,
      "computer_payoff": 3.0,
      "round_winner": "tie",
      "running_user_total": 3.0,
      "running_computer_total": 3.0,
      "game_context": { ... }
    }
  ],
  "analysis_metadata": {
    "plus_moves": 200,
    "user_wins": 95,
    "computer_wins": 89,
    "ties": 16,
    "avg_user_payoff": 4.25,
    "avg_computer_payoff": 4.10
  }
}
```

### Analysis Format (.csv)

```csv
timestamp,round_number,phase,user_move_name,user_move_type,user_payoff,computer_move_name,computer_move_type,computer_payoff,round_winner,running_user_total,running_computer_total,game_context
2025-10-24T16:40:10.714203,1,Phase 1 (Nash Equilibrium),Cooperate,cooperate,3.0,Cooperate,cooperate,3.0,tie,3.0,3.0,"{""strategy"": ""copy_cat""}"
2025-10-24T16:40:10.714307,2,Phase 1 (Nash Equilibrium),Defect,defect,5.0,Cooperate,cooperate,0.0,user,8.0,3.0,"{""strategy"": ""copy_cat""}"
```

## Log Management

### Automatic Cleanup

```python
# Clean up logs older than 30 days
logger.cleanup_old_logs(days_to_keep=30)

# Rotate logs to keep only the 100 most recent files
logger.rotate_logs(max_files_per_type=100)
```

### Statistics

```python
# Get log statistics
stats = logger.get_log_statistics()
print(f"Total sessions: {stats['total_sessions']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
print(f"Oldest log: {stats['oldest_log']}")
print(f"Newest log: {stats['newest_log']}")
```

## Integration with Existing Code

The logging system is automatically integrated into the main game flow. No changes are required to existing game code - logging happens transparently.

### In `game_theory.py`

```python
# Logging is automatically initialized and used
def play_full_game(game: dict, socketio=None, comp_game_id=None, round_delay: float = 0.5):
    # ... existing code ...
    
    # Initialize game logger (automatically done)
    logger = get_game_logger()
    session_id = logger.start_game_session(game_id or "unknown_game", game)
    
    for i in range(PHASE_3_END):
        # ... game logic ...
        
        # Log the move (automatically done)
        logger.log_move(
            round_number=i + 1,
            phase=phase,
            user_move=user_move,
            computer_move=computer_move,
            user_payoff=user_payoff,
            computer_payoff=computer_payoff,
            round_winner=round_winner,
            running_user_total=final_user_payoff,
            running_computer_total=final_computer_payoff,
            game_context=game_context
        )
    
    # End the session (automatically done)
    logger.end_game_session(final_user_payoff, final_computer_payoff)
```

## Testing

Run the test script to verify the logging system:

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python test_game_logging.py

# Run analysis
python analyze_game_logs.py
```

## Configuration

### Environment Variables

You can customize the logging behavior:

```python
# Custom log directory
logger = initialize_game_logger("custom_logs", enable_console_logging=True)

# Disable console logging
logger = initialize_game_logger("logs", enable_console_logging=False)
```

### Log Levels

The system uses Python's standard logging levels:
- `INFO`: Normal game events and moves
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors

## Analysis Examples

### Move Pattern Analysis

```python
analyzer = GameLogAnalyzer()
sessions = analyzer.load_all_sessions()

for session in sessions:
    analysis = analyzer.analyze_move_patterns(session)
    
    print(f"Session: {session['session_id']}")
    print(f"User move distribution: {analysis['user_move_distribution']}")
    print(f"Computer move distribution: {analysis['computer_move_distribution']}")
    print(f"Phase performance: {analysis['phase_performance']}")
```

### Statistical Analysis

```python
# Export to pandas for advanced analysis
import pandas as pd

df = pd.read_csv("game_data_analysis.csv")

# Analyze win rates by phase
phase_analysis = df.groupby('phase').agg({
    'round_winner': lambda x: (x == 'user').sum() / len(x),
    'user_payoff': 'mean',
    'computer_payoff': 'mean'
})

print(phase_analysis)
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure the log directory is writable
2. **Disk Space**: Use log rotation and cleanup features
3. **Import Errors**: Make sure all dependencies are installed

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('game_logger').setLevel(logging.DEBUG)
```

## Future Enhancements

- Real-time log streaming
- Web-based log viewer
- Advanced analytics dashboard
- Integration with external analysis tools
- Automated report generation

---

## Quick Start

1. **Run a game** - logs are automatically generated
2. **Check the logs** in the `game_logs/` directory
3. **Analyze the data** using the provided analysis tools
4. **Export to CSV** for further analysis in your preferred tools

The logging system is designed to be both powerful and easy to use, providing comprehensive insights into game behavior while remaining transparent to existing code.
