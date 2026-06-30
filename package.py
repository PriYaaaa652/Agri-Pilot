import os
import zipfile

def package_project():
    # Root of the project (where package.py sits)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    # Workspace directory (one level up)
    workspace_dir = os.path.dirname(project_dir)
    # Output zip path in the workspace root
    zip_path = os.path.join(workspace_dir, "agripilot.zip")
    
    print(f"Creating Kaggle submission archive at: {zip_path}")
    
    exclude_dirs = {
        '.venv',
        '__pycache__',
        '.pytest_cache',
        '.ruff_cache',
        '.git',
        '.adk'
    }
    
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(project_dir):
            # Prune directory list in-place so os.walk does not traverse excluded dirs
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # Exclude python bytecode compilation artifacts or session db files
                if file.endswith('.pyc') or file.endswith('.pyo') or file.endswith('.pyd') or file == 'session.db':
                    continue
                
                full_path = os.path.join(root, file)
                # Ensure the root folder of the archive is 'agripilot/'
                rel_path = os.path.relpath(full_path, workspace_dir)
                z.write(full_path, rel_path)
                count += 1
                
    print(f"Archive created successfully with {count} files.")

if __name__ == "__main__":
    package_project()
