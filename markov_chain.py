import numpy as np
import json
import os

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
