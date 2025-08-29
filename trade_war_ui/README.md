# 🎮 Trade War Game UI

A React-based user interface for the Trade War Game Theory simulation. This UI provides an interactive way to configure and play trade war scenarios between countries using sophisticated game theory algorithms.

## Features

### Phase 1: Core Game Interface
- **Game Setup Screen**: Country selection, strategy configuration, and game parameters
- **Main Game Dashboard**: Real-time game monitoring with visual feedback
- **Round Results View**: Detailed analysis of each round's outcomes

### Phase 2.1: Visual Game Elements
- **Trade Route Visualization**: Animated connections between countries
- **Economic Indicators**: Charts showing trade balance and GDP impact
- **Move Animations**: Visual feedback for different move types
- **Modern UI Design**: Clean, intuitive interface with Material-UI components

## Technology Stack

- **Frontend**: React 18 with TypeScript
- **UI Framework**: Material-UI (MUI) v5
- **State Management**: React Hooks
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Routing**: React Router DOM

## Project Structure

```
src/
├── components/
│   ├── GameSetup.tsx      # Game configuration interface
│   └── GameDashboard.tsx  # Main game dashboard
├── types/
│   └── game.ts           # TypeScript type definitions
├── services/
│   └── api.ts            # API communication layer
├── data/
│   └── countries.ts      # Country and move definitions
└── App.tsx               # Main application component
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- The Flask backend running on `http://localhost:5010`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Backend Integration

Make sure your Flask backend is running:
```bash
cd ../  # Go back to the main project directory
python rest_api.py
```

The UI will automatically connect to the backend API at `http://localhost:5010`.

## Usage

### 1. Game Setup
- Select your country and opponent country from the dropdown menus
- Choose your strategy (Copy Cat, Tit for Tat, Grim Trigger, Random, or Mixed)
- Configure your first move and cooperation start round
- Select available moves for the game
- Click "Start Trade War Game" to begin

### 2. Game Dashboard
- View real-time game progress and controls
- Monitor your available moves and strategy configuration
- See game history and round-by-round results
- View final payoffs and game outcomes

### 3. Game Results
- Analyze final payoffs for both players
- Review game history and move patterns
- Understand strategy effectiveness

## Game Theory Strategies

- **Copy Cat**: Copies your opponent's last move
- **Tit for Tat**: Starts cooperative, then copies opponent
- **Grim Trigger**: Cooperates until opponent defects, then always defects
- **Random**: Chooses moves randomly
- **Mixed**: Uses probability-based strategy

## Available Moves

- **Cooperative Moves**: `open_dialogue`, `wait_and_see`, `subsidize_export`
- **Defective Moves**: `raise_tariffs`, `sanction`, `impose_quota`

## API Endpoints

The UI communicates with the Flask backend using these endpoints:

- `POST /games/test/play` - Play a complete game simulation
- `GET /sample_game_model.json` - Load sample game configuration

## Development

### Building for Production

```bash
npm run build
```

### Running Tests

```bash
npm test
```

### Code Formatting

```bash
npm run format
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Trade War Game Theory simulation system.

## Support

For issues and questions, please refer to the main project documentation or create an issue in the repository.
