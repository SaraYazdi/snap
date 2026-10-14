"""Idempotent seed: SNAP Records, SNAP, sample users & content."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app

from app.extensions import db
from app.models import Band, ContentItem, Label, Membership, User


SAMPLE_USERS = [
    ("admin@snap.records", "Label Admin", "professional", "administrator", None, "admin123"),
    ("member@snap.band", "Alex SNAP", "professional", "band_member", "snap", "member123"),
    ("crew@snap.band", "Tour Manager", "professional", "crew", "snap", "crew123"),
    ("press@example.com", "Press Partner", "professional", "press", "snap", "press123"),
    ("fanclub@example.com", "Fan Club Member", "fan", "fan_club", "snap", "fanclub123"),
    ("fan@example.com", "Registered Fan", "fan", "registered", "snap", "fan123"),
]

# Old Delivery-01 sample titles → remove so dashboard isn't confusing
LEGACY_SAMPLE_TITLES = [
    "SNAP — Demo reel",
    "Tour EU 2026 rider",
    "SNAP — Album X master",
    "Fan BTS clip #1",
    "Public single artwork",
    "Sync license draft",
]


def _write_sample_file(folder: Path, name: str, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if not path.exists():
        path.write_text(text)
    return path


def seed():
    label = Label.query.filter_by(slug="snap-records").first()
    if not label:
        label = Label(name="SNAP Records", slug="snap-records")
        db.session.add(label)
        db.session.flush()

    band = Band.query.filter_by(slug="snap").first()
    if not band:
        band = Band(
            label_id=label.id,
            name="SNAP",
            slug="snap",
            bio="SNAP Records roster act.",
        )
        db.session.add(band)
        db.session.flush()

    users_by_email = {}
    for email, name, acct, role, band_slug, password in SAMPLE_USERS:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                label_id=label.id,
                email=email,
                display_name=name,
                account_type=acct,
                status="active",
                email_verified=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            bid = None if role == "administrator" else band.id
            db.session.add(Membership(user_id=user.id, band_id=bid, role=role))
        users_by_email[email] = user

    db.session.commit()

    # Soft-delete confusing legacy seed rows (keeps FK/history simple)
    for title in LEGACY_SAMPLE_TITLES:
        for old in ContentItem.query.filter_by(title=title, band_id=band.id, is_deleted=False).all():
            old.is_deleted = True
    db.session.commit()

    member = users_by_email["member@snap.band"]
    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    now = datetime.now(timezone.utc)

    samples = [
        {
            "title": "SNAP — Midnight (single)",
            "category": "new_music",
            "audience_level": "public",
            "filename": "midnight-single.txt",
            "body": "Public single — stream / download placeholder.\n",
            "is_public": True,
        },
        {
            "title": "SNAP — Album X (press master)",
            "category": "new_music",
            "audience_level": "press",
            "filename": "album-x-press.txt",
            "body": "Press master placeholder — embargoed until window opens.\n",
            "available_from_press": now + timedelta(days=7),
            "is_public": False,
        },
        {
            "title": "SNAP — Studio demo pack",
            "category": "new_music",
            "audience_level": "band",
            "filename": "studio-demos.txt",
            "body": "Internal demos for the band only.\n",
            "is_public": False,
        },
        {
            "title": "SNAP logo tee",
            "category": "merch",
            "audience_level": "public",
            "filename": "logo-tee.txt",
            "body": "Merch drop — logo tee details placeholder.\n",
            "is_public": True,
        },
        {
            "title": "Tour hoodie (crew kit)",
            "category": "merch",
            "audience_level": "crew",
            "filename": "tour-hoodie.txt",
            "body": "Crew merch / kit notes.\n",
            "is_public": False,
        },
        {
            "title": "About SNAP",
            "category": "band_pages",
            "audience_level": "public",
            "filename": "about-snap.txt",
            "body": "Band bio and links placeholder.\n",
            "is_public": True,
        },
        {
            "title": "EU 2026 tour rider",
            "category": "band_pages",
            "audience_level": "crew",
            "filename": "tour-rider.txt",
            "body": "Technical / hospitality rider (placeholder).\n",
            "is_public": False,
        },
        {
            "title": "Sync license draft",
            "category": "band_pages",
            "audience_level": "restricted",
            "filename": "sync-license.txt",
            "body": "Restricted contract draft.\n",
            "is_public": False,
        },
        {
            "title": "Tour dates announced",
            "category": "news",
            "audience_level": "public",
            "filename": "tour-dates.txt",
            "body": "Public news: tour dates announcement.\n",
            "is_public": True,
        },
        {
            "title": "Fan club BTS drop",
            "category": "news",
            "audience_level": "fan_club",
            "filename": "bts-drop.txt",
            "body": "Fan-club early BTS / news placeholder.\n",
            "available_from_fans": now - timedelta(days=1),
            "is_public": False,
        },
    ]

    for s in samples:
        existing = ContentItem.query.filter_by(title=s["title"], band_id=band.id).first()
        if existing and not existing.is_deleted:
            continue
        if existing and existing.is_deleted:
            # revive + retarget to new section/audience
            item = existing
            item.is_deleted = False
            item.description = s.get("body", "").strip()
            item.category = s["category"]
            item.audience_level = s["audience_level"]
            item.is_public = s.get("is_public", False)
            item.available_from_press = s.get("available_from_press")
            item.available_from_fans = s.get("available_from_fans")
            item.uploaded_by_user_id = member.id
        else:
            item = ContentItem(
                band_id=band.id,
                uploaded_by_user_id=member.id,
                title=s["title"],
                description=s.get("body", "").strip(),
                category=s["category"],
                audience_level=s["audience_level"],
                is_public=s.get("is_public", False),
                available_from_press=s.get("available_from_press"),
                available_from_fans=s.get("available_from_fans"),
                storage_path="pending",
                mime_type="text/plain",
                original_filename=s["filename"],
            )
            db.session.add(item)
            db.session.flush()
        path = _write_sample_file(upload_root / item.id, s["filename"], s["body"])
        item.storage_path = str(path)
        item.size_bytes = path.stat().st_size
        item.original_filename = s["filename"]
        item.mime_type = "text/plain"
    db.session.commit()
    print("Seed complete. Sample logins: admin@snap.records / admin123, member@snap.band / member123, …")


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        seed()
