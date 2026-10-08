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

    member = users_by_email["member@snap.band"]
    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    now = datetime.now(timezone.utc)

    samples = [
        {
            "title": "SNAP — Demo reel",
            "category": "demo",
            "audience_level": "band",
            "filename": "demo-reel.txt",
            "body": "Demo reel placeholder for SNAP.\n",
            "is_public": False,
        },
        {
            "title": "Tour EU 2026 rider",
            "category": "tour_rider",
            "audience_level": "crew",
            "filename": "tour-rider.txt",
            "body": "Technical / hospitality rider (placeholder).\n",
            "is_public": False,
        },
        {
            "title": "SNAP — Album X master",
            "category": "master",
            "audience_level": "press",
            "filename": "album-x-master.txt",
            "body": "Master placeholder — embargoed for press.\n",
            "available_from_press": now + timedelta(days=7),
            "is_public": False,
        },
        {
            "title": "Fan BTS clip #1",
            "category": "video",
            "audience_level": "fan_club",
            "filename": "bts-clip.txt",
            "body": "Behind-the-scenes clip placeholder.\n",
            "available_from_fans": now - timedelta(days=1),
            "is_public": False,
        },
        {
            "title": "Public single artwork",
            "category": "photo",
            "audience_level": "public",
            "filename": "single-artwork.txt",
            "body": "Public artwork placeholder.\n",
            "is_public": True,
        },
        {
            "title": "Sync license draft",
            "category": "contract",
            "audience_level": "restricted",
            "filename": "sync-license.txt",
            "body": "Restricted contract draft.\n",
            "is_public": False,
        },
    ]

    for s in samples:
        if ContentItem.query.filter_by(title=s["title"], band_id=band.id).first():
            continue
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
    db.session.commit()
    print("Seed complete. Sample logins: admin@snap.records / admin123, member@snap.band / member123, …")


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        seed()
