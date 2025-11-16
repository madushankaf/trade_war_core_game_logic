from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Literal, Union
from enum import Enum


class PlayerType(str, Enum):
    """Enum for player types"""
    USER = "user"
    COMPUTER = "computer"


class MoveType(str, Enum):
    """Enum for move types"""
    COOPERATIVE = "cooperative"
    DEFECTIVE = "defective"
    MIXED = "mixed"


class StrategyType(str, Enum):
    """Enum for strategy types"""
    COPY_CAT = "copy_cat"
    TIT_FOR_TAT = "tit_for_tat"
    GRIM_TRIGGER = "grim_trigger"
    RANDOM = "random"
    MIXED = "mixed"


class PayoffEntry(BaseModel):
    """Model for a single payoff matrix entry"""
    user_move_name: str = Field(..., description="Name of the user's move")
    computer_move_name: str = Field(..., description="Name of the computer's move")
    payoff: Dict[str, float] = Field(..., description="Payoff values for user and computer")

    @field_validator('payoff')
    @classmethod
    def validate_payoff(cls, v):
        """Validate that payoff contains both user and computer values"""
        if 'user' not in v or 'computer' not in v:
            raise ValueError("Payoff must contain both 'user' and 'computer' values")
        return v


class Move(BaseModel):
    """Model for a single move/strategy"""
    name: str = Field(..., description="Name of the move")
    type: MoveType = Field(..., description="Type of the move (cooperative/defective/mixed)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of selecting this move")
    player: PlayerType = Field(..., description="Player who can make this move")

    @field_validator('probability')
    @classmethod
    def validate_probability(cls, v):
        """Validate probability is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Probability must be between 0 and 1")
        return v


class UserStrategySettings(BaseModel):
    """Model for user strategy settings"""
    strategy: StrategyType = Field(..., description="Strategy type for the user")
    first_move: Optional[str] = Field(None, description="First move name for the user")
    cooperation_start: Optional[int] = Field(None, ge=0, description="Round when cooperation starts")
    mixed_strategy_array: Optional[List[str]] = Field(None, description="Array for mixed strategy moves")

    @field_validator('cooperation_start')
    @classmethod
    def validate_cooperation_start(cls, v):
        """Validate cooperation_start is non-negative if provided"""
        if v is not None and v < 0:
            raise ValueError("Cooperation start must be non-negative")
        return v


class GameState(BaseModel):
    """Model for internal game state"""
    equalizer_strategy: Optional[List[float]] = Field(None, description="Equalizer strategy probabilities")
    round_idx: int = Field(0, ge=0, description="Current round index")
    last_strategy_update: int = Field(0, ge=0, description="Last round when strategy was updated")
    generated_mixed_moves_array: Optional[List[str]] = Field(None, description="Generated mixed moves array")
    last_computer_move: Optional[str] = Field(None, description="Last computer move name")
    grim_triggered: bool = Field(False, description="Whether grim trigger has been activated (permanent punishment)")

    @field_validator('round_idx', 'last_strategy_update')
    @classmethod
    def validate_non_negative(cls, v):
        """Validate that round indices are non-negative"""
        if v < 0:
            raise ValueError("Round indices must be non-negative")
        return v


class Country(BaseModel):
    """Model for country information"""
    name: str = Field(..., description="Country name")
    flag: str = Field(..., description="Country flag emoji")
    code: str = Field(..., description="Country code")


class ComputerProfile(BaseModel):
    """Model for computer profile information"""
    name: str = Field(..., description="Profile name")
    settings: Dict = Field(..., description="Profile settings")


class GameModel(BaseModel):
    """Complete game model for the trade war game theory simulation"""
    
    # Core game components
    user_moves: List[Move] = Field(..., description="Available moves for the user")
    computer_moves: List[Move] = Field(..., description="Available moves for the computer")
    payoff_matrix: List[PayoffEntry] = Field(..., description="Payoff matrix for all move combinations")
    
    # Strategy and state
    user_strategy_settings: UserStrategySettings = Field(..., description="User strategy configuration")
    state: GameState = Field(default_factory=GameState, description="Internal game state")
    
    # Additional fields for UI integration
    computer_profile_name: Optional[str] = Field(None, description="Computer profile name")
    computer_profile: Optional[ComputerProfile] = Field(None, description="Computer profile details")
    countries: Optional[Dict[str, Country]] = Field(None, description="User and computer countries")

    @field_validator('user_moves')
    @classmethod
    def validate_user_moves(cls, v):
        """Validate user moves have correct player type"""
        for move in v:
            if move.player != PlayerType.USER:
                raise ValueError(f"User move {move.name} must have player='user'")
        return v

    @field_validator('computer_moves')
    @classmethod
    def validate_computer_moves(cls, v):
        """Validate computer moves have correct player type"""
        for move in v:
            if move.player != PlayerType.COMPUTER:
                raise ValueError(f"Computer move {move.name} must have player='computer'")
        return v

    @field_validator('payoff_matrix')
    @classmethod
    def validate_payoff_matrix(cls, v, info):
        """Validate payoff matrix references valid moves"""
        if not hasattr(info.data, 'user_moves') or not hasattr(info.data, 'computer_moves'):
            return v
        
        user_move_names = {move.name for move in info.data.user_moves}
        computer_move_names = {move.name for move in info.data.computer_moves}
        
        for entry in v:
            if entry.user_move_name not in user_move_names:
                raise ValueError(f"Payoff matrix references unknown user move: {entry.user_move_name}")
            if entry.computer_move_name not in computer_move_names:
                raise ValueError(f"Payoff matrix references unknown computer move: {entry.computer_move_name}")
        
        return v

    @field_validator('user_strategy_settings')
    @classmethod
    def validate_strategy_settings(cls, v, info):
        """Validate strategy settings are consistent with moves"""
        if not hasattr(info.data, 'user_moves'):
            return v
        
        user_move_names = {move.name for move in info.data.user_moves}
        
        if v.first_move and v.first_move not in user_move_names:
            raise ValueError(f"First move '{v.first_move}' not found in user moves")
        
        return v

    def to_dict(self) -> Dict:
        """Convert the Pydantic model to a dictionary for use with game_theory functions"""
        result = {
            'user_moves': [move.model_dump() for move in self.user_moves],
            'computer_moves': [move.model_dump() for move in self.computer_moves],
            'payoff_matrix': [entry.model_dump() for entry in self.payoff_matrix],
            'user_strategy_settings': self.user_strategy_settings.model_dump(),
            'state': self.state.model_dump()
        }
        
        # Add optional fields if they exist
        if self.computer_profile_name is not None:
            result['computer_profile_name'] = self.computer_profile_name
        if self.computer_profile is not None:
            result['computer_profile'] = self.computer_profile.model_dump()
        if self.countries is not None:
            result['countries'] = {k: v.model_dump() for k, v in self.countries.items()}
            
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameModel':
        """Create a GameModel from a dictionary"""
        return cls(**data)

    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "allow"  # Allow extra fields for UI integration
    }


# Example usage and validation
if __name__ == "__main__":
    # Example game configuration
    example_game = GameModel(
        user_moves=[
            Move(
                name="open_dialogue",
                type=MoveType.COOPERATIVE,
                probability=0.4,
                player=PlayerType.USER
            ),
            Move(
                name="raise_tariffs",
                type=MoveType.DEFECTIVE,
                probability=0.3,
                player=PlayerType.USER
            ),
            Move(
                name="wait_and_see",
                type=MoveType.COOPERATIVE,
                probability=0.3,
                player=PlayerType.USER
            )
        ],
        computer_moves=[
            Move(
                name="open_dialogue",
                type=MoveType.COOPERATIVE,
                probability=0.4,
                player=PlayerType.COMPUTER
            ),
            Move(
                name="raise_tariffs",
                type=MoveType.DEFECTIVE,
                probability=0.3,
                player=PlayerType.COMPUTER
            ),
            Move(
                name="wait_and_see",
                type=MoveType.COOPERATIVE,
                probability=0.3,
                player=PlayerType.COMPUTER
            )
        ],
        payoff_matrix=[
            PayoffEntry(
                user_move_name="open_dialogue",
                computer_move_name="open_dialogue",
                payoff={"user": 3, "computer": 3}
            ),
            PayoffEntry(
                user_move_name="open_dialogue",
                computer_move_name="raise_tariffs",
                payoff={"user": 1, "computer": 4}
            ),
            PayoffEntry(
                user_move_name="open_dialogue",
                computer_move_name="wait_and_see",
                payoff={"user": 2, "computer": 2}
            ),
            PayoffEntry(
                user_move_name="raise_tariffs",
                computer_move_name="open_dialogue",
                payoff={"user": 4, "computer": 1}
            ),
            PayoffEntry(
                user_move_name="raise_tariffs",
                computer_move_name="raise_tariffs",
                payoff={"user": 2, "computer": 2}
            ),
            PayoffEntry(
                user_move_name="raise_tariffs",
                computer_move_name="wait_and_see",
                payoff={"user": 3, "computer": 1}
            ),
            PayoffEntry(
                user_move_name="wait_and_see",
                computer_move_name="open_dialogue",
                payoff={"user": 2, "computer": 2}
            ),
            PayoffEntry(
                user_move_name="wait_and_see",
                computer_move_name="raise_tariffs",
                payoff={"user": 1, "computer": 3}
            ),
            PayoffEntry(
                user_move_name="wait_and_see",
                computer_move_name="wait_and_see",
                payoff={"user": 1, "computer": 1}
            )
        ],
        user_strategy_settings=UserStrategySettings(
            strategy=StrategyType.COPY_CAT,
            first_move="open_dialogue",
            cooperation_start=2,
            mixed_strategy_array=None
        ),
        state=GameState(
            equalizer_strategy=None,
            round_idx=0,
            last_strategy_update=0,
            generated_mixed_moves_array=None,
            last_computer_move=None
        )
    )
    
    print("Example game model created successfully!")
    print(f"User moves: {len(example_game.user_moves)}")
    print(f"Computer moves: {len(example_game.computer_moves)}")
    print(f"Payoff matrix entries: {len(example_game.payoff_matrix)}")
    print(f"Strategy: {example_game.user_strategy_settings.strategy}")
    
    # Test conversion to dict
    game_dict = example_game.to_dict()
    print(f"Converted to dict: {type(game_dict)}")
    
    # Test conversion from dict
    game_from_dict = GameModel.from_dict(game_dict)
    print(f"Converted from dict: {type(game_from_dict)}") 