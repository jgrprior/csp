"""Initialise the database with generated users, rooms and activities."""

import argparse
import collections
import datetime
import hashlib
import itertools
import pathlib
import random
import secrets
import string
import sqlite3
import sys

from dataclasses import dataclass
from dataclasses import field

from typing import NamedTuple
from typing import Optional

# A list of colours that are used to generate usernames.
COLOURS = [
    "Aquamarine",
    "Chocolate",
    "Crimson",
    "Coral",
    "Magenta",
    "Olive",
    "Orchid",
    "Salmon",
    "Fire",
    "Ghost",
    "Golden",
    "Honey",
    "Lavender",
    "Lime",
    "Spring",
    "Rose",
    "Violet",
    "Peach",
    "Turquoise",
]

# A list of animals that are used to generate usernames.
ANIMALS = [
    "Aardvark",
    "Albatross",
    "Goat",
    "Alsatian",
    "Leopard",
    "Angelfish",
    "Antelope",
    "Fox",
    "Armadillo",
    "Alpaca",
    "Baboon",
    "Bandicoot",
    "Badger",
    "Barracuda",
    "Bison",
    "Camel",
    "Chinchilla",
    "Cockatoo",
    "Dingo",
    "Shrew",
    "Eskipoo",
    "Ermine",
]

# Characters used for generating password hashing salt.
SALT_CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits

# Default number of iterations used by the password hashing algorithm.
HASH_ITERATIONS = 10  # 260000

# Choose a random mean (average) performance per user from this list.
PERFORMANCE_MEANS = [5000, 7500, 10000, 15000]

# Choose a random standard deviation per user from this list.
PERFORMANCE_SD = [1000, 1250, 1500]

# Choose a random performance trend per user/week from this list.
PERFORMANCE_TRENDS = [0.8, 1, 1.2]

# Skew average performance on gender.
GENDER_PERFORMANCE = {
    "male": 0.9,
    "female": 1.2,
    "neutral": 1,
}

# Skew average performance on age band.
AGEBAND_PERFORMANCE = {
    1: 1.3,
    2: 1.1,
    3: 0.8,
    4: 1.1,
    5: 1.2,
    6: 1.0,
    7: 0.9,
    8: 0.8,
    9: 0.7,
    10: 0.6,
    11: 0.6,
}


class User(NamedTuple):
    """A generated user that does not yet have a user ID."""

    email: str
    nickname: str
    hashed_password: str
    gender: Optional[str] = None
    dob: Optional[datetime.date] = None


class Room(NamedTuple):
    """A generated room that does not yet have a room ID."""

    user_id: int
    name: str
    description: str
    units: str
    access: str
    created: datetime.datetime


class RoomMember(NamedTuple):
    """A generated room member that does not yet have a member ID."""

    room_id: int
    user_id: int


class Activity(NamedTuple):
    """A generated activity that does not yet have an activity ID."""

    room_id: int
    user_id: int
    timestamp: datetime.datetime
    performance: int
    effort: int


class Buddy(NamedTuple):
    """A generated buddy relationship between two users."""

    room_id: int
    inviter_id: int
    invitee_id: int


def init_db(db):
    """Initialise the database. If the database already exists, data will be
    deleted before creating new tables."""
    with open("schema.sql") as fd:
        db.executescript(fd.read())


def insert_users(db, users):
    """Insert users into the database."""
    with db:
        db.executemany(
            "INSERT INTO user "
            "(email, nickname, hashed_password, gender, dob) "
            "VALUES (?, ?, ?, ?, ?)",
            users,
        )


def insert_rooms(db, rooms):
    """Insert rooms into the database."""
    with db:
        db.executemany(
            "INSERT INTO room "
            "(owner_id, name, description, units, access, created) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rooms,
        )


def insert_room_members(db, members):
    """Insert room members into the database."""
    with db:
        db.executemany(
            "INSERT INTO room_member (room_id, user_id) VALUES (?, ?)",
            members,
        )


def insert_activities(db, activities):
    """Insert activities into the database."""
    with db:
        db.executemany(
            "INSERT INTO activity "
            "(room_id, user_id, timestamp, performance, effort) "
            "VALUES (?, ?, ?, ?, ?)",
            activities,
        )


def insert_buddies(db, buddies):
    """Insert buddies into the database."""
    with db:
        db.executemany(
            "INSERT INTO buddy "
            "(room_id, inviter_id, invitee_id) "
            "VALUES (?, ?, ?)",
            buddies,
        )


def hash_password(password, salt_length=16, iterations=HASH_ITERATIONS):
    """Securely hash the given password."""
    salt = "".join(secrets.choice(SALT_CHARS) for _ in range(salt_length))
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${dk.hex()}"


def generate_users(hash_iterations=HASH_ITERATIONS):
    """Generate users with arbitrary names and email addresses."""
    animal_colour_product = list(itertools.product(set(COLOURS), set(ANIMALS)))
    random.shuffle(animal_colour_product)

    genders = random.choices(
        ["male", "female", "neutral"],
        weights=[100, 100, 2],
        k=len(animal_colour_product),
    )

    ages = []
    for _ in range(len(animal_colour_product)):
        age = int(random.gauss(35, 20))
        while age < 3 or age > 110:
            age = int(random.gauss(35, 20))
        ages.append(age)

    users = []

    for animal, colour in animal_colour_product:
        nickname = animal + colour
        email = nickname + "@example.com"

        # XXX: Never use a user's username as a default password, or use any
        # default password whatsoever.
        users.append(
            User(
                email,
                nickname,
                hash_password(nickname, iterations=hash_iterations),
                gender=genders.pop(),
                dob=datetime.date.today() - datetime.timedelta(days=ages.pop() * 365),
            )
        )

    return users


def generate_rooms(db):
    """Generate some activity rooms owned by randomly selected users."""
    users = db.execute("SELECT user_id FROM user ORDER BY RANDOM()")

    rooms = [
        Room(
            user_id=next(users)["user_id"],
            name="Fleet Steppers",
            description="Fleet town daily step counters.",
            units="steps/day",
            access="public",
            created=random_timestamp(
                datetime.datetime.now() - datetime.timedelta(days=90)
            ),
        ),
        Room(
            user_id=next(users)["user_id"],
            name="Hart Steppers",
            description="Hart district daily step counters.",
            units="steps/day",
            access="public",
            created=random_timestamp(
                datetime.datetime.now() - datetime.timedelta(days=100)
            ),
        ),
        Room(
            user_id=next(users)["user_id"],
            name="Holly's Steppers",
            description="Daily steps for Holly and friends.",
            units="steps/day",
            access="private",
            created=random_timestamp(
                datetime.datetime.now() - datetime.timedelta(days=85)
            ),
        ),
    ]

    return rooms


def generate_room_members(db):
    """Generate some records for the `room_member` table, indicating that a
    user is a member of a room."""
    rooms = db.execute("SELECT room_id FROM room")
    users = db.execute("SELECT user_id FROM user")
    user_ids = [user["user_id"] for user in users]

    members = []

    for room in rooms:
        room_users = random.sample(user_ids, len(user_ids) // 3)
        for user_id in room_users:
            members.append(RoomMember(room["room_id"], user_id))

    return members


def random_timestamp(dt):
    """Return a random datetime on the same day as `dt`. `dt` is assumed
    to be a ``datetime.datetime``."""
    start = dt.replace(hour=23, minute=59, second=59)
    end = dt.replace(hour=0, minute=0, second=0)
    max_timestamp = int(start.timestamp())
    min_timestamp = int(end.timestamp())

    timestamp = random.randrange(min_timestamp, max_timestamp)
    return datetime.datetime.fromtimestamp(timestamp)


def age_band_from_dob(dob):
    """Return the ageband given a date of birth."""
    today = datetime.date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    if age <= 15:
        band = 1
    elif age <= 25:
        band = 2
    elif age <= 35:
        band = 3
    elif age <= 45:
        band = 4
    elif age <= 55:
        band = 5
    elif age <= 65:
        band = 6
    elif age <= 75:
        band = 7
    elif age <= 85:
        band = 8
    elif age <= 95:
        band = 9
    elif age <= 105:
        band = 10
    else:
        band = 11

    return band


@dataclass
class UserPerformance:
    user_id: int
    gender: str
    dob: datetime.datetime
    age_band: int = field(init=False)
    mu: int = field(init=False)
    sigma: int = field(init=False)
    week_number: int = field(init=False, default=-1)
    activities: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.age_band = age_band_from_dob(self.dob)
        self.mu = (
            random.choice(PERFORMANCE_MEANS) * GENDER_PERFORMANCE[self.gender]
        ) * AGEBAND_PERFORMANCE[self.age_band]
        self.sigma = random.choice(PERFORMANCE_SD)

    def activity(self, room_id, timestamp: datetime.datetime) -> Activity:
        """Return a new activity for this user for the given timestamp."""
        date = timestamp.date()

        if date in self.activities:
            # We've already generated an activity for this user on this day,
            # but in a different room. Copy the activity to the new room.
            return self.activities[date]._replace(room_id=room_id)

        # Trend up or down when we start a new week.
        week_number = timestamp.isocalendar()[1]

        if self.week_number != week_number:
            self.week_number = week_number
            self.mu *= random.choice(PERFORMANCE_TRENDS)

        performance = int(random.gauss(self.mu, self.sigma))
        effort = random.randint(1, 10)

        return Activity(
            room_id=room_id,
            user_id=self.user_id,
            timestamp=timestamp,
            performance=performance,
            effort=effort,
        )


def generate_activities(db):
    """Generate some activities representing users that have completed the
    activity defined in a room."""
    members = db.execute(
        "SELECT room.room_id, room.created AS 'room_timestamp [timestamp]', "
        "user.user_id, user.gender, user.dob AS 'dob [date]' "
        "FROM room_member "
        "JOIN room ON (room.room_id = room_member.room_id) "
        "JOIN user ON (user.user_id = room_member.user_id) "
        "WHERE departed is NULL"
    )

    # XXX: Assumes all activities are step counts for now.
    activities = []

    # We're trying to simulate performance trends for each user. We'll keep
    # track of a user's performance with a map of user_ids to UserPerformance
    # objects.
    users_performance = {}

    # XXX: There are no gaps. We're assuming all users have recorded their
    # performance every day since the creation of the room. Even if they
    # didn't join the room until later.
    now = datetime.datetime.now()

    for room_id, room_timestamp, user_id, gender, dob in members:
        if user_id not in users_performance:
            # First time we're seeing this user. Create a new UserPerformance
            # object with a random (skewed) performance mean and standard
            # deviation.
            users_performance[user_id] = UserPerformance(user_id, gender, dob)

        user = users_performance[user_id]

        # Generate an activity for the current room and user for each day
        # since the room was created.
        max_delta = now - room_timestamp
        for day in range(max_delta.days):
            timestamp = random_timestamp(now - datetime.timedelta(days=day))
            activities.append(user.activity(room_id, timestamp))

    return activities


def pop_users(ids, n):
    invitees = []
    for _ in range(n):
        try:
            invitees.append(ids.pop())
        except IndexError:
            break

    return invitees


def generate_buddies(db):
    """Generate some buddies representing users that have invited other users
    to join a room."""
    members = db.execute(
        "SELECT room.room_id, room.owner_id, user_id "
        "FROM room_member JOIN room "
        "ON (room.room_id = room_member.room_id) "
        "WHERE departed IS NULL "
        "ORDER BY room_member.room_id"
    )

    # Rather than making multiple SQL queries, at least one for each room,
    # we're grabbing them all in one go, then grouping them into rooms here.
    room_ids = []
    room_members = []

    for key, group in itertools.groupby(members, key=lambda r: r["room_id"]):
        room_ids.append(key)
        room_members.append(list(group))

    buddies = []

    # We're trying to simulate a directed graph. The `buddy` table effectively
    # being an adjacency list but with the added dimension of a room.
    for room_id, room in zip(room_ids, room_members):
        owner = room[0]["owner_id"]
        queue = collections.deque([[owner]])

        user_ids = [member["user_id"] for member in room]
        if owner in user_ids:
            user_ids.remove(owner)

        random.shuffle(user_ids)

        while queue:
            for inviter in queue.popleft():
                invitees = pop_users(user_ids, random.randrange(2, 5))
                for invitee in invitees:
                    buddies.append(Buddy(room_id, inviter, invitee))

                if invitees:
                    queue.append(invitees)

    return buddies


def main(path_to_database, init_only=False, hash_iterations=HASH_ITERATIONS):
    db = sqlite3.connect(
        path_to_database,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    db.row_factory = sqlite3.Row

    init_db(db)

    if not init_only:
        users = generate_users(hash_iterations=hash_iterations)
        insert_users(db, users)

        rooms = generate_rooms(db)
        insert_rooms(db, rooms)

        room_members = generate_room_members(db)
        insert_room_members(db, room_members)

        activities = generate_activities(db)
        insert_activities(db, activities)

        buddies = generate_buddies(db)
        insert_buddies(db, buddies)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Project database initialisation and mock data generation."
    )

    parser.add_argument(
        "path",
        help="Name or path to the SQLite database file.",
        metavar="PATH",
    )

    parser.add_argument(
        "--hash-iterations",
        type=int,
        default=HASH_ITERATIONS,
        help=(
            "The number of iterations used by the password "
            f"hahsing algorithm. Defaults to {HASH_ITERATIONS}."
        ),
    )

    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Initialise the database without generating mock data.",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Don't wait for confirmation before overriting an existing database.",
    )

    args = parser.parse_args()
    path = pathlib.Path(args.path).with_suffix(".sqlite")

    if not args.force and path.exists():
        overwrite = input(
            f"The database at '{path}' already exists. Overwrite (y/[n])? "
        )

        if overwrite.lower() not in ("y", "yes"):
            sys.exit(1)

    main(
        str(path),
        init_only=args.init_only,
        hash_iterations=args.hash_iterations,
    )
