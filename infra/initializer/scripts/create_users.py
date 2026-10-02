#!/usr/bin/env -S uv run --script
"""Create deterministic users for local TripSphere acceptance flows."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_VERSION = "users-v1"
DEFAULT_DSN = "postgresql://postgres:fudanse@localhost:5432/user_db"


@dataclass(frozen=True, slots=True)
class SeedUser:
    id: str
    name: str
    email: str
    password: str
    password_hash: str
    role: str = "USER"


USERS = (
    SeedUser(
        id="00000000-0000-4000-8000-000000000001",
        name="TripSphere User A",
        email="user-a@tripsphere.local",
        password="TripSphereA1!",
        password_hash="$2b$12$QGmJu.CdTtzLqurORqlpUuIUJs1gjZHZx3DTQZScYhGCYW8eK54oy",
    ),
    SeedUser(
        id="00000000-0000-4000-8000-000000000002",
        name="TripSphere User B",
        email="user-b@tripsphere.local",
        password="TripSphereB1!",
        password_hash="$2b$12$VOrzFlyOJGLXl.4KhKorJugmroPOosoyz1rrgYnh8zh90Bgxo5gJe",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or replace the deterministic TripSphere acceptance users."
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("USER_DATABASE_DSN", DEFAULT_DSN),
        help="PostgreSQL DSN for user_db.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=BASE_DIR / "data" / "temp" / "users_manifest.json",
        help="Path for the generated seed manifest.",
    )
    return parser.parse_args()


def ensure_schema(connection: psycopg.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id VARCHAR(36) NOT NULL,
            role VARCHAR(255) NOT NULL,
            PRIMARY KEY (user_id, role),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )


def upsert_user(connection: psycopg.Connection, user: SeedUser) -> None:
    connection.execute(
        "DELETE FROM users WHERE email = %s AND id <> %s",
        (user.email, user.id),
    )
    connection.execute(
        """
        INSERT INTO users (id, name, email, password)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            email = EXCLUDED.email,
            password = EXCLUDED.password
        """,
        (user.id, user.name, user.email, user.password_hash),
    )
    connection.execute("DELETE FROM user_roles WHERE user_id = %s", (user.id,))
    connection.execute(
        "INSERT INTO user_roles (user_id, role) VALUES (%s, %s)",
        (user.id, user.role),
    )


def write_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "seed_version": SEED_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "users": [
            {
                key: value
                for key, value in asdict(user).items()
                if key != "password_hash"
            }
            for user in USERS
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    with psycopg.connect(args.dsn) as connection:
        with connection.transaction():
            ensure_schema(connection)
            for user in USERS:
                upsert_user(connection, user)

    write_manifest(args.manifest)
    print(f"seed_version: {SEED_VERSION}")
    print(f"manifest: {args.manifest}")
    for user in USERS:
        print(
            f"{user.name}: id={user.id} email={user.email} "
            f"password={user.password} role={user.role}"
        )


if __name__ == "__main__":
    main()
