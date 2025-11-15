import axios from 'axios';
import { io, Socket } from 'socket.io-client';
import { GameModel } from '../types/game';
import {
  buildPayoffMatrix,
  getMoveTypeFromUiName,
  countryPairExists,
  getAvailableMovesForPair,
} from '../utils/payoffMapper';
import { defaultMoves } from '../data/countries';
import { profiles } from '../data/profiles';

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

  // Load sample game data using dynamic payoffs
  loadSampleGame: async (): Promise<GameModel> => {
    try {
      // Use US vs China as default sample game
      const userCountryName = 'United States';
      const computerCountryName = 'China';
      const defaultProfile = 'Hawkish';
      
      // Get available moves for the country pair, or use all default moves
      const availableMoves = countryPairExists(userCountryName, computerCountryName)
        ? getAvailableMovesForPair(userCountryName, computerCountryName)
        : defaultMoves.map(m => m.name);
      
      // Use first 3 available moves as sample
      const sampleMoves = availableMoves.slice(0, 3).length >= 2
        ? availableMoves.slice(0, 3)
        : ['open_dialogue', 'raise_tariffs', 'wait_and_see'];
      
      // Build payoff matrix dynamically
      const payoffMatrix = countryPairExists(userCountryName, computerCountryName)
        ? buildPayoffMatrix(userCountryName, computerCountryName, sampleMoves, sampleMoves)
        : sampleMoves.flatMap(userMove =>
            sampleMoves.map(computerMove => ({
              user_move_name: userMove,
              computer_move_name: computerMove,
              payoff: { user: 2, computer: 2 }, // Default fallback
            }))
          );
      
      // Create sample game model
      const sampleGame: GameModel = {
        user_moves: sampleMoves.map(moveName => ({
          name: moveName,
          type: getMoveTypeFromUiName(moveName) || defaultMoves.find(m => m.name === moveName)?.type || 'cooperative',
          probability: 1 / sampleMoves.length,
          player: 'user' as const,
        })),
        computer_moves: sampleMoves.map(moveName => ({
          name: moveName,
          type: getMoveTypeFromUiName(moveName) || defaultMoves.find(m => m.name === moveName)?.type || 'cooperative',
          probability: 1 / sampleMoves.length,
          player: 'computer' as const,
        })),
        payoff_matrix: payoffMatrix,
        user_strategy_settings: {
          strategy: 'copy_cat',
          first_move: sampleMoves[0],
          cooperation_start: 2,
          mixed_strategy_array: null,
        },
        computer_profile_name: defaultProfile,
        computer_profile: {
          name: defaultProfile,
          settings: profiles[defaultProfile as keyof typeof profiles],
        },
        countries: {
          user: {
            name: userCountryName,
            flag: '🇺🇸',
            code: 'US',
          },
          computer: {
            name: computerCountryName,
            flag: '🇨🇳',
            code: 'CN',
          },
        },
        state: {
          equalizer_strategy: null,
          round_idx: 0,
          last_strategy_update: 0,
          generated_mixed_moves_array: null,
          last_computer_move: null,
        },
      };
      
      return sampleGame;
    } catch (error) {
      console.error('Error generating sample game:', error);
      throw error;
    }
  },
};

export default api; 