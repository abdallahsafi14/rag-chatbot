import os

# ============================
# إعدادات
# ============================
INCLUDE_CONTENT = True   # True = اسم + محتوى | False = شجرة أسماء فقط

IGNORED_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    '.venv', 'venv', 'env', '.env', 'virtualenv',
    '.idea', '.vscode', 'dist', 'build', '.next',
    '.nuxt', 'target', '.gradle', '.mvn', 'vendor',
    'bower_components', '.pytest_cache', '.mypy_cache',
    'site-packages', 'eggs', '.eggs', 'htmlcov', '.tox','chroma_db', 'data', 
}

IGNORED_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    '.webp', '.tiff', '.tif', '.heic', '.raw', '.psd',
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.mpeg', '.mpg', '.3gp',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.o',
    '.a', '.lib', '.bin', '.class', '.jar', '.war', '.ear',
    '.whl', '.egg',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
    '.db', '.sqlite', '.sqlite3', '.mdb',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.lock', '.DS_Store', '.map', '.min.js', '.min.css', '.lock','.bin', '.tiktoken',
}

IGNORED_FILENAMES = {
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    'composer.lock',
    'content fie',
    '.env',  
}

SEPARATOR = "---FILE_SEPARATOR---"
OUTPUT_FILE = "project_dump.txt"
SCRIPT_NAME = os.path.basename(__file__)


# ============================
# دوال مشتركة
# ============================
def should_ignore_dir(name):
    return name in IGNORED_DIRS or name.startswith('.')


def should_ignore_file(filename):
    if filename == SCRIPT_NAME or filename == OUTPUT_FILE:
        return True
    if filename in IGNORED_FILENAMES:    
        return True
    _, ext = os.path.splitext(filename)  
    return ext.lower() in IGNORED_EXTENSIONS 


def collect_files(root_dir):
    collected = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for filename in filenames:
            if not should_ignore_file(filename):
                collected.append(os.path.join(dirpath, filename))
    return sorted(collected)


# ============================
# وضع المحتوى الكامل
# ============================
def dump_with_content(root_dir, output_path):
    files = collect_files(root_dir)
    count = 0
    with open(output_path, 'w', encoding='utf-8') as out:
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                rel_path = os.path.relpath(filepath, root_dir)
                out.write(f"{rel_path}\n{content}\n{SEPARATOR}\n")
                count += 1
                print(f"  + {rel_path}")
            except Exception as e:
                print(f"  ! تخطي {filepath}: {e}")
    return count


# ============================
# وضع الشجرة فقط
# ============================
def build_tree(root_dir):
    """يبني قاموساً هرمياً يمثل شجرة المجلدات"""
    tree = {}
    for filepath in collect_files(root_dir):
        rel = os.path.relpath(filepath, root_dir)
        parts = rel.replace('\\', '/').split('/')
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
    return tree


def render_tree(node, output_lines, prefix=""):
    entries = sorted(node.keys())
    for i, name in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        output_lines.append(f"{prefix}{connector}{name}")
        if node[name]:  # مجلد (له أبناء)
            extension = "    " if is_last else "│   "
            render_tree(node[name], output_lines, prefix + extension)


def dump_tree_only(root_dir, output_path):
    tree = build_tree(root_dir)
    lines = [os.path.basename(root_dir) + "/"]
    render_tree(tree, lines)

    with open(output_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(lines) + '\n')

    for line in lines:
        print(" ", line)
    return len([l for l in lines if '──' in l])  # عدد الملفات فقط


# ============================
# نقطة الدخول
# ============================
if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    output = os.path.join(root, OUTPUT_FILE)

    mode = "المحتوى الكامل" if INCLUDE_CONTENT else "شجرة الأسماء"
    print(f"الوضع : {mode}")
    print(f"المجلد: {root}")
    print(f"الإخراج: {output}\n")

    if INCLUDE_CONTENT:
        count = dump_with_content(root, output)
    else:
        count = dump_tree_only(root, output)

    print(f"\nتم: {count} ملف → {OUTPUT_FILE}")