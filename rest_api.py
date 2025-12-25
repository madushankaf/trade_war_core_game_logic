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
from game_session import GameSessionManager
from game_simulation import (
    run_single_simulation,
    run_simulation_suite,
    run_multi_profile_simulation,
    create_default_game_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
profile_manager = ProfileManager()
game_manager = GameSessionManager(profile_manager)

app = Flask(__name__)
# Configure CORS explicitly to allow all origins, methods, and headers
# This ensures proper CORS handling in production (Gunicorn + eventlet)
CORS(app, 
     resources={r"/*": {
         "origins": "*",
         "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": False
     }})
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable SocketIO with CORS

# Explicit CORS headers as backup (ensures headers are always present)
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
    return response

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

@socketio.on('join_simulation')
def handle_join_simulation(data):
    """Handle client joining a simulation room"""
    simulation_id = data.get('simulation_id')
    if simulation_id:
        join_room(simulation_id)
        emit('joined_simulation', {'simulation_id': simulation_id, 'message': 'Successfully joined simulation room'})
        logger.info(f"Client joined simulation room: {simulation_id}")

@socketio.on('leave_simulation')
def handle_leave_simulation(data):
    """Handle client leaving a simulation room"""
    simulation_id = data.get('simulation_id')
    if simulation_id:
        leave_room(simulation_id)
        emit('left_simulation', {'simulation_id': simulation_id, 'message': 'Left simulation room'})
        logger.info(f"Client left simulation room: {simulation_id}")

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

        # Override num_rounds if provided in request
        num_rounds_override = data.get('num_rounds')
        if num_rounds_override:
            # Recalculate phases if phase_percentages exist
            if computer_profile.phase_percentages:
                from game_theory import calculate_phase_boundaries
                phases = calculate_phase_boundaries(num_rounds_override, computer_profile.phase_percentages)
                # Update the profile's phases
                from profile_manager import PhaseConfig
                computer_profile.phases = PhaseConfig(
                    p1_start=phases['p1'][0],
                    p1_end=phases['p1'][1],
                    p2_start=phases['p2'][0],
                    p2_end=phases['p2'][1],
                    p3_start=phases['p3'][0],
                    p3_end=phases['p3'][1]
                )
            computer_profile.num_rounds = num_rounds_override

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

@app.route('/games/<game_id>/round', methods=['POST'])
def play_round(game_id):
    """
    Play a single round of the game.
    
    Request body (first call):
    - Full game configuration (same as /games/<game_id>/play)
    - Optional: user_move (dict with 'name' field) to override strategy
    
    Request body (subsequent calls):
    - Optional: user_move (dict with 'name' field) to override strategy
    - If game not initialized, full game configuration is required
    
    Returns:
    - Round result with moves, payoffs, and updated game state
    """
    try:
        data = request.get_json() or {}
        is_valid, error_msg = validate_json_data(data) if data else (True, None)
        
        # Check if game exists, initialize if needed
        if not game_manager.get_game(game_id):
            if not data:
                return jsonify({'error': 'Game not found. Please provide game configuration to initialize.'}), 404
            
            try:
                game_manager.initialize_game(game_id, data)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Error initializing game: {str(e)}")
                return jsonify({'error': 'Internal server error'}), 500
        
        # Get user move override if provided
        user_move_override = data.get('user_move')
        
        # Play the round
        try:
            response_data = game_manager.play_round(game_id, user_move_override)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error playing round: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500
        
        # Emit WebSocket update if client is connected
        if socketio:
            socketio.emit('round_update', response_data, room=game_id)
        
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error in play_round endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/games/<game_id>/state', methods=['GET'])
def get_game_state(game_id):
    """
    Get the current state of a game.
    
    Returns:
    - Current round, running totals, and game status
    """
    try:
        state = game_manager.get_game_state(game_id)
        return jsonify(state), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting game state: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/games/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    """
    Delete a game from memory.
    """
    try:
        if game_manager.delete_game(game_id):
            return jsonify({'message': 'Game deleted successfully'}), 200
        else:
            return jsonify({'error': 'Game not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting game: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Simulation Endpoints

@app.route('/simulation/single', methods=['POST'])
def run_single_simulation_endpoint():
    """
    Run a single simulation: one user strategy against one computer profile.
    
    Request body:
    {
        "base_game_config": {
            "user_moves": [...],
            "computer_moves": [...],
            "payoff_matrix": [...]
        },
        "user_strategy": "tit_for_tat",  # or "copy_cat", "grim_trigger", "random", "mixed"
        "computer_profile_name": "Hawkish",
        "num_rounds": 200  # optional, overrides profile default
    }
    
    Returns:
    {
        "simulation_id": str,
        "user_strategy": str,
        "computer_profile": str,
        "final_user_payoff": float,
        "final_computer_payoff": float,
        "num_rounds": int,
        "user_won": bool,
        "payoff_difference": float
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_json_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate required fields
        required_fields = ['base_game_config', 'user_strategy', 'computer_profile_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate strategy
        valid_strategies = ['copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed']
        if data['user_strategy'] not in valid_strategies:
            return jsonify({'error': f'Invalid strategy. Must be one of: {valid_strategies}'}), 400
        
        # Run simulation
        result = run_single_simulation(
            base_game_config=data['base_game_config'],
            user_strategy=data['user_strategy'],
            computer_profile_name=data['computer_profile_name'],
            profile_manager=profile_manager,
            num_rounds=data.get('num_rounds')
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in simulation: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/simulation/suite', methods=['POST'])
def run_simulation_suite_endpoint():
    """
    Run a Monte Carlo simulation suite: multiple user strategies against one computer profile.
    
    Uses a Monte Carlo approach where each simulation runs for a randomly sampled number of rounds.
    Returns 201 (Accepted) and runs simulation asynchronously. Results are sent via WebSocket.
    
    Request body:
    {
        "base_game_config": {
            "user_moves": [...],
            "computer_moves": [...],
            "payoff_matrix": [...]
        },
        "user_strategies": ["copy_cat", "tit_for_tat", "grim_trigger", "random"],
        "computer_profile_name": "Hawkish",
        "num_simulations": 5000,  # optional, default: 5000
        "rounds_mean": 200,  # optional, mean rounds for distribution (uses profile default if not provided)
        "rounds_std": 50,  # optional, standard deviation for rounds distribution (default: 50)
        "rounds_min": 50,  # optional, minimum rounds (default: 50)
        "rounds_max": 500  # optional, maximum rounds (default: 500)
    }
    
    Returns 201 with:
    {
        "simulation_id": str,
        "message": "Simulation started",
        "status": "running"
    }
    
    WebSocket events (join room with simulation_id):
    - simulation_progress: Progress updates during simulation
    - simulation_complete: Final results when simulation completes
    - simulation_error: Error occurred during simulation
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_json_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate required fields
        required_fields = ['base_game_config', 'user_strategies', 'computer_profile_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate strategies
        valid_strategies = ['copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed']
        if not isinstance(data['user_strategies'], list):
            return jsonify({'error': 'user_strategies must be a list'}), 400
        
        for strategy in data['user_strategies']:
            if strategy not in valid_strategies:
                return jsonify({'error': f'Invalid strategy: {strategy}. Must be one of: {valid_strategies}'}), 400
        
        # Generate simulation ID
        simulation_id = f"sim_suite_{uuid.uuid4()}"
        
        # Run simulation in background thread
        def run_simulation_async():
            try:
                # Emit start event
                socketio.emit('simulation_started', {
                    'simulation_id': simulation_id,
                    'message': 'Simulation started',
                    'user_strategies': data['user_strategies'],
                    'computer_profile': data['computer_profile_name'],
                    'num_simulations': data.get('num_simulations', 5000)
                }, room=simulation_id)
                
                # Run Monte Carlo simulation suite with progress updates
                result = run_simulation_suite(
                    base_game_config=data['base_game_config'],
                    user_strategies=data['user_strategies'],
                    computer_profile_name=data['computer_profile_name'],
                    profile_manager=profile_manager,
                    num_simulations=data.get('num_simulations', 5000),
                    rounds_mean=data.get('rounds_mean'),
                    rounds_std=data.get('rounds_std'),
                    rounds_min=data.get('rounds_min', 50),
                    rounds_max=data.get('rounds_max', 500),
                    socketio=socketio,
                    simulation_id=simulation_id
                )
                
                # Emit completion event with results
                socketio.emit('simulation_complete', {
                    'simulation_id': simulation_id,
                    'result': result
                }, room=simulation_id)
                
                logger.info(f"Simulation {simulation_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in background simulation {simulation_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                socketio.emit('simulation_error', {
                    'simulation_id': simulation_id,
                    'error': str(e)
                }, room=simulation_id)
        
        # Start simulation in background thread
        sim_thread = threading.Thread(target=run_simulation_async)
        sim_thread.daemon = True
        sim_thread.start()
        
        return jsonify({
            'simulation_id': simulation_id,
            'message': 'Simulation started',
            'status': 'running'
        }), 201
        
    except ValueError as e:
        logger.error(f"Validation error in simulation suite: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error starting simulation suite: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/simulation/multi-profile', methods=['POST'])
def run_multi_profile_simulation_endpoint():
    """
    Run Monte Carlo simulations across multiple computer profiles.
    
    Request body:
    {
        "base_game_config": {
            "user_moves": [...],
            "computer_moves": [...],
            "payoff_matrix": [...]
        },
        "user_strategies": ["tit_for_tat", "grim_trigger"],
        "computer_profiles": ["Hawkish", "Dovish", "Opportunist"],
        "num_simulations": 5000,  # optional, default: 5000
        "rounds_mean": 200,  # optional, mean rounds for distribution
        "rounds_std": 50,  # optional, standard deviation for rounds distribution (default: 50)
        "rounds_min": 50,  # optional, minimum rounds (default: 50)
        "rounds_max": 500  # optional, maximum rounds (default: 500)
    }
    
    Returns:
    {
        "profiles": {
            "profile_name_1": {suite_results},
            "profile_name_2": {suite_results},
            ...
        },
        "cross_profile_summary": {
            "best_strategy_overall": str,
            "strategy_averages": {strategy: avg_payoff}
        }
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_json_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate required fields
        required_fields = ['base_game_config', 'user_strategies', 'computer_profiles']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate strategies
        valid_strategies = ['copy_cat', 'tit_for_tat', 'grim_trigger', 'random', 'mixed']
        if not isinstance(data['user_strategies'], list):
            return jsonify({'error': 'user_strategies must be a list'}), 400
        
        for strategy in data['user_strategies']:
            if strategy not in valid_strategies:
                return jsonify({'error': f'Invalid strategy: {strategy}. Must be one of: {valid_strategies}'}), 400
        
        # Validate profiles is a list
        if not isinstance(data['computer_profiles'], list):
            return jsonify({'error': 'computer_profiles must be a list'}), 400
        
        # Run multi-profile Monte Carlo simulation
        result = run_multi_profile_simulation(
            base_game_config=data['base_game_config'],
            user_strategies=data['user_strategies'],
            computer_profiles=data['computer_profiles'],
            profile_manager=profile_manager,
            num_simulations=data.get('num_simulations', 5000),
            rounds_mean=data.get('rounds_mean'),
            rounds_std=data.get('rounds_std'),
            rounds_min=data.get('rounds_min', 50),
            rounds_max=data.get('rounds_max', 500)
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in multi-profile simulation: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error running multi-profile simulation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/simulation/default-config', methods=['POST'])
def create_default_config_endpoint():
    """
    Create a default game configuration from move names.
    
    Request body:
    {
        "move_names": ["open_dialogue", "raise_tariffs", "wait_and_see"],
        "move_types": {  # optional
            "open_dialogue": "cooperative",
            "raise_tariffs": "defective",
            "wait_and_see": "cooperative"
        },
        "payoff_matrix": [...]  # optional, if not provided generates default
    }
    
    Returns:
    {
        "user_moves": [...],
        "computer_moves": [...],
        "payoff_matrix": [...]
    }
    """
    try:
        data = request.get_json()
        is_valid, error_msg = validate_json_data(data)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate required fields
        if 'move_names' not in data:
            return jsonify({'error': 'Missing required field: move_names'}), 400
        
        if not isinstance(data['move_names'], list):
            return jsonify({'error': 'move_names must be a list'}), 400
        
        # Create default config
        config = create_default_game_config(
            move_names=data['move_names'],
            move_types=data.get('move_types'),
            payoff_matrix=data.get('payoff_matrix')
        )
        
        return jsonify(config), 200
        
    except Exception as e:
        logger.error(f"Error creating default config: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
