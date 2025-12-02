"""Pretty printing utilities for better console output."""
from typing import Any


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def print_header(text: str, char: str = "=", color: str = Colors.CYAN) -> None:
    """Print a formatted header."""
    width = 60
    print(f"\n{color}{char * width}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{text.center(width)}{Colors.RESET}")
    print(f"{color}{char * width}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.GREEN}{text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.BRIGHT_BLUE}ℹ{Colors.RESET} {Colors.BLUE}{text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.BRIGHT_YELLOW}⚠{Colors.RESET} {Colors.YELLOW}{text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.BRIGHT_RED}✗{Colors.RESET} {Colors.RED}{text}{Colors.RESET}")


def print_box(title: str, content: str, color: str = Colors.CYAN) -> None:
    """Print content in a box with title."""
    width = 60
    border = f"{color}{'─' * (width - 2)}{Colors.RESET}"
    
    print(f"\n{color}┌{border}┐{Colors.RESET}")
    print(f"{color}│{Colors.RESET} {Colors.BOLD}{title:<{width-4}}{Colors.RESET}{color}│{Colors.RESET}")
    print(f"{color}├{border}┤{Colors.RESET}")
    
    # Wrap content if needed
    lines = content.split("\n")
    for line in lines:
        if len(line) <= width - 4:
            print(f"{color}│{Colors.RESET} {line:<{width-4}}{color}│{Colors.RESET}")
        else:
            # Word wrap
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line + word) + 1 <= width - 4:
                    current_line += word + " "
                else:
                    if current_line:
                        print(f"{color}│{Colors.RESET} {current_line:<{width-4}}{color}│{Colors.RESET}")
                    current_line = word + " "
            if current_line:
                print(f"{color}│{Colors.RESET} {current_line:<{width-4}}{color}│{Colors.RESET}")
    
    print(f"{color}└{border}┘{Colors.RESET}\n")


def print_key_value(key: str, value: Any, key_color: str = Colors.BRIGHT_CYAN, 
                    value_color: str = Colors.WHITE) -> None:
    """Print a key-value pair."""
    print(f"{key_color}{key}:{Colors.RESET} {value_color}{value}{Colors.RESET}")


def print_tool_call(tool_name: str, args: dict[str, Any], result: str) -> None:
    """Print a formatted tool call."""
    print(f"\n{Colors.BRIGHT_MAGENTA}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}🔧 Tool Call: {Colors.BOLD}{tool_name}{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.DIM}Arguments:{Colors.RESET}")
    for k, v in args.items():
        print(f"  {Colors.CYAN}{k}:{Colors.RESET} {Colors.WHITE}{v}{Colors.RESET}")
    print(f"{Colors.DIM}Result:{Colors.RESET}")
    print(f"  {Colors.GREEN}{result}{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}{'─' * 60}{Colors.RESET}\n")


def print_step(step_num: int, total: int, description: str) -> None:
    """Print a step indicator."""
    print(f"{Colors.BRIGHT_BLUE}[{step_num}/{total}]{Colors.RESET} {Colors.BOLD}{description}{Colors.RESET}")


def print_separator(char: str = "─", color: str = Colors.DIM) -> None:
    """Print a separator line."""
    print(f"{color}{char * 60}{Colors.RESET}")

