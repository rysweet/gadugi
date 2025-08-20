#!/usr/bin/env python3
import time
import json
from pathlib import Path
from datetime import datetime
import os

def clear_screen():
    os.system('clear')

def find_log_files(task_id):
    """Find log files for a specific task"""
    log_files = []
    
    # Check common log locations
    worktree_path = Path(f'.worktrees/task-{task_id}')
    if worktree_path.exists():
        # Look for workflow logs
        workflow_logs = list(worktree_path.glob('**/*.log'))
        log_files.extend(workflow_logs)
        
        # Look for state files
        state_files = list(worktree_path.glob('**/*state*.json'))
        log_files.extend(state_files)
        
        # Look for workflow files
        workflow_files = list(worktree_path.glob('**/*workflow*.md'))
        log_files.extend(workflow_files)
        
        # Look for output files
        output_files = list(worktree_path.glob('**/*output*.txt'))
        log_files.extend(output_files)
    
    # Check monitoring directory
    monitoring_dir = Path('.gadugi/monitoring')
    if monitoring_dir.exists():
        task_logs = list(monitoring_dir.glob(f'*{task_id}*.json'))
        log_files.extend(task_logs)
    
    return [str(f) for f in log_files if f.exists()]

def show_enhanced_dashboard():
    print('🚀 GADUGI ORCHESTRATOR LIVE DASHBOARD')
    print('🔗 Enhanced with Clickable Log Files')
    print('=' * 80)
    
    while True:
        try:
            print(f'\\n[{datetime.now().strftime("%H:%M:%S")}] Refreshing dashboard...')
            
            # Find latest status file
            status_files = list(Path('.gadugi/monitoring/').glob('orchestration-*_status.json'))
            if not status_files:
                print('❌ No orchestrator status found')
                print('   Looking in:', os.path.abspath('.gadugi/monitoring/'))
                time.sleep(5)
                continue
                
            latest = max(status_files, key=lambda x: x.stat().st_mtime)
            
            # Check if file is recent (within last 5 minutes)
            file_age = time.time() - latest.stat().st_mtime
            if file_age > 300:  # 5 minutes
                print('⚠️  Orchestrator appears to be stopped')
                print(f'   Last update: {int(file_age/60)} minutes ago')
                print(f'   Latest file: {latest}')
            
            with open(latest) as f:
                data = json.load(f)
            
            # Main status
            total = data['total_processes']
            running = data['status_breakdown']['running']
            queued = data['status_breakdown']['queued']
            completed = total - running - queued
            
            print(f'📊 STATUS: {completed}/{total} complete | 🟢 {running} running | 🟡 {queued} queued')
            
            # Process details with clickable logs
            print('\\n🔄 ACTIVE PROCESSES & LOGS:')
            print('-' * 60)
            
            for proc in data['active_processes']:
                status_emoji = '🟢' if proc['status'] == 'running' else '🟡'
                runtime_mins = int(proc['runtime_seconds'] / 60)
                runtime_secs = int(proc['runtime_seconds'] % 60)
                
                print(f'{status_emoji} {proc["task_id"]:8} | {proc["status"]:8} | {runtime_mins:2}m {runtime_secs:2}s')
                
                # Find and display clickable log files
                log_files = find_log_files(proc['task_id'])
                if log_files:
                    for i, log_file in enumerate(log_files[:2]):  # Show max 2 files
                        file_name = Path(log_file).name
                        abs_path = os.path.abspath(log_file)
                        print(f'   📄 file://{abs_path}')
                else:
                    # Check if worktree exists
                    worktree_path = Path(f'.worktrees/task-{proc["task_id"]}')
                    if worktree_path.exists():
                        abs_wt_path = os.path.abspath(worktree_path)
                        print(f'   📁 file://{abs_wt_path}')
                    else:
                        print(f'   ❓ No worktree found')
            
            print('\\n🔗 DIRECTORIES:')
            if Path('.worktrees').exists():
                print(f'📁 file://{os.path.abspath(".worktrees")}')
            if Path('.gadugi/monitoring').exists():
                print(f'📊 file://{os.path.abspath(".gadugi/monitoring")}')
            
            # Check for completions
            if completed == total:
                print('\\n🎉 ALL WORKFLOWS COMPLETE!')
                break
            elif file_age > 300:
                print(f'\\n⚠️  Orchestrator stopped ({int(file_age/60)}m ago)')
                break
                
            print('\\n⏰ Next update in 10 seconds... (Ctrl+C to exit)')
            time.sleep(10)
            
        except KeyboardInterrupt:
            print('\\n👋 Dashboard stopped')
            break
        except Exception as e:
            print(f'❌ Error: {e}')
            print(f'Working directory: {os.getcwd()}')
            time.sleep(5)

if __name__ == "__main__":
    show_enhanced_dashboard()