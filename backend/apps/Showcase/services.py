# backend/apps/Showcase/services.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Iterable, Mapping, Sequence, List, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    Media,
    Project,
    ProjectMember,
    ProjectTag,
    ProjectTagMap,
    ProjectMedia,
    Competition,
    CompetitionMedia,
    CompetitionAchievement,
    CompetitionAchievementProject,
    CompetitionAchievementUser,
)

User = get_user_model()


# ---------- util helpers (pure Python) ----------

def _now() -> datetime:
    return timezone.now()


def _rel_time(dt: datetime | str | None) -> str:
    if not dt:
        return ""

    if isinstance(dt, str):
        # keep old behaviour for string timestamps if needed
        try:
            dt_parsed = datetime.strptime(dt[:19], "%Y-%m-%d %H:%M:%S")
            dt = timezone.make_aware(dt_parsed, timezone.get_current_timezone())
        except Exception:
            return ""
    elif not timezone.is_aware(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())

    now = timezone.now()
    s = int((now - dt).total_seconds())
    if s < 0:
        s = 0

    if s < 60:
        return f"{s}s ago"
    m = s // 60
    if m < 60:
        return f"{m}m ago"
    h = m // 60
    if h < 24:
        return f"{h}h ago"
    d = h // 24
    if d < 30:
        return f"{d}d ago"
    mo = d // 30
    if mo < 12:
        return f"{mo}mo ago"
    y = mo // 12
    return f"{y}y ago"


def _blurb(text: str | None, limit: int = 160) -> str:
    t = (text or "").strip().replace("\n", " ")
    return t if len(t) <= limit else t[: limit - 1].rstrip() + "…"


def _basename(p: str | None) -> str | None:
    if not p:
        return None
    return os.path.basename(p)


# ---------- media helpers ----------

def list_project_media(project_id: int) -> list[dict[str, Any]]:
    links = (
        ProjectMedia.objects
        .select_related("media")
        .filter(project_id=project_id)
        .order_by("-is_primary", "sort_order", "media_id")
    )

    out: list[dict[str, Any]] = []
    for link in links:
        m = link.media
        out.append(
            {
                "media_id": m.id,
                "media_type": m.media_type,
                "path_or_url": m.path_or_url,
                "mime_type": m.mime_type,
                "size_bytes": m.size_bytes,
                "checksum": m.checksum,
                "caption": m.caption,
                "alt_text": m.alt_text,
                "uploaded_by_id": m.uploaded_by_id,
                "created_at": m.created_at,
                "sort_order": link.sort_order,
                "is_primary": link.is_primary,
            }
        )
    return out


def list_competition_media(competition_id: int) -> list[dict[str, Any]]:
    links = (
        CompetitionMedia.objects
        .select_related("media")
        .filter(competition_id=competition_id)
        .order_by("-is_primary", "sort_order", "media_id")
    )

    out: list[dict[str, Any]] = []
    for link in links:
        m = link.media
        out.append(
            {
                "media_id": m.id,
                "media_type": m.media_type,
                "path_or_url": m.path_or_url,
                "mime_type": m.mime_type,
                "size_bytes": m.size_bytes,
                "checksum": m.checksum,
                "caption": m.caption,
                "alt_text": m.alt_text,
                "uploaded_by_id": m.uploaded_by_id,
                "created_at": m.created_at,
                "sort_order": link.sort_order,
                "is_primary": link.is_primary,
            }
        )
    return out


def project_primary_image_path(project_id: int) -> str | None:
    link = (
        ProjectMedia.objects
        .select_related("media")
        .filter(project_id=project_id, is_primary=True)
        .order_by("sort_order", "media_id")
        .first()
    )
    return link.media.path_or_url if link and link.media else None


def attach_media_to_project(
    project_id: int,
    media_id: int,
    is_primary: bool = False,
    sort_order: int | None = None,
) -> None:
    ProjectMedia.objects.get_or_create(
        project_id=project_id,
        media_id=media_id,
        defaults={"is_primary": bool(is_primary), "sort_order": sort_order},
    )


def attach_media_to_competition(
    competition_id: int,
    media_id: int,
    is_primary: bool = False,
    sort_order: int | None = None,
) -> None:
    CompetitionMedia.objects.get_or_create(
        competition_id=competition_id,
        media_id=media_id,
        defaults={"is_primary": bool(is_primary), "sort_order": sort_order},
    )


def remove_project_media_link(project_id: int, media_id: int) -> None:
    ProjectMedia.objects.filter(project_id=project_id, media_id=media_id).delete()


def remove_competition_media_link(competition_id: int, media_id: int) -> None:
    CompetitionMedia.objects.filter(
        competition_id=competition_id,
        media_id=media_id,
    ).delete()


def delete_media(media_id: int) -> None:
    # cascades on ProjectMedia / CompetitionMedia will clean up links
    Media.objects.filter(pk=media_id).delete()


# ---------- showcase card feeds ----------

def _project_card_dict(p: Project) -> dict[str, Any]:
    media = list_project_media(p.id)
    image_paths = [m["path_or_url"] for m in media]
    primary = image_paths[0] if image_paths else None
    tags = list(p.tags.values_list("name", flat=True))

    posted_src = p.publish_at or p.created_at

    return {
        "id": p.id,
        "title": p.title or "",
        "blurb": _blurb(p.description),
        "long_text": (p.description or "").strip(),
        "image": _basename(primary),
        "images": [_basename(x) for x in image_paths],
        "posted_ago": _rel_time(posted_src),
        "status": p.status,
        "author_display": p.author_display,
        "category": p.category,
        "context": p.context,
        "images_count": len(image_paths),
        "tags": tags,
        "external_url": p.external_url,
    }


def _competition_card_dict(c: Competition) -> dict[str, Any]:
    media = list_competition_media(c.id)
    image_paths = [m["path_or_url"] for m in media]
    primary = image_paths[0] if image_paths else None
    posted_src = c.publish_at or c.created_at

    return {
        "id": c.id,
        "title": c.name or "",
        "blurb": _blurb(c.description),
        "long_text": (c.description or "").strip(),
        "image": _basename(primary),
        "images": [_basename(x) for x in image_paths],
        "posted_ago": _rel_time(posted_src),
        "status": c.status,
        "author_display": None,
        "category": c.event_type,
        "context": None,
        "images_count": len(image_paths),
        "tags": [],
        "external_url": c.external_url,
    }


def list_showcase_cards(
    kind: str = "project",
    q: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    assert kind in ("project", "competition")

    if kind == "project":
        qs = Project.objects.all()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(author_display__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)

        qs = qs.annotate(order_dt=Coalesce("publish_at", "created_at")).order_by(
            "-order_dt",
            "-id",
        )
        qs = qs[offset : offset + limit]

        return [_project_card_dict(p) for p in qs]

    # competitions
    qs = Competition.objects.all()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(organizer__icontains=q)
            | Q(description__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    qs = qs.annotate(order_dt=Coalesce("publish_at", "created_at")).order_by(
        "-order_dt",
        "-id",
    )
    qs = qs[offset : offset + limit]

    return [_competition_card_dict(c) for c in qs]


# ---------- richer project helpers ----------

def list_projects(
    status: str | None = None,
    is_public: int | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "-created_at",
) -> list[dict[str, Any]]:
    qs = Project.objects.all()
    if status:
        qs = qs.filter(status=status)
    if is_public is not None:
        qs = qs.filter(is_public=bool(is_public))
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(author_display__icontains=q)
        )

    qs = qs.order_by(order_by)
    qs = qs[offset : offset + limit]

    out: list[dict[str, Any]] = []
    for p in qs:
        out.append(
            {
                "projects_id": p.id,
                "title": p.title,
                "description": p.description,
                "submitted_by_id": p.submitted_by_id,
                "course_id": p.course_id,
                "organization_id": p.organization_id,
                "status": p.status,
                "is_public": p.is_public,
                "publish_at": p.publish_at,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "category": p.category,
                "context": p.context,
                "external_url": p.external_url,
                "author_display": p.author_display,
            }
        )
    return out


def get_project(project_id: int) -> dict[str, Any] | None:
    try:
        p = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return None

    proj = {
        "projects_id": p.id,
        "title": p.title,
        "description": p.description,
        "submitted_by_id": p.submitted_by_id,
        "course_id": p.course_id,
        "organization_id": p.organization_id,
        "status": p.status,
        "is_public": p.is_public,
        "publish_at": p.publish_at,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "category": p.category,
        "context": p.context,
        "external_url": p.external_url,
        "author_display": p.author_display,
    }
    proj["media"] = list_project_media(project_id)
    proj["tags"] = list_project_tags(project_id)
    members = (
        ProjectMember.objects.select_related("user")
        .filter(project_id=project_id)
        .order_by("id")
    )
    proj["members"] = [
        {
            "project_members_id": m.id,
            "project_id": m.project_id,
            "user_id": m.user_id,
            "role": m.role,
            "contributions": m.contributions,
            "username": getattr(m.user, "username", None),
            "email": getattr(m.user, "email", None),
        }
        for m in members
    ]
    proj["posted_ago"] = _rel_time(p.publish_at or p.created_at)
    return proj


def create_project(data: Mapping[str, Any]) -> int:
    fields = {
        "title",
        "description",
        "submitted_by",
        "course_id",
        "organization_id",
        "status",
        "is_public",
        "publish_at",
        "category",
        "context",
        "external_url",
        "author_display",
    }
    payload: dict[str, Any] = {}
    for k in fields:
        if k in data:
            payload[k] = data[k]

    proj = Project.objects.create(**payload)
    return proj.id


def update_project(project_id: int, data: Mapping[str, Any]) -> None:
    if not data:
        return
    allowed = {
        "title",
        "description",
        "submitted_by",
        "course_id",
        "organization_id",
        "status",
        "is_public",
        "publish_at",
        "category",
        "context",
        "external_url",
        "author_display",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    if not payload:
        return
    Project.objects.filter(pk=project_id).update(**payload)


def set_project_status(project_id: int, status: str) -> None:
    Project.objects.filter(pk=project_id).update(
        status=status,
        updated_at=_now(),
    )


def delete_project(project_id: int) -> None:
    Project.objects.filter(pk=project_id).delete()


# ---------- tags ----------

def ensure_tag(name: str) -> int:
    tag, _ = ProjectTag.objects.get_or_create(name=name)
    return tag.id


def set_project_tags(project_id: int, tag_names: Sequence[str]) -> None:
    tag_ids = [ensure_tag(t) for t in tag_names]

    with transaction.atomic():
        ProjectTagMap.objects.filter(project_id=project_id).delete()
        for tid in tag_ids:
            ProjectTagMap.objects.get_or_create(project_id=project_id, tag_id=tid)


def list_project_tags(project_id: int) -> list[dict[str, Any]]:
    tags = (
        ProjectTag.objects.filter(project__id=project_id)
        .distinct()
        .order_by("name")
    )
    return [{"tag_id": t.id, "name": t.name} for t in tags]


# ---------- members ----------

def add_member(
    project_id: int,
    user_id: int,
    role: str | None,
    contributions: str | None,
) -> int:
    m = ProjectMember.objects.create(
        project_id=project_id,
        user_id=user_id,
        role=role,
        contributions=contributions,
    )
    return m.id


def remove_member(project_members_id: int) -> None:
    ProjectMember.objects.filter(pk=project_members_id).delete()


# ---------- competitions / achievements ----------

def list_competitions(
    q: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    qs = Competition.objects.all()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(organizer__icontains=q)
            | Q(description__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    qs = qs.order_by("-created_at")
    qs = qs[offset : offset + limit]

    out: list[dict[str, Any]] = []
    for c in qs:
        d = {
            "competition_id": c.id,
            "name": c.name,
            "organizer": c.organizer,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "related_event_id": c.related_event_id,
            "description": c.description,
            "event_type": c.event_type,
            "external_url": c.external_url,
            "submitted_by_id": c.submitted_by_id,
            "status": c.status,
            "is_public": c.is_public,
            "publish_at": c.publish_at,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        d["posted_ago"] = _rel_time(c.publish_at or c.created_at)
        out.append(d)
    return out


def get_competition(competition_id: int) -> dict[str, Any] | None:
    try:
        c = Competition.objects.get(pk=competition_id)
    except Competition.DoesNotExist:
        return None

    row = {
        "competition_id": c.id,
        "name": c.name,
        "organizer": c.organizer,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "related_event_id": c.related_event_id,
        "description": c.description,
        "event_type": c.event_type,
        "external_url": c.external_url,
        "submitted_by_id": c.submitted_by_id,
        "status": c.status,
        "is_public": c.is_public,
        "publish_at": c.publish_at,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }
    row["media"] = list_competition_media(competition_id)
    row["posted_ago"] = _rel_time(c.publish_at or c.created_at)
    return row


def create_competition(data: Mapping[str, Any]) -> int:
    allowed = {
        "name",
        "organizer",
        "start_date",
        "end_date",
        "related_event_id",
        "description",
        "event_type",
        "external_url",
        "submitted_by",
        "status",
        "is_public",
        "publish_at",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    c = Competition.objects.create(**payload)
    return c.id


def update_competition(competition_id: int, data: Mapping[str, Any]) -> None:
    allowed = {
        "name",
        "organizer",
        "start_date",
        "end_date",
        "related_event_id",
        "description",
        "event_type",
        "external_url",
        "submitted_by",
        "status",
        "is_public",
        "publish_at",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    if not payload:
        return
    Competition.objects.filter(pk=competition_id).update(**payload)


def set_competition_status(competition_id: int, status: str) -> None:
    Competition.objects.filter(pk=competition_id).update(
        status=status,
        updated_at=_now(),
    )


def delete_competition(competition_id: int) -> None:
    Competition.objects.filter(pk=competition_id).delete()


def list_showcase_categories() -> list[str]:
    cats: set[str] = set()
    for c in (
        Project.objects.exclude(category__isnull=True)
        .exclude(category__exact="")
        .values_list("category", flat=True)
        .distinct()
    ):
        cats.add(c)
    for c in (
        Competition.objects.exclude(event_type__isnull=True)
        .exclude(event_type__exact="")
        .values_list("event_type", flat=True)
        .distinct()
    ):
        cats.add(c)
    return sorted(cats)


def list_achievements(competition_id: int | None = None) -> list[dict[str, Any]]:
    qs = CompetitionAchievement.objects.select_related("competition")
    if competition_id:
        qs = qs.filter(competition_id=competition_id)
    qs = qs.order_by("-awarded_at", "-id")

    out: list[dict[str, Any]] = []
    for a in qs:
        out.append(
            {
                "achievement_id": a.id,
                "competition_id": a.competition_id,
                "competition_name": a.competition.name if a.competition else None,
                "achievement_title": a.achievement_title,
                "result_recognition": a.result_recognition,
                "specific_awards": a.specific_awards,
                "notes": a.notes,
                "awarded_at": a.awarded_at,
            }
        )
    return out


def create_achievement(data: Mapping[str, Any]) -> int:
    allowed = {
        "competition",
        "competition_id",
        "achievement_title",
        "result_recognition",
        "specific_awards",
        "notes",
        "awarded_at",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    a = CompetitionAchievement.objects.create(**payload)
    return a.id


def update_achievement(achievement_id: int, data: Mapping[str, Any]) -> None:
    allowed = {
        "competition",
        "competition_id",
        "achievement_title",
        "result_recognition",
        "specific_awards",
        "notes",
        "awarded_at",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    if not payload:
        return
    CompetitionAchievement.objects.filter(pk=achievement_id).update(**payload)


def delete_achievement(achievement_id: int) -> None:
    CompetitionAchievement.objects.filter(pk=achievement_id).delete()


def link_achievement_to_project(achievement_id: int, project_id: int) -> None:
    CompetitionAchievementProject.objects.get_or_create(
        achievement_id=achievement_id,
        project_id=project_id,
    )


def link_achievement_to_user(
    achievement_id: int,
    user_id: int,
    role: str | None,
) -> None:
    CompetitionAchievementUser.objects.update_or_create(
        achievement_id=achievement_id,
        user_id=user_id,
        defaults={"role": role},
    )


# ---------- seed images (for dev) ----------

def seed_images_if_missing(
    paths: Iterable[str],
    uploaded_by: int | None = None,
) -> list[int]:
    ids: list[int] = []
    uploader = User.objects.filter(pk=uploaded_by).first() if uploaded_by else None

    for p in paths:
        m, _ = Media.objects.get_or_create(
            path_or_url=p,
            defaults={
                "media_type": "image",
                "mime_type": "image/jpeg",
                "uploaded_by": uploader,
                "caption": f"Seed {p}",
                "alt_text": f"Seed {p}",
            },
        )
        ids.append(m.id)
    return ids


# ---------- competitions: richer helpers ----------

def competition_exists(competition_id: int) -> bool:
    return Competition.objects.filter(pk=competition_id).exists()


def get_competition_with_relations(competition_id: int) -> dict[str, Any] | None:
    comp = get_competition(competition_id)
    if not comp:
        return None

    achievements = (
        CompetitionAchievement.objects
        .filter(competition_id=competition_id)
        .order_by("-awarded_at", "-id")
    )

    out_achievements: list[dict[str, Any]] = []
    for a in achievements:
        proj_rows = list(
            a.projects.order_by("title").values("id", "title")
        )
        user_rows = list(
            a.users.order_by("username").values("id", "username", "email")
        )
        out_achievements.append(
            {
                "achievement_id": a.id,
                "competition_id": a.competition_id,
                "achievement_title": a.achievement_title,
                "result_recognition": a.result_recognition,
                "specific_awards": a.specific_awards,
                "notes": a.notes,
                "awarded_at": a.awarded_at,
                "projects": [
                    {"projects_id": r["id"], "title": r["title"]} for r in proj_rows
                ],
                "users": [
                    {
                        "auth_user_id": r["id"],
                        "username": r["username"],
                        "email": r["email"],
                        "role": CompetitionAchievementUser.objects.filter(
                            achievement_id=a.id,
                            user_id=r["id"],
                        )
                        .values_list("role", flat=True)
                        .first(),
                    }
                    for r in user_rows
                ],
            }
        )

    comp["achievements"] = out_achievements
    return comp


# ---------- auth helpers ----------

def get_auth_user_id_by_username(username: str) -> int | None:
    username = (username or "").strip()
    if not username:
        return None
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        return None
    return int(u.id)


def ensure_auth_user(username: str, email: str | None = None) -> int | None:
    """
    Django version: ensure a User with this username exists.
    IMPORTANT: adapt to your custom BaseUser required fields if needed.
    """
    username = (username or "").strip()
    if not username:
        return None

    u = User.objects.filter(username=username).first()
    if u:
        return int(u.id)

    # Minimal creation; extend with required fields for your BaseUser.
    u = User.objects.create_user(username=username, email=email or "")
    return int(u.id)
