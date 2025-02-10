from invenio_db import db
from invenio_oaiserver.models import OAISet

oaiset = OAISet(
    spec="Datasets",
    name="dataset",
    description=f"Datasets from high energy experiments.",
    system_created=True,
)
oaiset.search_pattern = "type.primary:Dataset"
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
    oaiset = OAISet(
        spec=exp,
        name=exp,
        description=f"Records related to the experiment {exp}.",
        system_created=True,
    )
    oaiset.search_pattern = f"experiment:{exp}"
    db.session.add(oaiset)
db.session.commit()
