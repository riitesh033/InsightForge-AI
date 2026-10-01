"""Inspect or promote an existing user to administrator."""

import argparse
import sys

from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.user import User


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect admin accounts or manually promote an existing user. "
            "This command never creates users or changes passwords."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--email",
        help="Inspect or promote this existing account by email.",
    )
    action.add_argument(
        "--list",
        action="store_true",
        help="List existing administrator account emails.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="With --email, report its admin status without changing it.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.check and args.list:
        print("--check cannot be used with --list.", file=sys.stderr)
        return 2

    with SessionLocal() as db:
        if args.list:
            admins = (
                db.query(User.email)
                .filter(User.is_superuser.is_(True))
                .order_by(User.email)
                .all()
            )
            if not admins:
                print("No administrator accounts found.")
            else:
                for (email,) in admins:
                    print(email)
            return 0

        email = args.email.strip().lower()
        if not email:
            print("An account email is required.", file=sys.stderr)
            return 2

        user = (
            db.query(User)
            .filter(func.lower(User.email) == email)
            .with_for_update()
            .first()
        )
        if user is None:
            print(
                "No existing account matches the supplied email.",
                file=sys.stderr,
            )
            return 1

        if args.check:
            print(
                f"Account {user.email}: "
                f"is_superuser={str(user.is_superuser).lower()}"
            )
            return 0

        if user.is_superuser:
            print(f"Account {user.email} is already an administrator.")
            return 0

        print(
            f"Promote existing account {user.email} "
            f"(user id {user.id}) to administrator?"
        )
        try:
            confirmation = input('Type "PROMOTE" to continue: ')
        except EOFError:
            print("Promotion cancelled: interactive confirmation is required.")
            return 1
        if confirmation != "PROMOTE":
            print("Promotion cancelled.")
            return 1

        user.is_superuser = True
        db.commit()
        db.refresh(user)
        if not user.is_superuser:
            print("Promotion did not persist.", file=sys.stderr)
            return 1

        print(f"Account {user.email} is now an administrator.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
