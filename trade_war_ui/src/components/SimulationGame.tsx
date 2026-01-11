import React, { useState, useEffect } from 'react';
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
  Collapse,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ErrorIcon from '@mui/icons-material/Error';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Country, GameModel } from '../types/game';
import { countries, defaultMoves } from '../data/countries';
import { profiles } from '../data/profiles';
import { getMoveTypeFromUiName, getAvailableMovesForPair, buildPayoffMatrix, countryPairExists } from '../utils/payoffMapper';
import { gameApi } from '../services/api';

interface SimulationGameProps {
  onBackToSetup?: () => void;
}

interface FailedSimulation {
  simulation_number: number;
  simulation_id: string;
  strategy: string;
  computer_profile: string;
  num_rounds: number;
  error_message: string;
  error_type: string;
  traceback?: string;
}

interface MoveStatistics {
  user_moves: {
    [moveName: string]: {
      frequency: number;
      frequency_percentage: number;
      average_payoff: number;
      win_rate: number;
      usage_count: number;
    };
  };
  computer_moves: {
    [moveName: string]: {
      frequency: number;
      frequency_percentage: number;
      average_payoff: number;
      win_rate: number;
      usage_count: number;
    };
  };
  move_combinations: {
    [comboKey: string]: {
      frequency: number;
      frequency_percentage: number;
      average_user_payoff: number;
      average_computer_payoff: number;
    };
  };
  total_moves_analyzed: number;
  total_combinations_analyzed: number;
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
  num_failed_simulations?: number;
  failed_simulations?: FailedSimulation[];
  move_statistics?: MoveStatistics;
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

// Component for displaying move histograms
const MoveHistograms: React.FC<{ moveStatistics: MoveStatistics }> = ({ moveStatistics }) => {
  // Debug: Log the computer moves data received
  console.log('MoveHistograms - computer_moves received:', moveStatistics.computer_moves);
  console.log('MoveHistograms - number of computer moves:', Object.keys(moveStatistics.computer_moves).length);
  console.log('MoveHistograms - computer move names:', Object.keys(moveStatistics.computer_moves));

  // Prepare data for user moves frequency histogram
  const userMovesFrequencyData = Object.entries(moveStatistics.user_moves).map(([name, stats]) => ({
    name: name.replace(/_/g, ' ').toUpperCase(),
    frequency: stats.frequency,
    percentage: stats.frequency_percentage.toFixed(1),
  })).sort((a, b) => b.frequency - a.frequency);

  // Prepare data for user moves win rate histogram
  const userMovesWinRateData = Object.entries(moveStatistics.user_moves).map(([name, stats]) => ({
    name: name.replace(/_/g, ' ').toUpperCase(),
    winRate: parseFloat(stats.win_rate.toFixed(1)),
    usageCount: stats.usage_count,
  })).sort((a, b) => b.winRate - a.winRate);

  // Prepare data for computer moves frequency histogram
  const computerMovesFrequencyData = Object.entries(moveStatistics.computer_moves).map(([name, stats]) => ({
    name: name.replace(/_/g, ' ').toUpperCase(),
    frequency: stats.frequency,
    percentage: stats.frequency_percentage.toFixed(1),
  })).sort((a, b) => b.frequency - a.frequency);

  // Prepare data for computer moves win rate histogram
  const computerMovesWinRateData = Object.entries(moveStatistics.computer_moves).map(([name, stats]) => ({
    name: name.replace(/_/g, ' ').toUpperCase(),
    winRate: parseFloat(stats.win_rate.toFixed(1)),
    usageCount: stats.usage_count,
  })).sort((a, b) => b.winRate - a.winRate);

  // Debug: Log the processed data
  console.log('MoveHistograms - computerMovesFrequencyData:', computerMovesFrequencyData);

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
      {/* User Moves Frequency */}
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            User Moves - Frequency
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            How often each move was used
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={userMovesFrequencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                interval={0}
                tick={{ fontSize: 10 }}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: any, name?: string) => {
                  if (name === 'frequency') {
                    const item = userMovesFrequencyData.find(d => d.frequency === value);
                    return [`${value} (${item?.percentage}%)`, 'Frequency'];
                  }
                  return [value, name ?? ''];
                }}
              />
              <Legend />
              <Bar dataKey="frequency" fill="#1976d2" name="Frequency" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* User Moves Win Rate */}
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            User Moves - Win Rate
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Success rate when each move was used
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={userMovesWinRateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                interval={0}
                tick={{ fontSize: 10 }}
              />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value: any, name?: string) => {
                  if (name === 'winRate') {
                    const item = userMovesWinRateData.find(d => d.winRate === value);
                    return [`${value.toFixed(1)}% (used in ${item?.usageCount} simulations)`, 'Win Rate'];
                  }
                  return [value, name ?? ''];
                }}
              />
              <Legend />
              <Bar dataKey="winRate" fill="#2e7d32" name="Win Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Computer Moves Frequency */}
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Computer Moves - Frequency
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            How often each move was used
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={computerMovesFrequencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                interval={0}
                tick={{ fontSize: 10 }}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: any, name?: string) => {
                  if (name === 'frequency') {
                    const item = computerMovesFrequencyData.find(d => d.frequency === value);
                    return [`${value} (${item?.percentage}%)`, 'Frequency'];
                  }
                  return [value, name ?? ''];
                }}
              />
              <Legend />
              <Bar dataKey="frequency" fill="#d32f2f" name="Frequency" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Computer Moves Win Rate */}
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Computer Moves - Win Rate
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Success rate when each move was used
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={computerMovesWinRateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                interval={0}
                tick={{ fontSize: 10 }}
              />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value: any, name?: string) => {
                  if (name === 'winRate') {
                    const item = computerMovesWinRateData.find(d => d.winRate === value);
                    return [`${value.toFixed(1)}% (used in ${item?.usageCount} simulations)`, 'Win Rate'];
                  }
                  return [value, name ?? ''];
                }}
              />
              <Legend />
              <Bar dataKey="winRate" fill="#ed6c02" name="Win Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

// Component for expandable strategy row
const StrategyRow: React.FC<{
  result: SimulationResult;
  simulationResults: SimulationSuiteResponse;
  expanded: boolean;
  onToggle: () => void;
}> = ({ result, simulationResults, expanded, onToggle }) => {
  // Calculate computer win rate
  let computerWinRate: number;
  if (result.simulations && result.simulations.length > 0 && result.simulations.length <= 1000) {
    const computerWins = result.simulations.filter((sim: any) => 
      sim.final_computer_payoff > sim.final_user_payoff
    ).length;
    computerWinRate = (computerWins / result.simulations.length) * 100;
  } else {
    computerWinRate = 100 - result.win_rate;
  }
  
  const numFailed = result.num_failed_simulations || 0;
  const hasFailures = numFailed > 0;

  return (
    <React.Fragment>
      <TableRow>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip 
              label={result.user_strategy} 
              color={simulationResults?.summary?.best_strategy && result.user_strategy === simulationResults.summary.best_strategy ? 'primary' : 'default'}
            />
            {result.move_statistics && (
              <IconButton
                size="small"
                onClick={onToggle}
                sx={{ ml: 1 }}
              >
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            )}
          </Box>
        </TableCell>
        <TableCell align="right">{result.average_user_payoff.toFixed(2)}</TableCell>
        <TableCell align="right">{result.std_user_payoff.toFixed(2)}</TableCell>
        <TableCell align="right">{result.average_computer_payoff.toFixed(2)}</TableCell>
        <TableCell align="right">{result.win_rate.toFixed(1)}%</TableCell>
        <TableCell align="right">{computerWinRate.toFixed(1)}%</TableCell>
        <TableCell align="right">{result.num_successful_simulations}</TableCell>
        <TableCell align="right">
          {hasFailures ? (
            <Chip 
              label={numFailed} 
              color="error" 
              size="small"
              icon={<ErrorIcon />}
            />
          ) : (
            <Typography variant="body2" color="text.secondary">0</Typography>
          )}
        </TableCell>
      </TableRow>
      {result.move_statistics && (
        <TableRow>
          <TableCell colSpan={8} sx={{ py: 0, border: 0 }}>
            <Collapse in={expanded} timeout="auto" unmountOnExit>
              <Box sx={{ py: 3, px: 2, bgcolor: 'rgba(0, 0, 0, 0.02)' }}>
                <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
                  Move Statistics for {result.user_strategy}
                </Typography>
                <MoveHistograms moveStatistics={result.move_statistics} />
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </React.Fragment>
  );
};

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
  const [partialResults, setPartialResults] = useState<SimulationResult[]>([]); // Track partial results in real-time
  const [simulationStats, setSimulationStats] = useState<{
    totalCompleted: number;
    currentStrategy: string;
    currentSimulation: number;
    totalSimulations: number;
    recentResults: any[];
  }>({
    totalCompleted: 0,
    currentStrategy: '',
    currentSimulation: 0,
    totalSimulations: 0,
    recentResults: []
  });
  const [numSimulations, setNumSimulations] = useState<number>(100); // Default to 100 for faster testing
  const [roundsMean, setRoundsMean] = useState<number>(15);
  const [roundsMin, setRoundsMin] = useState<number>(5);
  const [roundsMax, setRoundsMax] = useState<number>(30);
  const [expandedStrategies, setExpandedStrategies] = useState<{ [key: string]: boolean }>({});
  const [simulationProgress, setSimulationProgress] = useState<{
    currentStrategy?: string;
    strategyIndex?: number;
    totalStrategies?: number;
    progressPercentage?: number;
    message?: string;
  } | null>(null);

  const strategies = [
    { value: 'copy_cat', label: 'Copy Cat' },
    { value: 'tit_for_tat', label: 'Tit for Tat' },
    { value: 'grim_trigger', label: 'Grim Trigger' },
    { value: 'random', label: 'Random' },
    { value: 'mixed', label: 'Mixed Strategy' }
  ];

  // Helper to get display results (prioritize partial results during loading for real-time updates)
  const getDisplayResults = (): SimulationResult[] => {
    // During loading, show partial results for real-time updates
    // After loading completes, show final results
    if (loading && partialResults.length > 0) {
      console.log('📊 getDisplayResults: Returning', partialResults.length, 'partial results during loading');
      return partialResults;
    }
    if (simulationResults) {
      console.log('📊 getDisplayResults: Returning', simulationResults.results.length, 'final results');
      return simulationResults.results;
    }
    if (partialResults.length > 0) {
      console.log('📊 getDisplayResults: Returning', partialResults.length, 'partial results (no final yet)');
      return partialResults;
    }
    console.log('📊 getDisplayResults: No results available');
    return [];
  };

  // Helper to get display summary (prioritize partial during loading for real-time updates)
  const getDisplaySummary = () => {
    // During loading, calculate summary from partial results for real-time updates
    if (loading && partialResults.length > 0) {
      const bestStrategy = partialResults.reduce((best, current) => 
        current.average_user_payoff > best.average_user_payoff ? current : best
      );
      const mostWins = partialResults.reduce((best, current) => 
        current.win_rate > best.win_rate ? current : best
      );
      return {
        best_strategy: bestStrategy.user_strategy,
        most_wins: mostWins.user_strategy,
        worst_strategy: partialResults.reduce((worst, current) => 
          current.average_user_payoff < worst.average_user_payoff ? current : worst
        ).user_strategy
      };
    }
    // After loading, use final results summary
    if (simulationResults) {
      return simulationResults.summary;
    }
    return null;
  };

  // Auto-advance to results step when partial results arrive
  useEffect(() => {
    if (partialResults.length > 0 && activeStep < 2) {
      console.log('📊 useEffect: Advancing to results step, partial results:', partialResults.length);
      setActiveStep(2);
    }
  }, [partialResults.length, activeStep]);

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
    setPartialResults([]); // Reset partial results
    setSimulationProgress(null);
    setSimulationStats({
      totalCompleted: 0,
      currentStrategy: '',
      currentSimulation: 0,
      totalSimulations: 0,
      recentResults: []
    });

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
        undefined, // roundsStd no longer used - replaced with Discrete Weibull mixture model
        roundsMin,
        roundsMax,
        // Progress callback
        (progress: any) => {
          if (progress.type === 'progress') {
            setSimulationProgress({
              currentStrategy: progress.current_strategy,
              strategyIndex: progress.strategy_index,
              totalStrategies: progress.total_strategies,
              progressPercentage: progress.progress_percentage,
              message: progress.message
            });
          } else if (progress.type === 'started') {
            setSimulationProgress({
              message: 'Simulation started...'
            });
          } else if (progress.type === 'single_simulation_complete') {
            // Handle per-simulation completion for real-time updates
            console.log('📊 Single simulation completed:', progress);
            setSimulationStats(prev => ({
              ...prev,
              totalCompleted: prev.totalCompleted + 1,
              recentResults: [...prev.recentResults.slice(-9), {
                strategy: progress.user_strategy,
                user_payoff: progress.final_user_payoff,
                computer_payoff: progress.final_computer_payoff,
                user_won: progress.user_won,
                num_rounds: progress.num_rounds
              }]
            }));
          } else if (progress.type === 'round_update') {
            // Handle per-round updates during simulations
            console.log('📊 Round update:', progress);
            // Update current simulation progress
            if (progress.round) {
              setSimulationStats(prev => ({
                ...prev,
                currentSimulation: progress.round
              }));
            }
          } else if (progress.type === 'strategy_result') {
            // Handle partial strategy results in real-time
            const strategyResult = progress.strategy_result;
            console.log('📊 Strategy result received:', strategyResult.user_strategy, strategyResult);
            setPartialResults(prev => {
              // Update or add the strategy result
              const existingIndex = prev.findIndex(r => r.user_strategy === strategyResult.user_strategy);
              if (existingIndex >= 0) {
                const updated = [...prev];
                updated[existingIndex] = strategyResult;
                console.log('📊 Updated partial results, total:', updated.length);
                return updated;
              } else {
                const newResults = [...prev, strategyResult];
                console.log('📊 Added to partial results, total:', newResults.length);
                return newResults;
              }
            });
            // Note: Step advancement is handled by useEffect when partialResults changes
            // This ensures we always advance even if the callback has stale state
          } else if (progress.type === 'complete') {
            // Final results received - keep loading state until promise resolves
            // Don't clear progress yet, let the promise handler do it
            console.log('📊 Simulation complete event received');
          }
        },
        // Error callback
        (error: any) => {
          setError(error.error || 'Simulation error occurred');
          setLoading(false);
        }
      );

      // Only set final results if we don't already have them from partial updates
      // This ensures partial results are shown in real-time
      if (!simulationResults || partialResults.length === 0) {
        setSimulationResults(results);
      } else {
        // Merge final results with any partial results that might have been missed
        setSimulationResults(results);
      }
      setSimulationProgress(null);
      setActiveStep(2);
      setLoading(false);
    } catch (err: any) {
      console.error('Error running simulation:', err);
      setError(err.message || 'Failed to run simulation');
      setLoading(false);
      setSimulationProgress(null);
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
                  onChange={(e) => setRoundsMean(parseInt(e.target.value) || 15)}
                  helperText="Target average number of rounds (uses Discrete Weibull mixture model)"
                />

                <TextField
                  fullWidth
                  label="Min Rounds"
                  type="number"
                  value={roundsMin}
                  onChange={(e) => setRoundsMin(parseInt(e.target.value) || 5)}
                  helperText="Minimum number of rounds (safety limit)"
                />

                <TextField
                  fullWidth
                  label="Max Rounds"
                  type="number"
                  value={roundsMax}
                  onChange={(e) => setRoundsMax(parseInt(e.target.value) || 30)}
                  helperText="Maximum number of rounds (hard cap)"
                />
              </Box>

              {/* Model Information */}
              <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Simulation Model: Discrete Weibull Mixture
                </Typography>
                <Typography variant="body2" component="div">
                  The simulation uses a realistic stochastic model with two regimes:
                  <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                    <li><strong>80% Normal/Negotiable:</strong> Increasing hazard (conflicts get harder to resolve over time)</li>
                    <li><strong>20% Entrenched:</strong> Decreasing hazard (conflicts stabilize and persist)</li>
                  </ul>
                  This better captures the stochastic nature of trade war durations compared to simple normal distributions.
                </Typography>
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

            {loading && activeStep < 2 && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                {simulationProgress ? (
                  <>
                    <LinearProgress 
                      variant={simulationProgress.progressPercentage !== undefined ? "determinate" : "indeterminate"}
                      value={simulationProgress.progressPercentage || 0}
                      sx={{ height: 10, mb: 1.5, borderRadius: 1 }} 
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {simulationProgress.message || `Running ${numSimulations} simulations per strategy...`}
                      </Typography>
                      {simulationProgress.progressPercentage !== undefined && (
                        <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {simulationProgress.progressPercentage.toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                    {simulationProgress.currentStrategy && (
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
                        Current Strategy: <strong>{simulationProgress.currentStrategy}</strong>
                        {simulationProgress.strategyIndex && simulationProgress.totalStrategies && (
                          <> ({simulationProgress.strategyIndex} of {simulationProgress.totalStrategies})</>
                        )}
                      </Typography>
                    )}
                    <Typography variant="caption" sx={{ color: 'info.main', display: 'block', mt: 1, fontStyle: 'italic' }}>
                      Note: Each simulation is a full game with multiple rounds. Progress shows simulations completed, not rounds.
                    </Typography>
                  </>
                ) : (
                  <Box>
                    <LinearProgress sx={{ height: 10, mb: 1.5, borderRadius: 1 }} />
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Starting simulation... Running {numSimulations} simulations per strategy.
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: View Results - Show partial results in real-time */}
      {(() => {
        const shouldShow = activeStep === 2 && (simulationResults || partialResults.length > 0);
        if (shouldShow) {
          console.log('📊 Rendering results view:', {
            activeStep,
            hasSimulationResults: !!simulationResults,
            partialResultsCount: partialResults.length,
            loading,
            displayResultsCount: getDisplayResults().length
          });
        }
        return shouldShow;
      })() && (
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <CardContent sx={{ flex: 1, overflow: 'auto' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Typography variant="h5">
                Simulation Results
              </Typography>
              {loading && (
                <Chip 
                  label={partialResults.length > 0 ? "🟢 Live Updates" : "⏳ Running..."} 
                  color={partialResults.length > 0 ? "success" : "warning"} 
                  size="small"
                  sx={{ fontWeight: 'bold' }}
                />
              )}
            </Box>
            
            {/* Show progress bar at top when loading - always visible during simulation */}
            {loading && (
              <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                {simulationProgress ? (
                  <>
                    <LinearProgress 
                      variant={simulationProgress.progressPercentage !== undefined ? "determinate" : "indeterminate"}
                      value={simulationProgress.progressPercentage || 0}
                      sx={{ height: 10, mb: 1.5, borderRadius: 1 }} 
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {simulationProgress.message || 'Running simulations...'}
                      </Typography>
                      {simulationProgress.progressPercentage !== undefined && (
                        <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {simulationProgress.progressPercentage.toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                    {simulationProgress.currentStrategy && (
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
                        Current Strategy: <strong>{simulationProgress.currentStrategy}</strong>
                        {simulationProgress.strategyIndex && simulationProgress.totalStrategies && (
                          <> ({simulationProgress.strategyIndex} of {simulationProgress.totalStrategies})</>
                        )}
                      </Typography>
                    )}
                    {partialResults.length > 0 && (
                      <Typography variant="caption" sx={{ color: 'success.main', display: 'block', mt: 0.5, fontWeight: 'bold' }}>
                        ✓ {partialResults.length} strategy{partialResults.length !== 1 ? 'ies' : 'y'} completed
                      </Typography>
                    )}
                    {simulationStats.totalCompleted > 0 && (
                      <Box sx={{ mt: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block' }}>
                          📊 Real-time Stats:
                        </Typography>
                        <Typography variant="caption" sx={{ display: 'block' }}>
                          • {simulationStats.totalCompleted} simulation{simulationStats.totalCompleted !== 1 ? 's' : ''} completed
                        </Typography>
                        {simulationStats.currentStrategy && (
                          <Typography variant="caption" sx={{ display: 'block' }}>
                            • Current: {simulationStats.currentStrategy}
                          </Typography>
                        )}
                        {simulationStats.recentResults.length > 0 && (
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                            • Latest: {simulationStats.recentResults[simulationStats.recentResults.length - 1].strategy} 
                            ({simulationStats.recentResults[simulationStats.recentResults.length - 1].user_won ? 'Won' : 'Lost'})
                          </Typography>
                        )}
                      </Box>
                    )}
                    <Typography variant="caption" sx={{ color: 'info.main', display: 'block', mt: 1, fontStyle: 'italic' }}>
                      📊 Progress is per simulation (each simulation is a full game with multiple rounds)
                    </Typography>
                  </>
                ) : (
                  <Box>
                    <LinearProgress sx={{ height: 10, mb: 1.5, borderRadius: 1 }} />
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      Starting simulation...
                    </Typography>
                  </Box>
                )}
              </Box>
            )}

            {/* Summary */}
            <Alert severity={loading ? "warning" : "info"} sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Summary {loading && partialResults.length > 0 && "(Partial Results - Updating...)"}
              </Typography>
              {simulationResults && (
                <>
                  <Typography>Computer Profile: <strong>{simulationResults.computer_profile}</strong></Typography>
                  <Typography>Simulations per Strategy: <strong>{simulationResults.num_simulations}</strong></Typography>
                  <Typography>Rounds Distribution: Mean={simulationResults.rounds_statistics.mean.toFixed(1)}, 
                    Std={simulationResults.rounds_statistics.std.toFixed(1)}, 
                    Range=[{simulationResults.rounds_statistics.min}, {simulationResults.rounds_statistics.max}]
                  </Typography>
                </>
              )}
              {getDisplaySummary() && (
                <>
                  <Typography>Best Strategy: <strong>{getDisplaySummary()?.best_strategy}</strong></Typography>
                  <Typography>Most Wins: <strong>{getDisplaySummary()?.most_wins}</strong></Typography>
                </>
              )}
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
                    <TableCell align="right"><strong>Failed Sims</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {getDisplayResults().map((result) => (
                    <StrategyRow
                      key={result.user_strategy}
                      result={result}
                      simulationResults={simulationResults || {
                        computer_profile: selectedProfile,
                        num_simulations: numSimulations,
                        rounds_statistics: { mean: roundsMean, std: 0, min: roundsMin, max: roundsMax },
                        results: getDisplayResults(),
                        summary: getDisplaySummary() || { best_strategy: '', worst_strategy: '', most_wins: '' }
                      }}
                      expanded={expandedStrategies[result.user_strategy] || false}
                      onToggle={() => setExpandedStrategies(prev => ({
                        ...prev,
                        [result.user_strategy]: !prev[result.user_strategy]
                      }))}
                    />
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Failed Simulations Errors Section */}
            {getDisplayResults().some(r => r.num_failed_simulations && r.num_failed_simulations > 0) && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ color: 'error.main', display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ErrorIcon /> Failed Simulations - Error Details
                </Typography>
                {getDisplayResults().map((result) => {
                  if (!result.failed_simulations || result.failed_simulations.length === 0) {
                    return null;
                  }
                  
                  return (
                    <Accordion key={`errors-${result.user_strategy}`} sx={{ mt: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                            {result.user_strategy}
                          </Typography>
                          <Chip 
                            label={`${result.failed_simulations.length} Failed`} 
                            color="error" 
                            size="small"
                          />
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {result.failed_simulations.map((failed, idx) => (
                            <Card key={idx} variant="outlined" sx={{ bgcolor: 'rgba(211, 47, 47, 0.08)' }}>
                              <CardContent>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                                    Simulation #{failed.simulation_number} - {failed.simulation_id}
                                  </Typography>
                                  <Box sx={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 1, fontSize: '0.875rem' }}>
                                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Strategy:</Typography>
                                    <Typography variant="body2">{failed.strategy}</Typography>
                                    
                                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Profile:</Typography>
                                    <Typography variant="body2">{failed.computer_profile}</Typography>
                                    
                                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Rounds:</Typography>
                                    <Typography variant="body2">{failed.num_rounds}</Typography>
                                    
                                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Error Type:</Typography>
                                    <Typography variant="body2" sx={{ color: 'error.main' }}>{failed.error_type}</Typography>
                                    
                                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Error Message:</Typography>
                                    <Typography variant="body2" sx={{ color: 'error.main', fontFamily: 'monospace' }}>
                                      {failed.error_message}
                                    </Typography>
                                  </Box>
                                  
                                  {failed.traceback && (
                                    <Box sx={{ mt: 2 }}>
                                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                                        Full Traceback:
                                      </Typography>
                                      <Paper 
                                        variant="outlined" 
                                        sx={{ 
                                          p: 1, 
                                          bgcolor: 'rgba(0, 0, 0, 0.05)',
                                          maxHeight: 200,
                                          overflow: 'auto',
                                          fontFamily: 'monospace',
                                          fontSize: '0.75rem'
                                        }}
                                      >
                                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                          {failed.traceback}
                                        </pre>
                                      </Paper>
                                    </Box>
                                  )}
                                </Box>
                              </CardContent>
                            </Card>
                          ))}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  );
                })}
              </Box>
            )}

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

