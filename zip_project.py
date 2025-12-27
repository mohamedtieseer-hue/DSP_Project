import zipfile
import os

zip_name = "DSP_Project_Source.zip"
extensions_to_include = ['.py', '.md', '.txt', '.gitignore']
excluded_files = [zip_name]
excluded_dirs = ['__pycache__', 'outputs', '.git']

with zipfile.ZipFile(zip_name, 'w') as zf:
    for root, dirs, files in os.walk('.'):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            if file in excluded_files:
                continue
            
            # Check extension
            _, ext = os.path.splitext(file)
            if ext in extensions_to_include or file == '.gitignore':
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, '.'))
                print(f"Added {file_path}")

print(f"Created {zip_name}")
