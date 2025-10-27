"""
Game Logger Module for Trade War Game Theory Simulation

This module provides comprehensive logging functionality for game moves, strategies, 
and outcomes in both human-readable and machine-readable formats.

Features:
- Structured logging with timestamps
- Human-readable game summaries
- Machine-readable formats (JSON, CSV) for analysis
- Log rotation and cleanup
- Game session management
- Move-by-move tracking with context
"""

import logging
import json
import csv
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import defaultdict


@dataclass
class GameMoveLog:
    """Data structure for logging individual game moves"""
    timestamp: str
    round_number: int
    phase: str
    user_move: Dict[str, Any]
    computer_move: Dict[str, Any]
    user_payoff: float
    computer_payoff: float
    round_winner: str
    running_user_total: float
    running_computer_total: float
    game_context: Dict[str, Any]  # Additional context like strategy info


@dataclass
class GameSessionLog:
    """Data structure for logging complete game sessions"""
    session_id: str
    start_time: str
    end_time: str
    total_rounds: int
    final_user_payoff: float
    final_computer_payoff: float
    game_config: Dict[str, Any]
    moves: List[GameMoveLog]
    analysis_metadata: Dict[str, Any]


class GameLogger:
    """
    Main game logging class that handles all logging operations
    """
    
    def __init__(self, log_directory: str = "game_logs", enable_console_logging: bool = True):
        """
        Initialize the game logger
        
        Args:
            log_directory: Directory to store log files
            enable_console_logging: Whether to also log to console
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        self.enable_console_logging = enable_console_logging
        self.current_session = None
        self.session_moves = []
        self._lock = threading.Lock()
        
        # Setup logging configuration
        self._setup_logging()
        
        # Create subdirectories for different log types
        self.human_logs_dir = self.log_directory / "human_readable"
        self.machine_logs_dir = self.log_directory / "machine_readable"
        self.analysis_logs_dir = self.log_directory / "analysis"
        
        for dir_path in [self.human_logs_dir, self.machine_logs_dir, self.analysis_logs_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup file handler
        log_file = self.log_directory / f"game_log_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Setup console handler if enabled
        console_handler = None
        if self.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
        
        # Configure logger
        self.logger = logging.getLogger('game_logger')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        if console_handler:
            self.logger.addHandler(console_handler)
    
    def start_game_session(self, game_id: str, game_config: Dict[str, Any]) -> str:
        """
        Start a new game session
        
        Args:
            game_id: Unique identifier for the game
            game_config: Game configuration dictionary
            
        Returns:
            Session ID for tracking
        """
        with self._lock:
            session_id = f"{game_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_session = {
                'session_id': session_id,
                'game_id': game_id,
                'start_time': datetime.now().isoformat(),
                'game_config': game_config,
                'moves': []
            }
            self.session_moves = []
            
            # Log session start
            self.logger.info(f"=== GAME SESSION STARTED ===")
            self.logger.info(f"Session ID: {session_id}")
            self.logger.info(f"Game ID: {game_id}")
            self.logger.info(f"Game Configuration: {json.dumps(game_config, indent=2)}")
            self.logger.info("=" * 50)
            
            return session_id
    
    def log_move(self, round_number: int, phase: str, user_move: Dict[str, Any], 
                 computer_move: Dict[str, Any], user_payoff: float, computer_payoff: float,
                 round_winner: str, running_user_total: float, running_computer_total: float,
                 game_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a single game move
        
        Args:
            round_number: Current round number
            phase: Game phase (Phase 1, 2, or 3)
            user_move: User's move dictionary
            computer_move: Computer's move dictionary
            user_payoff: User's payoff for this round
            computer_payoff: Computer's payoff for this round
            round_winner: Winner of this round
            running_user_total: Cumulative user payoff
            running_computer_total: Cumulative computer payoff
            game_context: Additional context information
        """
        if not self.current_session:
            self.logger.warning("No active game session. Move not logged.")
            return
        
        # Create move log entry
        move_log = GameMoveLog(
            timestamp=datetime.now().isoformat(),
            round_number=round_number,
            phase=phase,
            user_move=user_move,
            computer_move=computer_move,
            user_payoff=user_payoff,
            computer_payoff=computer_payoff,
            round_winner=round_winner,
            running_user_total=running_user_total,
            running_computer_total=running_computer_total,
            game_context=game_context or {}
        )
        
        with self._lock:
            self.current_session['moves'].append(move_log)
            self.session_moves.append(move_log)
        
        # Log to console/file
        self.logger.info(f"Round {round_number} ({phase}):")
        self.logger.info(f"  User: {user_move.get('name', 'Unknown')} ({user_move.get('type', 'Unknown')}) - Payoff: {user_payoff:.2f}")
        self.logger.info(f"  Computer: {computer_move.get('name', 'Unknown')} ({computer_move.get('type', 'Unknown')}) - Payoff: {computer_payoff:.2f}")
        self.logger.info(f"  Winner: {round_winner}")
        self.logger.info(f"  Running Totals - User: {running_user_total:.2f}, Computer: {running_computer_total:.2f}")
        
        if game_context:
            self.logger.info(f"  Context: {game_context}")
    
    def end_game_session(self, final_user_payoff: float, final_computer_payoff: float) -> str:
        """
        End the current game session and save logs
        
        Args:
            final_user_payoff: Final user payoff
            final_computer_payoff: Final computer payoff
            
        Returns:
            Session ID of the completed game
        """
        if not self.current_session:
            self.logger.warning("No active game session to end.")
            return None
        
        with self._lock:
            # Update session with final data
            self.current_session['end_time'] = datetime.now().isoformat()
            self.current_session['final_user_payoff'] = final_user_payoff
            self.current_session['final_computer_payoff'] = final_computer_payoff
            self.current_session['total_rounds'] = len(self.current_session['moves'])
            
            # Create session log
            session_log = GameSessionLog(
                session_id=self.current_session['session_id'],
                start_time=self.current_session['start_time'],
                end_time=self.current_session['end_time'],
                total_rounds=self.current_session['total_rounds'],
                final_user_payoff=final_user_payoff,
                final_computer_payoff=final_computer_payoff,
                game_config=self.current_session['game_config'],
                moves=self.current_session['moves'],
                analysis_metadata={
                    'total_moves': len(self.current_session['moves']),
                    'user_wins': sum(1 for move in self.current_session['moves'] if move.round_winner == 'user'),
                    'computer_wins': sum(1 for move in self.current_session['moves'] if move.round_winner == 'computer'),
                    'ties': sum(1 for move in self.current_session['moves'] if move.round_winner == 'tie'),
                    'avg_user_payoff': sum(move.user_payoff for move in self.current_session['moves']) / len(self.current_session['moves']) if self.current_session['moves'] else 0,
                    'avg_computer_payoff': sum(move.computer_payoff for move in self.current_session['moves']) / len(self.current_session['moves']) if self.current_session['moves'] else 0
                }
            )
            
            # Save logs in multiple formats
            session_id = self.current_session['session_id']
            try:
                self._save_human_readable_log(session_log)
                self.logger.info(f"Human-readable log saved: {session_id}_human.txt")
            except Exception as e:
                self.logger.error(f"Failed to save human-readable log: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            
            try:
                self._save_machine_readable_log(session_log)
                self.logger.info(f"Machine-readable log saved: {session_id}_machine.json")
            except Exception as e:
                self.logger.error(f"Failed to save machine-readable log: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            
            try:
                self._save_analysis_log(session_log)
                self.logger.info(f"Analysis log saved: {session_id}_analysis.csv")
            except Exception as e:
                self.logger.error(f"Failed to save analysis log: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            
            # Log session end
            self.logger.info("=" * 50)
            self.logger.info(f"=== GAME SESSION COMPLETED ===")
            self.logger.info(f"Session ID: {session_id}")
            self.logger.info(f"Total Rounds: {session_log.total_rounds}")
            self.logger.info(f"Final User Payoff: {final_user_payoff:.2f}")
            self.logger.info(f"Final Computer Payoff: {final_computer_payoff:.2f}")
            self.logger.info(f"User Wins: {session_log.analysis_metadata['user_wins']}")
            self.logger.info(f"Computer Wins: {session_log.analysis_metadata['computer_wins']}")
            self.logger.info(f"Ties: {session_log.analysis_metadata['ties']}")
            self.logger.info("=" * 50)
            
            # Clear current session
            self.current_session = None
            self.session_moves = []
            
            return session_id
    
    def _save_human_readable_log(self, session_log: GameSessionLog) -> None:
        """Save human-readable log file"""
        log_file = self.human_logs_dir / f"{session_log.session_id}_human.txt"
        
        with open(log_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("TRADE WAR GAME THEORY SIMULATION - GAME SESSION LOG\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Session ID: {session_log.session_id}\n")
            f.write(f"Start Time: {session_log.start_time}\n")
            f.write(f"End Time: {session_log.end_time}\n")
            f.write(f"Total Rounds: {session_log.total_rounds}\n")
            f.write(f"Final User Payoff: {session_log.final_user_payoff:.2f}\n")
            f.write(f"Final Computer Payoff: {session_log.final_computer_payoff:.2f}\n\n")
            
            f.write("GAME CONFIGURATION:\n")
            f.write("-" * 40 + "\n")
            f.write(json.dumps(session_log.game_config, indent=2))
            f.write("\n\n")
            
            f.write("GAME ANALYSIS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"User Wins: {session_log.analysis_metadata['user_wins']}\n")
            f.write(f"Computer Wins: {session_log.analysis_metadata['computer_wins']}\n")
            f.write(f"Ties: {session_log.analysis_metadata['ties']}\n")
            f.write(f"Average User Payoff per Round: {session_log.analysis_metadata['avg_user_payoff']:.2f}\n")
            f.write(f"Average Computer Payoff per Round: {session_log.analysis_metadata['avg_computer_payoff']:.2f}\n\n")
            
            f.write("MOVE-BY-MOVE LOG:\n")
            f.write("-" * 40 + "\n")
            
            for move in session_log.moves:
                f.write(f"Round {move.round_number} ({move.phase}) - {move.timestamp}\n")
                f.write(f"  User Move: {move.user_move.get('name', 'Unknown')} ({move.user_move.get('type', 'Unknown')}) - Payoff: {move.user_payoff:.2f}\n")
                f.write(f"  Computer Move: {move.computer_move.get('name', 'Unknown')} ({move.computer_move.get('type', 'Unknown')}) - Payoff: {move.computer_payoff:.2f}\n")
                f.write(f"  Round Winner: {move.round_winner}\n")
                f.write(f"  Running Totals - User: {move.running_user_total:.2f}, Computer: {move.running_computer_total:.2f}\n")
                if move.game_context:
                    f.write(f"  Context: {move.game_context}\n")
                f.write("\n")
    
    def _save_machine_readable_log(self, session_log: GameSessionLog) -> None:
        """Save machine-readable JSON log file"""
        log_file = self.machine_logs_dir / f"{session_log.session_id}_machine.json"
        
        # Convert to dictionary for JSON serialization
        session_dict = asdict(session_log)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):
                return obj.item()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        session_dict = convert_numpy_types(session_dict)
        
        with open(log_file, 'w') as f:
            json.dump(session_dict, f, indent=2)
    
    def _save_analysis_log(self, session_log: GameSessionLog) -> None:
        """Save CSV file for analysis"""
        csv_file = self.analysis_logs_dir / f"{session_log.session_id}_analysis.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'timestamp', 'round_number', 'phase', 
                'user_move_name', 'user_move_type', 'user_payoff',
                'computer_move_name', 'computer_move_type', 'computer_payoff',
                'round_winner', 'running_user_total', 'running_computer_total',
                'game_context'
            ])
            
            # Write data
            for move in session_log.moves:
                writer.writerow([
                    move.timestamp,
                    move.round_number,
                    move.phase,
                    move.user_move.get('name', ''),
                    move.user_move.get('type', ''),
                    move.user_payoff,
                    move.computer_move.get('name', ''),
                    move.computer_move.get('type', ''),
                    move.computer_payoff,
                    move.round_winner,
                    move.running_user_total,
                    move.running_computer_total,
                    json.dumps(move.game_context)
                ])
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a specific game session"""
        json_file = self.machine_logs_dir / f"{session_id}_machine.json"
        
        if not json_file.exists():
            return None
        
        with open(json_file, 'r') as f:
            return json.load(f)
    
    def list_all_sessions(self) -> List[str]:
        """List all available game sessions"""
        json_files = list(self.machine_logs_dir.glob("*_machine.json"))
        return [f.stem.replace("_machine", "") for f in json_files]
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up log files older than specified days"""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for log_dir in [self.human_logs_dir, self.machine_logs_dir, self.analysis_logs_dir]:
            for log_file in log_dir.iterdir():
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file}")
    
    def rotate_logs(self, max_files_per_type: int = 100) -> None:
        """Rotate logs to prevent too many files from accumulating"""
        for log_dir in [self.human_logs_dir, self.machine_logs_dir, self.analysis_logs_dir]:
            # Get all files sorted by modification time (oldest first)
            files = sorted(log_dir.iterdir(), key=lambda x: x.stat().st_mtime)
            
            # Remove oldest files if we exceed the limit
            if len(files) > max_files_per_type:
                files_to_remove = files[:-max_files_per_type]
                for file_to_remove in files_to_remove:
                    file_to_remove.unlink()
                    self.logger.info(f"Rotated log file: {file_to_remove}")
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get statistics about log files"""
        stats = {
            'total_sessions': 0,
            'total_human_logs': 0,
            'total_machine_logs': 0,
            'total_analysis_logs': 0,
            'oldest_log': None,
            'newest_log': None,
            'total_size_mb': 0
        }
        
        all_files = []
        for log_dir in [self.human_logs_dir, self.machine_logs_dir, self.analysis_logs_dir]:
            files = list(log_dir.iterdir())
            if 'human' in log_dir.name:
                stats['total_human_logs'] = len(files)
            elif 'machine' in log_dir.name:
                stats['total_machine_logs'] = len(files)
                stats['total_sessions'] = len(files)  # Machine logs represent sessions
            elif 'analysis' in log_dir.name:
                stats['total_analysis_logs'] = len(files)
            
            for file_path in files:
                stats['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)
                all_files.append((file_path, file_path.stat().st_mtime))
        
        if all_files:
            all_files.sort(key=lambda x: x[1])
            stats['oldest_log'] = all_files[0][0].name
            stats['newest_log'] = all_files[-1][0].name
        
        return stats


# Global logger instance
_game_logger = None

def get_game_logger() -> GameLogger:
    """Get the global game logger instance"""
    global _game_logger
    if _game_logger is None:
        _game_logger = GameLogger()
    return _game_logger

def initialize_game_logger(log_directory: str = "game_logs", enable_console_logging: bool = True) -> GameLogger:
    """Initialize the global game logger with custom settings"""
    global _game_logger
    _game_logger = GameLogger(log_directory, enable_console_logging)
    return _game_logger
