# Automatically triggered when new agent added
def handle_new_agent(agent_name, agent_file):
    agent_info = parse_agent_metadata(agent_file)
    readme_content = read_readme()

    updated_content = add_agent_to_list(
        readme_content,
        agent_name,
        agent_info
    )

    if validate_changes(updated_content):
        write_readme(updated_content)
        commit_readme_update(f"docs: add {agent_name} to README agent list")
