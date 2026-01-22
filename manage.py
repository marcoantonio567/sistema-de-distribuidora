#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "distribuidora_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django não está instalado ou não pôde ser importado."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
