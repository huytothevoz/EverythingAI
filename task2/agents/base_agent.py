from abc import ABC, abstractmethod
from game_state import GameState

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        #benchmark
        self.nodes_expanded = 0
        self.pruned_count = 0
        self.execution_time = 0.0

    @abstractmethod
    def choose_action(self, state: GameState):
        """Nhận state hiện tại, trả về Action tốt nhất cho lượt đi."""
        pass