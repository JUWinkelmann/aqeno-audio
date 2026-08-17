"""Adapters — concrete implementations of `ports/`, behind their Protocols.

May import `ports/` and `domain/`, never `ui/`, and never each other
(`DEVELOPMENT.md` § "Rules the layout enforces", rule 3). Not part of the
import-boundary check: third-party and hardware libraries live here.
"""
