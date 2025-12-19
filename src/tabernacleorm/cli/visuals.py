
import sys
import os

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Check if we should disable colors (Windows cmd without support, though most modern terminals support it)
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

LOGO = r"""
  _______      _                                  _       
 |__   __|    | |                                | |      
    | |  _ __ | | __   ___  _ __  _ __ ___   __ _| | ___  
    | | | '_ \| |/ /  / _ \| '__|| '_ ` _ \ / _` | |/ _ \ 
    | | | |_) |   <  | (_) | |   | | | | | | (_| | |  __/ 
    |_| | .__/|_|\_\  \___/|_|   |_| |_| |_|\__,_|_|\___| 
        | |                                               
        |_|                                               
               Async ORM for Modern Python
"""

def print_logo():
    print(f"{Colors.CYAN}{Colors.BOLD}{LOGO}{Colors.ENDC}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")

def print_error(msg: str):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def print_warning(msg: str):
    print(f"{Colors.WARNING}! {msg}{Colors.ENDC}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")
