import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  TrendingUp,
  TrendingDown,
  EmojiEvents,
  Warning
} from '@mui/icons-material';
import { GameModel, GameResult, RoundMove, Move } from '../types/game';
import { gameApi } from '../services/api';

interface GameDashboardProps {
  gameData: GameModel;
  onBackToSetup: () => void;
}

const GameDashboard: React.FC<GameDashboardProps> = ({ gameData, onBackToSetup }) => {
  const [gameResult, setGameResult] = useState<GameResult | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentRound, setCurrentRound] = useState(0);
  const [gameHistory, setGameHistory] = useState<RoundMove[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalRounds = 200; // From game_theory.py PHASE_3_END

  const handlePlayGame = async () => {
    setLoading(true);
    setError(null);
    setIsPlaying(true);
    
    try {
      const result = await gameApi.playGame(gameData);
      setGameResult(result);
      
      // Simulate game history for visualization
      const simulatedHistory: RoundMove[] = [];
      for (let i = 0; i < Math.min(20, totalRounds); i++) {
        const userMove = gameData.user_moves[Math.floor(Math.random() * gameData.user_moves.length)];
        const computerMove = gameData.computer_moves[Math.floor(Math.random() * gameData.computer_moves.length)];
        
        simulatedHistory.push({
          user_move: userMove,
          computer_move: computerMove,
          user_payoff: Math.floor(Math.random() * 5) + 1,
          computer_payoff: Math.floor(Math.random() * 5) + 1,
          round: i + 1
        });
      }
      setGameHistory(simulatedHistory);
      
    } catch (err) {
      setError('Failed to play game. Please try again.');
      console.error('Game play error:', err);
    } finally {
      setLoading(false);
      setIsPlaying(false);
    }
  };

  const handlePauseGame = () => {
    setIsPlaying(false);
  };

  const handleStopGame = () => {
    setIsPlaying(false);
    setCurrentRound(0);
    setGameHistory([]);
    setGameResult(null);
  };

  const getMoveColor = (move: Move) => {
    switch (move.type) {
      case 'cooperative':
        return 'success';
      case 'defective':
        return 'error';
      case 'mixed':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getMoveIcon = (move: Move) => {
    switch (move.type) {
      case 'cooperative':
        return '🤝';
      case 'defective':
        return '⚔️';
      case 'mixed':
        return '🎲';
      default:
        return '❓';
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          🎮 Trade War Game
        </Typography>
        <Button variant="outlined" onClick={onBackToSetup}>
          ← Back to Setup
        </Button>
      </Box>

      {/* Game Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="h6">Game Controls</Typography>
            <Chip 
              label={`Round ${currentRound} / ${totalRounds}`} 
              color="primary" 
              variant="outlined"
            />
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={handlePlayGame}
              disabled={loading || isPlaying}
            >
              {loading ? 'Playing...' : 'Play Full Game'}
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Pause />}
              onClick={handlePauseGame}
              disabled={!isPlaying}
            >
              Pause
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Stop />}
              onClick={handleStopGame}
            >
              Stop
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={handleStopGame}
            >
              Reset
            </Button>
          </Box>

          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                Simulating trade war game...
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card sx={{ mb: 3, bgcolor: 'error.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Warning color="error" />
              <Typography color="error">{error}</Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Game Results */}
      {gameResult && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🏆 Final Results
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {gameResult.final_user_payoff.toFixed(2)}
                </Typography>
                <Typography variant="subtitle1">Your Total Payoff</Typography>
                <TrendingUp color="success" sx={{ fontSize: 40, mt: 1 }} />
              </Paper>
              
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="secondary">
                  {gameResult.final_computer_payoff.toFixed(2)}
                </Typography>
                <Typography variant="subtitle1">Opponent Total Payoff</Typography>
                <TrendingDown color="error" sx={{ fontSize: 40, mt: 1 }} />
              </Paper>
            </Box>

            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Chip
                icon={<EmojiEvents />}
                label={
                  gameResult.final_user_payoff > gameResult.final_computer_payoff
                    ? 'You Won! 🎉'
                    : gameResult.final_user_payoff < gameResult.final_computer_payoff
                    ? 'Opponent Won 😔'
                    : 'It\'s a Tie! 🤝'
                }
                color={
                  gameResult.final_user_payoff > gameResult.final_computer_payoff
                    ? 'success'
                    : gameResult.final_user_payoff < gameResult.final_computer_payoff
                    ? 'error'
                    : 'warning'
                }
                variant="filled"
                sx={{ fontSize: '1.1rem', py: 1 }}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Game Information */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
        {/* Available Moves */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Your Available Moves
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {gameData.user_moves.map((move) => (
                <Paper key={move.name} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h4">{getMoveIcon(move)}</Typography>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle1">
                      {move.name.replace('_', ' ').toUpperCase()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Probability: {(move.probability * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Chip 
                    label={move.type} 
                    color={getMoveColor(move) as any}
                    size="small"
                  />
                </Paper>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Strategy Information */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Strategy Configuration
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Strategy Type
                </Typography>
                <Typography variant="h6">
                  {gameData.user_strategy_settings.strategy.replace('_', ' ').toUpperCase()}
                </Typography>
              </Paper>

              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  First Move
                </Typography>
                <Typography variant="h6">
                  {gameData.user_strategy_settings.first_move?.replace('_', ' ').toUpperCase() || 'Random'}
                </Typography>
              </Paper>

              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Cooperation Start
                </Typography>
                <Typography variant="h6">
                  Round {gameData.user_strategy_settings.cooperation_start || 0}
                </Typography>
              </Paper>
            </Box>
          </CardContent>
        </Card>

        {/* Game History */}
        {gameHistory.length > 0 && (
          <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Game History
                </Typography>
                
                <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {gameHistory.slice(-10).map((round, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle2">
                          Round {round.round}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="caption">You</Typography>
                            <Typography variant="h6">{getMoveIcon(round.user_move)}</Typography>
                            <Typography variant="caption">{round.user_payoff}</Typography>
                          </Box>
                          <Typography variant="h4">⚔️</Typography>
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography variant="caption">Opponent</Typography>
                            <Typography variant="h6">{getMoveIcon(round.computer_move)}</Typography>
                            <Typography variant="caption">{round.computer_payoff}</Typography>
                          </Box>
                        </Box>
                      </Box>
                    </Paper>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default GameDashboard; 