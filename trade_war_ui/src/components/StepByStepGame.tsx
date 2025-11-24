import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Stepper,
  Step,
  StepLabel,
  Alert,
  LinearProgress
} from '@mui/material';
import { Country, GameModel } from '../types/game';
import { countries, defaultMoves } from '../data/countries';
import { profiles } from '../data/profiles';
import { getMoveTypeFromUiName, getAvailableMovesForPair, buildPayoffMatrix, countryPairExists } from '../utils/payoffMapper';
import { gameApi } from '../services/api';

interface StepByStepGameProps {
  onBackToSetup?: () => void;
}

interface RoundResult {
  round: number;
  userMove: string;
  computerMove: string;
  userPayoff: number;
  computerPayoff: number;
  roundWinner: string;
  phase: string;
  runningTotals: {
    user_total: number;
    computer_total: number;
  };
}

const StepByStepGame: React.FC<StepByStepGameProps> = ({ onBackToSetup }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [userCountry, setUserCountry] = useState<Country | null>(null);
  const [opponentCountry, setOpponentCountry] = useState<Country | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [currentRound, setCurrentRound] = useState(1);
  const [gameHistory, setGameHistory] = useState<RoundResult[]>([]);
  const [availableMoves, setAvailableMoves] = useState<string[]>(defaultMoves.map(m => m.name));
  const [sameCountryError, setSameCountryError] = useState<string>('');
  const [gameId, setGameId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runningTotals, setRunningTotals] = useState({ user_total: 0, computer_total: 0 });
  const [gameStatus, setGameStatus] = useState<'in_progress' | 'completed'>('in_progress');
  const [totalRounds, setTotalRounds] = useState<number>(20);
  const [lastOpponentMove, setLastOpponentMove] = useState<string | null>(null);

  // Update available moves when countries are selected
  React.useEffect(() => {
    if (userCountry && opponentCountry && userCountry.code === opponentCountry.code) {
      setSameCountryError('Error: You cannot select the same country for both player and opponent.');
      setAvailableMoves(defaultMoves.map(m => m.name));
      return;
    } else {
      setSameCountryError('');
    }

    if (userCountry && opponentCountry) {
      const moves = getAvailableMovesForPair(userCountry.name, opponentCountry.name);
      setAvailableMoves(moves.length > 0 ? moves : defaultMoves.map(m => m.name));
    } else {
      setAvailableMoves(defaultMoves.map(m => m.name));
    }
  }, [userCountry, opponentCountry]);

  const handleCountrySelect = (country: Country) => {
    setUserCountry(country);
    if (activeStep === 0) {
      setActiveStep(1);
    }
  };

  const handleOpponentSelect = (country: Country) => {
    setOpponentCountry(country);
    setSelectedProfile(''); // Reset profile when opponent changes
  };

  const handleProfileSelect = (profileName: string) => {
    setSelectedProfile(profileName);
  };

  const buildGameData = (): GameModel => {
    if (!userCountry || !opponentCountry || !selectedProfile) {
      throw new Error('Missing required game configuration');
    }

    // Build payoff matrix
    const payoffMatrix = countryPairExists(userCountry.name, opponentCountry.name)
      ? buildPayoffMatrix(userCountry.name, opponentCountry.name, availableMoves, availableMoves)
      : availableMoves.flatMap(userMove =>
          availableMoves.map(computerMove => ({
            user_move_name: userMove,
            computer_move_name: computerMove,
            payoff: { user: 2, computer: 2 }, // Default fallback
          }))
        );

    // Create game data structure
    return {
      user_moves: availableMoves.map(moveName => ({
        name: moveName,
        type: getMoveTypeFromUiName(moveName) || defaultMoves.find(m => m.name === moveName)?.type || 'cooperative',
        probability: 1 / availableMoves.length,
        player: 'user' as const,
      })),
      computer_moves: availableMoves.map(moveName => ({
        name: moveName,
        type: getMoveTypeFromUiName(moveName) || defaultMoves.find(m => m.name === moveName)?.type || 'cooperative',
        probability: 1 / availableMoves.length,
        player: 'computer' as const,
      })),
      payoff_matrix: payoffMatrix,
      user_strategy_settings: {
        strategy: 'copy_cat', // Default strategy for step-by-step
        first_move: availableMoves[0],
        cooperation_start: 2,
        mixed_strategy_array: null,
      },
      computer_profile_name: selectedProfile,
      computer_profile: {
        name: selectedProfile,
        settings: profiles[selectedProfile as keyof typeof profiles],
      },
      countries: {
        user: userCountry,
        computer: opponentCountry,
      },
      state: {
        equalizer_strategy: null,
        round_idx: 0,
        last_strategy_update: 0,
        generated_mixed_moves_array: null,
        last_computer_move: null,
      },
    };
  };

  const handleStartGame = async () => {
    if (!userCountry || !opponentCountry || !selectedProfile) {
      return;
    }

    setLoading(true);
    setError(null);
    setActiveStep(2);
    setCurrentRound(1);
    setGameHistory([]);
    setRunningTotals({ user_total: 0, computer_total: 0 });
    setGameStatus('in_progress');

    try {
      // Generate unique game ID
      const newGameId = 'step_game_' + Date.now();
      setGameId(newGameId);

      // Build game data
      const gameData = buildGameData();

      // Initialize game on backend (first call to /round endpoint)
      await gameApi.initializeStepByStepGame(newGameId, gameData);

      // Get initial game state to get total rounds
      const gameState = await gameApi.getGameState(newGameId);
      setTotalRounds(gameState.total_rounds);

      setLoading(false);
    } catch (err: any) {
      console.error('Error starting game:', err);
      setError(err.message || 'Failed to start game');
      setLoading(false);
      setActiveStep(1); // Go back to setup
    }
  };

  const handleMoveSelect = async (moveName: string) => {
    if (!gameId) {
      setError('Game not initialized');
      return;
    }

    if (gameStatus === 'completed') {
      setError('Game is already completed');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Play round with user's selected move
      const roundResult = await gameApi.playRound(gameId, { name: moveName });

      // Update state with round result
      const roundData: RoundResult = {
        round: roundResult.round,
        userMove: roundResult.user_move.name,
        computerMove: roundResult.computer_move.name,
        userPayoff: roundResult.user_payoff,
        computerPayoff: roundResult.computer_payoff,
        roundWinner: roundResult.round_winner,
        phase: roundResult.phase,
        runningTotals: roundResult.running_totals,
      };

      setGameHistory(prev => [...prev, roundData]);
      setCurrentRound(roundResult.current_round);
      setRunningTotals(roundResult.running_totals);
      setGameStatus(roundResult.game_status as 'in_progress' | 'completed');
      setLastOpponentMove(roundResult.computer_move.name);

      setLoading(false);
    } catch (err: any) {
      console.error('Error playing round:', err);
      setError(err.message || 'Failed to play round');
      setLoading(false);
    }
  };

  const handleResetGame = async () => {
    // Delete game from backend if it exists
    if (gameId) {
      try {
        await gameApi.deleteGame(gameId);
      } catch (err) {
        console.error('Error deleting game:', err);
      }
    }

    setActiveStep(0);
    setUserCountry(null);
    setOpponentCountry(null);
    setSelectedProfile('');
    setCurrentRound(1);
    setGameHistory([]);
    setGameId(null);
    setError(null);
    setLoading(false);
    setRunningTotals({ user_total: 0, computer_total: 0 });
    setGameStatus('in_progress');
    setTotalRounds(20);
    setLastOpponentMove(null);
  };

  const getMoveType = (moveName: string) => {
    return getMoveTypeFromUiName(moveName) || 'cooperative';
  };

  const getMoveColor = (moveType: string) => {
    return moveType === 'cooperative' ? 'success' : 'error';
  };

  const getMoveIcon = (moveType: string) => {
    return moveType === 'cooperative' ? '🤝' : '⚔️';
  };

  const steps = ['Select Your Country', 'Select Opponent & Profile', 'Play Game'];

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: { xs: 2, sm: 3 }, pb: 4 }}>
      {onBackToSetup && (
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="outlined" onClick={onBackToSetup}>
            ← Back to Setup
          </Button>
        </Box>
      )}
      
      <Typography variant="h4" gutterBottom align="center" sx={{ mb: 4 }}>
        🎮 Step-by-Step Trade War Game
      </Typography>

      {/* Stepper */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Step 0: Select Your Country */}
      {activeStep === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Step 1: Select Your Country
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
              gap: 2
            }}>
              {countries.map((country) => {
                const isSelected = userCountry?.code === country.code;
                return (
                  <Card
                    key={country.code}
                    onClick={() => handleCountrySelect(country)}
                    sx={{
                      cursor: 'pointer',
                      border: isSelected ? '3px solid' : '2px solid',
                      borderColor: isSelected ? 'primary.main' : 'divider',
                      bgcolor: isSelected ? 'primary.light' : 'background.paper',
                      transition: 'all 0.2s ease-in-out',
                      '&:hover': {
                        transform: 'scale(1.05)',
                        borderColor: 'primary.main',
                        boxShadow: 3
                      }
                    }}
                  >
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" sx={{ mb: 1 }}>
                        {country.flag}
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: isSelected ? 'bold' : 'normal' }}>
                        {country.name}
                      </Typography>
                      {isSelected && (
                        <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                          ✓ Selected
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Step 1: Select Opponent Country and Profile */}
      {activeStep === 1 && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                Step 2: Select Opponent Country
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
                gap: 2
              }}>
                {countries
                  .filter(country => !userCountry || country.code !== userCountry.code)
                  .map((country) => {
                    const isSelected = opponentCountry?.code === country.code;
                    return (
                      <Card
                        key={country.code}
                        onClick={() => handleOpponentSelect(country)}
                        sx={{
                          cursor: 'pointer',
                          border: isSelected ? '3px solid' : '2px solid',
                          borderColor: isSelected ? 'secondary.main' : 'divider',
                          bgcolor: isSelected ? 'secondary.light' : 'background.paper',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'scale(1.05)',
                            borderColor: 'secondary.main',
                            boxShadow: 3
                          }
                        }}
                      >
                        <CardContent sx={{ textAlign: 'center', py: 2 }}>
                          <Typography variant="h4" sx={{ mb: 1 }}>
                            {country.flag}
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: isSelected ? 'bold' : 'normal' }}>
                            {country.name}
                          </Typography>
                          {isSelected && (
                            <Typography variant="caption" color="secondary" sx={{ display: 'block', mt: 0.5 }}>
                              ✓ Selected
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
              </Box>
            </CardContent>
          </Card>

          {sameCountryError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {sameCountryError}
            </Alert>
          )}

          {opponentCountry && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                  Step 3: Select Computer Behavior Profile
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Choose how the computer opponent will behave during the game.
                </Typography>
                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
                  gap: 2,
                  mb: 3
                }}>
                  {Object.entries(profiles).map(([profileName, profileData]) => {
                    const isSelected = selectedProfile === profileName;
                    return (
                      <Card
                        key={profileName}
                        onClick={() => handleProfileSelect(profileName)}
                        sx={{
                          cursor: 'pointer',
                          border: isSelected ? '3px solid' : '2px solid',
                          borderColor: isSelected ? 'secondary.main' : 'divider',
                          bgcolor: isSelected ? 'secondary.light' : 'background.paper',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            borderColor: 'secondary.main',
                            boxShadow: 4
                          }
                        }}
                      >
                        <CardContent sx={{ py: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                            <Typography 
                              variant="subtitle1" 
                              sx={{ 
                                fontWeight: isSelected ? 'bold' : 600,
                                color: isSelected ? 'secondary.main' : 'text.primary'
                              }}
                            >
                              {profileName}
                            </Typography>
                            {isSelected && (
                              <Box
                                sx={{
                                  bgcolor: 'secondary.main',
                                  color: 'white',
                                  borderRadius: '50%',
                                  width: 24,
                                  height: 24,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '0.875rem',
                                  fontWeight: 'bold'
                                }}
                              >
                                ✓
                              </Box>
                            )}
                          </Box>
                          <Typography 
                            variant="body2" 
                            color="text.secondary" 
                            sx={{ fontSize: '0.875rem', lineHeight: 1.5 }}
                          >
                            {profileData.description}
                          </Typography>
                        </CardContent>
                      </Card>
                    );
                  })}
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                  <Button variant="outlined" onClick={() => setActiveStep(0)}>
                    ← Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleStartGame}
                    disabled={!opponentCountry || !selectedProfile}
                    size="large"
                  >
                    Start Game →
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Step 2: Play Game Step by Step */}
      {activeStep === 2 && userCountry && opponentCountry && selectedProfile && (
        <Box>
          {/* Current Winner Display - Prominent at Top */}
          {gameHistory.length > 0 && (
            <Card sx={{ 
              mb: 3, 
              bgcolor: runningTotals.user_total > runningTotals.computer_total 
                ? 'success.light' 
                : runningTotals.computer_total > runningTotals.user_total 
                ? 'error.light' 
                : 'warning.light',
              border: '3px solid',
              borderColor: runningTotals.user_total > runningTotals.computer_total 
                ? 'success.main' 
                : runningTotals.computer_total > runningTotals.user_total 
                ? 'error.main' 
                : 'warning.main',
              boxShadow: 6
            }}>
              <CardContent>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
                    {runningTotals.user_total > runningTotals.computer_total 
                      ? '🎉 You Are Winning! 🎉' 
                      : runningTotals.computer_total > runningTotals.user_total 
                      ? '⚠️ Opponent Is Winning' 
                      : '🤝 It\'s a Tie!'}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 4, mt: 2, flexWrap: 'wrap' }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        Your Score
                      </Typography>
                      <Typography 
                        variant="h3" 
                        sx={{ 
                          fontWeight: 'bold',
                          color: runningTotals.user_total > runningTotals.computer_total ? 'success.main' : 'text.primary'
                        }}
                      >
                        {runningTotals.user_total.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center', alignSelf: 'center' }}>
                      <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                        VS
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        Opponent Score
                      </Typography>
                      <Typography 
                        variant="h3" 
                        sx={{ 
                          fontWeight: 'bold',
                          color: runningTotals.computer_total > runningTotals.user_total ? 'error.main' : 'text.primary'
                        }}
                      >
                        {runningTotals.computer_total.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Difference: {Math.abs(runningTotals.user_total - runningTotals.computer_total).toFixed(2)} points
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Game Info Header */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Game Information
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                    <Chip 
                      label={`You: ${userCountry.flag} ${userCountry.name}`} 
                      color="primary" 
                      sx={{ fontSize: '0.9rem', py: 2 }}
                    />
                    <Chip 
                      label={`Opponent: ${opponentCountry.flag} ${opponentCountry.name}`} 
                      color="secondary" 
                      sx={{ fontSize: '0.9rem', py: 2 }}
                    />
                    <Chip 
                      label={`Profile: ${selectedProfile}`} 
                      variant="outlined"
                      sx={{ fontSize: '0.9rem', py: 2 }}
                    />
                    <Chip 
                      label={`Round: ${currentRound} / ${totalRounds}`} 
                      color="info"
                      sx={{ fontSize: '0.9rem', py: 2 }}
                    />
                    {gameStatus === 'completed' && (
                      <Chip 
                        label="Game Completed" 
                        color="success"
                        sx={{ fontSize: '0.9rem', py: 2 }}
                      />
                    )}
                  </Box>
                </Box>
                <Button variant="outlined" onClick={handleResetGame}>
                  Reset Game
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Loading Indicator */}
          {loading && (
            <Box sx={{ mb: 3 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                Processing round...
              </Typography>
            </Box>
          )}

          {/* Last Round Played - Card Game Style */}
          {gameHistory.length > 0 && (
            <Card sx={{ mb: 3, bgcolor: 'background.paper', border: '2px solid', borderColor: 'divider' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', mb: 3 }}>
                  Last Round Played
                </Typography>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  gap: 4,
                  flexWrap: 'wrap'
                }}>
                  {/* Your Last Move Card */}
                  <Card sx={{
                    minWidth: 180,
                    maxWidth: 220,
                    bgcolor: 'primary.light',
                    border: '3px solid',
                    borderColor: 'primary.main',
                    boxShadow: 4,
                    transform: 'rotate(-2deg)',
                    transition: 'transform 0.3s',
                    '&:hover': {
                      transform: 'rotate(-2deg) scale(1.05)',
                    }
                  }}>
                    <CardContent sx={{ textAlign: 'center', py: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        YOUR MOVE
                      </Typography>
                      <Typography variant="h3" sx={{ mb: 1 }}>
                        {getMoveIcon(getMoveType(gameHistory[gameHistory.length - 1].userMove))}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {gameHistory[gameHistory.length - 1].userMove.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip 
                        label={getMoveType(gameHistory[gameHistory.length - 1].userMove)} 
                        size="small"
                        color={getMoveType(gameHistory[gameHistory.length - 1].userMove) === 'cooperative' ? 'success' : 'error'}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
                        +{gameHistory[gameHistory.length - 1].userPayoff.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>

                  {/* VS Divider */}
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                      VS
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Round {gameHistory[gameHistory.length - 1].round}
                    </Typography>
                  </Box>

                  {/* Opponent's Last Move Card */}
                  <Card sx={{
                    minWidth: 180,
                    maxWidth: 220,
                    bgcolor: 'secondary.light',
                    border: '3px solid',
                    borderColor: 'secondary.main',
                    boxShadow: 4,
                    transform: 'rotate(2deg)',
                    transition: 'transform 0.3s',
                    '&:hover': {
                      transform: 'rotate(2deg) scale(1.05)',
                    }
                  }}>
                    <CardContent sx={{ textAlign: 'center', py: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        OPPONENT'S MOVE
                      </Typography>
                      <Typography variant="h3" sx={{ mb: 1 }}>
                        {getMoveIcon(getMoveType(gameHistory[gameHistory.length - 1].computerMove))}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {gameHistory[gameHistory.length - 1].computerMove.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip 
                        label={getMoveType(gameHistory[gameHistory.length - 1].computerMove)} 
                        size="small"
                        color={getMoveType(gameHistory[gameHistory.length - 1].computerMove) === 'cooperative' ? 'success' : 'error'}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="h6" color="secondary.main" sx={{ fontWeight: 'bold' }}>
                        +{gameHistory[gameHistory.length - 1].computerPayoff.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                {/* Round Winner */}
                <Box sx={{ textAlign: 'center', mt: 3 }}>
                  <Chip 
                    label={
                      gameHistory[gameHistory.length - 1].roundWinner === 'user'
                        ? '🎉 You Won This Round!'
                        : gameHistory[gameHistory.length - 1].roundWinner === 'computer'
                        ? 'Opponent Won This Round'
                        : '🤝 Round Tied'
                    }
                    color={
                      gameHistory[gameHistory.length - 1].roundWinner === 'user'
                        ? 'success'
                        : gameHistory[gameHistory.length - 1].roundWinner === 'computer'
                        ? 'error'
                        : 'warning'
                    }
                    sx={{ fontSize: '1rem', py: 1.5, px: 2 }}
                  />
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Opponent's Last Move Display (Before User Selects) */}
          {lastOpponentMove && gameStatus !== 'completed' && (
            <Card sx={{ mb: 3, bgcolor: 'secondary.light', border: '2px dashed', borderColor: 'secondary.main' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom sx={{ textAlign: 'center', fontWeight: 'bold' }}>
                  Opponent's Last Move
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mt: 2 }}>
                  <Card sx={{
                    bgcolor: 'secondary.main',
                    color: 'white',
                    minWidth: 150,
                    boxShadow: 3
                  }}>
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" sx={{ mb: 1 }}>
                        {getMoveIcon(getMoveType(lastOpponentMove))}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {lastOpponentMove.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip 
                        label={getMoveType(lastOpponentMove)} 
                        size="small"
                        sx={{ 
                          mt: 1,
                          bgcolor: 'white',
                          color: getMoveType(lastOpponentMove) === 'cooperative' ? 'success.main' : 'error.main'
                        }}
                      />
                    </CardContent>
                  </Card>
                </Box>
              </CardContent>
            </Card>
          )}


          {/* Current Round - Select Move - Card Game Style */}
          {gameStatus !== 'completed' && (
            <Card sx={{ mb: 3, bgcolor: 'background.paper', border: '2px solid', borderColor: 'primary.main' }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ mb: 3, textAlign: 'center', fontWeight: 'bold' }}>
                  Round {currentRound}: Select Your Move
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
                  Choose your move card to play against the opponent
                </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
                gap: 3
              }}>
                {defaultMoves
                  .filter(move => availableMoves.includes(move.name))
                  .map((move) => {
                    const moveType = getMoveType(move.name);
                    return (
                      <Card
                        key={move.name}
                        onClick={() => !loading && handleMoveSelect(move.name)}
                        sx={{
                          cursor: loading ? 'not-allowed' : 'pointer',
                          border: '3px solid',
                          borderColor: moveType === 'cooperative' ? 'success.main' : 'error.main',
                          bgcolor: loading ? 'action.disabledBackground' : (moveType === 'cooperative' ? 'success.light' : 'error.light'),
                          opacity: loading ? 0.6 : 1,
                          transition: 'all 0.3s ease-in-out',
                          transform: 'rotate(0deg)',
                          boxShadow: 2,
                          minHeight: 200,
                          display: 'flex',
                          flexDirection: 'column',
                          '&:hover': {
                            transform: loading ? 'none' : 'translateY(-8px) rotate(2deg)',
                            boxShadow: loading ? 2 : 8,
                            borderWidth: loading ? '3px' : '4px',
                            zIndex: 1
                          }
                        }}
                      >
                        <CardContent sx={{ 
                          textAlign: 'center', 
                          py: 3,
                          flexGrow: 1,
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}>
                          <Typography variant="h2" sx={{ mb: 2 }}>
                            {getMoveIcon(moveType)}
                          </Typography>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, lineHeight: 1.2 }}>
                            {move.name.replace('_', ' ').toUpperCase()}
                          </Typography>
                          <Chip 
                            label={moveType.toUpperCase()} 
                            size="small" 
                            color={getMoveColor(moveType) as any}
                            sx={{ 
                              fontSize: '0.75rem',
                              fontWeight: 'bold',
                              mb: 1
                            }}
                          />
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                            Click to play
                          </Typography>
                        </CardContent>
                      </Card>
                    );
                  })}
              </Box>
            </CardContent>
          </Card>
          )}

          {/* Game History - Card Game Style */}
          {gameHistory.length > 1 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ mb: 3, textAlign: 'center' }}>
                  Game History
                </Typography>
                <Box sx={{ maxHeight: 500, overflow: 'auto', pr: 1 }}>
                  {gameHistory.slice().reverse().slice(1).map((round, index) => {
                    const userMoveType = getMoveType(round.userMove);
                    const computerMoveType = getMoveType(round.computerMove);
                    const roundWinner = round.roundWinner === 'user'
                      ? 'You'
                      : round.roundWinner === 'computer'
                      ? 'Opponent'
                      : 'Tie';
                    
                    return (
                      <Box 
                        key={gameHistory.length - index - 1}
                        sx={{ 
                          mb: 3,
                          p: 2,
                          bgcolor: 'background.default',
                          borderRadius: 2,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 2 }}>
                          <Chip 
                            label={`Round ${round.round}`}
                            color="info"
                            sx={{ fontSize: '0.9rem', fontWeight: 'bold' }}
                          />
                          {round.phase && (
                            <Chip 
                              label={round.phase}
                              variant="outlined"
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                        
                        <Box sx={{ 
                          display: 'flex', 
                          justifyContent: 'center', 
                          alignItems: 'center',
                          gap: 3,
                          flexWrap: 'wrap',
                          mb: 2
                        }}>
                          {/* Your Move Card */}
                          <Card sx={{
                            minWidth: 140,
                            maxWidth: 160,
                            bgcolor: 'primary.light',
                            border: '2px solid',
                            borderColor: 'primary.main',
                            boxShadow: 2,
                            transform: 'rotate(-1deg)'
                          }}>
                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                YOU
                              </Typography>
                              <Typography variant="h5" sx={{ mb: 0.5 }}>
                                {getMoveIcon(userMoveType)}
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5, fontSize: '0.75rem' }}>
                                {round.userMove.replace('_', ' ').toUpperCase()}
                              </Typography>
                              <Chip 
                                label={`+${round.userPayoff.toFixed(2)}`} 
                                color="primary" 
                                size="small"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            </CardContent>
                          </Card>

                          {/* VS */}
                          <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                            VS
                          </Typography>

                          {/* Opponent Move Card */}
                          <Card sx={{
                            minWidth: 140,
                            maxWidth: 160,
                            bgcolor: 'secondary.light',
                            border: '2px solid',
                            borderColor: 'secondary.main',
                            boxShadow: 2,
                            transform: 'rotate(1deg)'
                          }}>
                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                OPPONENT
                              </Typography>
                              <Typography variant="h5" sx={{ mb: 0.5 }}>
                                {getMoveIcon(computerMoveType)}
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5, fontSize: '0.75rem' }}>
                                {round.computerMove.replace('_', ' ').toUpperCase()}
                              </Typography>
                              <Chip 
                                label={`+${round.computerPayoff.toFixed(2)}`} 
                                color="secondary" 
                                size="small"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            </CardContent>
                          </Card>
                        </Box>

                        {/* Round Winner */}
                        <Box sx={{ textAlign: 'center' }}>
                          <Chip 
                            label={roundWinner === 'Tie' ? '🤝 Tie' : `${roundWinner === 'You' ? '🎉' : ''} ${roundWinner} Won`}
                            color={roundWinner === 'You' ? 'success' : roundWinner === 'Opponent' ? 'error' : 'warning'}
                            size="small"
                          />
                        </Box>
                      </Box>
                    );
                  })}
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
};

export default StepByStepGame;

