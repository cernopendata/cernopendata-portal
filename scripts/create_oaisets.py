from invenio_db import db
from invenio_oaiserver.models import OAISet


OAISet().query.delete()

oaiset = OAISet(
    spec="openaire_data",
    name="Openaire data",
    description="Records to be harvested by openaire",
    system_created=True,
)
oaiset.search_pattern = f"pids.oai.id:*"
db.session.add(oaiset)
db.session.commit()

for type in 'Dataset', 'Documentation', 'Software':
    oaiset = OAISet(
        spec=f"records-{type}",
        name=f"Records of type {type}",
        description=f"{type} from high energy experiments.",
        system_created=True,
    )
    oaiset.search_pattern = f"type.primary:{type}"
    db.session.add(oaiset)


for exp in ["ALICE", "ATLAS", "CMS", "DELPHI", "LHCb", "TOTEM"]:
    print(f"Adding the set {exp}")
    oaiset = OAISet(
        spec=f"exp-{exp}",
        name=f"Experiment {exp}",
        description=f"Records created by the experiment {exp} Collaboration.",
        system_created=True,
    )
    oaiset.search_pattern = f'collaboration.name:"{exp} Collaboration"'
    db.session.add(oaiset)
db.session.commit()
print("All sets have been added :-)")
