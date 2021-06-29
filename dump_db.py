import argparse
import csv
import pathlib
import sqlite3
import sys


def dump_users(db, path):
    users = db.execute(
        "SELECT user_id, email, verified, hashed_password, nickname, "
        "bio, gender, dob, active, joined, administrator "
        "FROM user "
        "ORDER BY user_id"
    )

    with open(path / "user.csv", "w", newline="") as fd:
        writer = csv.writer(fd, dialect="excel")
        # Header row.
        writer.writerow(
            [
                "user_id",
                "email",
                "verified",
                "hashed_password",
                "nickname",
                "bio",
                "gender",
                "dob",
                "active",
                "joined",
                "administrator",
            ]
        )
        writer.writerows(users)


def dump_rooms(db, path):
    rooms = db.execute(
        "SELECT room_id, owner_id, name, description, units, "
        "access, absolute, created "
        "FROM room "
        "ORDER BY room_id"
    )

    with open(path / "room.csv", "w", newline="") as fd:
        writer = csv.writer(fd, dialect="excel")
        # Header row.
        writer.writerow(
            [
                "room_id",
                "owner_id",
                "name",
                "description",
                "units",
                "access",
                "absolute",
                "created",
            ]
        )
        writer.writerows(rooms)


def dump_activities(db, path):
    activities = db.execute(
        "SELECT activity_id, room_id, user_id, timestamp, performance, effort "
        "FROM activity "
        "ORDER BY activity_id"
    )

    with open(path / "activity.csv", "w", newline="") as fd:
        writer = csv.writer(fd, dialect="excel")
        # Header row.
        writer.writerow(
            [
                "activity_id",
                "room_id",
                "user_id",
                "timestamp",
                "performance",
                "effort",
            ]
        )
        writer.writerows(activities)


def dump_room_members(db, path):
    members = db.execute(
        "SELECT member_id, room_id, user_id, joined, departed "
        "FROM room_member "
        "ORDER BY member_id"
    )

    with open(path / "room_member.csv", "w", newline="") as fd:
        writer = csv.writer(fd, dialect="excel")
        # Header row.
        writer.writerow(
            [
                "member_id",
                "room_id",
                "user_id",
                "joined",
                "departed",
            ]
        )
        writer.writerows(members)


def dump_buddies(db, path):
    buddies = db.execute(
        "SELECT buddy_id, room_id, inviter_id, invitee_id, sent, accepted "
        "FROM buddy "
        "ORDER BY buddy_id"
    )

    with open(path / "buddy.csv", "w", newline="") as fd:
        writer = csv.writer(fd, dialect="excel")
        # Header row.
        writer.writerow(
            [
                "buddy_id",
                "room_id",
                "inviter_id",
                "invitee_id",
                "sent",
                "accepted",
            ]
        )
        writer.writerows(buddies)


def main(path_to_database, path):
    db = sqlite3.connect(path_to_database)
    db.row_factory = sqlite3.Row

    dump_users(db, path)
    dump_rooms(db, path)
    dump_activities(db, path)
    dump_room_members(db, path)
    dump_buddies(db, path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export project data to CSV files.")

    parser.add_argument(
        "db",
        help="Name or path to the SQLite database file.",
        metavar="DB",
    )

    parser.add_argument(
        "path",
        help="Location to save CSV files to.",
        metavar="PATH",
    )

    args = parser.parse_args()
    path = pathlib.Path(args.path).with_suffix(".sqlite")

    if not path.is_dir():
        sys.stderr.write(f"Path '{path}' does not exist.\n")
        sys.exit(1)

    main(args.db, path)
