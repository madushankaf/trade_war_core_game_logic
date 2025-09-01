import axios from 'axios';
import { GameModel, GameResult } from '../types/game';

const API_BASE_URL = `${process.env.API_BASE_URL}` || 'http://localhost:5010';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const gameApi = {
  // Play a game with the provided game model
  playGame: async (gameData: GameModel): Promise<GameResult> => {
    try {
      const response = await api.post('/games/test/play', gameData);
      return response.data.payoff_outcome;
    } catch (error) {
      console.error('Error playing game:', error);
      throw error;
    }
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