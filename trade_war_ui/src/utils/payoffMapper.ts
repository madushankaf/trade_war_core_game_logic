/**
 * Utility to map two_country_games_with_payoffs.json data to backend game model format
 */

import payoffData from '../data/two_country_games_with_payoffs.json';

interface PayoffEntry {
  player: string;
  opponent: string;
  move: string;
  strategy_type: 'cooperative' | 'defective';
  rationale: string;
  base_payoff: number;
}

interface MoveMapping {
  uiName: string; // e.g., 'open_dialogue'
  dataName: string; // e.g., 'OPEN DIALOGUE'
  type: 'cooperative' | 'defective';
}

/**
 * Move name mapping between UI format and data format
 */
const MOVE_MAPPING: MoveMapping[] = [
  { uiName: 'open_dialogue', dataName: 'OPEN DIALOGUE', type: 'cooperative' },
  { uiName: 'raise_tariffs', dataName: 'RAISE TARIFFS', type: 'defective' },
  { uiName: 'wait_and_see', dataName: 'WAIT AND SEE', type: 'cooperative' },
  { uiName: 'sanction', dataName: 'SANCTION', type: 'defective' },
  { uiName: 'subsidize_export', dataName: 'SUBSIDIZE EXPORT', type: 'cooperative' },
  { uiName: 'impose_quota', dataName: 'IMPOSE QUOTA', type: 'defective' },
];

/**
 * Convert UI move name to data format
 */
function uiToDataMoveName(uiName: string): string {
  const mapping = MOVE_MAPPING.find(m => m.uiName === uiName);
  return mapping ? mapping.dataName : uiName.toUpperCase().replace(/_/g, ' ');
}

/**
 * Convert data move name to UI format
 */
function dataToUiMoveName(dataName: string): string {
  const mapping = MOVE_MAPPING.find(m => m.dataName === dataName);
  return mapping ? mapping.uiName : dataName.toLowerCase().replace(/\s+/g, '_');
}

/**
 * Get move type from data
 */
function getMoveType(dataName: string): 'cooperative' | 'defective' {
  const mapping = MOVE_MAPPING.find(m => m.dataName === dataName);
  return mapping ? mapping.type : 'cooperative';
}

/**
 * Get available moves for a country pair
 */
export function getAvailableMovesForPair(
  userCountry: string,
  computerCountry: string
): string[] {
  const entries = (payoffData as PayoffEntry[]).filter(
    entry => entry.player === userCountry && entry.opponent === computerCountry
  );
  
  return entries.map(entry => dataToUiMoveName(entry.move));
}

/**
 * Get payoff for a specific move combination
 */
export function getPayoffForMove(
  userCountry: string,
  computerCountry: string,
  userMove: string,
  computerMove: string
): { user: number; computer: number } | null {
  const userMoveDataName = uiToDataMoveName(userMove);
  const computerMoveDataName = uiToDataMoveName(computerMove);
  
  // Find user's payoff (user country making user move against computer country)
  const userEntry = (payoffData as PayoffEntry[]).find(
    entry =>
      entry.player === userCountry &&
      entry.opponent === computerCountry &&
      entry.move === userMoveDataName
  );
  
  // Find computer's payoff (computer country making computer move against user country)
  const computerEntry = (payoffData as PayoffEntry[]).find(
    entry =>
      entry.player === computerCountry &&
      entry.opponent === userCountry &&
      entry.move === computerMoveDataName
  );
  
  if (!userEntry || !computerEntry) {
    return null;
  }
  
  return {
    user: userEntry.base_payoff,
    computer: computerEntry.base_payoff,
  };
}

/**
 * Build payoff matrix for a country pair and selected moves
 */
export function buildPayoffMatrix(
  userCountry: string,
  computerCountry: string,
  userMoves: string[],
  computerMoves: string[]
): Array<{
  user_move_name: string;
  computer_move_name: string;
  payoff: { user: number; computer: number };
}> {
  const payoffMatrix: Array<{
    user_move_name: string;
    computer_move_name: string;
    payoff: { user: number; computer: number };
  }> = [];
  
  for (const userMove of userMoves) {
    for (const computerMove of computerMoves) {
      const payoff = getPayoffForMove(userCountry, computerCountry, userMove, computerMove);
      
      if (payoff) {
        payoffMatrix.push({
          user_move_name: userMove,
          computer_move_name: computerMove,
          payoff,
        });
      } else {
        // Fallback: use default payoffs if data not found
        console.warn(
          `Payoff not found for ${userCountry} (${userMove}) vs ${computerCountry} (${computerMove}), using defaults`
        );
        payoffMatrix.push({
          user_move_name: userMove,
          computer_move_name: computerMove,
          payoff: { user: 2, computer: 2 }, // Default neutral payoff
        });
      }
    }
  }
  
  return payoffMatrix;
}

/**
 * Check if a country pair exists in the data
 */
export function countryPairExists(
  userCountry: string,
  computerCountry: string
): boolean {
  const entries = (payoffData as PayoffEntry[]).filter(
    entry => entry.player === userCountry && entry.opponent === computerCountry
  );
  return entries.length > 0;
}

/**
 * Get all available country pairs
 */
export function getAvailableCountryPairs(): Array<{ user: string; computer: string }> {
  const pairs = new Set<string>();
  
  (payoffData as PayoffEntry[]).forEach(entry => {
    pairs.add(`${entry.player}|${entry.opponent}`);
  });
  
  return Array.from(pairs).map(pair => {
    const [user, computer] = pair.split('|');
    return { user, computer };
  });
}

/**
 * Get move type from UI move name
 */
export function getMoveTypeFromUiName(uiName: string): 'cooperative' | 'defective' {
  const mapping = MOVE_MAPPING.find(m => m.uiName === uiName);
  return mapping ? mapping.type : 'cooperative';
}

