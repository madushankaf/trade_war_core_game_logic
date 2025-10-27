#!/usr/bin/env python3
"""
Game Log Analysis Script

This script demonstrates how to analyze logged game data for insights
into player behavior, strategy effectiveness, and game outcomes.
"""

import json
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_logger import get_game_logger


class GameLogAnalyzer:
    """Analyzer for game log data"""
    
    def __init__(self, log_directory: str = "game_logs"):
        self.log_directory = Path(log_directory)
        self.machine_logs_dir = self.log_directory / "machine_readable"
        self.analysis_logs_dir = self.log_directory / "analysis"
    
    def load_session_data(self, session_id: str) -> Dict[str, Any]:
        """Load data for a specific session"""
        json_file = self.machine_logs_dir / f"{session_id}_machine.json"
        
        if not json_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        
        with open(json_file, 'r') as f:
            return json.load(f)
    
    def load_all_sessions(self) -> List[Dict[str, Any]]:
        """Load data for all available sessions"""
        sessions = []
        json_files = list(self.machine_logs_dir.glob("*_machine.json"))
        
        for json_file in json_files:
            with open(json_file, 'r') as f:
                session_data = json.load(f)
                sessions.append(session_data)
        
        return sessions
    
    def analyze_move_patterns(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze move patterns for a single session"""
        moves = session_data['moves']
        
        if not moves:
            return {}
        
        # Count move types
        user_moves = [move['user_move']['type'] for move in moves]
        computer_moves = [move['computer_move']['type'] for move in moves]
        
        user_move_counts = {}
        computer_move_counts = {}
        
        for move_type in user_moves:
            user_move_counts[move_type] = user_move_counts.get(move_type, 0) + 1
        
        for move_type in computer_moves:
            computer_move_counts[move_type] = computer_move_counts.get(move_type, 0) + 1
        
        # Analyze phase performance
        phase_performance = {}
        for phase in ['Phase 1 (Nash Equilibrium)', 'Phase 2 (Greedy Response)', 'Phase 3 (Mixed Strategy)']:
            phase_moves = [move for move in moves if move['phase'] == phase]
            if phase_moves:
                phase_performance[phase] = {
                    'user_wins': sum(1 for move in phase_moves if move['round_winner'] == 'user'),
                    'computer_wins': sum(1 for move in phase_moves if move['round_winner'] == 'computer'),
                    'ties': sum(1 for move in phase_moves if move['round_winner'] == 'tie'),
                    'avg_user_payoff': sum(move['user_payoff'] for move in phase_moves) / len(phase_moves),
                    'avg_computer_payoff': sum(move['computer_payoff'] for move in phase_moves) / len(phase_moves)
                }
        
        return {
            'user_move_distribution': user_move_counts,
            'computer_move_distribution': computer_move_counts,
            'phase_performance': phase_performance,
            'total_rounds': len(moves),
            'user_wins': sum(1 for move in moves if move['round_winner'] == 'user'),
            'computer_wins': sum(1 for move in moves if move['round_winner'] == 'computer'),
            'ties': sum(1 for move in moves if move['round_winner'] == 'tie')
        }
    
    def analyze_multiple_sessions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple sessions"""
        if not sessions:
            return {}
        
        # Aggregate statistics
        total_sessions = len(sessions)
        total_rounds = sum(len(session['moves']) for session in sessions)
        total_user_wins = 0
        total_computer_wins = 0
        total_ties = 0
        
        user_move_totals = {}
        computer_move_totals = {}
        
        for session in sessions:
            analysis = self.analyze_move_patterns(session)
            
            total_user_wins += analysis.get('user_wins', 0)
            total_computer_wins += analysis.get('computer_wins', 0)
            total_ties += analysis.get('ties', 0)
            
            # Aggregate move counts
            for move_type, count in analysis.get('user_move_distribution', {}).items():
                user_move_totals[move_type] = user_move_totals.get(move_type, 0) + count
            
            for move_type, count in analysis.get('computer_move_distribution', {}).items():
                computer_move_totals[move_type] = computer_move_totals.get(move_type, 0) + count
        
        return {
            'total_sessions': total_sessions,
            'total_rounds': total_rounds,
            'overall_user_wins': total_user_wins,
            'overall_computer_wins': total_computer_wins,
            'overall_ties': total_ties,
            'user_win_rate': total_user_wins / total_rounds if total_rounds > 0 else 0,
            'computer_win_rate': total_computer_wins / total_rounds if total_rounds > 0 else 0,
            'tie_rate': total_ties / total_rounds if total_rounds > 0 else 0,
            'user_move_distribution': user_move_totals,
            'computer_move_distribution': computer_move_totals
        }
    
    def generate_analysis_report(self, output_file: str = "game_analysis_report.txt") -> None:
        """Generate a comprehensive analysis report"""
        sessions = self.load_all_sessions()
        
        if not sessions:
            print("No game sessions found to analyze")
            return
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("TRADE WAR GAME THEORY - ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Overall statistics
        overall_analysis = self.analyze_multiple_sessions(sessions)
        
        report_lines.append("OVERALL STATISTICS:")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Sessions Analyzed: {overall_analysis['total_sessions']}")
        report_lines.append(f"Total Rounds Played: {overall_analysis['total_rounds']}")
        report_lines.append(f"User Win Rate: {overall_analysis['user_win_rate']:.2%}")
        report_lines.append(f"Computer Win Rate: {overall_analysis['computer_win_rate']:.2%}")
        report_lines.append(f"Tie Rate: {overall_analysis['tie_rate']:.2%}")
        report_lines.append("")
        
        # Move distribution
        report_lines.append("MOVE DISTRIBUTION:")
        report_lines.append("-" * 40)
        report_lines.append("User Moves:")
        for move_type, count in overall_analysis['user_move_distribution'].items():
            percentage = (count / overall_analysis['total_rounds']) * 100
            report_lines.append(f"  {move_type}: {count} ({percentage:.1f}%)")
        
        report_lines.append("Computer Moves:")
        for move_type, count in overall_analysis['computer_move_distribution'].items():
            percentage = (count / overall_analysis['total_rounds']) * 100
            report_lines.append(f"  {move_type}: {count} ({percentage:.1f}%)")
        report_lines.append("")
        
        # Individual session analysis
        report_lines.append("INDIVIDUAL SESSION ANALYSIS:")
        report_lines.append("-" * 40)
        
        for i, session in enumerate(sessions, 1):
            analysis = self.analyze_move_patterns(session)
            report_lines.append(f"Session {i} ({session['session_id']}):")
            report_lines.append(f"  Rounds: {analysis.get('total_rounds', 0)}")
            report_lines.append(f"  User Wins: {analysis.get('user_wins', 0)}")
            report_lines.append(f"  Computer Wins: {analysis.get('computer_wins', 0)}")
            report_lines.append(f"  Ties: {analysis.get('ties', 0)}")
            report_lines.append(f"  Final User Payoff: {session['final_user_payoff']:.2f}")
            report_lines.append(f"  Final Computer Payoff: {session['final_computer_payoff']:.2f}")
            report_lines.append("")
        
        # Write report to file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Analysis report generated: {output_path}")
        print("Report preview:")
        print('\n'.join(report_lines[:20]) + "\n...")
    
    def export_to_csv(self, output_file: str = "game_data_analysis.csv") -> None:
        """Export analysis data to CSV for further processing"""
        sessions = self.load_all_sessions()
        
        if not sessions:
            print("No game sessions found to export")
            return
        
        # Prepare data for CSV export
        csv_data = []
        
        for session in sessions:
            session_info = {
                'session_id': session['session_id'],
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'total_rounds': session['total_rounds'],
                'final_user_payoff': session['final_user_payoff'],
                'final_computer_payoff': session['final_computer_payoff']
            }
            
            # Add analysis data
            analysis = self.analyze_move_patterns(session)
            session_info.update({
                'user_wins': analysis.get('user_wins', 0),
                'computer_wins': analysis.get('computer_wins', 0),
                'ties': analysis.get('ties', 0)
            })
            
            # Add move distribution
            for move_type, count in analysis.get('user_move_distribution', {}).items():
                session_info[f'user_{move_type}_count'] = count
            
            for move_type, count in analysis.get('computer_move_distribution', {}).items():
                session_info[f'computer_{move_type}_count'] = count
            
            csv_data.append(session_info)
        
        # Write to CSV
        if csv_data:
            df = pd.DataFrame(csv_data)
            df.to_csv(output_file, index=False)
            print(f"Data exported to CSV: {output_file}")
            print(f"Exported {len(csv_data)} sessions")


def main():
    """Main analysis function"""
    print("GAME LOG ANALYSIS")
    print("=" * 60)
    
    try:
        # Initialize analyzer
        analyzer = GameLogAnalyzer()
        
        # Generate analysis report
        analyzer.generate_analysis_report("game_analysis_report.txt")
        
        # Export to CSV
        analyzer.export_to_csv("game_data_analysis.csv")
        
        print("\nAnalysis completed successfully!")
        print("Files generated:")
        print("- game_analysis_report.txt (Human-readable analysis)")
        print("- game_data_analysis.csv (Data for further analysis)")
        
    except Exception as e:
        print(f"Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
