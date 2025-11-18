import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Paper
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  PieLabelRenderProps
} from 'recharts';
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
import { GameModel, GameResult, RoundMove, Move, MoveType, PlayerType } from '../types/game';
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
  const [stepData, setStepData] = useState<Array<{round: number, winner: number, winnerName: string}>>([]);

  // Get total rounds from game data, default to 200
  const totalRounds = gameData?.num_rounds || 200;

  const handlePlayGame = async () => {
    setLoading(true);
    setError(null);
    setIsPlaying(true);
    setGameHistory([]); // Clear previous history
    setStepData([]); // Clear previous step data
    
    try {
      const gameId = await gameApi.playGame(
        gameData,
        // onRoundUpdate callback
        (roundData) => {
          console.log('Round update:', roundData);
          
          // Convert WebSocket data to proper Move format
          const userMove: Move = {
            name: roundData.user_move.name,
            type: roundData.user_move.type as MoveType,
            probability: 1.0, // Default probability since WebSocket doesn't send this
            player: 'user' as PlayerType
          };
          
          const computerMove: Move = {
            name: roundData.computer_move.name,
            type: roundData.computer_move.type as MoveType,
            probability: 1.0, // Default probability since WebSocket doesn't send this
            player: 'computer' as PlayerType
          };
          
          // Add real round data to history
          const roundMove: RoundMove = {
            user_move: userMove,
            computer_move: computerMove,
            user_payoff: roundData.user_payoff,
            computer_payoff: roundData.computer_payoff,
            round: roundData.round
          };
          
          setGameHistory(prev => [...prev, roundMove]);
          setCurrentRound(roundData.round);
          
          // Update step function data with round winner
          const winner = roundData.round_winner === 'user' ? 0 : 1;
          const winnerName = roundData.round_winner === 'user' ? 'Me' : 'Opponent';
          setStepData(prev => [...prev, {
            round: roundData.round,
            winner: winner,
            winnerName: winnerName
          }]);
          
          // Check if game is completed
          if (roundData.game_status === 'completed') {
            // Set final game result
            setGameResult({
              final_user_payoff: roundData.running_totals.user_total,
              final_computer_payoff: roundData.running_totals.computer_total
            });
            setLoading(false);
            setIsPlaying(false);
          }
        },
        // onError callback
        (error) => {
          const errorMessage = typeof error === 'string' ? error : error?.error || 'Failed to play game. Please try again.';
          setError(errorMessage);
          console.error('Game play error:', error);
          setLoading(false);
          setIsPlaying(false);
        },
        0.2 // 200ms delay between rounds for better viewing experience
      );
      
      console.log('Game started with ID:', gameId);
      
    } catch (err) {
      setError('Failed to start game. Please try again.');
      console.error('Game start error:', err);
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

  // Calculate win statistics for pie chart
  const calculateWinStats = () => {
    if (gameHistory.length === 0) return null;
    
    let userWins = 0;
    let computerWins = 0;
    let ties = 0;
    
    gameHistory.forEach((round) => {
      if (round.user_payoff > round.computer_payoff) {
        userWins++;
      } else if (round.computer_payoff > round.user_payoff) {
        computerWins++;
      } else {
        ties++;
      }
    });
    
    const total = gameHistory.length;
    return [
      { name: 'You Won', value: userWins, percentage: ((userWins / total) * 100).toFixed(1) },
      { name: 'Opponent Won', value: computerWins, percentage: ((computerWins / total) * 100).toFixed(1) },
      { name: 'Ties', value: ties, percentage: ((ties / total) * 100).toFixed(1) }
    ];
  };

  // Calculate move counts for bar charts
  const calculateMoveCounts = () => {
    if (gameHistory.length === 0) return { user: [], computer: [] };
    
    const userMoveCounts: Record<string, number> = {};
    const computerMoveCounts: Record<string, number> = {};
    
    gameHistory.forEach((round) => {
      const userMoveName = round.user_move.name;
      const computerMoveName = round.computer_move.name;
      
      userMoveCounts[userMoveName] = (userMoveCounts[userMoveName] || 0) + 1;
      computerMoveCounts[computerMoveName] = (computerMoveCounts[computerMoveName] || 0) + 1;
    });
    
    // Convert to array format for charts
    const userMoves = Object.entries(userMoveCounts)
      .map(([name, count]) => ({
        name: name.replace('_', ' ').toUpperCase(),
        count: count,
        percentage: ((count / gameHistory.length) * 100).toFixed(1)
      }))
      .sort((a, b) => b.count - a.count);
    
    const computerMoves = Object.entries(computerMoveCounts)
      .map(([name, count]) => ({
        name: name.replace('_', ' ').toUpperCase(),
        count: count,
        percentage: ((count / gameHistory.length) * 100).toFixed(1)
      }))
      .sort((a, b) => b.count - a.count);
    
    return { user: userMoves, computer: computerMoves };
  };

  const winStats = calculateWinStats();
  const moveCounts = calculateMoveCounts();
  
  // Colors for pie chart
  const COLORS = ['#4CAF50', '#F44336', '#FF9800'];
  
  // Colors for bar charts
  const BAR_COLORS = {
    user: '#2196F3',
    computer: '#9C27B0'
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

      {/* Round-by-Round Winner Step Function */}
      {stepData.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom align="center" sx={{ fontWeight: 'bold', mb: 2 }}>
              Round-by-Round Winner Step Function
            </Typography>
            <Box sx={{ height: 300, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stepData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="round" 
                    domain={[0, 200]}
                    ticks={[0, 50, 100, 150, 200]}
                    label={{ value: 'Rounds', position: 'insideBottom', offset: -10 }}
                    stroke="#666"
                  />
                  <YAxis 
                    domain={[-0.1, 1.1]}
                    ticks={[0, 1]}
                    tickFormatter={(value) => value === 0 ? 'Me' : 'Opponent'}
                    label={{ value: 'Winner', angle: -90, position: 'insideLeft' }}
                    stroke="#666"
                  />
                  <Tooltip 
                    labelFormatter={(label) => `Round ${label}`}
                    formatter={(value: number, name: string, props: any) => [
                      props.payload.winnerName,
                      'Winner'
                    ]}
                    contentStyle={{
                      backgroundColor: '#f8f9fa',
                      border: '1px solid #dee2e6',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Legend 
                    wrapperStyle={{ paddingTop: '20px' }}
                    iconType="rect"
                  />
                  <Line
                    type="stepAfter"
                    dataKey="winner"
                    stroke="#2C3E50"
                    strokeWidth={3}
                    dot={false}
                    name="Round Winner"
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Step jumps show when the lead changes between players
              </Typography>
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

      {/* Win Percentage Pie Chart */}
      {winStats && winStats.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom align="center">
              📊 Round Win Distribution
            </Typography>
            <Box sx={{ height: 400, width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={winStats}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: PieLabelRenderProps) => {
                      const percent = props.percent as number;
                      return `${props.name}: ${(percent * 100).toFixed(1)}%`;
                    }}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {winStats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number, name: string, props: any) => [
                      `${((props.payload.percent || 0) * 100).toFixed(1)}% (${value} rounds)`,
                      name
                    ]}
                  />
                  <Legend 
                    verticalAlign="bottom" 
                    height={36}
                    formatter={(value, entry: any) => `${value}: ${((entry.payload?.percent || 0) * 100).toFixed(1)}%`}
                  />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Move Count Bar Charts */}
      {moveCounts.user.length > 0 && moveCounts.computer.length > 0 && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
          {/* User Move Counts */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom align="center">
                📈 Your Move Distribution
              </Typography>
              <Box sx={{ height: 350, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={moveCounts.user}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                    />
                    <YAxis 
                      label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value: number, name: string, props: any) => [
                        `${value} times (${props.payload.percentage}%)`,
                        'Usage'
                      ]}
                    />
                    <Bar dataKey="count" fill={BAR_COLORS.user} radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          {/* Computer Move Counts */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom align="center">
                📈 Opponent Move Distribution
              </Typography>
              <Box sx={{ height: 350, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={moveCounts.computer}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                    />
                    <YAxis 
                      label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value: number, name: string, props: any) => [
                        `${value} times (${props.payload.percentage}%)`,
                        'Usage'
                      ]}
                    />
                    <Bar dataKey="count" fill={BAR_COLORS.computer} radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Box>
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
                    {gameData.user_strategy_settings.strategy === 'mixed' && (
                      <Typography variant="caption" color="text.secondary">
                        Probability: {(move.probability * 100).toFixed(1)}%
                      </Typography>
                    )}
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