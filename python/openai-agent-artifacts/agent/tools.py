"""
This module is deprecated. Tools are now provided by DISK_TOOLS from acontext.agent.disk.

The agent now uses DISK_TOOLS directly, which provides:
- write_file: Create or overwrite text files
- read_file: Read file contents with optional line offset and limit
- replace_string: Find and replace text in files
- list_artifacts: List files and directories in a path

See agent/react.py for the updated implementation.
"""

