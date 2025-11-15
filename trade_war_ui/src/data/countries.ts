import { Country } from '../types/game';

export const countries: Country[] = [
  {
    name: 'United States',
    flag: '🇺🇸',
    code: 'US'
  },
  {
    name: 'China',
    flag: '🇨🇳',
    code: 'CN'
  },
  {
    name: 'United Kingdom',
    flag: '🇬🇧',
    code: 'UK'
  },
  {
    name: 'India',
    flag: '🇮🇳',
    code: 'IN'
  },
  {
    name: 'Russia',
    flag: '🇷🇺',
    code: 'RU'
  },
  {
    name: 'Saudi Arabia',
    flag: '🇸🇦',
    code: 'SA'
  }
];

export const defaultMoves = [
  {
    name: 'open_dialogue',
    type: 'cooperative' as const,
    description: 'Initiate diplomatic talks and trade negotiations'
  },
  {
    name: 'raise_tariffs',
    type: 'defective' as const,
    description: 'Increase import tariffs on foreign goods'
  },
  {
    name: 'wait_and_see',
    type: 'cooperative' as const,
    description: 'Maintain current trade policies and observe'
  },
  {
    name: 'sanction',
    type: 'defective' as const,
    description: 'Impose economic sanctions on trading partner'
  },
  {
    name: 'subsidize_export',
    type: 'cooperative' as const,
    description: 'Provide subsidies to domestic exporters'
  },
  {
    name: 'impose_quota',
    type: 'defective' as const,
    description: 'Set import quotas to limit foreign goods'
  }
]; 