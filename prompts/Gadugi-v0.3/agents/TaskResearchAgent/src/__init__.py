class ResearchKnowledgeBase:
    """Maintain research knowledge for future reference"""

    def __init__(self):
        self.research_cache = {}
        self.pattern_library = {}
        self.expert_network = {}

    def store_research_results(self, research_results):
        # Cache research for similar future tasks
        self.research_cache[research_results.topic] = research_results

        # Extract reusable patterns
        patterns = extract_solution_patterns(research_results)
        self.pattern_library.update(patterns)

        # Update expert network
        experts = extract_expert_contacts(research_results)
        self.expert_network.update(experts)

    def find_relevant_research(self, new_task):
        """Find existing research relevant to new task"""
        relevant_research = []

        for topic, research in self.research_cache.items():
            similarity = calculate_task_similarity(new_task, topic)
            if similarity > RELEVANCE_THRESHOLD:
                relevant_research.append((research, similarity))

        return sorted(relevant_research, key=lambda x: x[1], reverse=True)
