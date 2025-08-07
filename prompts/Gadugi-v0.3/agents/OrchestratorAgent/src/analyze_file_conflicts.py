def analyze_file_conflicts(tasks):
    \"\"\"Detect tasks that modify the same files\"\"\"
    file_map = {}
    conflicts = []

    for task in tasks:
        target_files = extract_target_files(task.prompt_content)
        for file_path in target_files:
            if file_path in file_map:
                conflicts.append((task.id, file_map[file_path]))
            file_map[file_path] = task.id

    return conflicts
