from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
ingredient = Table('ingredient', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('amount', String(length=12)),
)

ingredients_recipes = Table('ingredients_recipes', post_meta,
    Column('ingredient_id', Integer),
    Column('recipe_id', Integer),
)

pantry_item = Table('pantry_item', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('amount', String(length=12)),
    Column('user_id', Integer),
)

recipe = Table('recipe', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('user_id', Integer),
)

user = Table('user', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String(length=64)),
    Column('email', String(length=64)),
    Column('about_me', String(length=140)),
    Column('last_seen', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['ingredient'].create()
    post_meta.tables['ingredients_recipes'].create()
    post_meta.tables['pantry_item'].create()
    post_meta.tables['recipe'].create()
    post_meta.tables['user'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['ingredient'].drop()
    post_meta.tables['ingredients_recipes'].drop()
    post_meta.tables['pantry_item'].drop()
    post_meta.tables['recipe'].drop()
    post_meta.tables['user'].drop()
