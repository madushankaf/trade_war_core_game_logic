import axios from 'axios';
import { io, Socket } from 'socket.io-client';
import { GameModel, GameResult } from '../types/game';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5010';

// WebSocket event data types
interface WebSocketMove {
  name: string;
  type: string;
}

interface RoundUpdateData {
  type: string;
  round: number;
  user_move: WebSocketMove;
  computer_move: WebSocketMove;
  user_payoff: number;
  computer_payoff: number;
  round_winner: string;
  running_totals: {
    user_total: number;
    computer_total: number;
  };
  game_status: string;
}

interface GameErrorData {
  error: string;
}


const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const gameApi = {
  // Play a game with real-time updates via WebSocket
  playGame: async (
    gameData: GameModel,
    onRoundUpdate: (data: RoundUpdateData) => void,
    onError: (error: GameErrorData) => void,
    roundDelay: number = 0.5
  ): Promise<string> => {
    return new Promise((resolve, reject) => {
      try {
        // Generate a unique game ID for this play session
        const gameId = 'game_' + Date.now();
        
        // Create WebSocket connection with proper configuration
        const socket: Socket = io(API_BASE_URL, {
          timeout: 20000,
          forceNew: true,
          reconnection: false, // Disable auto-reconnection to prevent issues
          transports: ['websocket', 'polling']
        });
        
        // Join game room
        socket.emit('join_game', { game_id: gameId });
        
        // Set up event listeners
        socket.on('joined_game', () => {
          console.log('Successfully joined game room:', gameId);
        });
        
        socket.on('game_update', (data: RoundUpdateData) => {
          console.log('Round update:', data);
          onRoundUpdate(data);
          
          // Check if this is the final round
          if (data.game_status === 'completed') {
            console.log('Game completed - final round received');
            // Give a small delay to ensure all data is processed
            setTimeout(() => {
              socket.disconnect();
              resolve(gameId);
            }, 100);
          }
        });
        
        socket.on('game_error', (error: GameErrorData) => {
          console.error('Game error:', error);
          onError(error);
          socket.disconnect();
          reject(error);
        });
        
        socket.on('disconnect', (reason) => {
          console.log('Disconnected from game room:', reason);
          if (reason === 'io server disconnect') {
            // Server initiated disconnect - this is expected when game completes
            console.log('Server disconnected - game likely completed');
          }
        });
        
        socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          onError({ error: 'Connection failed. Please try again.' });
          socket.disconnect();
          reject(error);
        });
        
        socket.on('reconnect_error', (error) => {
          console.error('WebSocket reconnection error:', error);
          onError({ error: 'Connection lost. Game may have ended.' });
          socket.disconnect();
          reject(error);
        });
        
        // Start the game with real-time updates
        api.post(`/games/${gameId}/play?delay=${roundDelay}`, gameData)
          .then(response => {
            console.log('Game started with real-time updates:', response.data);
          })
          .catch(error => {
            console.error('Error starting real-time game:', error);
            socket.disconnect();
            reject(error);
          });
          
      } catch (error) {
        console.error('Error setting up real-time game:', error);
        reject(error);
      }
    });
  },

  // Load sample game data
  loadSampleGame: async (): Promise<GameModel> => {
    try {
      const response = await fetch('/sample_game_model.json');
      return await response.json();
    } catch (error) {
      console.error('Error loading sample game:', error);
      throw error;
    }
  },
};

export default api; 