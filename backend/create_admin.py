"""Create a local administrator without storing credentials in source control."""

import getpass
import os
import sys

sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import generate_token_str, hash_password


def main() -> None:
    username = os.getenv("ADMIN_USERNAME") or input("Admin username: ").strip()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Admin password: ")

    if not username:
        raise SystemExit("Admin username cannot be empty")
    if len(password) < 12:
        raise SystemExit("Admin password must contain at least 12 characters")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Administrator already exists: {username}")
            return

        db.add(
            User(
                username=username,
                nickname="Administrator",
                password_hash=hash_password(password),
                role="admin",
                token=generate_token_str(),
            )
        )
        db.commit()
        print(f"Created administrator: {username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
