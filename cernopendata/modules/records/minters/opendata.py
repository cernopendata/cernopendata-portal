from invenio_oaiserver.provider import OAIIDProvider


def cernopendata_generic_minter(
    record_uuid, data, pid_type, id_field, provider, oai=False
):
    provider = provider.create(
        object_type="rec",
        pid_type=pid_type,
        object_uuid=record_uuid,
        pid_value=str(f"{data[id_field]}-v{data['_versions']['index']}"),
    )
    if oai:
        data["pids"] = {"oai": {"id": f"oai:cernopendata.cern:{data[id_field]}"}}
        OAIIDProvider.create(
            object_type="rec",
            object_uuid=record_uuid,
            pid_value=f"oai:cernopendata.cern:{data[id_field]}-v{data['_versions']['index']}",
        )

    # The first version also registers the concept
    if data["_versions"]["index"] == 1:
        provider = provider.create(
            object_type="rec",
            pid_type=pid_type,
            object_uuid=record_uuid,
            pid_value=str(data[id_field]),
        )
        if oai:
            OAIIDProvider.create(
                object_type="rec",
                object_uuid=record_uuid,
                pid_value=f"oai:cernopendata.cern:{data[id_field]}",
            )
    return provider.pid
