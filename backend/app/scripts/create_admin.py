"""Interactively set credentials and admin status for an existing account."""

import argparse
import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User

MIN_PASSWORD_LENGTH = 12
_email_adapter = TypeAdapter(EmailStr)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Set the password and administrator flag for an existing user. "
            "The command does not create accounts."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report whether an existing account is an administrator.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing administrator account emails and exit.",
    )
    return parser


def _prompt_email() -> str | None:
    try:
        supplied_email = input("Admin email: ").strip()
        return str(_email_adapter.validate_python(supplied_email)).lower()
    except (EOFError, ValidationError, ValueError):
        print("Enter a valid email address.", file=sys.stderr)
        return None


def _password_is_strong(password: str) -> bool:
    return (
        len(password) >= MIN_PASSWORD_LENGTH
        and any(character.islower() for character in password)
        and any(character.isupper() for character in password)
        and any(character.isdigit() for character in password)
        and any(not character.isalnum() for character in password)
    )


def _get_account(db: Session, email: str) -> User | None:
    return (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .with_for_update()
        .first()
    )


def main() -> int:
    args = _parser().parse_args()
    if args.check and args.list:
        print("--check and --list cannot be used together.", file=sys.stderr)
        return 2

    if args.list:
        with SessionLocal() as db:
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

    email = _prompt_email()
    if email is None:
        return 2

    with SessionLocal() as db:
        user = _get_account(db, email)
        if user is None:
            print(
                "No existing account matches that email. Register the account "
                "through the normal application before using this command.",
                file=sys.stderr,
            )
            return 1

        if args.check:
            print(
                "Administrator access is enabled."
                if user.is_superuser
                else "Administrator access is not enabled."
            )
            return 0

        try:
            password = getpass.getpass("Admin password: ")
            password_confirmation = getpass.getpass("Confirm admin password: ")
        except EOFError:
            print("Password input was cancelled.", file=sys.stderr)
            return 2

        if password != password_confirmation:
            print("The passwords do not match.", file=sys.stderr)
            return 2
        if not _password_is_strong(password):
            print(
                "Use at least 12 characters, including uppercase, lowercase, "
                "a number, and a symbol.",
                file=sys.stderr,
            )
            return 2

        user.hashed_password = hash_password(password)
        user.is_superuser = True
        db.commit()
        db.refresh(user)
        if not user.is_superuser:
            print("Administrator update did not persist.", file=sys.stderr)
            return 1

        print("The existing account is now configured as an administrator.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
