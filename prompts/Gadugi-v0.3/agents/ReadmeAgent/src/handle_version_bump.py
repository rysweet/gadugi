# Coordinate with release workflows
def handle_version_bump(old_version, new_version):
    changes = [
        update_version_references(new_version),
        update_installation_instructions(),
        refresh_changelog_links(),
        validate_all_examples()
    ]

    apply_changes(changes)
    validate_readme_accuracy()
