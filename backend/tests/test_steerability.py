"""
Live Steerability Test Suite.
Validates the modularity of the LangGraph state machine by testing rapid addition
of new agent nodes (e.g. Red-Teaming, Code Sandbox Execution) in under 20 minutes.
"""

import sys
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.graph.workflow import build_interview_graph


class TestSteerability(unittest.TestCase):
    """Test suite demonstrating rapid extensibility of the graph architecture."""

    def test_dynamic_node_addition(self):
        """Verify that a custom agent node can be inserted into the StateGraph seamlessly."""
        # TODO: Add dynamic node and verify compilation
        graph = build_interview_graph()
        
        # Define mock steer node
        def mock_steer_node(state):
            return {"latest_reply": "Steered reply"}
        
        graph.add_node("steer_agent", mock_steer_node)
        compiled = graph.compile()
        self.assertIsNotNone(compiled)


if __name__ == "__main__":
    unittest.main()
