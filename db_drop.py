#!flask/bin/python

import sys
from app import db

if sys.argv[1] != 'safe':
	pass

else:
	
	db.session.remove()
	db.drop_all()
	
	print 'Database cleared. Run db_migrate.py'


