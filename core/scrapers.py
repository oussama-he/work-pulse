import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from slugify import slugify

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

SOURCES_CONFIG = {
    "mostaql": {
        "url": "https://mostaql.com/projects?category=development,support&budget_max=10000&sort=latest",
        "parser": "html",
        "type": "project",
    },
    "nafezly": {
        "url": "https://nafezly.com/projects?specialize=development&page=1",
        "parser": "html",
        "type": "project",
    },
    "emploitic": {
        "url": "https://emploitic.com/api/v4/jobs?sort[0]=publishedAt_timestamp:desc&filter=(criteria.profession.id=%27a0d04378f37973ffa3b2aa8b3e27a3f0a98de06d%27)&pagination[page]=1&pagination[pageSize]=20",
        "parser": "json",
        "type": "job",
    },
    "baaeed": {
        "url": "https://baaeed.com/remote-jobs?sort=latest&categories=remote-programming-jobs,other-remote-jobs",
        "parser": "html",
        "type": "job",
    },
    "bahr": {
        "url": (
            "https://bahr.sa/api/projects?status[]=Open&offset=10&sort=DESC&sortBy=publishDate"
            "&categories[]=0190c21f-f7cc-75f2-aef3-6d020d74e9a1"
            "&categories[]=0190c21f-f7ad-7222-9410-13e74073549c"
            "&categories[]=0190c21f-f7cd-7c9e-b4e5-01b4229cfc4f"
            "&categories[]=0190c21f-f7cc-75f2-aef3-6d020ca6b9c7"
            "&page=1"
        ),
        "parser": "json",
        "type": "project",
    },
    "ouedkniss": {
        "url": "https://api.ouedkniss.com/graphql",
        "parser": "graphql",
        "type": "offer",
    },
}

logger = logging.getLogger(__name__)


# --- Helper Functions ---


def _make_request(url: str, method: str = "GET", **kwargs) -> requests.Response | None:
    """Makes an HTTP request with error handling."""
    try:
        response = requests.request(
            method,
            url,
            headers=REQUEST_HEADERS,
            timeout=15,
            **kwargs,
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException:
        logger.exception("Request failed for '%s'", url)
    else:
        return response


def _parse_datetime(
    dt_str: str,
    fmt: str,
    *,
    make_aware: bool = True,
) -> datetime | None:
    """Safely parses datetime string, adjusts, and makes timezone-aware."""
    try:
        dt = datetime.strptime(dt_str, fmt)  # noqa: DTZ007
        if make_aware and timezone.is_naive(dt):
            dt = timezone.make_aware(dt, ZoneInfo("UTC"))
    except (ValueError, TypeError):
        logger.exception(
            f"Could not parse datetime string '{dt_str}' with format '{fmt}'",  # noqa: G004
        )
    else:
        return dt


def _safe_extract_text(element, selector: str, default: str = "") -> str:
    """Safely extracts text from a BeautifulSoup element."""
    try:
        target = element.select_one(selector)
        if target:
            text = target.text
            return text.strip()
    except Exception:
        logger.exception("Error extracting text with selector '%s'", selector)
    return default


def _safe_extract_attr(
    element,
    selector: str,
    attr: str,
    default: str | None = None,
) -> str | None:
    """Safely extracts an attribute from a BeautifulSoup element."""
    try:
        target = element.select_one(selector)
        if target and target.has_attr(attr):
            return target[attr]
    except Exception:
        logger.exception(
            f"Error extracting attribute '{attr}' with selector '{selector}'",  # noqa: G004
        )

    return default


# --- Scraper Functions ---


def fetch_mostaql_projects() -> list[dict[str, Any]]:
    config = SOURCES_CONFIG["mostaql"]
    response = _make_request(config["url"])
    if not response:
        return []

    projects = []
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for project_row in soup.select(".projects-table tbody tr"):
            published_at_str = _safe_extract_attr(project_row, "time", "datetime")
            projects.append(
                {
                    "title": _safe_extract_text(project_row, ".card--title a"),
                    "url": _safe_extract_attr(project_row, ".card--title a", "href"),
                    "description": _safe_extract_text(project_row, ".project__brief a"),
                    "published_at": _parse_datetime(
                        published_at_str,
                        "%Y-%m-%d %H:%M:%S",
                    ),
                },
            )
    except Exception:
        logger.exception("Error parsing Mostaql projects")
    return [p for p in projects if p.get("url")]  # Ensure URL is present


def fetch_nafezly_projects() -> list[dict[str, Any]]:
    config = SOURCES_CONFIG["nafezly"]
    response = _make_request(config["url"])
    if not response:
        return []

    projects = []
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        projects.extend(
            {
                "title": _safe_extract_text(project_box, "a.text-truncate"),
                "url": _safe_extract_attr(project_box, "a.text-truncate", "href"),
                "description": _safe_extract_text(project_box, "h3"),
            }
            for project_box in soup.select(".project-box")
        )
    except Exception:
        logger.exception("Error parsing Nafezly projects")
    return [p for p in projects if p.get("url")]


def fetch_emploitic_jobs() -> list[dict[str, Any]]:
    config = SOURCES_CONFIG["emploitic"]
    response = _make_request(config["url"])
    if not response:
        return []

    jobs = []
    try:
        data = response.json()
        base_url = "https://emploitic.com"

        def generate_job_url(job_alias, company_data):
            company_alias = company_data.get("alias")
            sector_slug = slugify(company_data.get("sector", {}).get("label", ""))
            if company_alias:
                return f"{base_url}/entreprises/{company_alias}/offres-d-emploi/{sector_slug}/{job_alias}/"
            return f"{base_url}/offres-d-emploi/{sector_slug}/{job_alias}"

        jobs.extend(
            {
                "title": job.get("title"),
                "url": generate_job_url(job.get("alias"), job.get("company", {})),
                "description": job.get(
                    "description",
                ),  # Assuming this is HTML description
                "published_at": job.get("publishedAt"),
            }
            for job in data.get("results", [])
        )

    except Exception:
        logger.exception("Error parsing Emploitic jobs")
    return [j for j in jobs if j.get("url")]


def fetch_baaeed_jobs() -> list[dict[str, Any]]:
    config = SOURCES_CONFIG["baaeed"]
    response = _make_request(config["url"])
    if not response:
        return []

    jobs = []
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for job_row in soup.select("section.baaeed-card table tr"):
            published_at_str = _safe_extract_attr(job_row, "time", "datetime")
            jobs.append(
                {
                    "title": _safe_extract_text(
                        job_row,
                        ".baaeed-list__details h3.card-title a",
                    ),
                    "url": _safe_extract_attr(
                        job_row,
                        ".baaeed-list__details h3.card-title a",
                        "href",
                    ),
                    "description": _safe_extract_text(job_row, ".card-brief a"),
                    "published_at": _parse_datetime(
                        published_at_str,
                        "%Y-%m-%d %H:%M:%S",
                    ),
                },
            )
    except Exception:
        logger.exception("Error parsing Baaeed jobs")
    return [j for j in jobs if j.get("url")]


def fetch_bahr_projects() -> list[dict[str, Any]]:
    config = SOURCES_CONFIG["bahr"]
    response = _make_request(config["url"])
    if not response:
        return []

    projects = []
    try:
        data = response.json().get("data", {}).get("projects", [])
        projects.extend(
            {
                "title": project.get("title"),
                "description": project.get("description"),
                "url": f"https://bahr.sa/en/projects/{project.get('id')}",
                "published_at": _parse_datetime(
                    project.get("createdAt"),
                    "%Y-%m-%d %H:%M:%S",
                ),
            }
            for project in data
        )

    except Exception:
        logger.exception("Error parsing Bahr projects")

    return [p for p in projects if p.get("url")]


def fetch_ouedkniss_offers() -> list[dict[str, Any]]:
    config = SOURCES_CONFIG["ouedkniss"]
    query = """
        query SearchQuery($q: String, $filter: SearchFilterInput,
                        $mediaSize: MediaSize = MEDIUM)
            {  search(q: $q, filter: $filter) {
            announcements {
                data {
                ...AnnouncementContent
                smallDescription {
                    valueText
                    __typename
                }
            noAdsense
        __typename
        }
        paginatorInfo
        {
            lastPage
        hasMorePages
        __typename
        }
        __typename
        }
        active
        {
            category
        {
            id
        name
        slug
        icon
        delivery
        deliveryType
        priceUnits
        children
        {
            id
        name
        slug
        icon
        __typename
        }
        specifications
        {
            isRequired
        specification
        {
            id
        codename
        label
        type

        class
            datasets
            {
                codename
            label
            __typename
            }
            dependsOn
            {
                id
            codename
            __typename
            }
            subSpecifications
            {
                id
            codename
            label
            type
            __typename
            }
            allSubSpecificationCodenames
            __typename

        }
        __typename
        }
        parentTree
        {
            id
        name
        slug
        icon
        children
        {
        id
        name
        slug
        icon
        __typename

        }
        __typename
        }
        parent
        {
            id
        name
        icon
        slug
        __typename
        }
        __typename
        }
        count
        filter
        {
            cities
        {
            id
        name
        __typename
        }
        regions
        {
            id
        name
        __typename
        }
        __typename
        }
        __typename
        }
        suggested
        {
            category
        {
            id
        name
        slug
        icon
        __typename
        }
        count
        __typename
        }
        __typename
        }
        }

        fragment
        AnnouncementContent
        on
        Announcement
        {
            id
        title
        slug
        createdAt: refreshedAt
        isFromStore
        isCommentEnabled
        userReaction
        {
            isBookmarked
        isLiked
        __typename
        }
        hasDelivery
        deliveryType
        likeCount
        description
        status
        cities
        {
            id
        name
        slug
        region
        {
            id
        name
        slug
        __typename
        }
        __typename
        }
        store
        {
            id
        name
        slug
        imageUrl
        isOfficial
        isVerified
        __typename
        }
        user
        {
            id
        __typename
        }
        defaultMedia(size: $mediaSize) {
            mediaUrl
        mimeType
        thumbnail
        __typename
        }
        price
        pricePreview
        priceUnit
        oldPrice
        oldPricePreview
        priceType
        exchangeType
        category
        {
            id
        slug
        __typename
        }
        __typename
        }
        """

    payload = {
        "operationName": "SearchQuery",
        "variables": {
            "mediaSize": "MEDIUM",
            "q": None,
            "filter": {
                "categorySlug": "emploi_offres-informatique-internet",
                "origin": None,
                "connected": False,
                "delivery": None,
                "regionIds": [],
                "cityIds": [],
                "priceRange": [],
                "exchange": False,
                "hasPictures": False,
                "hasPrice": False,
                "priceUnit": None,
                "fields": [],
                "page": 1,
                "count": 48,
            },
        },
        "query": query,
    }

    response = _make_request(config["url"], method="POST", json=payload)
    if not response:
        return []

    offers = []
    try:
        data = response.json().get("data", {}).get("search", {}).get("announcements", {}).get("data", [])
        offers.extend(
            {
                "title": offer.get("title"),
                "description": offer.get("description"),
                "url": f"https://ouedkniss.com/{offer.get('slug')}-d{offer.get('id')}",
                "published_at": offer.get("createdAt"),
            }
            for offer in data
        )

    except Exception:
        logger.exception("Error parsing Ouedkniss offers")
    return [o for o in offers if o.get("url")]
