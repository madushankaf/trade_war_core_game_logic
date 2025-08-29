import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import GameSetup from './components/GameSetup';
import GameDashboard from './components/GameDashboard';
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
  const [currentView, setCurrentView] = useState<'setup' | 'game'>('setup');
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
        {currentView === 'setup' ? (
          <GameSetup onGameStart={handleGameStart} />
        ) : (
          gameData && <GameDashboard gameData={gameData} onBackToSetup={handleBackToSetup} />
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
