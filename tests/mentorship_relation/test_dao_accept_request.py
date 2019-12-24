from datetime import datetime, timedelta

from app import messages
from app.api.dao.mentorship_relation import MentorshipRelationDAO
from app.database.models.mentorship_relation import MentorshipRelationModel
from app.database.models.tasks_list import TasksListModel
from app.utils.enum_utils import MentorshipRelationState
from tests.mentorship_relation.relation_base_setup import MentorshipRelationBaseTestCase
from app.database.sqlalchemy_extension import db


# TODO test when a user is in a current relation and tries to accept another relation
# TODO test when a user tries to accept a relation where this user is not involved

class TestMentorshipRelationAcceptRequestDAO(MentorshipRelationBaseTestCase):

    # Setup consists of adding 2 users into the database
    # User 1 is the mentorship relation requester = action user
    # User 2 is the receiver
    def setUp(self):
        super(TestMentorshipRelationAcceptRequestDAO, self).setUp()

        self.notes_example = 'description of a good mentorship relation'
        self.now_datetime = datetime.now()
        self.end_date_example = self.now_datetime + timedelta(weeks=5)

        # create new mentorship relation

        self.mentorship_relation = MentorshipRelationModel(
            action_user_id=self.first_user.id,
            mentor_user=self.first_user,
            mentee_user=self.second_user,
            creation_date=self.now_datetime.timestamp(),
            end_date=self.end_date_example.timestamp(),
            state=MentorshipRelationState.PENDING,
            notes=self.notes_example,
            tasks_list=TasksListModel()
        )

        db.session.add(self.mentorship_relation)
        db.session.commit()

    def test_dao_accept_non_existing_mentorship_request(self):
        DAO = MentorshipRelationDAO()

        result = DAO.accept_request(self.first_user.id, 123)

        self.assertEqual((messages.MENTORSHIP_RELATION_REQUEST_DOES_NOT_EXIST, 404), result)
        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)

    def test_dao_requester_tries_to_accept_mentorship_request(self):
        DAO = MentorshipRelationDAO()

        result = DAO.accept_request(self.first_user.id, self.mentorship_relation.id)

        # If a user tries to accepts a request where he is not involved, then
        # '400:Bad Request' error would be given displaying the message that 'You cannot accept a mentorship relation where you are not involved.'.
        if (self.mentorship_relation.mentor_id != self.first_user.id and self.mentorship_relation.mentee_id != self.first_user.id):
            self.assertEqual((messages.CANT_ACCEPT_UNINVOLVED_MENTOR_RELATION, 400), result)
        # If a user tries to accepts a request sent by him, then
        # '400:Bad Request' error would be given displaying the message that 'You cannot accept a mentorship request sent by yourself.'.
        elif (self.mentorship_relation.action_user_id == self.first_user.id):
            self.assertEqual((messages.CANT_ACCEPT_MENTOR_REQ_SENT_BY_USER, 400), result)

        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)

    def test_dao_receiver_accepts_mentorship_request(self):
        DAO = MentorshipRelationDAO()

        result = DAO.accept_request(self.second_user.id, self.mentorship_relation.id)

    # If the receiver tries to accepts a request while he is in another mentorship request, then
    # '400:Bad Request' error would be given displaying the message that 'You cannot accept a mentorship relation while you are already in another mentorship relation'.
    # else, the request would be accepted.
        if (not(self.second_user.current_mentorship_role is None)):
            self.assertEqual((messages.CANT_ACCEPT_WHILE_IN_A_RELATION, 400), result)
            self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)
        else:
            self.assertEqual((messages.MENTORSHIP_RELATION_WAS_ACCEPTED_SUCCESSFULLY, 200), result)
            self.assertEqual(MentorshipRelationState.ACCEPTED, self.mentorship_relation.state)

    def test_dao_sender_does_not_exist_mentorship_request(self):
        DAO = MentorshipRelationDAO()

        result = DAO.accept_request(123, self.mentorship_relation.id)

        self.assertEqual((messages.USER_DOES_NOT_EXIST, 404), result)
        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)

    def test_dao_mentorship_request_is_not_in_pending_state(self):
        DAO = MentorshipRelationDAO()

        self.mentorship_relation.state = MentorshipRelationState.ACCEPTED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.accept_request(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual((messages.NOT_PENDING_STATE_RELATION, 400), result)

        self.mentorship_relation.state = MentorshipRelationState.COMPLETED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.accept_request(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual((messages.NOT_PENDING_STATE_RELATION, 400), result)

        self.mentorship_relation.state = MentorshipRelationState.CANCELLED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.accept_request(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual((messages.NOT_PENDING_STATE_RELATION, 400), result)

        self.mentorship_relation.state = MentorshipRelationState.REJECTED
        db.session.add(self.mentorship_relation)
        db.session.commit()

        result = DAO.accept_request(self.second_user.id, self.mentorship_relation.id)
        self.assertEqual((messages.NOT_PENDING_STATE_RELATION, 400), result)
