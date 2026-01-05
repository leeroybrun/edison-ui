"""Actor identity models for auditing.

Actor identity must be stable and explicit for auditing (OS user + display name).
"""

from __future__ import annotations

import getpass

from pydantic import BaseModel


class ActorIdentity(BaseModel):
    """Identity of an actor performing actions.

    Attributes:
        os_user: Local OS username (from getpass.getuser()).
        display_name: Optional per-session display name.
    """

    os_user: str
    display_name: str | None = None


def get_current_actor() -> ActorIdentity:
    """Get the current actor identity from the OS.

    Returns:
        ActorIdentity with os_user populated from getpass.getuser().
    """
    return ActorIdentity(os_user=getpass.getuser(), display_name=None)
