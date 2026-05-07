"""
Tests for DecisionQueue
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.decision_queue import DecisionQueue
from src.database.models import DecisionStatus, DecisionType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestDecisionQueue(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.engine = create_engine('sqlite:///:memory:')
        from src.database.models import Base
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.dq = DecisionQueue(self.session)

        # Create test data
        from src.database.models import User, Project, Session as DBSession, Task
        self.user = User(username='testuser', email='test@example.com', password_hash='hash')
        self.session.add(self.user)
        self.session.commit()

        self.project = Project(name='Test Project', created_by=self.user.id)
        self.session.add(self.project)
        self.session.commit()

        self.db_session = DBSession(project_id=self.project.id, status='active')
        self.session.add(self.db_session)
        self.session.commit()

        self.task = Task(
            session_id=self.db_session.id,
            title='Test Task',
            current_agent='Developer',
            status='in_progress'
        )
        self.session.add(self.task)
        self.session.commit()

    def tearDown(self):
        """Clean up"""
        self.session.close()

    def test_create_decision(self):
        """Test creating a decision"""
        decision = self.dq.create_decision(
            task_id=self.task.id,
            agent_name='Developer',
            decision_type=DecisionType.APPROVAL,
            context={'question': 'Should we proceed?'},
            assigned_to=self.user.id
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.status, DecisionStatus.PENDING)
        self.assertEqual(decision.agent_name, 'Developer')

    def test_get_pending_decisions(self):
        """Test getting pending decisions"""
        self.dq.create_decision(
            task_id=self.task.id,
            agent_name='Developer',
            decision_type=DecisionType.APPROVAL,
            context={'question': 'Test?'},
            assigned_to=self.user.id
        )

        decisions = self.dq.get_pending_decisions(
            user_id=self.user.id,
            project_id=self.project.id
        )

        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].status, DecisionStatus.PENDING)

    def test_resolve_decision(self):
        """Test resolving a decision"""
        decision = self.dq.create_decision(
            task_id=self.task.id,
            agent_name='Developer',
            decision_type=DecisionType.APPROVAL,
            context={'question': 'Test?'},
            assigned_to=self.user.id
        )

        result = self.dq.resolve_decision(
            decision_id=decision.id,
            user_id=self.user.id,
            response={'approved': True, 'comment': 'Looks good'}
        )

        self.assertTrue(result)
        self.session.refresh(decision)
        self.assertEqual(decision.status, DecisionStatus.RESOLVED)
        self.assertIsNotNone(decision.resolved_at)


if __name__ == '__main__':
    unittest.main()
