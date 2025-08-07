   def create_test_backup(test_file_path):
       backup_path = f"{test_file_path}.backup"
       shutil.copy2(test_file_path, backup_path)
       return backup_path

   def rollback_test_changes(test_file_path, backup_path):
       shutil.copy2(backup_path, test_file_path)
       os.remove(backup_path)
   