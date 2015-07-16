from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from .forms import LoginForm, RecipeForm, EditProfileForm, IngredientForm
from .models import User, PantryItem, Recipe, Ingredient
from datetime import datetime


@lm.user_loader
def load_user(id):
	return User.query.get(int(id))


@app.before_request
def before_request():
	
	g.user = current_user
	
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		
		db.session.add(g.user)
		db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
	
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))

	form = LoginForm()
	
	if form.validate_on_submit():
		
		session['remember_me'] = form.remember_me.data
		#flash('Login requested for OpenID="%s", remember_me=%s' % (form.openid.data, str(form.remember_me.data)))
		
		return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])

	return render_template('login.html',
			       title='Sign In',
			       form=form,
			       providers=app.config['OPENID_PROVIDERS'])
			  

@app.route('/logout')
def logout():

	logout_user()
	return redirect(url_for('index'))


@oid.after_login
def after_login(resp):
	
	if resp.email is None or resp.email == "":
		
		flash('Invalid login. Please try again.')
		return redirect(url_for('login'))

	user = User.query.filter_by(email=resp.email).first()

	if user is None:
		
		nickname = resp.nickname

		if nickname is None or nickname == "":
			nickname = resp.email.split('@')[0]
		
		nickname = User.make_unique_nickname(nickname)
		user = User(nickname=nickname, email=resp.email)

		db.session.add(user)
		db.session.commit()
		
		# make user follow herself
		db.session.add(user.follow(user))
		db.session.commit()

	remember_me = False

	if 'remember_me' in session:
		
		remember_me = session['remember_me']
		session.pop('remember_me', None)

	login_user(user, remember=remember_me)

	return redirect(request.args.get('next') or url_for('index'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():	
	
	user = g.user
	recipes = None

	return render_template('index.html', 
			       title='Home',
			       user=user, 
			       recipes=recipes)


@app.route('/user/<nickname>')
@login_required
def user(nickname):
	
	user = User.query.filter_by(nickname=nickname).first()

	if user == None:

		flash('User %s not found' % nickname)
		return redirect(url_for('index'))

	return render_template('user.html', user=user,)


@app.route('/pantry', methods=['GET', 'POST'])
@login_required
def pantry():

        form = IngredientForm()
	pantry = PantryItem.query.filter_by(owner=g.user).all()

	if form.validate_on_submit():
		
		pantry_item = PantryItem(name=form.name.data, amount=form.amount.data, owner=g.user)
		db.session.add(pantry_item)
		db.session.commit()
                	
		flash('You added %s to the pantry.' % pantry_item.name)
		return redirect(url_for('pantry'))

	return render_template('pantry.html', 
			       form=form,
			       user=g.user,
			       pantry=pantry)

@app.route('/pantry_remove/<pantry_item_name>')
@login_required
def pantry_remove(pantry_item_name):
	
	item = PantryItem.query.filter_by(owner=g.user, name=pantry_item_name).first()
	
	if item is None:

		flash('No item called "%s" found in the pantry' % pantry_item_name)
		return redirect(url_for('pantry'))
	
	i = g.user.remove_item(item)

	if i is None:

		flash('Problem removing %s' % item.name)
		return redirect(url_for('pantry'))
	
	db.session.add(i)
	db.session.commit()
	
	return redirect(url_for('pantry'))
	
	

@app.route('/recipe', methods=['GET', 'POST'])
@login_required
def recipe():

	form = RecipeForm()
	
	if form.validate_on_submit():

		recipe = Recipe(name=form.name.data, author=g.user, timestamp=datetime.utcnow())

		db.session.add(recipe)
		db.session.commit()

		flash('Created recipe named "%s"' % recipe.name)
		return redirect(url_for('ingredient', recipe_name=recipe.name))
	
	return render_template('recipe.html',
			       title='Create a Recipe', 		       
			       form=form)

	
@app.route('/<recipe_name>/ingredient', methods=['GET', 'POST'])
@login_required
def ingredient(recipe_name):

	form = IngredientForm()
	recipe = Recipe.query.filter_by(name=recipe_name).first()

	if form.validate_on_submit():
		
		ingredient = Ingredient(name=form.name.data, amount=form.amount.data)
		
		# try recipe method next
		db.session.add(recipe.add_ingredient(ingredient))
		db.session.commit()

		flash('Added ingredient %s to %s' % (ingredient.name, recipe.name))
		return redirect(url_for('ingredient', recipe_name=recipe.name))

	return render_template('ingredient.html',
			       title='Add Ingredients',
			       recipe=recipe,
			       form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():

	form = EditProfileForm(g.user.nickname)

	if form.validate_on_submit():

		g.user.nickname = form.nickname.data
		g.user.about_me = form.about_me.data

		db.session.add(g.user)
		db.session.commit()

		flash('Your changes have been saved.')
		return redirect(url_for('edit_profile'))

	else:
		
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me
		
	return render_template('edit_profile.html', form=form)
	
	
@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
	
	user = User.query.filter_by(nickname=nickname).first()
	
	if user is None:
		
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	
	if user == g.user:
		
		flash('You can\'t follow yourself!')
		return redirect(url_for('user', nickname=nickname))

	u = g.user.follow(user)
	
	if u is None:

		flash('Cannot follow ' + nickname + '.')
		return redirect(url_for('user', nickname=nickname))

	db.session.add(u)
	db.session.commit()

	flash('You are now following ' + nickname + '!')
	return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
	
	user = User.query.filter_by(nickname=nickname).first()
	
	if user is None:
		
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))

	if user == g.user:
		
		flash('You can\'t unfollow yourself!')
		return redirect(url_for('user', nickname=nickname))

	u = g.user.unfollow(user)
	
	if u is None:
		
		flash('Cannot unfollow ' + nickname + '.')
		return redirect(url_for('user', nickname=nickname))
	
	db.session.add(u)
	db.session.commit()
	
	flash('You have stopped following ' + nickname + '.')
	return redirect(url_for('user', nickname=nickname))
	
	
@app.route('/followers/<nickname>')
@login_required
def followers(nickname):
	
	user = User.query.filter_by(nickname=nickname).first()

	if user is None:
		
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
		
	return render_template('followers.html', 
						user=user,
						followers=user.followers,
						followed=user.followed)


@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
	
	db.session.rollback()
	return render_template('500.html'), 500
	
