"""
Tests for HumanAgent
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import Mock, patch
from src.agents.human_agent import HumanAgent
from src.database.models import DecisionType


class TestHumanAgent(unittest.TestCase):
    def setUp(self):
        """Set up test agent"""
        self.decision_queue = Mock()
        self.agent_async = HumanAgent(
            user_id=1,
            decision_queue=self.decision_queue,
            mode='async'
        )
        self.agent_sync = HumanAgent(
            user_id=1,
            decision_queue=self.decision_queue,
            mode='sync'
        )

    def test_async_mode_creates_decision(self):
        """Test async mode creates pending decision"""
        task = Mock()
        task.task_id = 1
        task.title = 'Test Task'
        task.description = 'Test Description'

        self.decision_queue.create_decision.return_value = Mock(id=123)

        result = self.agent_async.process(task)

        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['decision_id'], 123)
        self.decision_queue.create_decision.assert_called_once()

    def test_sync_mode_waits_for_input(self):
        """Test sync mode behavior"""
        task = Mock()
        task.task_id = 1
        task.title = 'Test Task'

        # Mock the decision creation and resolution
        mock_decision = Mock(id=123, status='pending')
        self.decision_queue.create_decision.return_value = mock_decision

        with patch('time.sleep'):
            with patch.object(self.decision_queue, 'get_decision') as mock_get:
                # Simulate decision being resolved
                resolved_decision = Mock(
                    id=123,
                    status='resolved',
                    response={'approved': True, 'feedback': 'Good'}
                )
                mock_get.return_value = resolved_decision

                result = self.agent_sync.process(task)

                self.assertEqual(result['status'], 'completed')
                self.assertIn('response', result)

    def test_agent_name(self):
        """Test agent name property"""
        self.assertEqual(self.agent_async.agent_name, 'HumanAgent')


if __name__ == '__main__':
    unittest.main()
