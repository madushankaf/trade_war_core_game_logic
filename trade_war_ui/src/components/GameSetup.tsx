import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  Button,
  Chip,
  TextField,
  Alert
} from '@mui/material';
import { Country, StrategyType } from '../types/game';
import { countries, defaultMoves } from '../data/countries';
import { profiles } from '../data/profiles';
import {
  buildPayoffMatrix,
  countryPairExists,
  getAvailableMovesForPair,
  getMoveTypeFromUiName,
} from '../utils/payoffMapper';

interface GameSetupProps {
  onGameStart: (gameData: any) => void;
}

const GameSetup: React.FC<GameSetupProps> = ({ onGameStart }) => {
  const [userCountry, setUserCountry] = useState<Country | null>(null);
  const [computerCountry, setComputerCountry] = useState<Country | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [strategy, setStrategy] = useState<StrategyType>('copy_cat');
  const [firstMove, setFirstMove] = useState<string>('open_dialogue');
  const [cooperationStart, setCooperationStart] = useState<number>(2);
  const [selectedMoves, setSelectedMoves] = useState<string[]>(['open_dialogue', 'raise_tariffs', 'wait_and_see']);
  const [moveProbabilities, setMoveProbabilities] = useState<Record<string, number>>({});
  const [availableMoves, setAvailableMoves] = useState<string[]>(defaultMoves.map(m => m.name));
  const [countryPairWarning, setCountryPairWarning] = useState<string>('');
  const [sameCountryError, setSameCountryError] = useState<string>('');
  const [numRounds, setNumRounds] = useState<number>(200);

  const strategies = [
    { value: 'copy_cat', label: 'Copy Cat', description: 'Copy your opponent\'s last move' },
    { value: 'tit_for_tat', label: 'Tit for Tat', description: 'Start cooperative, then copy opponent' },
    { value: 'grim_trigger', label: 'Grim Trigger', description: 'Cooperate until opponent defects, then always defect' },
    { value: 'random', label: 'Random', description: 'Choose moves randomly' },
    { value: 'mixed', label: 'Mixed Strategy', description: 'Use probability-based strategy' }
  ];

  // Update available moves when countries are selected
  React.useEffect(() => {
    // Check if same country is selected
    if (userCountry && computerCountry && userCountry.code === computerCountry.code) {
      setSameCountryError('Error: You cannot select the same country for both player and opponent.');
      setAvailableMoves(defaultMoves.map(m => m.name));
      setCountryPairWarning('');
      return;
    } else {
      setSameCountryError('');
    }

    if (userCountry && computerCountry) {
      const pairExists = countryPairExists(userCountry.name, computerCountry.name);
      
      if (pairExists) {
        const moves = getAvailableMovesForPair(userCountry.name, computerCountry.name);
        setAvailableMoves(moves.length > 0 ? moves : defaultMoves.map(m => m.name));
        setCountryPairWarning('');
        
        // Filter selected moves to only include available moves
        setSelectedMoves(prev => prev.filter(move => 
          moves.length > 0 ? moves.includes(move) : true
        ));
        
        // Reset firstMove if it's not in available moves
        setFirstMove(prev => {
          if (moves.length > 0 && !moves.includes(prev)) {
            return moves[0];
          }
          return prev;
        });
      } else {
        // Country pair not in data, use all moves with warning
        setAvailableMoves(defaultMoves.map(m => m.name));
        setCountryPairWarning(
          `Warning: Payoff data not available for ${userCountry.name} vs ${computerCountry.name}. Using default payoffs.`
        );
      }
    } else {
      setAvailableMoves(defaultMoves.map(m => m.name));
      setCountryPairWarning('');
    }
  }, [userCountry, computerCountry]);

  // Initialize probabilities when selected moves change
  React.useEffect(() => {
    setMoveProbabilities((previousProbabilities) => {
      const newProbabilities: Record<string, number> = {};
      selectedMoves.forEach((move) => {
        newProbabilities[move] =
          previousProbabilities[move] ?? 1 / selectedMoves.length;
      });
      return newProbabilities;
    });
  }, [selectedMoves]);

  const handleProbabilityChange = (moveName: string, newProbability: number) => {
    setMoveProbabilities(prev => ({
      ...prev,
      [moveName]: newProbability
    }));
  };

  const normalizeProbabilities = () => {
    const total = Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0);
    if (total !== 1) {
      const normalized: Record<string, number> = {};
      Object.keys(moveProbabilities).forEach(move => {
        normalized[move] = moveProbabilities[move] / total;
      });
      setMoveProbabilities(normalized);
    }
  };

  const handleStartGame = () => {
    if (!userCountry || !computerCountry) {
      alert('Please select both countries');
      return;
    }

    if (userCountry.code === computerCountry.code) {
      alert('Error: You cannot select the same country for both player and opponent.');
      return;
    }
    
    if (!selectedProfile) {
      alert('Please select a computer behavior profile');
      return;
    }

    // Normalize probabilities before starting game
    if (strategy === 'mixed') {
      normalizeProbabilities();
    }

    // Build dynamic payoff matrix based on selected countries and moves
    const payoffMatrix = userCountry && computerCountry
      ? buildPayoffMatrix(
          userCountry.name,
          computerCountry.name,
          selectedMoves,
          selectedMoves
        )
      : generatePayoffMatrix(selectedMoves); // Fallback if countries not selected

    // Create game data structure
    const gameData = {
      user_moves: selectedMoves.map(moveName => {
        // Use move type from payoff data if available, otherwise use defaultMoves
        const moveType = getMoveTypeFromUiName(moveName);
        const moveInfo = defaultMoves.find(m => m.name === moveName);
        return {
          name: moveName,
          type: moveType || moveInfo?.type || 'cooperative',
          probability: strategy === 'mixed' ? moveProbabilities[moveName] : 1 / selectedMoves.length,
          player: 'user' as const
        };
      }),
      computer_moves: selectedMoves.map(moveName => {
        // Use move type from payoff data if available, otherwise use defaultMoves
        const moveType = getMoveTypeFromUiName(moveName);
        const moveInfo = defaultMoves.find(m => m.name === moveName);
        return {
          name: moveName,
          type: moveType || moveInfo?.type || 'cooperative',
          probability: strategy === 'mixed' ? moveProbabilities[moveName] : 1 / selectedMoves.length,
          player: 'computer' as const
        };
      }),
      payoff_matrix: payoffMatrix,
      user_strategy_settings: {
        strategy,
        first_move: firstMove,
        cooperation_start: cooperationStart,
        mixed_strategy_array: strategy === 'mixed' ? selectedMoves : null
      },
      computer_profile_name: selectedProfile, // API expects this as top-level field
      computer_profile: {
        name: selectedProfile,
        settings: profiles[selectedProfile as keyof typeof profiles]
      },
      countries: {
        user: userCountry,
        computer: computerCountry
      },
      state: {
        equalizer_strategy: null,
        round_idx: 0,
        last_strategy_update: 0,
        generated_mixed_moves_array: null,
        last_computer_move: null
      },
      num_rounds: numRounds
    };

    onGameStart(gameData);
  };

  const generatePayoffMatrix = (moves: string[]) => {
    const matrix = [];
    for (const userMove of moves) {
      for (const computerMove of moves) {
        matrix.push({
          user_move_name: userMove,
          computer_move_name: computerMove,
          payoff: {
            user: 4,
            computer: 4
          }
        });
      }
    }
    return matrix;
  };

  const handleMoveToggle = (moveName: string) => {
    setSelectedMoves(prev => 
      prev.includes(moveName) 
        ? prev.filter(m => m !== moveName)
        : [...prev, moveName]
    );
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: { xs: 2, sm: 3 }, pb: 4 }}>
      <Typography variant="h4" gutterBottom align="center" sx={{ mb: 4 }}>
        🎮 Trade War Game Setup
      </Typography>
      
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
        {/* Country Selection */}
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Your Country
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
                gap: 2,
                mt: 1 
              }}>
                {countries.map((country) => {
                  const isSelected = userCountry?.code === country.code;
                  return (
                    <Card
                      key={country.code}
                      onClick={() => setUserCountry(country)}
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
                        },
                        height: '100%'
                      }}
                    >
                      <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
                        <Typography variant="h4" sx={{ mb: 1 }}>
                          {country.flag}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: isSelected ? 'bold' : 'normal' }}>
                          {country.name}
                        </Typography>
                        {isSelected && (
                          <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                            Selected
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Opponent Country
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
                gap: 2,
                mt: 1 
              }}>
                {countries
                  .filter(country => !userCountry || country.code !== userCountry.code)
                  .map((country) => {
                    const isSelected = computerCountry?.code === country.code;
                    return (
                      <Card
                        key={country.code}
                        onClick={() => {
                          setComputerCountry(country);
                          // Reset profile selection when country changes
                          setSelectedProfile('');
                        }}
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
                          },
                          height: '100%'
                        }}
                      >
                        <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
                          <Typography variant="h4" sx={{ mb: 1 }}>
                            {country.flag}
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: isSelected ? 'bold' : 'normal' }}>
                            {country.name}
                          </Typography>
                          {isSelected && (
                            <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                              Selected
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Computer Behavior Profile - Separate card when opponent country is selected */}
        {computerCountry && (
          <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <Card sx={{ bgcolor: 'background.default', border: '2px solid', borderColor: 'divider' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
                  🤖 Computer Behavior Profile
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Choose how the computer opponent will behave during the game. Each profile has a different strategy and approach.
                </Typography>
                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
                  gap: 2
                }}>
                  {Object.entries(profiles).map(([profileName, profileData]) => {
                    const isSelected = selectedProfile === profileName;
                    return (
                      <Card
                        key={profileName}
                        onClick={() => setSelectedProfile(profileName)}
                        sx={{
                          cursor: 'pointer',
                          border: isSelected ? '3px solid' : '2px solid',
                          borderColor: isSelected ? 'secondary.main' : 'divider',
                          bgcolor: isSelected ? 'secondary.light' : 'background.paper',
                          transition: 'all 0.2s ease-in-out',
                          height: '100%',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            borderColor: isSelected ? 'secondary.main' : 'secondary.main',
                            boxShadow: 4,
                            bgcolor: isSelected ? 'secondary.light' : 'action.hover'
                          }
                        }}
                      >
                        <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                            <Typography 
                              variant="subtitle1" 
                              sx={{ 
                                fontWeight: isSelected ? 'bold' : 600,
                                fontSize: '1rem',
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
                            sx={{ 
                              fontSize: '0.875rem',
                              lineHeight: 1.5
                            }}
                          >
                            {profileData.description}
                          </Typography>
                        </CardContent>
                      </Card>
                    );
                  })}
                </Box>
                {selectedProfile && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'secondary.light', borderRadius: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      <strong>Selected:</strong> {selectedProfile} - {profiles[selectedProfile as keyof typeof profiles]?.description}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Same Country Error */}
        {sameCountryError && (
          <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <Alert severity="error" sx={{ fontWeight: 'bold' }}>
              {sameCountryError}
            </Alert>
          </Box>
        )}

        {/* Country Pair Warning */}
        {countryPairWarning && (
          <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <Card sx={{ bgcolor: 'warning.light', border: '1px solid', borderColor: 'warning.main' }}>
              <CardContent>
                <Typography variant="body2" color="warning.dark">
                  ⚠️ {countryPairWarning}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}


        {/* Strategy Configuration */}
        <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Your Strategy Configuration
              </Typography>
              
              {/* Strategy Type Tiles */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', mb: 1.5 }}>
                  Strategy Type
                </Typography>
                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
                  gap: 1.5
                }}>
                  {strategies.map((strat) => {
                    const isSelected = strategy === strat.value;
                    return (
                      <Card
                        key={strat.value}
                        onClick={() => setStrategy(strat.value as StrategyType)}
                        sx={{
                          cursor: 'pointer',
                          border: isSelected ? '3px solid' : '2px solid',
                          borderColor: isSelected ? 'primary.main' : 'divider',
                          bgcolor: isSelected ? 'primary.light' : 'background.paper',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            borderColor: 'primary.main',
                            boxShadow: 3
                          }
                        }}
                      >
                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: isSelected ? 'bold' : 'normal', mb: 0.5 }}>
                            {strat.label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.75rem' }}>
                            {strat.description}
                          </Typography>
                          {isSelected && (
                            <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5, fontWeight: 'bold' }}>
                              ✓ Selected
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </Box>
              </Box>

              {/* First Move Tiles */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', mb: 1.5 }}>
                  First Move
                </Typography>
                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
                  gap: 1.5
                }}>
                  {defaultMoves
                    .filter(move => availableMoves.includes(move.name))
                    .map((move) => {
                      const isSelected = firstMove === move.name;
                      const moveType = getMoveTypeFromUiName(move.name) || move.type;
                      return (
                        <Card
                          key={move.name}
                          onClick={() => setFirstMove(move.name)}
                          sx={{
                            cursor: 'pointer',
                            border: isSelected ? '3px solid' : '2px solid',
                            borderColor: isSelected 
                              ? (moveType === 'cooperative' ? 'success.main' : 'error.main')
                              : 'divider',
                            bgcolor: isSelected 
                              ? (moveType === 'cooperative' ? 'success.light' : 'error.light')
                              : 'background.paper',
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: 3
                            }
                          }}
                        >
                          <CardContent sx={{ textAlign: 'center', py: 1.5, '&:last-child': { pb: 1.5 } }}>
                            <Typography variant="body2" sx={{ fontWeight: isSelected ? 'bold' : 'normal', mb: 0.5 }}>
                              {move.name.replace('_', ' ').toUpperCase()}
                            </Typography>
                            <Chip 
                              label={moveType} 
                              size="small" 
                              color={moveType === 'cooperative' ? 'success' : 'error'}
                              sx={{ fontSize: '0.65rem', height: 20 }}
                            />
                            {isSelected && (
                              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, fontWeight: 'bold' }}>
                                ✓ Selected
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      );
                    })}
                </Box>
              </Box>

              <Box sx={{ mb: 2, mt: 2 }}>
                <Typography gutterBottom sx={{ mb: 1.5, fontWeight: 'medium' }}>
                  Cooperation Start Round: {cooperationStart}
                </Typography>
                <Slider
                  value={cooperationStart}
                  onChange={(_, value) => setCooperationStart(value as number)}
                  min={0}
                  max={10}
                  marks
                  valueLabelDisplay="auto"
                  sx={{ mt: 2 }}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom sx={{ mb: 1.5, fontWeight: 'medium' }}>
                  Number of Game Rounds
                </Typography>
                <TextField
                  fullWidth
                  type="number"
                  value={numRounds}
                  onChange={(e) => {
                    const value = parseInt(e.target.value, 10);
                    if (!isNaN(value) && value > 0) {
                      setNumRounds(value);
                    }
                  }}
                  inputProps={{ min: 1, max: 1000 }}
                  helperText="Total number of rounds in the game. Phases will be calculated based on profile percentages."
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Available Moves */}
        <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Available Moves
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Select at least 2 moves for the game. {userCountry && computerCountry && (
                  <span>{availableMoves.length} moves available for {userCountry.name} vs {computerCountry.name}</span>
                )}
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
                gap: 1.5,
                mb: 2
              }}>
                {defaultMoves.map((move) => {
                  const isAvailable = availableMoves.includes(move.name);
                  const isSelected = selectedMoves.includes(move.name);
                  const moveType = getMoveTypeFromUiName(move.name) || move.type;
                  return (
                    <Card
                      key={move.name}
                      onClick={() => isAvailable && handleMoveToggle(move.name)}
                      sx={{
                        cursor: isAvailable ? 'pointer' : 'not-allowed',
                        border: isSelected ? '3px solid' : '2px solid',
                        borderColor: isSelected 
                          ? (moveType === 'cooperative' ? 'success.main' : 'error.main')
                          : 'divider',
                        bgcolor: isSelected 
                          ? (moveType === 'cooperative' ? 'success.light' : 'error.light')
                          : 'background.paper',
                        opacity: isAvailable ? 1 : 0.4,
                        transition: isAvailable ? 'all 0.2s ease-in-out' : 'none',
                        ...(isAvailable && {
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: 3
                          }
                        })
                      }}
                    >
                      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                        <Typography variant="body2" sx={{ fontWeight: isSelected ? 'bold' : 'normal', mb: 1 }}>
                          {move.name.replace('_', ' ').toUpperCase()}
                        </Typography>
                        <Chip 
                          label={moveType} 
                          size="small" 
                          color={moveType === 'cooperative' ? 'success' : 'error'}
                          sx={{ fontSize: '0.7rem', mb: 0.5 }}
                        />
                        {isSelected && (
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.5, fontWeight: 'bold' }}>
                            ✓ Selected
                          </Typography>
                        )}
                        {!isAvailable && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.65rem' }}>
                            Not available
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
              <Typography variant="caption" color={selectedMoves.length < 2 ? 'error' : 'text.secondary'}>
                {selectedMoves.length} of {availableMoves.length} moves selected (minimum 2 required)
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Probability Configuration - Only show for Mixed Strategy */}
        {strategy === 'mixed' && (
          <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <Card sx={{ 
              border: Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 ? '2px solid #ff9800' : '1px solid rgba(0, 0, 0, 0.12)',
              bgcolor: Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 ? 'rgba(255, 152, 0, 0.05)' : 'inherit'
            }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Move Probabilities (Mixed Strategy)
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Set the probability for each selected move. Probabilities will be automatically normalized to sum to 100%.
                </Typography>
                {Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 && (
                  <Box sx={{ mb: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1, border: '1px solid #ff9800' }}>
                    <Typography variant="body2" color="warning.dark" sx={{ fontWeight: 'bold' }}>
                      ⚠️ Warning: Total probability is not 100%. Please adjust the probabilities to sum to exactly 100% before starting the game.
                    </Typography>
                  </Box>
                )}
                {selectedMoves.map((moveName) => (
                  <Box key={moveName} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1">
                        {moveName.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Typography variant="body2" color="primary">
                        {(moveProbabilities[moveName] * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    <Slider
                      value={moveProbabilities[moveName]}
                      onChange={(_, value) => handleProbabilityChange(moveName, value as number)}
                      min={0}
                      max={1}
                      step={0.01}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${(value * 100).toFixed(1)}%`}
                    />
                  </Box>
                ))}
                <Box sx={{ 
                  mt: 2, 
                  p: 2, 
                  bgcolor: Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 ? 'warning.light' : 'grey.100', 
                  borderRadius: 1,
                  border: Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 ? '1px solid #ff9800' : 'none'
                }}>
                  <Typography variant="body2" color={Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 ? 'warning.dark' : 'text.secondary'}>
                    Total Probability: {(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) * 100).toFixed(1)}%
                    {Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01 && (
                      <span style={{ color: '#d32f2f', fontWeight: 'bold' }}> ❌ Must equal 100%</span>
                    )}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Start Game Button */}
        <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' }, display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleStartGame}
            disabled={
              !userCountry || 
              !computerCountry || 
              !selectedProfile ||
              (userCountry && computerCountry && userCountry.code === computerCountry.code) ||
              selectedMoves.length < 2 || 
              (strategy === 'mixed' && Math.abs(Object.values(moveProbabilities).reduce((sum, prob) => sum + prob, 0) - 1) > 0.01)
            }
            sx={{ px: 4, py: 1.5 }}
          >
            🚀 Start Trade War Game
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default GameSetup; 