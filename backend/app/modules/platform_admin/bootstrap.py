import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.memberships import models as membership_models  # noqa: F401
from app.modules.platform_admin.models import PlatformAdminRole
from app.modules.stores import models as store_models  # noqa: F401
from app.modules.users.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant initial platform administrator access")
    parser.add_argument("email", help="Email address of an existing Dukkan account")
    args = parser.parse_args()
    email = args.email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            parser.error("No account exists for that email; register it before bootstrapping")
        grant = db.get(PlatformAdminRole, user.id)
        if grant is None:
            db.add(PlatformAdminRole(user_id=user.id, granted_by_user_id=user.id))
        else:
            grant.is_active = True
            grant.granted_by_user_id = user.id
        db.commit()
    print(f"Platform administrator access granted to {email}")


if __name__ == "__main__":
    main()
