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
  Chip,
  Paper
} from '@mui/material';
import { Country, StrategyType, Move } from '../types/game';
import { countries, defaultMoves } from '../data/countries';

interface GameSetupProps {
  onGameStart: (gameData: any) => void;
}

const GameSetup: React.FC<GameSetupProps> = ({ onGameStart }) => {
  const [userCountry, setUserCountry] = useState<Country | null>(null);
  const [computerCountry, setComputerCountry] = useState<Country | null>(null);
  const [strategy, setStrategy] = useState<StrategyType>('copy_cat');
  const [firstMove, setFirstMove] = useState<string>('open_dialogue');
  const [cooperationStart, setCooperationStart] = useState<number>(2);
  const [selectedMoves, setSelectedMoves] = useState<string[]>(['open_dialogue', 'raise_tariffs', 'wait_and_see']);

  const strategies = [
    { value: 'copy_cat', label: 'Copy Cat', description: 'Copy your opponent\'s last move' },
    { value: 'tit_for_tat', label: 'Tit for Tat', description: 'Start cooperative, then copy opponent' },
    { value: 'grim_trigger', label: 'Grim Trigger', description: 'Cooperate until opponent defects, then always defect' },
    { value: 'random', label: 'Random', description: 'Choose moves randomly' },
    { value: 'mixed', label: 'Mixed Strategy', description: 'Use probability-based strategy' }
  ];

  const handleStartGame = () => {
    if (!userCountry || !computerCountry) {
      alert('Please select both countries');
      return;
    }

    // Create game data structure
    const gameData = {
      user_moves: selectedMoves.map(moveName => {
        const moveInfo = defaultMoves.find(m => m.name === moveName);
        return {
          name: moveName,
          type: moveInfo?.type || 'cooperative',
          probability: 1 / selectedMoves.length,
          player: 'user' as const
        };
      }),
      computer_moves: selectedMoves.map(moveName => {
        const moveInfo = defaultMoves.find(m => m.name === moveName);
        return {
          name: moveName,
          type: moveInfo?.type || 'cooperative',
          probability: 1 / selectedMoves.length,
          player: 'computer' as const
        };
      }),
      payoff_matrix: generatePayoffMatrix(selectedMoves),
      user_strategy_settings: {
        strategy,
        first_move: firstMove,
        cooperation_start: cooperationStart,
        mixed_strategy_array: null
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
            user: Math.floor(Math.random() * 5) + 1,
            computer: Math.floor(Math.random() * 5) + 1
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
              <FormControl fullWidth>
                <InputLabel>Opponent Country</InputLabel>
                <Select
                  value={computerCountry?.code || ''}
                  onChange={(e) => {
                    const country = countries.find(c => c.code === e.target.value);
                    setComputerCountry(country || null);
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
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
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

        {/* Start Game Button */}
        <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' }, display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleStartGame}
            disabled={!userCountry || !computerCountry || selectedMoves.length < 2}
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