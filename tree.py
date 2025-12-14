import os

def print_clean_tree(startpath, ignore=None, prefix=""):
    if ignore is None:
        ignore = ['.git', '__pycache__']
    
    entries = [e for e in os.listdir(startpath) if e not in ignore]
    entries.sort()
    
    for i, entry in enumerate(entries):
        path = os.path.join(startpath, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + entry)
        
        if os.path.isdir(path):
            extension = "    " if i == len(entries) - 1 else "│   "
            print_clean_tree(path, ignore=ignore, prefix=prefix + extension)

# Run it in your project folder
print(os.path.basename(os.getcwd()) + "/")
print_clean_tree(os.getcwd())