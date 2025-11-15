from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from typing import Dict, List, Optional, Tuple
import uuid
import json
import threading
from game_moves import GameMoves
from game_theory import play_full_game
from game_model import GameModel
from profile_manager import ProfileManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
profile_manager = ProfileManager()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable SocketIO with CORS

# Game map to store game objects
game_map: Dict[str, dict] = {}

# WebSocket event handlers
@socketio.on('join_game')
def handle_join_game(data):
    """Handle client joining a game room"""
    game_id = data.get('game_id')
    if game_id:
        join_room(game_id)
        emit('joined_game', {'game_id': game_id, 'message': 'Successfully joined game room'})
        logger.info(f"Client joined game room: {game_id}")

@socketio.on('leave_game')
def handle_leave_game(data):
    """Handle client leaving a game room"""
    game_id = data.get('game_id')
    if game_id:
        leave_room(game_id)
        emit('left_game', {'game_id': game_id, 'message': 'Left game room'})
        logger.info(f"Client left game room: {game_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    logger.info('Client disconnected')

def validate_json_data(data):
    """
    Validate that the request data is valid JSON.
    
    Args:
        data: The data from request.get_json()
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if data is None:
        return False, "No JSON data provided"
    
    if not isinstance(data, dict):
        return False, "Data must be a JSON object"
    
    return True, None

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return jsonify({'status': 'healthy'}), 200

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

# @app.route('/games', methods=['POST'])
# def create_game():
#     try:
#         data = request.get_json()
#         is_valid, error_msg = validate_json_data(data)
#         if not is_valid:
#             return jsonify({'error': error_msg}), 400

#         # Validate required fields
#         required_fields = ['user_country', 'computer_country', 'computer_strategies', 'user_strategies']
#         for field in required_fields:
#             if field not in data:
#                 return jsonify({'error': f'Missing required field: {field}'}), 400

#         # Create new game
#         game_id = str(uuid.uuid4())
#         game_map[game_id] = {
#             'user_country': data['user_country'],
#             'computer_country': data['computer_country'],
#             'computer_strategies': data['computer_strategies'],
#             'user_strategies': data['user_strategies'],  # List of strategy objects
#             'moves': GameMoves()  # Initialize empty moves list
#         }

#         return jsonify({
#             'gameId': game_id   
#         }), 201

#     except Exception as e:
#         logger.error(f"Error creating game: {str(e)}")
#         return jsonify({'error': 'Internal server error'}), 500

# @app.route('/games/<game_id>', methods=['GET'])
# def get_game_state(game_id):
#     try:
#         if game_id not in game_map:
#             return jsonify({'error': 'Game not found'}), 404

#         game = game_map[game_id]
#         return jsonify({
#             'user_country': game['user_country'],
#             'computer_country': game['computer_country'],
#             'computer_strategies': game['computer_strategies'],
#             'user_strategies': game['user_strategies'],
#             'moves': game['moves'].get_moves()
#         }), 200

#     except Exception as e:
#         logger.error(f"Error getting game state: {str(e)}")
#         return jsonify({'error': 'Internal server error'}), 500

# @app.route('/games/<game_id>', methods=['DELETE'])
# def delete_game(game_id):
#     try:
#         if game_id not in game_map:
#             return jsonify({'error': 'Game not found'}), 404

#         del game_map[game_id]
#         return jsonify({'message': 'Game deleted successfully'}), 200

#     except Exception as e:
#         logger.error(f"Error deleting game: {str(e)}")
#         return jsonify({'error': 'Internal server error'}), 500

# User Configuration Endpoints

# @app.route('/games/<game_id>/user-strategy', methods=['PUT'])
# def set_user_strategy(game_id):
#     try:
#         if game_id not in game_map:
#             return jsonify({'error': 'Game not found'}), 404

#         data = request.get_json()
#         is_valid, error_msg = validate_json_data(data)
#         if not is_valid:
#             return jsonify({'error': error_msg}), 400

#         # Validate strategy type
#         valid_types = ['copy_cat', 'tit_for_tat', 'grim_trigger']
#         if 'type' not in data or data['type'] not in valid_types:
#             return jsonify({'error': f'Invalid strategy type. Must be one of: {valid_types}'}), 400

#         # Validate probability if provided
#         if 'probability' in data:
#             if not 0 <= data['probability'] <= 1:
#                 return jsonify({'error': 'Probability must be between 0 and 1'}), 400

#         # Add strategy to user's strategies
#         strategy = {
#             'type': data['type'],
#             'probability': data.get('probability', 1.0)  # Default to 1.0 if not provided
#         }
        
#         game_map[game_id]['user_strategies'].append(strategy)
        
#         return jsonify({
#             'message': 'Strategy added successfully',
#             'strategy': strategy
#         }), 200

#     except Exception as e:
#         logger.error(f"Error setting user strategy: {str(e)}")
#         return jsonify({'error': 'Internal server error'}), 500

# @app.route('/games/<game_id>/settings', methods=['PATCH'])
# def update_game_settings(game_id):
#     try:
#         if game_id not in game_map:
#             return jsonify({'error': 'Game not found'}), 404

#         game = game_map[game_id]
#         if game['current_round'] > 0:
#             return jsonify({'error': 'Cannot change settings after game has started'}), 400

#         data = request.get_json()
#         is_valid, error_msg = validate_json_data(data)
#         if not is_valid:
#             return jsonify({'error': error_msg}), 400

#         # Update settings
#         for key, value in data.items():
#             if key in game['settings']:
#                 if key == 'discount' and not 0 <= value <= 1:
#                     return jsonify({'error': 'Discount factor must be between 0 and 1'}), 400
#                 if key == 'tremble_prob' and not 0 <= value <= 1:
#                     return jsonify({'error': 'Tremble probability must be between 0 and 1'}), 400
#                 game['settings'][key] = value

#         return jsonify({'message': 'Settings updated successfully'}), 200

#     except Exception as e:
#         logger.error(f"Error updating game settings: {str(e)}")
#         return jsonify({'error': 'Internal server error'}), 500

@app.route('/games/<game_id>/play', methods=['POST'])
def play_game(game_id):
    try:
        data = request.get_json()
        is_valid, error_msg = validate_json_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        # Validate the game data using GameModel
        try:
            game_model = GameModel.from_dict(data)
            # Convert back to dict for play_full_game
            game = game_model.to_dict()
        except Exception as validation_error:
            logger.error(f"Game data validation error: {str(validation_error)}")
            return jsonify({'error': f'Invalid game data: {str(validation_error)}'}), 400

        # Get round delay from query parameter (default: 0.5 seconds)
        round_delay = float(request.args.get('delay', '0.5'))

        computer_profile_name = data.get('computer_profile_name')
        if not computer_profile_name:
            return jsonify({'error': 'Computer profile name is required'}), 400

        computer_profile = profile_manager.get_profile(computer_profile_name)
        if not computer_profile:
            return jsonify({'error': f'Computer profile not found: {computer_profile_name}'}), 400

        game['computer_profile_name'] = computer_profile_name
        game['computer_profile'] = computer_profile.to_dict()
        # Run game with real-time updates in background thread
        def run_game_with_websocket():
            try:
                payoff_outcome, iteration_moves = play_full_game(game, socketio, game_id, round_delay)
                logger.info(f"Game {game_id} completed successfully")
            except Exception as e:
                logger.error(f"Error in background game: {str(e)}")
                socketio.emit('game_error', {'error': str(e)}, room=game_id)
        
        # Start game in background thread
        game_thread = threading.Thread(target=run_game_with_websocket)
        game_thread.daemon = True
        game_thread.start()
        
        return jsonify({
            'message': 'Game started with real-time updates',
            'game_id': game_id
        }), 200

    except Exception as e:
        logger.error(f"Error during game play: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    import os
    # Check if running in production
    flask_env = os.environ.get('FLASK_ENV', 'development')
    is_production = flask_env == 'production'
    
    if is_production:
        # In production, use eventlet server directly (Gunicorn will be used via CMD in Dockerfile)
        # But for direct python execution, we'll use eventlet
        socketio.run(app, debug=False, host='0.0.0.0', port=5010, allow_unsafe_werkzeug=True)
    else:
        # In development, use Werkzeug with debug mode
        socketio.run(app, debug=True, host='0.0.0.0', port=5010)
