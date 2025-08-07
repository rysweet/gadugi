class LiteratureReviewMethod:
    """Systematic literature review approach"""

    def execute(self, research_topic):
        # Search academic databases
        academic_papers = search_academic_databases(research_topic)

        # Search technical blogs and articles
        technical_articles = search_technical_content(research_topic)

        # Search documentation and specifications
        official_docs = search_official_documentation(research_topic)

        # Synthesize findings
        return synthesize_literature_findings([
            academic_papers, technical_articles, official_docs
        ])
