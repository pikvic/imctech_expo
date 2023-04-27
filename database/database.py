from uuid import UUID, uuid4
from pony.orm import *


db = Database()
db.bind(provider='sqlite', filename='database.db', create_db=True)


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