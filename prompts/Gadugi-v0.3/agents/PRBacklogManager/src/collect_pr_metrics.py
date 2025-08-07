   def collect_pr_metrics(pr_number, readiness_result):
       metrics = {
           'processing_time': productivity_analyzer.get_processing_time(pr_task_id),
           'issues_resolved': count_resolved_issues(pr_number),
           'automation_success_rate': calculate_automation_success(readiness_result),
           'time_to_ready': calculate_time_to_ready(pr_number)
       }

       productivity_analyzer.record_pr_metrics(pr_number, metrics)
       state_manager.store_final_assessment(pr_task_id, readiness_result)
   