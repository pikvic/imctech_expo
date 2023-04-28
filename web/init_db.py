from database.database import db, User, Project, Member, Mark
from pony.orm import db_session
from uuid import uuid4
import yaml

def create_superadmin():
    with db_session:
        superadmin = User.get(type='superadmin')
        key = str(uuid4())
        if not superadmin:
            superadmin = User(name="Pikvic", key=key, type='superadmin', activated=True)

def create_projects():
    with open('projects.yaml', 'rt', encoding='utf-8') as file:
        projects = yaml.safe_load(file)

    with db_session:
        for p in projects["projects"]:
            proj = Project.get(key=p["key"])
            if proj:
                continue
            project = Project(name=p["name"], type=p["type"], description=p["description"], team=p["team"], key=p["key"])
            for m in p["members"]:
                mem_dict = {k: v for k, v in m.items() if v is not None}
                member = Member(**mem_dict, project=project)
            

        
            
