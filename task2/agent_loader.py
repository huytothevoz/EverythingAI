from agents.search_agent import (
    create_minimax_agent,
    create_alphabeta_agent,
    create_heuristic_minimax_agent,
    create_heuristic_alphabeta_agent
)
from config import AgentType

def load_agent(agent_type: str, depth: int = 3):
    if agent_type == AgentType.MINIMAX:
        return create_minimax_agent(depth)
    elif agent_type == AgentType.ALPHABETA:
        return create_alphabeta_agent(depth)
    elif agent_type == AgentType.MINIMAX_HEURISTIC:
        return create_heuristic_minimax_agent(depth)
    elif agent_type == AgentType.ALPHABETA_HEURISTIC:
        return create_heuristic_alphabeta_agent(depth)
    else:
        raise ValueError(f"Không tìm thấy Agent: {agent_type}")