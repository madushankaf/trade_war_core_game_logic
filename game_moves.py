from typing import Optional, Any
import copy

class MoveNode:
    def __init__(self, user_move: Any, computer_move: Any):
        self.user_move = user_move
        self.computer_move = computer_move
        self.next: Optional[MoveNode] = None

class GameMoves:
    def __init__(self):
        self.head: Optional[MoveNode] = None
        self.tail: Optional[MoveNode] = None
        self.size = 0

    def add_moves(self, user_move: Any, computer_move: Any) -> None:
        """Add a new pair of moves to the linked list.
        
        Makes a copy of move dictionaries to avoid reference issues where
        the same dictionary object is reused and modified.
        """
        # Make copies of move dictionaries to avoid reference issues
        # If moves are dicts, copy them; otherwise use as-is
        # Using copy.copy() (shallow copy) is sufficient since move dicts don't have nested mutable structures
        if isinstance(user_move, dict):
            user_move_copy = copy.copy(user_move)
        else:
            user_move_copy = user_move
            
        if isinstance(computer_move, dict):
            computer_move_copy = copy.copy(computer_move)
        else:
            computer_move_copy = computer_move
        
        new_node = MoveNode(user_move_copy, computer_move_copy)
        
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        
        self.size += 1

    def get_moves(self) -> list:
        """Get all moves as a list of (user_move, computer_move) tuples."""
        moves = []
        current = self.head
        while current:
            moves.append((current.user_move, current.computer_move))
            current = current.next
        return moves

    def get_last_moves(self) -> Optional[tuple]:
        """Get the last pair of moves."""
        if self.tail:
            return (self.tail.user_move, self.tail.computer_move)
        return None

    def clear(self) -> None:
        """Clear all moves."""
        self.head = None
        self.tail = None
        self.size = 0 