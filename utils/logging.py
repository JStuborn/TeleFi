from colorama import Back, Fore, Style, init

init(autoreset=True)

LIGHT_PURPLE    = '\033[38;2;100;100;255m'
PURPLE_BLUE     = '\033[38;2;100;100;255m'
LIGHT_PURPLE    = '\033[38;2;200;180;255m'
BOLD_WHITE      = '\033[1;37m'

def print_info(message):
    print(f"{PURPLE_BLUE}ℹ {BOLD_WHITE}{message}")

def print_success(message):
    print(f"{LIGHT_PURPLE}✔ {BOLD_WHITE}{message}")

def print_warning(message):
    print(f"{Fore.YELLOW}{Style.BRIGHT}⚠ {BOLD_WHITE}{message}")

def print_error(message):
    print(f"{Fore.RED}✘ {message}")

def print_header(message):
    print(f"\n{PURPLE_BLUE}{Style.BRIGHT}{message}")
    print(f"{PURPLE_BLUE}{'-' * len(message)}{Style.RESET_ALL}")

def print_subheader(message):
    print(f"\n{LIGHT_PURPLE}{Style.BRIGHT}{message}")
    print(f"{LIGHT_PURPLE}{'-' * len(message)}{Style.RESET_ALL}")
