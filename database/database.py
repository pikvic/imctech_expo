from uuid import UUID, uuid4
from pony.orm import *
from os import environ

db = Database()
PROVIDER = environ.get("PROVIDER", "sqlite")
if PROVIDER == "sqlite":
    db.bind(provider=PROVIDER, filename='database.db', create_db=True)
elif PROVIDER == "postgres":
    USER = environ.get("DB_USER", "postgres")
    PASSWORD = environ.get("DB_PASSWORD", "postgres")
    HOST = environ.get("DB_HOST", "localhost:5432")
    db.bind(provider=PROVIDER, user=USER, password=PASSWORD, host=HOST, database="expo")
else:
    db.bind(provider=PROVIDER, filename='database.db', create_db=True)


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    key = Required(str, unique=True)
    name = Optional(str)
    type = Required(str)
    count = Required(int, default=0)
    activated = Required(bool, default=False)
    marks = Set('Mark')
    votes = Set('Vote')


class Project(db.Entity):
    id = PrimaryKey(int, auto=True)
    key = Required(str, unique=True)
    name = Required(str)
    team = Required(str)
    description = Required(str)
    type = Required(str)
    members = Set('Member')
    marks = Set('Mark')
    votes = Set('Vote')


class Member(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    group = Optional(str)
    school = Optional(str)
    year = Optional(str)
    project = Required(Project)


class Mark(db.Entity):
    id = PrimaryKey(int, auto=True)
    idea = Required(int)
    design = Required(int)
    features = Required(int)
    mvp = Required(int)
    team = Required(int)
    user = Required(User)
    project = Required(Project)

class Vote(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    project = Required(Project)

db.generate_mapping(create_tables=True)