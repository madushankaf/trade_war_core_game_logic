import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import GameSetup from './components/GameSetup';
import GameDashboard from './components/GameDashboard';
import StepByStepGame from './components/StepByStepGame';
import SimulationGame from './components/SimulationGame';
import { GameModel } from './types/game';

// Create a custom theme for the trade war game
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 12,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
});

function App() {
  const [currentView, setCurrentView] = useState<'setup' | 'game' | 'step-by-step' | 'simulate'>('setup');
  const [gameData, setGameData] = useState<GameModel | null>(null);

  const handleGameStart = (data: GameModel) => {
    setGameData(data);
    setCurrentView('game');
  };

  const handleBackToSetup = () => {
    setCurrentView('setup');
    setGameData(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default', overflow: 'hidden' }}>
        {/* Navigation Bar */}
        <AppBar position="static" sx={{ flexShrink: 0 }}>
          <Toolbar sx={{ minHeight: '40px !important', py: 0.25 }}>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontSize: '0.875rem' }}>
              🎮 Trade War Game
            </Typography>
            <Button 
              color="inherit" 
              onClick={() => setCurrentView('setup')}
              sx={{ mr: 0.5, fontSize: '0.75rem', minWidth: 'auto', px: 0.75, py: 0.25 }}
            >
              Game Setup
            </Button>
            <Button 
              color="inherit" 
              onClick={() => setCurrentView('step-by-step')}
              sx={{ mr: 0.5, fontSize: '0.75rem', minWidth: 'auto', px: 0.75, py: 0.25 }}
            >
              Step-by-Step
            </Button>
            <Button 
              color="inherit" 
              onClick={() => setCurrentView('simulate')}
              sx={{ fontSize: '0.75rem', minWidth: 'auto', px: 0.75, py: 0.25 }}
            >
              Simulate
            </Button>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {currentView === 'setup' ? (
            <GameSetup onGameStart={handleGameStart} />
          ) : currentView === 'step-by-step' ? (
            <StepByStepGame onBackToSetup={() => setCurrentView('setup')} />
          ) : currentView === 'simulate' ? (
            <SimulationGame onBackToSetup={() => setCurrentView('setup')} />
          ) : (
            gameData && <GameDashboard gameData={gameData} onBackToSetup={handleBackToSetup} />
          )}
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
