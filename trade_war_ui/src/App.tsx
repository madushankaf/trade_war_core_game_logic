import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import GameSetup from './components/GameSetup';
import GameDashboard from './components/GameDashboard';
import StepByStepGame from './components/StepByStepGame';
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
  const [currentView, setCurrentView] = useState<'setup' | 'game' | 'step-by-step'>('setup');
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
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        {/* Navigation Bar */}
        <AppBar position="static" sx={{ mb: 3 }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              🎮 Trade War Game
            </Typography>
            <Button 
              color="inherit" 
              onClick={() => setCurrentView('setup')}
              sx={{ mr: 2 }}
            >
              Game Setup
            </Button>
            <Button 
              color="inherit" 
              onClick={() => setCurrentView('step-by-step')}
            >
              Step-by-Step
            </Button>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        {currentView === 'setup' ? (
          <GameSetup onGameStart={handleGameStart} />
        ) : currentView === 'step-by-step' ? (
          <StepByStepGame onBackToSetup={() => setCurrentView('setup')} />
        ) : (
          gameData && <GameDashboard gameData={gameData} onBackToSetup={handleBackToSetup} />
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
