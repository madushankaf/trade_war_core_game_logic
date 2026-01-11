import numpy as np
import json
import os
from typing import Optional
# Load data from markov_states.json
_JSON_PATH = os.path.join(os.path.dirname(__file__), "markov_states.json")
with open(_JSON_PATH, "r") as f:
    _JSON_DATA = json.load(f)

# Extract states
STATES = _JSON_DATA["states"]
STATE_TO_IDX = {state: idx for idx, state in enumerate(STATES)}
IDX_TO_STATE = {idx: state for idx, state in enumerate(STATES)}

def _json_matrix_to_numpy(json_matrix: dict) -> np.ndarray:
    """
    Convert JSON transition matrix (dict format) to numpy array.
    JSON format: {"from_state": {"to_state": prob, ...}, ...}
    """
    n = len(STATES)
    matrix = np.zeros((n, n))
    
    for from_state in STATES:
        from_idx = STATE_TO_IDX[from_state]
        json_key = f"from_{from_state}"
        if json_key in json_matrix:
            for to_state in STATES:
                to_idx = STATE_TO_IDX[to_state]
                json_key_to = f"to_{to_state}"
                if json_key_to in json_matrix[json_key]:
                    matrix[from_idx, to_idx] = json_matrix[json_key][json_key_to]
    
    return matrix

# Load transition matrices
P0 = _json_matrix_to_numpy(_JSON_DATA["transition_matrix_p0"])
P_inf_default = _json_matrix_to_numpy(_JSON_DATA["transition_matrix_p0_inf_default"])

# Load P_inf by type
P_INF_BY_TYPE = {}
for actor_type, json_matrix in _JSON_DATA["p_inf_by_type"].items():
    P_INF_BY_TYPE[actor_type] = _json_matrix_to_numpy(json_matrix)

# Load actor type parameters from JSON
ACTOR_TYPE_PARAMS = {}
for actor_type, params in _JSON_DATA["actor_type_params"].items():
    ACTOR_TYPE_PARAMS[actor_type] = params.copy()

# Load states_to_move_mapping and create reverse mapping (state -> list of moves)
STATES_TO_MOVE_MAPPING = _JSON_DATA.get("states_to_move_mapping", {})
STATE_TO_MOVES = {}  # Reverse mapping: state -> list of moves
for move_name, states_list in STATES_TO_MOVE_MAPPING.items():
    for state in states_list:
        if state not in STATE_TO_MOVES:
            STATE_TO_MOVES[state] = []
        STATE_TO_MOVES[state].append(move_name)

def alpha(t: int, tau: float, beta: float = 1.0) -> float:
    """
    Round-based weight in [0,1] that increases with t.
    """
    t = float(max(1, t))
    return 1.0 - np.exp(- (t / tau) ** beta)

def tau_for_target_alpha(t_target: int, alpha_target: float, beta: float) -> float:
    """
    Choose tau so that alpha(t_target) ~= alpha_target for a given beta.
    """
    if not (0.0 < alpha_target < 1.0):
        raise ValueError("alpha_target must be in (0,1)")
    return t_target / ((-np.log(1.0 - alpha_target)) ** (1.0 / beta))

# Compute tau for each actor type
for tname, p in ACTOR_TYPE_PARAMS.items():
    p["tau"] = tau_for_target_alpha(
        t_target=30,
        alpha_target=p["alpha_at_end"],
        beta=p["beta"]
    )

def transition_matrix_round(round_num: int, actor_type: str) -> np.ndarray:
    """
    Time-inhomogeneous Markov transition matrix for a given round and actor type:
    Pt = (1 - alpha) * P0 + alpha * P_inf(type)
    """
    if actor_type not in ACTOR_TYPE_PARAMS:
        raise KeyError(f"Unknown actor_type={actor_type}. Choose from {list(ACTOR_TYPE_PARAMS.keys())}")

    params = ACTOR_TYPE_PARAMS[actor_type]
    a = alpha(round_num, params["tau"], params["beta"])
    P_inf = P_INF_BY_TYPE.get(actor_type, P_inf_default)

    Pt = (1.0 - a) * P0 + a * P_inf

    # numerical safety
    Pt = np.clip(Pt, 0.0, 1.0)
    row_sums = Pt.sum(axis=1, keepdims=True)
    # avoid divide-by-zero (shouldn't happen if inputs are valid)
    row_sums = np.where(row_sums == 0.0, 1.0, row_sums)
    Pt = Pt / row_sums
    return Pt

def get_next_state(current_state: str, actor_type: str, round_num: int, rng=None) -> str:
    """
    Get the next state based on the current state, actor type, and round number.
    
    Args:
        current_state: Current state (must be in STATES)
        actor_type: Actor type (must be in ACTOR_TYPE_PARAMS)
        round_num: Round number
        rng: Optional numpy random number generator (default_rng instance)
    
    Returns:
        Next state (string)
    """
    if current_state not in STATE_TO_IDX:
        raise KeyError(f"Unknown current_state={current_state}. Choose from {STATES}")
    
    if rng is None:
        rng = np.random.default_rng()
    
    # Get transition matrix for this round and actor type
    Pt = transition_matrix_round(round_num, actor_type)
    
    # Get transition probabilities from current state
    current_idx = STATE_TO_IDX[current_state]
    probs = Pt[current_idx, :]
    
    # Sample next state
    next_idx = rng.choice(len(STATES), p=probs)
    next_state = IDX_TO_STATE[next_idx]
    
    return next_state


def get_next_move_based_on_markov_chain(current_move: str, actor_type: str, round_num: int, rng=None) -> Optional[str]:
    """
    Get the next move based on the current move, actor type, and round number.
    
    This function:
    1. Maps the input move to the corresponding Markov state(s)
    2. Randomly selects one state if multiple states map to the move
    3. Uses that state as the current state for the Markov chain transition
    4. Returns the move corresponding to the next state
    
    Args:
        current_move: Current move name (must be in STATES_TO_MOVE_MAPPING)
        actor_type: Actor type (must be in ACTOR_TYPE_PARAMS)
        round_num: Round number
        rng: Optional numpy random number generator (default_rng instance)
    
    Returns:
        Move name (string) corresponding to the next state, or None if no mapping exists
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Map the move to the corresponding Markov state(s)
    if current_move not in STATES_TO_MOVE_MAPPING:
        # Move not in mapping, return None
        return None
    
    possible_states = STATES_TO_MOVE_MAPPING[current_move]
    if not possible_states:
        # No states mapped to this move, return None
        return None
    
    # Normalize state names to handle inconsistencies (e.g., "opportunist" vs "opportunistic")
    # Check if we need to map "opportunist" to "opportunistic" or vice versa
    normalized_states = []
    for s in possible_states:
        if s in STATE_TO_IDX:
            normalized_states.append(s)
        elif s == "opportunist" and "opportunistic" in STATE_TO_IDX:
            # Map "opportunist" to "opportunistic" if it exists
            normalized_states.append("opportunistic")
        elif s == "opportunistic" and "opportunist" in STATE_TO_IDX:
            # Map "opportunistic" to "opportunist" if it exists
            normalized_states.append("opportunist")
    
    if not normalized_states:
        # No valid states found, return None
        return None
    
    # If multiple valid states map to this move, randomly select one
    # Otherwise, use the single state
    if len(normalized_states) == 1:
        current_state = normalized_states[0]
    else:
        current_state = rng.choice(normalized_states)
    
    # Get the next state from the Markov chain using the mapped state
    # Wrap in try-except to handle cases where transition probabilities are invalid
    # (but let KeyError propagate for invalid actor types or states)
    try:
        next_state = get_next_state(current_state, actor_type, round_num, rng)
    except ValueError as e:
        # If we can't get the next state due to invalid probabilities, return None
        return None
    
    # Map the next state to a move using the states_to_move_mapping
    if next_state in STATE_TO_MOVES:
        available_moves = STATE_TO_MOVES[next_state]
        if available_moves:
            # Randomly select one of the moves associated with this state
            selected_move = rng.choice(available_moves)
            return selected_move
        else:
            # No moves available for this state, return the state as fallback
            return next_state
    else:
        # State not in mapping, return None
        return None