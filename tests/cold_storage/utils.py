import json


def build_record(app, storage_paths, record_data_param):
    """
    Constructs a record dictionary and creates associated dummy files.
    """
    hot_path, cold_path = storage_paths

    files_list_for_record = []
    hot_file_paths = []
    cold_file_paths = []

    for spec in record_data_param["file_specs"]:
        file_name = spec["name"]
        file_type = spec.get("type")

        is_index = file_name == "index.json" and "referenced_file_info" in spec

        if is_index:
            referenced_info = spec["referenced_file_info"]
            ref_file_name = referenced_info["name"]
            ref_file_content = referenced_info["content"]

            ref_hot_path = hot_path / ref_file_name
            ref_hot_path.write_bytes(ref_file_content)

            index_content_data = [
                {
                    "checksum": "adler32:9719fd6a",
                    "size": len(ref_file_content),
                    "uri": str(ref_hot_path),
                }
            ]
            file_content_for_current_spec = json.dumps(index_content_data).encode(
                "utf-8"
            )
        else:
            file_content_for_current_spec = spec["content"]

        hot_file_path = hot_path / file_name
        hot_file_path.write_bytes(file_content_for_current_spec)

        file_entry_dict = {
            "checksum": "adler32:9719fd6a",
            "size": len(file_content_for_current_spec),
            "uri": str(hot_file_path),
        }
        if file_type:
            file_entry_dict["type"] = file_type

        files_list_for_record.append(file_entry_dict)
        hot_file_paths.append(str(ref_hot_path) if is_index else str(hot_file_path))
        cold_file_paths.append(
            str(cold_path / ref_file_name) if is_index else str(cold_path / file_name)
        )

    record_dict = {
        "$schema": app.extensions["invenio-jsonschemas"].path_to_url(
            record_data_param.get("schema_path", "records/record-v1.0.0.json")
        ),
        "recid": record_data_param["recid"],
        "date_published": "2024",
        "experiment": ["ALICE"],
        "publisher": "CERN Open Data Portal",
        "title": record_data_param["title"],
        "type": {
            "primary": "Dataset",
            "secondary": ["Derived"],
        },
        "files": files_list_for_record,
    }

    return (
        record_data_param["recid"],
        hot_file_paths,
        cold_file_paths,
        record_dict,
    )


def run_command(runner, app, command, args):
    """Helper to run a CLI command and assert success."""
    result = runner.invoke(command, args, obj=app)
    assert result.exit_code == 0
    return result


def assert_list_output(
    result,
    hot_file_paths,
    cold_file_paths,
    expected_hot_count,
    expected_cold_count,
):
    """
    Asserts common elements in the 'cold list' output.
    """
    assert result.exit_code == 0
    assert f"Summary: {len(hot_file_paths)} files" in result.output

    actual_hot_count = 0
    for hot_path in hot_file_paths:
        if f"Hot copy: {hot_path}" in result.output:
            actual_hot_count += 1
        else:
            assert f"Hot copy: {hot_path}" not in result.output

    assert actual_hot_count == expected_hot_count
    assert f"{expected_hot_count} hot copies" in result.output

    actual_cold_count = 0
    for cold_path_str in cold_file_paths:
        if f"Cold copy: {cold_path_str}" in result.output:
            actual_cold_count += 1
        else:
            assert f"Cold copy: {cold_path_str}" not in result.output

    assert actual_cold_count == expected_cold_count
    assert f"{expected_cold_count} cold copies" in result.output
