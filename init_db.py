from database.database import db, User, Project, Member, Mark
from pony.orm import db_session
from uuid import uuid4
import yaml

with open('projects.yaml', 'rt', encoding='utf-8') as file:
    projects = yaml.safe_load(file)

with db_session:
    for p in projects["projects"]:
        key = str(uuid4())
        project = Project(name=p["name"], type=p["type"], description=p["description"], team=p["team"], key=p["key"])
        for m in p["members"]:
            mem_dict = {k: v for k, v in m.items() if v is not None}
            member = Member(**mem_dict, project=project)
            
        

        
            
