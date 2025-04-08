import logging
from typing import Any

from core.models import Project
from core.scrapers import fetch_baaeed_jobs
from core.scrapers import fetch_bahr_projects
from core.scrapers import fetch_emploitic_jobs
from core.scrapers import fetch_mostaql_projects
from core.scrapers import fetch_nafezly_projects
from core.scrapers import fetch_ouedkniss_offers

logger = logging.getLogger(__name__)


def get_new_projects():
    """
    Fetch new projects from multiple sources and save them to the database.
    """
    # Define all source fetchers with their function references
    source_fetchers = [
        fetch_nafezly_projects,
        fetch_baaeed_jobs,
        fetch_emploitic_jobs,
        fetch_bahr_projects,
        fetch_ouedkniss_offers,
        fetch_mostaql_projects,
    ]

    all_projects = []
    for fetcher in source_fetchers:
        projects = fetcher()
        all_projects.extend(process_projects(projects))

    if not all_projects:
        logger.info("No new projects found")

    try:
        created_projects = Project.objects.bulk_create(
            all_projects,
            ignore_conflicts=True,
        )
        logger.info("Created %d new projects", len(created_projects))
    except Exception:
        logger.exception("Error when bulk creating new projects")
    else:
        return created_projects
    return []


def process_projects(projects: list[dict[Any, Any]]) -> list[Project]:
    """
    Process projects from various sources into Project model instances.

    Args:
        projects: List of project dictionaries from a source

    Returns:
        List of Project model instances ready to be created
    """
    result = []
    for project in projects:
        # Create a new Project instance
        new_project = Project(
            title=project["title"],
            description=project.get("description", ""),
            url=project["url"],
        )

        # Set published_at if available
        if "published_at" in project:
            new_project.published_at = project["published_at"]

        result.append(new_project)

    return result
