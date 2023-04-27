from flask import Flask, request, render_template, url_for, redirect, abort, make_response, session
from pony.flask import Pony
from database.database import db, User, Project, Member, Mark, Vote
import segno
from uuid import uuid4
from os import environ
from pony.orm import db_session, select
from enum import Enum


class UserType(Enum):
    superadmin = 'superadmin'
    admin = 'admin'
    expert = 'expert'
    guest = 'guest'
    anonymous = 'anonymous'

class ProjectType(Enum):
    external = 'external'
    internal = 'internal'
    study = 'study'

def get_all_projects_count():
    with db_session:
        query = select(p for p in Project)
        count = query.count()
    return count

def get_session_key(session):
    key = None
    if "key" in session:
        key = session["key"]
    return key


def get_user_type(session):
    if "key" in session:
        key = session["key"]
        with db_session:
            user = User.get(key=key)
        if not user:
            return UserType.anonymous
        return UserType(user.type)
    return UserType.anonymous


MAX_USER_VOTE_COUNT = 3
ALL_PROJECTS_COUNT = get_all_projects_count()
SUPERADMIN_PASSWORD = environ.get("SUPERADMIN_PASSWORD")
VALID_USER_TYPES = (UserType.guest, UserType.expert, UserType.admin)
VALID_ADMIN_TYPES = (UserType.admin, UserType.superadmin)
WHO = ('гостя', 'эксперта', 'администратора')


app = Flask(__name__)
app.secret_key = environ.get("SECRET_KEY")
Pony(app)

with db_session:
    superadmin = User.get(type=UserType.superadmin.value)
    key = str(uuid4())
    if not superadmin:
        superadmin = User(name="Pikvic", key=key, type=UserType.superadmin.value, activated=True)
   


# TODO везде проверять куки
# TODO во всех шаблонах проверять на ошибки


@app.route("/")
def index():
    user_type = get_user_type(session)
    return render_template('index.html', user_type=str(user_type))

@app.route("/login")
def login():
    user_type = get_user_type(session)
    return render_template('login.html', user_type=str(user_type))

@app.post("/login")
def login_post():
    password = request.form.get("password")
    if password == SUPERADMIN_PASSWORD:
        superadmin = User.get(type=UserType.superadmin.value)
        session["key"] = superadmin.key
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop('key', None)
    return redirect(url_for('index'))


@app.route("/invite")
def invite(error=None):
    user_type = get_user_type(session)
    if user_type not in VALID_ADMIN_TYPES:
        return redirect(url_for('index'))
    return render_template('invite.html', user_type=str(user_type))

@app.post("/invite")
def invite_post():
    user_type = get_user_type(session)
    if user_type not in VALID_ADMIN_TYPES:
        return redirect(url_for('index'))
    
    new_user_type = request.form.get("user_type")
    if UserType(new_user_type) not in VALID_USER_TYPES:
        error = "Ошибка: тип пользователя не в списке пользователей"
        return invite(error)

    key = str(uuid4())
    url = url_for('register', key=key, _external=True)
    who = [WHO[i] for i, ut in enumerate(VALID_USER_TYPES) if ut == UserType(new_user_type)][0]

    if UserType(new_user_type) == UserType.expert or UserType(new_user_type) == UserType.admin:
        name = request.form.get("name")
        new_user = User(key=key, type=new_user_type, name=name)
    else:
        new_user = User(key=key, type=new_user_type)
    return invite_qrcode(url=url, who=who)

@app.route("/invite/qrcode")
def invite_qrcode(url, who):
    user_type = get_user_type(session)
    if user_type not in VALID_ADMIN_TYPES:
        return redirect(url_for('index'))
    qrcode = segno.make(url)
    return render_template('invite_qrcode.html', who=who, qrcode=qrcode, url=url, user_type=str(user_type))

@app.route("/register/<key>")
def register(key):
    user = User.get(key=key)
    session_key = get_session_key(session)
    error = None
    if not user:
        error = "Ошибка: недействительный QR-код"
    if session_key and session_key != user.key:
        error = "Ошибка: по этому QR-коду уже кто-то зарегистрирован"
    if session_key and session_key == user.key:
        error = "Ошибка: вы уже зарегистрированы по этому QR-коду"
    if error:
        user_type=get_user_type(session)
        return render_template("register.html", error=error, user_type=str(user_type))
    
    if not session_key and not user.activated:
        user.activated = True
        who = [WHO[i] for i, ut in enumerate(VALID_USER_TYPES) if ut == UserType(user.type)][0]
        session["key"] = user.key
        user_type=get_user_type(session)
        return render_template("register.html", who=who, error=error, user_type=str(user_type))


@app.route("/projects")
def projects():
    user_type=get_user_type(session)
    projects = [p.to_dict() for p in Project.select()[:]]
    for p in projects:
        url = url_for('vote', project_key=p["key"], _external=True)
        qrcode = segno.make(url)
        p["url"] = url
        p["qrcode"] = qrcode
    return render_template('projects.html', projects=projects, user_type=str(user_type))

@app.route("/vote/<project_key>")
def vote(project_key):
    error = None
    user_type=get_user_type(session)
    # TODO Show errors in template for this route
    session_key = get_session_key(session)
    project = Project.get(key=project_key)
    if not project:
        return redirect(url_for('index'))
    # Anonimous
    if not session_key:
        return redirect(url_for('index'))
    user = User.get(key=session_key)
    
    #TODO show error

    # Wrong session key (no user with such key)
    if not user:
        return redirect(url_for('index'))
    
    # Not guest or expert
    if UserType(user.type) not in (UserType.guest, UserType.expert):
        return redirect(url_for('index'))

    # Already voted or marked

    votes = user.votes.select(project=project.id)[:]
    print(votes)
    marks = user.marks.select(project=project.id)[:]
    if marks:
        error = "Error: already marked!"
    if votes:
        error = "Error: already voted!"

    # Проверить, голосовал ли юзер
    # По юзеру выдать вариант голосования 
    #error = None
    
    return render_template('vote.html', user=user, error=error, project=project, user_type=str(user_type))

@app.post("/vote/<project_key>")
def vote_submit(project_key):
    session_key = get_session_key(session)
    project = Project.get(key=project_key)
    form = request.form
    if not form:
        return redirect(url_for('index'))
    if not project:
        return redirect(url_for('index'))
    # Anonimous
    if not session_key:
        return redirect(url_for('index'))
    user = User.get(key=session_key)
    # Wrong session key (no user with such key)
    if not user:
        return redirect(url_for('index'))
    # Not guest or expert
    if UserType(user.type) not in (UserType.guest, UserType.expert):
        return redirect(url_for('index'))
    
    if UserType(user.type) == UserType.guest:
        vote = Vote(project=project.id, user=user.id)
    if UserType(user.type) == UserType.expert:
        marks = {
            "idea": int(form.get("idea", 0)),
            "design": int(form.get("design", 0)),
            "features": int(form.get("features", 0)),
            "mvp": int(form.get("mvp", 0)),
            "team": int(form.get("team", 0))
        }
        mark = Mark(project=project.id, user=user.id, idea=marks["idea"], design=marks["design"], features=marks["features"], mvp=marks["mvp"], team=marks["team"])
    return vote_result()

@app.route("/vote/result")
def vote_result():
    user_type=get_user_type(session)
    session_key = get_session_key(session)
    # Anonymous
    if not session_key:
        return redirect(url_for('index'))
    user = User.get(key=session_key)
    if not user:
        return redirect(url_for('index'))
    if UserType(user.type) not in (UserType.guest, UserType.expert):
        return redirect(url_for('index'))

    if UserType(user.type) == UserType.guest:
        count_left = MAX_USER_VOTE_COUNT - len(user.votes)
    if UserType(user.type) == UserType.expert:
        count_left = get_all_projects_count() - len(user.marks)
    context = {
        "count_left": count_left,
        "user": user,
        "user_type": str(user_type)
    }
    return render_template('vote_result.html', **context)