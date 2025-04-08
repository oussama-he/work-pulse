from django.urls import include
from django.urls import path

from core.views import get_project_count_card
from core.views import home
from core.views import mark_viewed
from core.views import project_archive_view
from core.views import stats

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
    path("projects/<int:pk>/mark-as-viewed/", mark_viewed, name="mark-viewed"),
    path("projects/archive/", project_archive_view, name="projects-archive"),
    path("stats/", stats, name="stats"),
    # htmx views
    path(
        "",
        include(
            [
                path("project-count/", get_project_count_card, name="project-count"),
            ],
        ),
    ),
]
