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
  LinearProgress,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { Country, GameModel } from '../types/game';
import { countries, defaultMoves } from '../data/countries';
import { profiles } from '../data/profiles';
import { getMoveTypeFromUiName, getAvailableMovesForPair, buildPayoffMatrix, countryPairExists } from '../utils/payoffMapper';
import { gameApi } from '../services/api';

interface SimulationGameProps {
  onBackToSetup?: () => void;
}

interface SimulationResult {
  user_strategy: string;
  simulations: any[];
  average_user_payoff: number;
  average_computer_payoff: number;
  average_payoff_difference: number;
  win_rate: number;
  std_user_payoff: number;
  std_computer_payoff: number;
  num_successful_simulations: number;
}

interface SimulationSuiteResponse {
  computer_profile: string;
  num_simulations: number;
  rounds_statistics: {
    mean: number;
    std: number;
    min: number;
    max: number;
  };
  results: SimulationResult[];
  summary: {
    best_strategy: string;
    worst_strategy: string;
    most_wins: string;
  };
}

const SimulationGame: React.FC<SimulationGameProps> = ({ onBackToSetup }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [userCountry, setUserCountry] = useState<Country | null>(null);
  const [opponentCountry, setOpponentCountry] = useState<Country | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(['copy_cat', 'tit_for_tat']);
  const [availableMoves, setAvailableMoves] = useState<string[]>(defaultMoves.map(m => m.name));
  const [sameCountryError, setSameCountryError] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulationResults, setSimulationResults] = useState<SimulationSuiteResponse | null>(null);
  const [numSimulations, setNumSimulations] = useState<number>(100); // Default to 100 for faster testing
  const [roundsMean, setRoundsMean] = useState<number>(200);
  const [roundsStd, setRoundsStd] = useState<number>(50);
  const [roundsMin, setRoundsMin] = useState<number>(50);
  const [roundsMax, setRoundsMax] = useState<number>(500);

  const strategies = [
    { value: 'copy_cat', label: 'Copy Cat' },
    { value: 'tit_for_tat', label: 'Tit for Tat' },
    { value: 'grim_trigger', label: 'Grim Trigger' },
    { value: 'random', label: 'Random' },
    { value: 'mixed', label: 'Mixed Strategy' }
  ];

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

  const handleCountrySelect = (country: Country, type: 'user' | 'opponent') => {
    if (type === 'user') {
      setUserCountry(country);
    } else {
      setOpponentCountry(country);
    }
  };

  const handleProfileSelect = (profileName: string) => {
    setSelectedProfile(profileName);
  };

  const handleStrategyToggle = (strategy: string) => {
    setSelectedStrategies(prev => {
      if (prev.includes(strategy)) {
        return prev.filter(s => s !== strategy);
      } else {
        return [...prev, strategy];
      }
    });
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
        strategy: 'copy_cat', // This will be overridden in simulation
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

  const handleRunSimulation = async () => {
    if (!userCountry || !opponentCountry || !selectedProfile) {
      setError('Please select countries and computer profile');
      return;
    }

    if (selectedStrategies.length === 0) {
      setError('Please select at least one strategy to test');
      return;
    }

    setLoading(true);
    setError(null);
    setSimulationResults(null);

    try {
      const gameData = buildGameData();
      
      // Extract base game config for simulation
      const baseGameConfig = {
        user_moves: gameData.user_moves,
        computer_moves: gameData.computer_moves,
        payoff_matrix: gameData.payoff_matrix,
      };

      const results = await gameApi.runSimulationSuite(
        baseGameConfig,
        selectedStrategies,
        selectedProfile,
        numSimulations,
        roundsMean,
        roundsStd,
        roundsMin,
        roundsMax
      );

      setSimulationResults(results);
      setActiveStep(2);
      setLoading(false);
    } catch (err: any) {
      console.error('Error running simulation:', err);
      setError(err.message || 'Failed to run simulation');
      setLoading(false);
    }
  };

  const steps = ['Select Countries & Profile', 'Configure Simulation', 'View Results'];

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
        📊 Monte Carlo Simulation
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

      {/* Step 0: Select Countries & Profile */}
      {activeStep === 0 && (
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <CardContent sx={{ flex: 1, overflow: 'auto' }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
              Select Countries & Computer Profile
            </Typography>

            {sameCountryError && (
              <Alert severity="error" sx={{ mb: 2 }}>{sameCountryError}</Alert>
            )}

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              {/* User Country Selection */}
              <Box>
                <Typography variant="h6" gutterBottom>Your Country</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {countries.map((country) => (
                    <Chip
                      key={country.code}
                      label={`${country.flag} ${country.name}`}
                      onClick={() => handleCountrySelect(country, 'user')}
                      color={userCountry?.code === country.code ? 'primary' : 'default'}
                      sx={{ fontSize: '0.9rem', py: 2.5, cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              </Box>

              {/* Opponent Country Selection */}
              <Box>
                <Typography variant="h6" gutterBottom>Opponent Country</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {countries.map((country) => (
                    <Chip
                      key={country.code}
                      label={`${country.flag} ${country.name}`}
                      onClick={() => handleCountrySelect(country, 'opponent')}
                      color={opponentCountry?.code === country.code ? 'primary' : 'default'}
                      sx={{ fontSize: '0.9rem', py: 2.5, cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              </Box>

              {/* Computer Profile Selection */}
              <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
                <Typography variant="h6" gutterBottom>Computer Behavior Profile</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {Object.keys(profiles).map((profileName) => (
                    <Chip
                      key={profileName}
                      label={profileName}
                      onClick={() => handleProfileSelect(profileName)}
                      color={selectedProfile === profileName ? 'primary' : 'default'}
                      sx={{ fontSize: '0.9rem', py: 2.5, cursor: 'pointer' }}
                    />
                  ))}
                </Box>
                {selectedProfile && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {profiles[selectedProfile as keyof typeof profiles]?.description || ''}
                  </Typography>
                )}
              </Box>
            </Box>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => setActiveStep(1)}
                disabled={!userCountry || !opponentCountry || !selectedProfile}
                sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}
              >
                Next: Configure Simulation
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Step 1: Configure Simulation */}
      {activeStep === 1 && (
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <CardContent sx={{ flex: 1, overflow: 'auto' }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
              Configure Simulation Parameters
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Strategy Selection */}
              <Box>
                <Typography variant="h6" gutterBottom>Strategies to Test</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {strategies.map((strategy) => (
                    <Chip
                      key={strategy.value}
                      label={strategy.label}
                      onClick={() => handleStrategyToggle(strategy.value)}
                      color={selectedStrategies.includes(strategy.value) ? 'primary' : 'default'}
                      sx={{ fontSize: '0.9rem', py: 2, cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              </Box>

              {/* Simulation Parameters */}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
                <TextField
                  fullWidth
                  label="Number of Simulations"
                  type="number"
                  value={numSimulations}
                  onChange={(e) => setNumSimulations(parseInt(e.target.value) || 100)}
                  helperText="Number of simulations per strategy (default: 100, max recommended: 5000)"
                  inputProps={{ min: 10, max: 5000 }}
                />

                <TextField
                  fullWidth
                  label="Mean Rounds"
                  type="number"
                  value={roundsMean}
                  onChange={(e) => setRoundsMean(parseInt(e.target.value) || 200)}
                  helperText="Average number of rounds per simulation"
                />

                <TextField
                  fullWidth
                  label="Rounds Std Deviation"
                  type="number"
                  value={roundsStd}
                  onChange={(e) => setRoundsStd(parseFloat(e.target.value) || 50)}
                  helperText="Standard deviation for rounds distribution"
                />

                <TextField
                  fullWidth
                  label="Min Rounds"
                  type="number"
                  value={roundsMin}
                  onChange={(e) => setRoundsMin(parseInt(e.target.value) || 50)}
                />

                <TextField
                  fullWidth
                  label="Max Rounds"
                  type="number"
                  value={roundsMax}
                  onChange={(e) => setRoundsMax(parseInt(e.target.value) || 500)}
                />
              </Box>
            </Box>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="outlined"
                size="large"
                onClick={() => setActiveStep(0)}
                sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}
              >
                Back
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={handleRunSimulation}
                disabled={loading || selectedStrategies.length === 0}
                sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}
              >
                {loading ? 'Running Simulation...' : 'Run Simulation'}
              </Button>
            </Box>

            {loading && (
              <Box sx={{ mt: 3 }}>
                <LinearProgress sx={{ height: 8 }} />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                  Running {numSimulations} simulations per strategy. This may take a while...
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: View Results */}
      {activeStep === 2 && simulationResults && (
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <CardContent sx={{ flex: 1, overflow: 'auto' }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
              Simulation Results
            </Typography>

            {/* Summary */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>Summary</Typography>
              <Typography>Computer Profile: <strong>{simulationResults.computer_profile}</strong></Typography>
              <Typography>Simulations per Strategy: <strong>{simulationResults.num_simulations}</strong></Typography>
              <Typography>Best Strategy: <strong>{simulationResults.summary.best_strategy}</strong></Typography>
              <Typography>Most Wins: <strong>{simulationResults.summary.most_wins}</strong></Typography>
              <Typography>Rounds Distribution: Mean={simulationResults.rounds_statistics.mean.toFixed(1)}, 
                Std={simulationResults.rounds_statistics.std.toFixed(1)}, 
                Range=[{simulationResults.rounds_statistics.min}, {simulationResults.rounds_statistics.max}]
              </Typography>
            </Alert>

            {/* Results Table */}
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Strategy</strong></TableCell>
                    <TableCell align="right"><strong>Avg User Payoff</strong></TableCell>
                    <TableCell align="right"><strong>Std Dev</strong></TableCell>
                    <TableCell align="right"><strong>Avg Computer Payoff</strong></TableCell>
                    <TableCell align="right"><strong>User Win Rate %</strong></TableCell>
                    <TableCell align="right"><strong>Computer Win Rate %</strong></TableCell>
                    <TableCell align="right"><strong>Successful Sims</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {simulationResults.results.map((result) => {
                    // Calculate computer win rate
                    // If simulations array is available and not too large, calculate from data
                    // Otherwise, use 100 - user_win_rate (assuming no ties or treating ties as losses)
                    let computerWinRate: number;
                    if (result.simulations && result.simulations.length > 0 && result.simulations.length <= 1000) {
                      // Calculate from actual data for accuracy (handles ties)
                      const computerWins = result.simulations.filter((sim: any) => 
                        sim.final_computer_payoff > sim.final_user_payoff
                      ).length;
                      computerWinRate = (computerWins / result.simulations.length) * 100;
                    } else {
                      // Fallback: assume computer win rate is 100 - user win rate
                      // (ties would be excluded from both, but this is a reasonable approximation)
                      computerWinRate = 100 - result.win_rate;
                    }
                    
                    return (
                      <TableRow key={result.user_strategy}>
                        <TableCell>
                          <Chip 
                            label={result.user_strategy} 
                            color={result.user_strategy === simulationResults.summary.best_strategy ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">{result.average_user_payoff.toFixed(2)}</TableCell>
                        <TableCell align="right">{result.std_user_payoff.toFixed(2)}</TableCell>
                        <TableCell align="right">{result.average_computer_payoff.toFixed(2)}</TableCell>
                        <TableCell align="right">{result.win_rate.toFixed(1)}%</TableCell>
                        <TableCell align="right">{computerWinRate.toFixed(1)}%</TableCell>
                        <TableCell align="right">{result.num_successful_simulations}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="outlined"
                size="large"
                onClick={() => {
                  setActiveStep(0);
                  setSimulationResults(null);
                }}
                sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}
              >
                Run New Simulation
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default SimulationGame;

