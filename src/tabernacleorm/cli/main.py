"""
CLI entry point.
"""

import argparse
import asyncio
import sys

from . import commands

def main():
    parser = argparse.ArgumentParser(description="TabernacleORM CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init
    subparsers.add_parser("init", help="Initialize project")
    
    # makemigrations
    mm_parser = subparsers.add_parser("makemigrations", help="Create new migration")
    mm_parser.add_argument("name", help="Name of the migration", nargs="?", default="update")
    
    # migrate
    subparsers.add_parser("migrate", help="Apply migrations")
    
    # rollback
    subparsers.add_parser("rollback", help="Rollback last migration")
    
    # shell
    subparsers.add_parser("shell", help="Start interactive shell")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "init":
        asyncio.run(commands.init_project())
    elif args.command == "makemigrations":
        asyncio.run(commands.makemigrations(args.name))
    elif args.command == "migrate":
        asyncio.run(commands.migrate())
    elif args.command == "rollback":
        asyncio.run(commands.rollback())
    elif args.command == "shell":
        asyncio.run(commands.shell())

if __name__ == "__main__":
    main()
