def model_dependencies(subtasks):
    """Create dependency graph between subtasks"""

    dependency_graph = DependencyGraph()

    for subtask in subtasks:
        # Add subtask as node
        dependency_graph.add_node(subtask)

        # Analyze dependencies
        for other_subtask in subtasks:
            if subtask != other_subtask:
                dependency_type = analyze_dependency(subtask, other_subtask)
                if dependency_type:
                    dependency_graph.add_edge(subtask, other_subtask, dependency_type)

    return dependency_graph
