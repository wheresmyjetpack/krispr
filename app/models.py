from app import db
import hashlib
import urllib



followers = db.Table('followers',
		db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
		db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
		)

ingredients_recipes = db.Table('ingredients_recipes', db.Model.metadata,
		db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id')),
		db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredient.id'))
				)

ingredients_pantry = db.Table('ingredients_pantry', db.Model.metadata,
		db.Column('pantry_item_id', db.Integer, db.ForeignKey('pantry_item.id')),
		db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredient.id'))
		)


class User(db.Model):
	
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	nickname = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(64), index=True, unique=True)
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime)
	recipes = db.relationship('Recipe', backref='author', lazy='dynamic')
	pantry = db.relationship('PantryItem', backref='owner', lazy='dynamic')
	followed = db.relationship('User',
			secondary=followers,
			primaryjoin=(followers.c.follower_id == id),
			secondaryjoin=(followers.c.followed_id == id),
			backref=db.backref('followers', lazy='dynamic'),
			lazy='dynamic')

	@staticmethod
	def make_unique_nickname(nickname):

		if User.query.filter_by(nickname=nickname).first() is None:
			return nickname

		version = 2

		while True:

			new_nickname = nickname + str(version)

			if User.query.filter_by(nickname=new_nickname).first() is None:
				break
			version += 1

		return new_nickname

	def follow(self, user):

		if not self.is_following(user):
			
			self.followed.append(user)
			return self

	def unfollow(self, user):

		if self.is_following(user):

			self.followed.remove(user)
			return self

	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0

	def followed_recipes(self):
		return Recipe.query.join(followers, (followers.c.followed_id == Recipe.user_id)).filter(followers.c.follower_id == self.id).order_by(Recipe.timestamp.desc())
	
	def remove_item(self, item):
		
		self.pantry.remove(item)
		return self
	
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)
	
	def avatar(self, size):
		
		default = 'http://en.gravatar.com/avatar/'
		avatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.email.lower()).hexdigest() + "?"
		avatar_url += urllib.urlencode({'d':default, 's':str(size)})
		
		return avatar_url

	def __repr__(self):
		return '<User %r>' % self.nickname


class PantryItem(db.Model):
	
	__tablename__ = 'pantry_item'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64))
	amount = db.Column(db.String(12))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	
	def __repr__(self):
		return '<PantryItem %r>' % self.name


class Ingredient(db.Model):
	
	__tablename__ = 'ingredient'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), index=True)
	amount = db.Column(db.String(12), index=True)
	recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
	'''
	recipes = db.relationship('Recipe',
			           secondary=ingredients_recipes,
				   primaryjoin=ingredients_recipes.c.ingredient_id == id,
				   secondaryjoin=ingredients_recipes.c.recipe_id == id,
				   backref=db.backref('ingredient_in_recipe', lazy='dynamic'),
				   lazy='dynamic'
				   )
'''
	def __repr__(self):
		return '<Ingredient %r>' % self.name


class Recipe(db.Model):
	
	__tablename__ = 'recipe'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), index=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.DateTime)
	ingredients = db.relationship('Ingredient',
			secondary=lambda: ingredients_recipes,
			backref=db.backref('recipes'))	
	
	def add_ingredient(self, ingredient):

		self.ingredients.append(ingredient)
		return self

	def remove_ingredient(self, ingredient):

		self.ingredients.remove(ingredient)
		return self

	def __repr__(self):
		return '<Recipe %r>' % self.name	
