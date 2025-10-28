import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Button,
  Chip
} from '@mui/material';
import { Country, StrategyType } from '../types/game';
import { countries, defaultMoves } from '../data/countries';
import { profiles } from '../data/profiles';

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

  const strategies = [
    { value: 'copy_cat', label: 'Copy Cat', description: 'Copy your opponent\'s last move' },
    { value: 'tit_for_tat', label: 'Tit for Tat', description: 'Start cooperative, then copy opponent' },
    { value: 'grim_trigger', label: 'Grim Trigger', description: 'Cooperate until opponent defects, then always defect' },
    { value: 'random', label: 'Random', description: 'Choose moves randomly' },
    { value: 'mixed', label: 'Mixed Strategy', description: 'Use probability-based strategy' }
  ];

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
    
    if (!selectedProfile) {
      alert('Please select a computer behavior profile');
      return;
    }

    // Normalize probabilities before starting game
    if (strategy === 'mixed') {
      normalizeProbabilities();
    }

    // Create game data structure
    const gameData = {
      user_moves: selectedMoves.map(moveName => {
        const moveInfo = defaultMoves.find(m => m.name === moveName);
        return {
          name: moveName,
          type: moveInfo?.type || 'cooperative',
          probability: strategy === 'mixed' ? moveProbabilities[moveName] : 1 / selectedMoves.length,
          player: 'user' as const
        };
      }),
      computer_moves: selectedMoves.map(moveName => {
        const moveInfo = defaultMoves.find(m => m.name === moveName);
        return {
          name: moveName,
          type: moveInfo?.type || 'cooperative',
          probability: strategy === 'mixed' ? moveProbabilities[moveName] : 1 / selectedMoves.length,
          player: 'computer' as const
        };
      }),
      payoff_matrix: generatePayoffMatrix(selectedMoves),
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
      }
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
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom align="center">
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
              <FormControl fullWidth>
                <InputLabel>Your Country</InputLabel>
                <Select
                  value={userCountry?.code || ''}
                  onChange={(e) => {
                    const country = countries.find(c => c.code === e.target.value);
                    setUserCountry(country || null);
                  }}
                >
                  {countries.map((country) => (
                    <MenuItem key={country.code} value={country.code}>
                      {country.flag} {country.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Opponent Country
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Opponent Country</InputLabel>
                <Select
                  value={computerCountry?.code || ''}
                  onChange={(e) => {
                    const country = countries.find(c => c.code === e.target.value);
                    setComputerCountry(country || null);
                    // Reset profile selection when country changes
                    if (!country) {
                      setSelectedProfile('');
                    }
                  }}
                >
                  {countries.map((country) => (
                    <MenuItem key={country.code} value={country.code}>
                      {country.flag} {country.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {/* Profile Selection - Only enabled when opponent country is selected */}
              <FormControl fullWidth disabled={!computerCountry}>
                <InputLabel>Computer Behavior Profile</InputLabel>
                <Select
                  value={selectedProfile}
                  onChange={(e) => setSelectedProfile(e.target.value)}
                  disabled={!computerCountry}
                >
                  {Object.entries(profiles).map(([profileName, profileData]) => (
                    <MenuItem key={profileName} value={profileName}>
                      <Box>
                        <Typography variant="subtitle1">{profileName}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {profileData.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Box>

        {/* Profile Description - Only show when profile is selected */}
        {selectedProfile && (
          <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
            <Card sx={{ bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  🤖 Selected Computer Profile: {selectedProfile}
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {profiles[selectedProfile as keyof typeof profiles]?.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This profile will determine how the computer opponent behaves during the game.
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
                Strategy Configuration
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Strategy Type</InputLabel>
                <Select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value as StrategyType)}
                >
                  {strategies.map((strat) => (
                    <MenuItem key={strat.value} value={strat.value}>
                      <Box>
                        <Typography variant="subtitle1">{strat.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {strat.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>First Move</InputLabel>
                <Select
                  value={firstMove}
                  onChange={(e) => setFirstMove(e.target.value)}
                >
                  {defaultMoves.map((move) => (
                    <MenuItem key={move.name} value={move.name}>
                      {move.name.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  Cooperation Start Round: {cooperationStart}
                </Typography>
                <Slider
                  value={cooperationStart}
                  onChange={(_, value) => setCooperationStart(value as number)}
                  min={0}
                  max={10}
                  marks
                  valueLabelDisplay="auto"
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
                Available Moves
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {defaultMoves.map((move) => (
                  <Chip
                    key={move.name}
                    label={`${move.name.replace('_', ' ').toUpperCase()} (${move.type})`}
                    color={selectedMoves.includes(move.name) ? 'primary' : 'default'}
                    onClick={() => handleMoveToggle(move.name)}
                    variant={selectedMoves.includes(move.name) ? 'filled' : 'outlined'}
                    sx={{ mb: 1 }}
                  />
                ))}
              </Box>
              <Typography variant="caption" color="text.secondary">
                Selected moves: {selectedMoves.length} (minimum 2 required)
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