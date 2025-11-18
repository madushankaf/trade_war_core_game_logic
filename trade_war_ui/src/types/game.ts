export type PlayerType = 'user' | 'computer';
export type MoveType = 'cooperative' | 'defective' | 'mixed';
export type StrategyType = 'copy_cat' | 'tit_for_tat' | 'grim_trigger' | 'random' | 'mixed';

export interface Move {
  name: string;
  type: MoveType;
  probability: number;
  player: PlayerType;
}

export interface PayoffEntry {
  user_move_name: string;
  computer_move_name: string;
  payoff: {
    user: number;
    computer: number;
  };
}

export interface UserStrategySettings {
  strategy: StrategyType;
  first_move?: string;
  cooperation_start?: number;
  mixed_strategy_array?: string[] | null;
}

export interface GameState {
  equalizer_strategy?: number[] | null;
  round_idx: number;
  last_strategy_update: number;
  generated_mixed_moves_array?: string[] | null;
  last_computer_move?: string | null;
}

export interface GameModel {
  user_moves: Move[];
  computer_moves: Move[];
  payoff_matrix: PayoffEntry[];
  user_strategy_settings: UserStrategySettings;
  computer_profile_name: string;
  computer_profile?: {
    name: string;
    settings: any;
  };
  countries?: {
    user: Country;
    computer: Country;
  };
  state: GameState;
  num_rounds?: number; // Optional: number of game rounds (defaults to profile's num_rounds)
}

export interface GameResult {
  final_user_payoff: number;
  final_computer_payoff: number;
}

export interface RoundMove {
  user_move: Move;
  computer_move: Move;
  user_payoff: number;
  computer_payoff: number;
  round: number;
}

export interface Country {
  name: string;
  flag: string;
  code: string;
} 