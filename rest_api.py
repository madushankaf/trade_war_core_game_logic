from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from typing import Dict, List, Optional, Tuple
import uuid
from game_moves import GameMoves
from game_theory import play_full_game

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Game map to store game objects
game_map: Dict[str, dict] = {}

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Game Lifecycle Endpoints

@app.route('/games', methods=['POST'])
def create_game():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['user_country', 'computer_country', 'computer_strategies', 'user_strategies']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create new game
        game_id = str(uuid.uuid4())
        game_map[game_id] = {
            'user_country': data['user_country'],
            'computer_country': data['computer_country'],
            'computer_strategies': data['computer_strategies'],
            'user_strategies': data['user_strategies'],  # List of strategy objects
            'moves': GameMoves()  # Initialize empty moves list
        }

        return jsonify({
            'gameId': game_id   
        }), 201

    except Exception as e:
        logger.error(f"Error creating game: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/games/<game_id>', methods=['GET'])
def get_game_state(game_id):
    try:
        if game_id not in game_map:
            return jsonify({'error': 'Game not found'}), 404

        game = game_map[game_id]
        return jsonify({
            'user_country': game['user_country'],
            'computer_country': game['computer_country'],
            'computer_strategies': game['computer_strategies'],
            'user_strategies': game['user_strategies'],
            'moves': game['moves'].get_moves()
        }), 200

    except Exception as e:
        logger.error(f"Error getting game state: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/games/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    try:
        if game_id not in game_map:
            return jsonify({'error': 'Game not found'}), 404

        del game_map[game_id]
        return jsonify({'message': 'Game deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Error deleting game: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# User Configuration Endpoints

@app.route('/games/<game_id>/user-strategy', methods=['PUT'])
def set_user_strategy(game_id):
    try:
        if game_id not in game_map:
            return jsonify({'error': 'Game not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate strategy type
        valid_types = ['copy_cat', 'tit_for_tat', 'grim_trigger']
        if 'type' not in data or data['type'] not in valid_types:
            return jsonify({'error': f'Invalid strategy type. Must be one of: {valid_types}'}), 400

        # Validate probability if provided
        if 'probability' in data:
            if not 0 <= data['probability'] <= 1:
                return jsonify({'error': 'Probability must be between 0 and 1'}), 400

        # Add strategy to user's strategies
        strategy = {
            'type': data['type'],
            'probability': data.get('probability', 1.0)  # Default to 1.0 if not provided
        }
        
        game_map[game_id]['user_strategies'].append(strategy)
        
        return jsonify({
            'message': 'Strategy added successfully',
            'strategy': strategy
        }), 200

    except Exception as e:
        logger.error(f"Error setting user strategy: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/games/<game_id>/settings', methods=['PATCH'])
def update_game_settings(game_id):
    try:
        if game_id not in game_map:
            return jsonify({'error': 'Game not found'}), 404

        game = game_map[game_id]
        if game['current_round'] > 0:
            return jsonify({'error': 'Cannot change settings after game has started'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update settings
        for key, value in data.items():
            if key in game['settings']:
                if key == 'discount' and not 0 <= value <= 1:
                    return jsonify({'error': 'Discount factor must be between 0 and 1'}), 400
                if key == 'tremble_prob' and not 0 <= value <= 1:
                    return jsonify({'error': 'Tremble probability must be between 0 and 1'}), 400
                game['settings'][key] = value

        return jsonify({'message': 'Settings updated successfully'}), 200

    except Exception as e:
        logger.error(f"Error updating game settings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/games/<game_id>/play', methods=['POST'])
def play_game(game_id):
    try:
        if game_id not in game_map:
            return jsonify({'error': 'Game not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        game = game_map[game_id]
        moves, user_dominant, computer_dominant = play_full_game(game)
        game['moves'] = GameMoves()  # Reset moves
        for user_move, computer_move in moves:
            game['moves'].add_moves(user_move, computer_move)

        return jsonify({
            'message': 'Game completed successfully',
            'moves': moves,
            'dominant_strategies': {
                'user': user_dominant,
                'computer': computer_dominant
            }
        }), 200

    except Exception as e:
        logger.error(f"Error during game play: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
