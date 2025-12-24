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
    <Box sx={{ width: '100%', mx: 'auto', p: { xs: 2, sm: 3 }, pb: 2, height: 'calc(100vh - 40px)', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
      {onBackToSetup && (
        <Box sx={{ mb: 1, display: 'flex', justifyContent: 'flex-end', flexShrink: 0 }}>
          <Button variant="outlined" size="large" onClick={onBackToSetup} sx={{ fontSize: '1rem', py: 1, px: 2 }}>
            ← Back to Setup
          </Button>
        </Box>
      )}
      
      <Typography variant="h4" gutterBottom align="center" sx={{ mb: 2, fontSize: '2rem', fontWeight: 'bold', flexShrink: 0 }}>
        🎮 Step-by-Step Trade War Game
      </Typography>

      {/* Stepper */}
      <Card sx={{ mb: 2, flexShrink: 0 }}>
        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel sx={{ '& .MuiStepLabel-label': { fontSize: '1.1rem' } }}>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Step 0: Select Your Country */}
      {activeStep === 0 && (
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 }, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 2, fontWeight: 'bold', fontSize: '1.5rem' }}>
              Step 1: Select Your Country
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: 'repeat(3, 1fr)', sm: 'repeat(4, 1fr)', md: 'repeat(5, 1fr)' },
              gap: 1.5,
              flex: 1,
              overflow: 'auto'
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
                    <CardContent sx={{ textAlign: 'center', py: 1.5, px: 1, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="h3" sx={{ mb: 1, fontSize: '2.5rem' }}>
                        {country.flag}
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: isSelected ? 'bold' : 'normal', fontSize: '1rem', lineHeight: 1.3 }}>
                        {country.name}
                      </Typography>
                      {isSelected && (
                        <Typography variant="body1" color="primary" sx={{ display: 'block', mt: 0.5, fontSize: '1.2rem', fontWeight: 'bold' }}>
                          ✓
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
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          <Card sx={{ mb: 2 }}>
            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Typography variant="h6" gutterBottom sx={{ mb: 1, fontWeight: 'bold', fontSize: '1.25rem' }}>
                Step 2: Select Opponent Country
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(4, 1fr)', sm: 'repeat(5, 1fr)', md: 'repeat(6, 1fr)' },
                gap: 1
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
                        <CardContent sx={{ textAlign: 'center', py: 1, px: 0.5, '&:last-child': { pb: 1 } }}>
                          <Typography variant="h4" sx={{ mb: 0.5, fontSize: '1.75rem' }}>
                            {country.flag}
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: isSelected ? 'bold' : 'normal', fontSize: '0.875rem', lineHeight: 1.2 }}>
                            {country.name}
                          </Typography>
                          {isSelected && (
                            <Typography variant="caption" color="secondary" sx={{ display: 'block', mt: 0.25, fontSize: '0.875rem', fontWeight: 'bold' }}>
                              ✓
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
            <Alert severity="error" sx={{ mb: 0.75, fontSize: '0.7rem' }}>
              {sameCountryError}
            </Alert>
          )}

          {opponentCountry && (
            <>
              <Card sx={{ mb: 2 }}>
                <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Typography variant="h6" gutterBottom sx={{ mb: 1, fontWeight: 'bold', fontSize: '1.25rem' }}>
                    Step 3: Select Computer Behavior Profile
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1, display: 'block', fontSize: '0.875rem' }}>
                    Choose how the computer opponent will behave during the game.
                  </Typography>
                  <Box sx={{ 
                    display: 'grid', 
                    gridTemplateColumns: { xs: 'repeat(3, 1fr)', sm: 'repeat(4, 1fr)', lg: 'repeat(4, 1fr)' },
                    gap: 1
                  }}>
                    {Object.entries(profiles).map(([profileName, profileData]) => {
                      const isSelected = selectedProfile === profileName;
                      return (
                        <Card
                          key={profileName}
                          onClick={() => {
                            console.log('Profile clicked:', profileName);
                            handleProfileSelect(profileName);
                          }}
                          sx={{
                            cursor: 'pointer',
                            border: isSelected ? '3px solid' : '2px solid',
                            borderColor: isSelected ? 'secondary.main' : 'divider',
                            bgcolor: isSelected ? 'secondary.light' : 'background.paper',
                            transition: 'all 0.2s ease-in-out',
                            minHeight: 90,
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              borderColor: 'secondary.main',
                              boxShadow: 3
                            }
                          }}
                        >
                          <CardContent sx={{ py: 1, px: 1, '&:last-child': { pb: 1 } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontWeight: isSelected ? 'bold' : 600,
                                  color: isSelected ? 'secondary.main' : 'text.primary',
                                  fontSize: '0.875rem'
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
                                    width: 20,
                                    height: 20,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold'
                                  }}
                                >
                                  ✓
                                </Box>
                              )}
                            </Box>
                            <Typography 
                              variant="caption" 
                              color="text.secondary" 
                              sx={{ fontSize: '0.75rem', lineHeight: 1.3 }}
                            >
                              {profileData.description || 'No description available'}
                            </Typography>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </Box>
                </CardContent>
              </Card>
              
              {/* Buttons in separate card at bottom to ensure visibility */}
              <Card>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                    <Button variant="outlined" size="large" onClick={() => setActiveStep(0)} sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}>
                      ← Back
                    </Button>
                    <Button
                      variant="contained"
                      onClick={handleStartGame}
                      disabled={!opponentCountry || !selectedProfile || loading}
                      size="large"
                      sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}
                    >
                      {loading ? 'Starting...' : 'Start Game →'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </>
          )}
        </Box>
      )}

      {/* Step 2: Play Game Step by Step */}
      {activeStep === 2 && userCountry && opponentCountry && selectedProfile && (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>
          {/* Current Winner Display - Prominent at Top */}
          {gameHistory.length > 0 && (
            <Card sx={{ 
              mb: 0.75, 
              bgcolor: runningTotals.user_total > runningTotals.computer_total 
                ? 'success.light' 
                : runningTotals.computer_total > runningTotals.user_total 
                ? 'error.light' 
                : 'warning.light',
              border: '2px solid',
              borderColor: runningTotals.user_total > runningTotals.computer_total 
                ? 'success.main' 
                : runningTotals.computer_total > runningTotals.user_total 
                ? 'error.main' 
                : 'warning.main',
              boxShadow: 3,
              flexShrink: 0
            }}>
              <CardContent sx={{ p: 0.75, '&:last-child': { pb: 0.75 } }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', fontSize: '0.875rem' }}>
                    {runningTotals.user_total > runningTotals.computer_total 
                      ? '🎉 You Are Winning! 🎉' 
                      : runningTotals.computer_total > runningTotals.user_total 
                      ? '⚠️ Opponent Is Winning' 
                      : '🤝 It\'s a Tie!'}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5, mt: 0.5, flexWrap: 'wrap' }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom sx={{ fontSize: '0.65rem' }}>
                        Your Score
                      </Typography>
                      <Typography 
                        variant="h5" 
                        sx={{ 
                          fontWeight: 'bold',
                          fontSize: '1.1rem',
                          color: runningTotals.user_total > runningTotals.computer_total ? 'success.main' : 'text.primary'
                        }}
                      >
                        {runningTotals.user_total.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center', alignSelf: 'center' }}>
                      <Typography variant="body1" sx={{ fontWeight: 'bold', color: 'text.secondary', fontSize: '0.8rem' }}>
                        VS
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom sx={{ fontSize: '0.65rem' }}>
                        Opponent Score
                      </Typography>
                      <Typography 
                        variant="h5" 
                        sx={{ 
                          fontWeight: 'bold',
                          fontSize: '1.1rem',
                          color: runningTotals.computer_total > runningTotals.user_total ? 'error.main' : 'text.primary'
                        }}
                      >
                        {runningTotals.computer_total.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, fontSize: '0.65rem' }}>
                    Difference: {Math.abs(runningTotals.user_total - runningTotals.computer_total).toFixed(2)} points
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Game Info Header */}
          <Card sx={{ mb: 0.75, flexShrink: 0 }}>
            <CardContent sx={{ p: 0.75, '&:last-child': { pb: 0.75 } }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
                <Box>
                  <Typography variant="subtitle1" gutterBottom sx={{ mb: 0.5, fontWeight: 'bold', fontSize: '0.8rem' }}>
                    Game Information
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    <Chip 
                      label={`You: ${userCountry.flag} ${userCountry.name}`} 
                      color="primary" 
                      size="small"
                      sx={{ fontSize: '0.65rem', height: 20 }}
                    />
                    <Chip 
                      label={`Opponent: ${opponentCountry.flag} ${opponentCountry.name}`} 
                      color="secondary" 
                      size="small"
                      sx={{ fontSize: '0.65rem', height: 20 }}
                    />
                    <Chip 
                      label={`Profile: ${selectedProfile}`} 
                      variant="outlined"
                      size="small"
                      sx={{ fontSize: '0.65rem', height: 20 }}
                    />
                    <Chip 
                      label={`Round: ${currentRound} / ${totalRounds}`} 
                      color="info"
                      size="small"
                      sx={{ fontSize: '0.65rem', height: 20 }}
                    />
                    {gameStatus === 'completed' && (
                      <Chip 
                        label="Game Completed" 
                        color="success"
                        size="small"
                        sx={{ fontSize: '0.65rem', height: 20 }}
                      />
                    )}
                  </Box>
                </Box>
                <Button variant="outlined" size="small" onClick={handleResetGame} sx={{ fontSize: '0.75rem', py: 0.25 }}>
                  Reset Game
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 0.75, fontSize: '0.7rem', flexShrink: 0 }} onClose={() => setError(null)}>
              <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>{error}</Typography>
            </Alert>
          )}

          {/* Loading Indicator */}
          {loading && (
            <Box sx={{ mb: 0.75, flexShrink: 0 }}>
              <LinearProgress sx={{ height: 4 }} />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, textAlign: 'center', display: 'block', fontSize: '0.65rem' }}>
                Processing round...
              </Typography>
            </Box>
          )}

          {/* Last Round Played - Card Game Style */}
          {gameHistory.length > 0 && (
            <Card sx={{ mb: 0.75, bgcolor: 'background.paper', border: '2px solid', borderColor: 'divider', flexShrink: 0 }}>
              <CardContent sx={{ p: 0.75, '&:last-child': { pb: 0.75 } }}>
                <Typography variant="subtitle1" gutterBottom sx={{ textAlign: 'center', mb: 0.5, fontWeight: 'bold', fontSize: '0.8rem' }}>
                  Last Round Played
                </Typography>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  gap: 2,
                  flexWrap: 'wrap'
                }}>
                  {/* Your Last Move Card */}
                  <Card sx={{
                    minWidth: 140,
                    maxWidth: 160,
                    bgcolor: 'primary.light',
                    border: '2px solid',
                    borderColor: 'primary.main',
                    boxShadow: 3,
                    transform: 'rotate(-2deg)',
                    transition: 'transform 0.3s',
                    '&:hover': {
                      transform: 'rotate(-2deg) scale(1.05)',
                    }
                  }}>
                    <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontSize: '0.6rem' }}>
                        YOUR MOVE
                      </Typography>
                      <Typography variant="h4" sx={{ mb: 0.5, fontSize: '1.5rem' }}>
                        {getMoveIcon(getMoveType(gameHistory[gameHistory.length - 1].userMove))}
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 0.5, fontSize: '0.75rem' }}>
                        {gameHistory[gameHistory.length - 1].userMove.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip 
                        label={getMoveType(gameHistory[gameHistory.length - 1].userMove)} 
                        size="small"
                        color={getMoveType(gameHistory[gameHistory.length - 1].userMove) === 'cooperative' ? 'success' : 'error'}
                        sx={{ mb: 0.5, fontSize: '0.6rem', height: 18 }}
                      />
                      <Typography variant="body1" color="primary.main" sx={{ fontWeight: 'bold', fontSize: '0.875rem' }}>
                        +{gameHistory[gameHistory.length - 1].userPayoff.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>

                  {/* VS Divider */}
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'text.secondary', fontSize: '1rem' }}>
                      VS
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                      Round {gameHistory[gameHistory.length - 1].round}
                    </Typography>
                  </Box>

                  {/* Opponent's Last Move Card */}
                  <Card sx={{
                    minWidth: 140,
                    maxWidth: 160,
                    bgcolor: 'secondary.light',
                    border: '2px solid',
                    borderColor: 'secondary.main',
                    boxShadow: 3,
                    transform: 'rotate(2deg)',
                    transition: 'transform 0.3s',
                    '&:hover': {
                      transform: 'rotate(2deg) scale(1.05)',
                    }
                  }}>
                    <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5, fontSize: '0.6rem' }}>
                        OPPONENT'S MOVE
                      </Typography>
                      <Typography variant="h4" sx={{ mb: 0.5, fontSize: '1.5rem' }}>
                        {getMoveIcon(getMoveType(gameHistory[gameHistory.length - 1].computerMove))}
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 0.5, fontSize: '0.75rem' }}>
                        {gameHistory[gameHistory.length - 1].computerMove.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip 
                        label={getMoveType(gameHistory[gameHistory.length - 1].computerMove)} 
                        size="small"
                        color={getMoveType(gameHistory[gameHistory.length - 1].computerMove) === 'cooperative' ? 'success' : 'error'}
                        sx={{ mb: 0.5, fontSize: '0.6rem', height: 18 }}
                      />
                      <Typography variant="body1" color="secondary.main" sx={{ fontWeight: 'bold', fontSize: '0.875rem' }}>
                        +{gameHistory[gameHistory.length - 1].computerPayoff.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
                
                {/* Round Winner */}
                <Box sx={{ textAlign: 'center', mt: 1 }}>
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
                    sx={{ fontSize: '0.75rem', py: 0.5, px: 1 }}
                  />
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Current Round - Select Move - Card Game Style - ALWAYS SHOW WHEN GAME IS IN PROGRESS */}
          {gameStatus !== 'completed' && (
            <Card sx={{ 
              mb: 2, 
              bgcolor: 'primary.light', 
              border: '3px solid', 
              borderColor: 'primary.main',
              boxShadow: 6,
              flexShrink: 0
            }}>
              <CardContent sx={{ p: 2 }}>
                <Typography variant="h4" gutterBottom sx={{ mb: 1.5, textAlign: 'center', fontWeight: 'bold', fontSize: '2rem', color: 'primary.dark' }}>
                  Round {gameHistory.length + 1}: Select Your Move
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2, textAlign: 'center', fontSize: '1.1rem', fontWeight: 500 }}>
                  Choose your move card to play against the opponent
                </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' },
                gap: 1.5
              }}>
                {defaultMoves
                  .filter(move => availableMoves.includes(move.name))
                  .map((move) => {
                    const moveType = getMoveType(move.name);
                    return (
                      <Card
                        key={move.name}
                        onClick={() => {
                          if (!loading) {
                            console.log('Move selected:', move.name);
                            handleMoveSelect(move.name);
                          }
                        }}
                        sx={{
                          cursor: loading ? 'not-allowed' : 'pointer',
                          border: '2px solid',
                          borderColor: moveType === 'cooperative' ? 'success.main' : 'error.main',
                          bgcolor: loading ? 'action.disabledBackground' : (moveType === 'cooperative' ? 'success.light' : 'error.light'),
                          opacity: loading ? 0.6 : 1,
                          transition: 'all 0.3s ease-in-out',
                          transform: 'rotate(0deg)',
                          boxShadow: 2,
                          minHeight: 150,
                          display: 'flex',
                          flexDirection: 'column',
                          position: 'relative',
                          zIndex: 1,
                          '&:hover': {
                            transform: loading ? 'none' : 'translateY(-8px) rotate(2deg)',
                            boxShadow: loading ? 2 : 8,
                            borderWidth: loading ? '2px' : '4px',
                            zIndex: 10
                          }
                        }}
                      >
                        <CardContent sx={{ 
                          textAlign: 'center', 
                          py: 1.5,
                          flexGrow: 1,
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}>
                          <Typography variant="h2" sx={{ mb: 1, fontSize: '2.5rem' }}>
                            {getMoveIcon(moveType)}
                          </Typography>
                          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, lineHeight: 1.2, fontSize: '1rem' }}>
                            {move.name.replace('_', ' ').toUpperCase()}
                          </Typography>
                          <Chip 
                            label={moveType.toUpperCase()} 
                            size="small" 
                            color={getMoveColor(moveType) as any}
                            sx={{ 
                              fontSize: '0.875rem',
                              fontWeight: 'bold',
                              mb: 1,
                              height: 28
                            }}
                          />
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontSize: '0.875rem' }}>
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
            <Card sx={{ mt: 0.75, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, p: 0.75, '&:last-child': { pb: 0.75 } }}>
                <Typography variant="h6" gutterBottom sx={{ mb: 0.5, textAlign: 'center', fontSize: '0.8rem' }}>
                  Game History
                </Typography>
                <Box sx={{ flex: 1, overflow: 'auto', pr: 0.5 }}>
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
                          mb: 1,
                          p: 0.75,
                          bgcolor: 'background.default',
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 0.75 }}>
                          <Chip 
                            label={`Round ${round.round}`}
                            color="info"
                            sx={{ fontSize: '0.7rem', fontWeight: 'bold', height: 20 }}
                          />
                          {round.phase && (
                            <Chip 
                              label={round.phase}
                              variant="outlined"
                              size="small"
                              sx={{ ml: 0.5, fontSize: '0.65rem', height: 18 }}
                            />
                          )}
                        </Box>
                        
                        <Box sx={{ 
                          display: 'flex', 
                          justifyContent: 'center', 
                          alignItems: 'center',
                          gap: 1.5,
                          flexWrap: 'wrap',
                          mb: 0.75
                        }}>
                          {/* Your Move Card */}
                          <Card sx={{
                            minWidth: 100,
                            maxWidth: 120,
                            bgcolor: 'primary.light',
                            border: '2px solid',
                            borderColor: 'primary.main',
                            boxShadow: 1,
                            transform: 'rotate(-1deg)'
                          }}>
                            <CardContent sx={{ textAlign: 'center', py: 1 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.3, fontSize: '0.55rem' }}>
                                YOU
                              </Typography>
                              <Typography variant="h6" sx={{ mb: 0.3, fontSize: '1rem' }}>
                                {getMoveIcon(userMoveType)}
                              </Typography>
                              <Typography variant="caption" sx={{ fontWeight: 'bold', mb: 0.3, fontSize: '0.65rem' }}>
                                {round.userMove.replace('_', ' ').toUpperCase()}
                              </Typography>
                              <Chip 
                                label={`+${round.userPayoff.toFixed(2)}`} 
                                color="primary" 
                                size="small"
                                sx={{ fontSize: '0.6rem', height: 16 }}
                              />
                            </CardContent>
                          </Card>

                          {/* VS */}
                          <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'text.secondary', fontSize: '0.75rem' }}>
                            VS
                          </Typography>

                          {/* Opponent Move Card */}
                          <Card sx={{
                            minWidth: 100,
                            maxWidth: 120,
                            bgcolor: 'secondary.light',
                            border: '2px solid',
                            borderColor: 'secondary.main',
                            boxShadow: 1,
                            transform: 'rotate(1deg)'
                          }}>
                            <CardContent sx={{ textAlign: 'center', py: 1 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.3, fontSize: '0.55rem' }}>
                                OPPONENT
                              </Typography>
                              <Typography variant="h6" sx={{ mb: 0.3, fontSize: '1rem' }}>
                                {getMoveIcon(computerMoveType)}
                              </Typography>
                              <Typography variant="caption" sx={{ fontWeight: 'bold', mb: 0.3, fontSize: '0.65rem' }}>
                                {round.computerMove.replace('_', ' ').toUpperCase()}
                              </Typography>
                              <Chip 
                                label={`+${round.computerPayoff.toFixed(2)}`} 
                                color="secondary" 
                                size="small"
                                sx={{ fontSize: '0.6rem', height: 16 }}
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
                            sx={{ fontSize: '0.7rem', height: 20 }}
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

