import json
import os
import random
from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass
class PhaseConfig:
    """Configuration for game phases"""
    p1_start: int
    p1_end: int
    p2_start: int
    p2_end: int
    p3_start: int
    p3_end: int
    
    @classmethod
    def from_percentages(cls, num_rounds: int, phase_percentages: Dict[str, float]):
        """
        Create PhaseConfig from percentages and total rounds.
        
        Args:
            num_rounds: Total number of game rounds
            phase_percentages: Dictionary with phase percentages, e.g. {'p1': 0.20, 'p2': 0.50, 'p3': 0.30}
        """
        from game_theory import calculate_phase_boundaries
        phases = calculate_phase_boundaries(num_rounds, phase_percentages)
        return cls(
            p1_start=phases['p1'][0],
            p1_end=phases['p1'][1],
            p2_start=phases['p2'][0],
            p2_end=phases['p2'][1],
            p3_start=phases['p3'][0],
            p3_end=phases['p3'][1]
        )


@dataclass
class EpsilonConfig:
    """Configuration for epsilon (exploration) schedule"""
    type: str  # 'constant', 'linear', 'decay', 'piecewise', 'linear_decay'
    value: Optional[float] = None  # for constant
    start: Optional[float] = None  # for linear/decay
    end: Optional[float] = None  # for linear/decay
    end_round: Optional[int] = None  # for linear/decay
    base: Optional[float] = None  # for decay
    floor: Optional[float] = None  # for decay
    tau: Optional[int] = None  # for decay
    values: Optional[Dict[str, float]] = None  # for piecewise
    switch_round: Optional[int] = None  # for piecewise


@dataclass
class SecurityConfig:
    """Configuration for security level triggers"""
    trigger: Dict[str, Any]
    prob: float


@dataclass
class RetaliationConfig:
    """Configuration for retaliation behavior"""
    user_defected_prev: Optional[Dict[str, Any]] = None
    user_coop_streak_ge: Optional[Dict[str, Any]] = None
    user_defected_first: Optional[Dict[str, Any]] = None
    user_defected_last_2: Optional[Dict[str, Any]] = None


@dataclass
class MixedStrategyConfig:
    """Configuration for mixed strategy behavior"""
    refresh_every: int
    bias: Dict[str, Any]


# Mapping from profile names to Markov chain actor types
PROFILE_TO_ACTOR_TYPE = {
    "Hawkish": "aggressive",
    "Dovish": "isolationist",
    "Opportunist": "opportunist",
    "TitForTatPlus": "neutralist",
    "GrimTriggerPlus": "aggressive",
    "GenerousTFT": "neutralist",
    "SecurityFirst": "isolationist",
    "NoisyExplorer": "opportunist",
}

def get_actor_type_for_profile(profile_name: str) -> str:
    """
    Map profile name to Markov chain actor type.
    
    Args:
        profile_name: Name of the profile (e.g., "Hawkish", "Opportunist")
    
    Returns:
        Actor type string for Markov chain (e.g., "aggressive", "opportunist")
        Defaults to "neutralist" if profile not found in mapping
    """
    return PROFILE_TO_ACTOR_TYPE.get(profile_name, "neutralist")


@dataclass
class ProfileConfig:
    """Complete profile configuration"""
    name: str
    phases: PhaseConfig
    dominant_probabilities: Dict[str, float]
    epsilon_schedule: EpsilonConfig
    security_level: SecurityConfig
    retaliation: RetaliationConfig
    mixed_strategy: MixedStrategyConfig
    description: str
    num_rounds: int = 200  # Default number of rounds
    phase_percentages: Optional[Dict[str, float]] = None  # Optional: percentages for phases
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProfileConfig to dictionary"""
        result = {
            'name': self.name,
            'type': get_actor_type_for_profile(self.name),  # Add Markov chain actor type
            'phases': {
                'p1': [self.phases.p1_start, self.phases.p1_end],
                'p2': [self.phases.p2_start, self.phases.p2_end],
                'p3': [self.phases.p3_start, self.phases.p3_end]
            },
            'dominant_probabilities': self.dominant_probabilities,
            'epsilon_schedule': {
                'type': self.epsilon_schedule.type,
                'value': self.epsilon_schedule.value,
                'start': self.epsilon_schedule.start,
                'end': self.epsilon_schedule.end,
                'end_round': self.epsilon_schedule.end_round,
                'base': self.epsilon_schedule.base,
                'floor': self.epsilon_schedule.floor,
                'tau': self.epsilon_schedule.tau,
                'values': self.epsilon_schedule.values,
                'switch_round': self.epsilon_schedule.switch_round
            },
            'security_level': {
                'trigger': self.security_level.trigger,
                'prob': self.security_level.prob
            },
            'retaliation': {
                'user_defected_prev': self.retaliation.user_defected_prev,
                'user_coop_streak_ge': self.retaliation.user_coop_streak_ge,
                'user_defected_first': self.retaliation.user_defected_first,
                'user_defected_last_2': self.retaliation.user_defected_last_2
            },
            'mixed_strategy': {
                'refresh_every': self.mixed_strategy.refresh_every,
                'bias': self.mixed_strategy.bias
            },
            'description': self.description,
            'num_rounds': self.num_rounds
        }
        
        # Include phase_percentages if available
        if self.phase_percentages:
            result['phase_percentages'] = self.phase_percentages
        
        return result


class ProfileManager:
    """Manages AI player profiles and their parameters"""
    
    def __init__(self, profiles_file: str = "profiles.json"):
        self.profiles_file = profiles_file
        self.profiles: Dict[str, ProfileConfig] = {}
        self.load_profiles()
    
    def load_profiles(self):
        """Load profiles from JSON file"""
        try:
            with open(self.profiles_file, 'r') as f:
                data = json.load(f)
            
            profiles_data = data.get('profiles', {})
            
            for profile_name, profile_data in profiles_data.items():
                self.profiles[profile_name] = self._parse_profile(profile_name, profile_data)
                
            print(f"Loaded {len(self.profiles)} profiles: {list(self.profiles.keys())}")
            
        except FileNotFoundError:
            print(f"Warning: {self.profiles_file} not found. Using default profiles.")
            self._create_default_profiles()
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self._create_default_profiles()
    
    def _parse_profile(self, name: str, data: Dict) -> ProfileConfig:
        """Parse a single profile from JSON data"""
        # Get num_rounds from data, default to 200
        num_rounds = data.get('num_rounds', 200)
        
        # Check if phase_percentages are provided
        phase_percentages = data.get('phase_percentages')
        
        if phase_percentages:
            # Calculate phases from percentages
            phases = PhaseConfig.from_percentages(num_rounds, phase_percentages)
        else:
            # Use explicit phase boundaries (backward compatibility)
            phases_data = data.get('phases', {})
            if not phases_data:
                # Default phases if neither provided
                phase_percentages_default = {'p1': 0.075, 'p2': 0.425, 'p3': 0.5}  # Approximates old defaults
                phases = PhaseConfig.from_percentages(num_rounds, phase_percentages_default)
            else:
                phases = PhaseConfig(
                    p1_start=phases_data['p1'][0],
                    p1_end=phases_data['p1'][1],
                    p2_start=phases_data['p2'][0],
                    p2_end=phases_data['p2'][1],
                    p3_start=phases_data['p3'][0],
                    p3_end=phases_data['p3'][1]
                )
        
        epsilon_data = data['epsilon_schedule']
        epsilon = EpsilonConfig(
            type=epsilon_data['type'],
            value=epsilon_data.get('value'),
            start=epsilon_data.get('start'),
            end=epsilon_data.get('end'),
            end_round=epsilon_data.get('end_round'),
            base=epsilon_data.get('base'),
            floor=epsilon_data.get('floor'),
            tau=epsilon_data.get('tau'),
            values=epsilon_data.get('values'),
            switch_round=epsilon_data.get('switch_round')
        )
        
        security_data = data['security_level']
        security = SecurityConfig(
            trigger=security_data['trigger'],
            prob=security_data['prob']
        )
        
        retaliation_data = data['retaliation']
        retaliation = RetaliationConfig(
            user_defected_prev=retaliation_data.get('user_defected_prev'),
            user_coop_streak_ge=retaliation_data.get('user_coop_streak_ge'),
            user_defected_first=retaliation_data.get('user_defected_first'),
            user_defected_last_2=retaliation_data.get('user_defected_last_2')
        )
        
        mixed_strategy_data = data['mixed_strategy']
        mixed_strategy = MixedStrategyConfig(
            refresh_every=mixed_strategy_data['refresh_every'],
            bias=mixed_strategy_data['bias']
        )
        
        return ProfileConfig(
            name=name,
            phases=phases,
            dominant_probabilities=data['dominant_probabilities'],
            epsilon_schedule=epsilon,
            security_level=security,
            retaliation=retaliation,
            mixed_strategy=mixed_strategy,
            description=data['description'],
            num_rounds=num_rounds,
            phase_percentages=phase_percentages
        )
    
    def _create_default_profiles(self):
        """Create default profiles if loading fails"""
        # Create a simple default profile
        default_phase_percentages = {'p1': 0.10, 'p2': 0.50, 'p3': 0.40}
        default_profile = ProfileConfig(
            name="Default",
            phases=PhaseConfig.from_percentages(200, default_phase_percentages),
            dominant_probabilities={"p1": 0.6, "p2": 0.4, "p3": 0.2},
            epsilon_schedule=EpsilonConfig(type="constant", value=0.3),
            security_level=SecurityConfig(trigger={"user_dominant": True}, prob=0.5),
            retaliation=RetaliationConfig(user_defected_prev={"prob": 0.5, "duration": 1}),
            mixed_strategy=MixedStrategyConfig(refresh_every=10, bias={"toward": "neutral", "amount": 0.0}),
            description="Default computer behavior",
            num_rounds=200,
            phase_percentages=default_phase_percentages
        )
        self.profiles["Default"] = default_profile
    
    def get_profile(self, profile_name: str) -> Optional[ProfileConfig]:
        """Get a specific profile by name"""
        return self.profiles.get(profile_name)
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profile names"""
        return list(self.profiles.keys())
    
    def get_profile_description(self, profile_name: str) -> str:
        """Get description of a profile"""
        profile = self.get_profile(profile_name)
        return profile.description if profile else "Unknown profile"
    
    def calculate_epsilon(self, profile_name: str, round_idx: int) -> float:
        """Calculate epsilon value for a given round based on profile"""
        profile = self.get_profile(profile_name)
        if not profile:
            return 0.3  # default
        
        epsilon_config = profile.epsilon_schedule
        
        if epsilon_config.type == "constant":
            return epsilon_config.value or 0.3
        
        elif epsilon_config.type == "linear":
            if round_idx >= epsilon_config.end_round:
                return epsilon_config.end or 0.05
            progress = round_idx / epsilon_config.end_round
            return epsilon_config.start + (epsilon_config.end - epsilon_config.start) * progress
        
        elif epsilon_config.type == "decay":
            if epsilon_config.tau and round_idx >= epsilon_config.tau:
                return epsilon_config.floor or 0.1
            decay_factor = 2 ** (-round_idx / epsilon_config.tau) if epsilon_config.tau else 1
            return epsilon_config.base * decay_factor + epsilon_config.floor
        
        elif epsilon_config.type == "piecewise":
            if round_idx < epsilon_config.switch_round:
                return epsilon_config.values.get("early", 0.35)
            else:
                return epsilon_config.values.get("late", 0.20)
        
        elif epsilon_config.type == "linear_decay":
            if round_idx >= epsilon_config.end_round:
                return epsilon_config.end or 0.1
            progress = round_idx / epsilon_config.end_round
            return epsilon_config.start - (epsilon_config.start - epsilon_config.end) * progress
        
        return 0.3  # fallback
    
    def get_dominant_probability(self, profile_name: str, round_idx: int) -> float:
        """Get dominant move probability for current round based on profile"""
        profile = self.get_profile(profile_name)
        if not profile:
            return 0.5  # default
        
        phases = profile.phases
        dominant_probs = profile.dominant_probabilities
        
        if phases.p1_start <= round_idx <= phases.p1_end:
            return dominant_probs.get("p1", 0.6)
        elif phases.p2_start <= round_idx <= phases.p2_end:
            return dominant_probs.get("p2", 0.4)
        elif phases.p3_start <= round_idx <= phases.p3_end:
            return dominant_probs.get("p3", 0.2)
        
        return 0.5  # fallback
    
    def should_trigger_security_level(self, profile_name: str, game_state: Dict) -> bool:
        """Check if security level should be triggered based on profile"""
        profile = self.get_profile(profile_name)
        if not profile:
            return False
        
        trigger = profile.security_level.trigger
        prob = profile.security_level.prob
        
        # Check various trigger conditions
        if trigger.get("user_dominant") and game_state.get("user_dominant"):
            return random.random() < prob
        
        if trigger.get("user_dominant_streak") and game_state.get("user_dominant_streak", 0) >= trigger["user_dominant_streak"]:
            return random.random() < prob
        
        if trigger.get("payoff_gap_lt") and game_state.get("payoff_gap", 0) < trigger["payoff_gap_lt"]:
            return random.random() < prob
        
        if trigger.get("avg_payoff_gap_lt") and game_state.get("avg_payoff_gap", 0) < trigger["avg_payoff_gap_lt"]:
            return random.random() < prob
        
        if trigger.get("consecutive_losses") and game_state.get("consecutive_losses", 0) >= trigger["consecutive_losses"]:
            return random.random() < prob
        
        if trigger.get("in_punish_mode") and game_state.get("in_punish_mode"):
            return random.random() < prob
        
        return False
    
    def should_retaliate(self, profile_name: str, game_state: Dict) -> bool:
        """Check if computer should retaliate based on profile and game state"""
        profile = self.get_profile(profile_name)
        if not profile:
            return False
        
        retaliation = profile.retaliation
        
        # Check user defected previous round
        if retaliation.user_defected_prev and game_state.get("user_defected_prev"):
            return random.random() < retaliation.user_defected_prev.get("prob", 0.5)
        
        # Check user cooperation streak
        if retaliation.user_coop_streak_ge and game_state.get("user_coop_streak", 0) >= retaliation.user_coop_streak_ge.get("streak", 5):
            return random.random() < retaliation.user_coop_streak_ge.get("oneshot_defect_prob", 0.5)
        
        # Check user defected first
        if retaliation.user_defected_first and game_state.get("user_defected_first"):
            return random.random() < retaliation.user_defected_first.get("prob", 0.5)
        
        # Check user defected last 2 rounds
        if retaliation.user_defected_last_2 and game_state.get("user_defected_last_2"):
            return random.random() < retaliation.user_defected_last_2.get("prob", 0.5)
        
        return False
    
    def get_mixed_strategy_bias(self, profile_name: str) -> Dict[str, Any]:
        """Get mixed strategy bias configuration"""
        profile = self.get_profile(profile_name)
        if not profile:
            return {"toward": "neutral", "amount": 0.0}
        
        return profile.mixed_strategy.bias
    
    def should_refresh_mixed_strategy(self, profile_name: str, round_idx: int, last_refresh: int) -> bool:
        """Check if mixed strategy should be refreshed"""
        profile = self.get_profile(profile_name)
        if not profile:
            return round_idx - last_refresh >= 10
        
        return round_idx - last_refresh >= profile.mixed_strategy.refresh_every





