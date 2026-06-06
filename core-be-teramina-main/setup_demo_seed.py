#!/usr/bin/env python
"""Compatibility entry point for the onboarding demo seed."""

import os

import django
from django.core.management import call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teramina.settings")
django.setup()

call_command("seed_demo")
