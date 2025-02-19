from invenio_db import db
from invenio_oaiserver.models import OAISet


OAISet().query.delete()

oaiset = OAISet(
    spec="Records to be harvested by openaire",
    name="openaire_data",
    description="Records to be harvested by openaire",
    system_created=True,
)
oaiset.search_pattern = f"pids.oai.id:*"
db.session.add(oaiset)
db.session.commit()

for type in 'Dataset', 'Documentation', 'Software':
    oaiset = OAISet(
        spec=f"Records of type {type}",
        name=type,
        description=f"{type} from high energy experiments.",
        system_created=True,
    )
    oaiset.search_pattern = f"type.primary:{type}"
    db.session.add(oaiset)


oaiset = OAISet(
    spec="Documentation",
    name="documentation",
    description=f"Documentation for the datasets.",
    system_created=True,
)
oaiset.search_pattern = "type.primary:Documentation"
db.session.add(oaiset)

for exp in ["ALICE", "ATLAS", "CMS", "DELPHI", "LHCb", "TOTEM"]:
    print(f"Adding the set {exp}")
    oaiset = OAISet(
        spec=f"Records created by the {exp} collaboration",
        name=exp,
        description=f"Records created by the experiment {exp} Collaboration.",
        system_created=True,
    )
    oaiset.search_pattern = f'collaboration.name:"{exp} Collaboration"'
    db.session.add(oaiset)
db.session.commit()
print("All sets have been added :-)")
