#!flask/bin/python

import os
import unittest

from config import basedir
from app import app, db
from app.models import User


class TestCase(unittest.TestCase):

	def setUp(self):

		app.config['TESTING'] = True
		app.config['WTF_CSRF_ENABLED'] = False
		app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
		self.app = app.test_client()
		db.create_all()

	def tearDown(self):

		db.session.remove()
		db.drop_all()
	
	'''
	def test_avatar(self):

		u = User(nickname='Paul', email='paul@example.com')
		avatar = u.avatar(128)
		expected = 'http://www.gravatar.com/avatar/' +  'd4c74594d841139328695756648b6bd6'
		print len(expected)
		print len(avatar)

		assert avatar[0:len(expected)] == expected
	'''

	def test_make_unique_nickname(self):

		u = User(nickname='Paul', email='paul@example.com')
		db.session.add(u)
		db.session.commit()

		nickname = User.make_unique_nickname('Paul')

		assert nickname != 'Paul'

		u = User(nickname=nickname, email='jordan@example.com')
		db.session.add(u)
		db.session.commit()

		nickname2 = User.make_unique_nickname('Paul')

		assert nickname2 != 'Paul'
		assert nickname2 != nickname


if __name__ == '__main__':

	unittest.main()
