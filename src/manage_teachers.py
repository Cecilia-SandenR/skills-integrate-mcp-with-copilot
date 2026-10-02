import getpass
import json
import sys

if __package__:
    from .auth import (
        TEACHER_CREDENTIALS_FILE,
        create_password_record,
        load_teacher_credentials,
        normalize_username,
    )
else:
    from auth import (
        TEACHER_CREDENTIALS_FILE,
        create_password_record,
        load_teacher_credentials,
        normalize_username,
    )


def main():
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        print("Usage: python src/manage_teachers.py <username>", file=sys.stderr)
        return 2

    username = normalize_username(sys.argv[1])
    password = getpass.getpass("Teacher password (at least 12 characters): ")
    if len(password) < 12:
        print("Password must contain at least 12 characters.", file=sys.stderr)
        return 2

    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 2

    try:
        teachers = load_teacher_credentials()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    teachers[username] = create_password_record(password)
    TEACHER_CREDENTIALS_FILE.write_text(
        json.dumps({"teachers": teachers}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Teacher account saved for {username}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())