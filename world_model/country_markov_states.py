import numpy as np
import json
import os
import logging
import sys

# Configure logging for this module
# Check if root logger is configured, if not configure it
root_logger = logging.getLogger()
if not root_logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_JSON_PATH_FOR_COUNTRIES = os.path.join(os.path.dirname(__file__), "country_states.json")
logger.info(f"Loading country states from: {_JSON_PATH_FOR_COUNTRIES}")
with open(_JSON_PATH_FOR_COUNTRIES, "r") as f:
    _JSON_DATA_FOR_COUNTRIES = json.load(f)

COUNTRIES = _JSON_DATA_FOR_COUNTRIES["countries"]
logger.info(f"Loaded {len(COUNTRIES)} countries: {list(COUNTRIES.keys())}")

_JSON_PATH_FOR_COUPLING_RULES = os.path.join(os.path.dirname(__file__), "country_coupling_rules.json")
logger.info(f"Loading coupling rules from: {_JSON_PATH_FOR_COUPLING_RULES}")
with open(_JSON_PATH_FOR_COUPLING_RULES, "r") as f:
    _JSON_DATA_FOR_COUPLING_RULES = json.load(f)

COUPLING_RULES = _JSON_DATA_FOR_COUPLING_RULES["coupling_rules_by_country"]
logger.info(f"Loaded coupling rules for {len(COUPLING_RULES)} countries: {list(COUPLING_RULES.keys())}")

_JSON_PATH_FOR_CHANNELS_MAP = os.path.join(os.path.dirname(__file__), "channels_map.json")
logger.info(f"Loading channels map from: {_JSON_PATH_FOR_CHANNELS_MAP}")
with open(_JSON_PATH_FOR_CHANNELS_MAP, "r") as f:
    _JSON_DATA_FOR_CHANNELS_MAP = json.load(f)

CHANNELS_MAP = _JSON_DATA_FOR_CHANNELS_MAP["cap_group_state_map"]
logger.info(f"Loaded channels map: {CHANNELS_MAP}")

_JSON_PATH_FOR_LEADER_BEHAVIOURS = os.path.join(os.path.dirname(__file__), "leader_behaviours.json")
logger.info(f"Loading leader behaviours from: {_JSON_PATH_FOR_LEADER_BEHAVIOURS}")
with open(_JSON_PATH_FOR_LEADER_BEHAVIOURS, "r") as f:
    _JSON_DATA_FOR_LEADER_BEHAVIOURS = json.load(f)

LEADER_BEHAVIOURS = _JSON_DATA_FOR_LEADER_BEHAVIOURS["countries"]
logger.info(f"Loaded leader behaviours: {LEADER_BEHAVIOURS}")

def get_transition_matrix(current_state: str, country: str) -> np.ndarray:
    """
    Get the transition matrix for a given country and timestep.
    """
    if country not in COUNTRIES:
        logger.error(f"Country {country} not found. Available countries: {list(COUNTRIES.keys())}")
        raise ValueError(f"Country {country} not found in {COUNTRIES}")
    
    if current_state not in COUNTRIES[country]["P_rows_in_state_order"]:
        logger.error(f"State {current_state} not found for country {country}. Available states: {list(COUNTRIES[country]['P_rows_in_state_order'].keys())}")
        raise KeyError(f"State {current_state} not found for country {country}")
    
    transition_matrix = np.array(COUNTRIES[country]["P_rows_in_state_order"][current_state])
    logger.debug(f"Retrieved transition matrix for {country}/{current_state}: shape={transition_matrix.shape}, sum={transition_matrix.sum():.6f}")
    return transition_matrix


def get_next_state(current_state: str, country: str, timestep: int) -> str:
    """
    Get the next state based on the current state.
    """
    transition_matrix = get_transition_matrix(current_state, country)
    next_state = np.random.choice(COUNTRIES[country]["states"], p=transition_matrix)
    logger.debug(f"State transition for {country} at timestep {timestep}: {current_state} -> {next_state}")
    return next_state

def softmax(logits) -> np.ndarray:
    x = np.asarray(logits, dtype=np.float64)
    x = x - np.max(x)              # stability
    ex = np.exp(x)
    return ex / np.sum(ex)


def get_coupling_probabilities(current_state: str, country: str) -> list[float]:
    """
        Get the coupling probabilities for a given country and current state.
    """
    if country not in COUPLING_RULES:
        logger.error(f"Country {country} not found in coupling rules. Available countries: {list(COUPLING_RULES.keys())}")
        raise ValueError(f"Country {country} not found in {COUPLING_RULES}")

    country_states = COUNTRIES[country]["states"]
    
    base_probabilities = get_transition_matrix(current_state, country)
    logits = np.log(np.maximum(base_probabilities, 1e-12))
    rules = COUPLING_RULES[country]
    
    rules_applied = 0
    for rule in rules:
        source_states = rule["source_states"]
        if current_state in source_states:
            target_states = rule["target_states"]
            logit_bump = rule["logit_bump"]
            for j, state in enumerate(country_states):
                if state in target_states:
                    logits[j] += logit_bump
            rules_applied += 1
            logger.debug(f"Applied coupling rule for {country}/{current_state}: bump={logit_bump}, targets={target_states}")

    coupling_probs = softmax(logits)
    if rules_applied > 0:
        logger.debug(f"Coupling probabilities calculated for {country}/{current_state}: {rules_applied} rule(s) applied, sum={coupling_probs.sum():.6f}")
    else:
        logger.debug(f"No coupling rules matched for {country}/{current_state}, using base probabilities")
    
    return coupling_probs

def sample_categorical(states, probs):
    # u = np.random.random()
    # c = 0.0
    # for st, p in zip(states, probs, strict=True):
    #     c += p
    #     if u <= c:
    #         return st
    # return states[-1]    
    return np.random.choice(states, p=probs)
        
def calculate_world_order(no_of_weeks: int, seed: int = 42) -> list[dict]:
    """
    Calculate the world order based on the number of weeks.
    
    Args:
        no_of_weeks: Number of weeks to simulate
        seed: Random seed for reproducibility (default: 42)
        
    Returns:
        List of dictionaries, where each dictionary represents the world order at a given week.
        Each dictionary maps country names to their current state.
        The list has length no_of_weeks + 1 (initial state + no_of_weeks transitions).
    """
    logger.info(f"Starting world order simulation: {no_of_weeks} weeks, seed={seed}")
    np.random.seed(seed)
    
    # Initialize each country to a random state
    world_order = {}
    for country_name in COUNTRIES.keys():
        country_states = COUNTRIES[country_name]["states"]
        # Randomly select initial state for each country
        initial_state = np.random.choice(country_states)
        world_order[country_name] = initial_state
    
    logger.info(f"Initialized world order with {len(world_order)} countries: {list(world_order.keys())}")
    logger.debug(f"Initial states: {world_order}")
    
    trajectory = [world_order.copy()]

    for week in range(no_of_weeks):
        next_world_order = {}
        state_transitions = []
        
        for country_name in COUNTRIES.keys():
            # Get current state of this country
            current_state = world_order[country_name]
            country_states = COUNTRIES[country_name]["states"]
            
            # Calculate coupling probabilities based on current state
            coupled_probabilities = get_coupling_probabilities(current_state, country_name)
            
            # Sample next state
            next_state = sample_categorical(country_states, coupled_probabilities)
            next_world_order[country_name] = next_state
            
            if current_state != next_state:
                state_transitions.append(f"{country_name}: {current_state} -> {next_state}")
        
        world_order = next_world_order
        trajectory.append(world_order.copy())
        
        if state_transitions:
            logger.debug(f"Week {week + 1}/{no_of_weeks}: {len(state_transitions)} state transition(s): {', '.join(state_transitions)}")
    
    logger.info(f"Completed world order simulation: trajectory length={len(trajectory)}, final week states={world_order}")
    return trajectory

def run_length_geometric(q, max_weeks=260):

    t = 0
    while t < max_weeks:
        t += 1
        if np.random.random() < q:  # stop event
            break
    return t


def simulate_world_using_monte_carlo( no_of_runs: int = 1000, q: float = 0.0769, max_weeks: int = 260) -> tuple:
    """
    Simulate the world using Monte Carlo method.
    
    Args:
        no_of_runs: Number of Monte Carlo runs (default: 1000)
        q: Probability of stopping the simulation (default: 26)
        max_weeks: Maximum number of weeks to simulate (default: 260)
        
    Returns:
        A tuple containing:
        - final_distribution_per_country_state: Normalized probability distribution per country-state
          Shape: (no_of_weeks + 1, num_countries, max_num_states)
          Each country's distribution is normalized to sum to 1.0
        - final_occupancy_matrix: Normalized occupancy probabilities per country-state
          Shape: (no_of_weeks + 1, num_countries, max_num_states)
          Same as distribution (occupancy and distribution are the same for this use case)
        
    The distributions are normalized per country at each time step, so for each country
    at each time step, the probabilities across all states sum to 1.0.
    """


    # Create mappings from country names and state names to indices
    country_names = list(COUNTRIES.keys())
    country_to_idx = {country: idx for idx, country in enumerate(country_names)}
    logger.debug(f"Created country mappings for {len(country_names)} countries")
    
    # Get maximum number of states across all countries (for array sizing)
    max_num_states = max(len(COUNTRIES[country]["states"]) for country in country_names)
    logger.debug(f"Maximum number of states across all countries: {max_num_states}")
    
    # Create state to index mappings for each country
    country_state_to_idx = {}
    for country_name in country_names:
        states = COUNTRIES[country_name]["states"]
        country_state_to_idx[country_name] = {state: idx for idx, state in enumerate(states)}
    
    # Initialize count matrices
    # Shape: (time_steps, num_countries, max_num_states)
    counts_per_country_state = np.zeros((max_weeks + 1, len(country_names), max_num_states))
    logger.debug(f"Initialized count matrix: shape={counts_per_country_state.shape}")
    
    # Run Monte Carlo simulations
    logger.info(f"Running {no_of_runs} Monte Carlo simulations...")
    progress_interval = max(100, no_of_runs // 10)  # Log progress every 10% or every 100 runs
    
    for run in range(no_of_runs):
        if (run + 1) % progress_interval == 0 or (run + 1) == no_of_runs:
            logger.info(f"Progress: {run + 1}/{no_of_runs} runs completed ({(run + 1) / no_of_runs * 100:.1f}%)")
        
        no_of_weeks = run_length_geometric(q=q, max_weeks=max_weeks)
        logger.info(f"Starting Monte Carlo simulation: {no_of_weeks} weeks, {no_of_runs} runs")
        trajectory = calculate_world_order(no_of_weeks, seed=run+1)
        for t, world_order in enumerate(trajectory):
            for country_name, state in world_order.items():
                country_idx = country_to_idx[country_name]
                state_idx = country_state_to_idx[country_name][state]
                counts_per_country_state[t, country_idx, state_idx] += 1
    
    logger.info(f"Completed all {no_of_runs} Monte Carlo runs. Normalizing distributions...")
    
    # Normalize per country at each time step
    # Initialize normalized distributions
    final_distribution_per_country_state = np.zeros_like(counts_per_country_state, dtype=np.float64)
    
    normalization_errors = 0
    for t in range(no_of_weeks + 1):
        for country_idx, country_name in enumerate(country_names):
            # Get counts for this country at this time step
            country_counts = counts_per_country_state[t, country_idx, :]
            num_states = len(COUNTRIES[country_name]["states"])
            
            # Normalize only the relevant states for this country
            total_count = country_counts[:num_states].sum()
            if total_count > 0:
                # Normalize so probabilities sum to 1.0 for this country
                final_distribution_per_country_state[t, country_idx, :num_states] = country_counts[:num_states] / total_count
                
                # Verify normalization
                prob_sum = final_distribution_per_country_state[t, country_idx, :num_states].sum()
                if not np.isclose(prob_sum, 1.0, atol=1e-6):
                    logger.warning(f"Normalization issue at t={t}, country={country_name}: sum={prob_sum:.6f} (expected 1.0)")
                    normalization_errors += 1
            else:
                logger.warning(f"Zero counts at t={t} for country={country_name}, cannot normalize")
            # States beyond num_states remain 0 (not applicable for this country)
    
    if normalization_errors > 0:
        logger.warning(f"Found {normalization_errors} normalization issues during processing")
    else:
        logger.debug("All distributions normalized correctly (sum to 1.0)")
    
    # Occupancy matrix is the same as distribution for this use case
    final_occupancy_matrix = final_distribution_per_country_state.copy()
    
    logger.info(f"Monte Carlo simulation completed. Returning distributions: shape={final_distribution_per_country_state.shape}")
    return final_distribution_per_country_state, final_occupancy_matrix


if __name__ == "__main__":
    final_distribution_per_country_state, final_occupancy_matrix = simulate_world_using_monte_carlo( no_of_runs=10000, q=0.0096, max_weeks=260)
    print(final_distribution_per_country_state)
    print(final_occupancy_matrix)
    

            
        


    

