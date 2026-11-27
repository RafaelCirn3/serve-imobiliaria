from importlib import import_module


class Command(import_module("apps.robot.management.commands.robot-fonte").Command):
    developer_profile = "icon"
