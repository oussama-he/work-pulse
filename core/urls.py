from django.urls import path

from core.views import home
from core.views import mark_viewed
from core.views import project_archive_view
from core.views import stats_view

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
    path("projects/<int:pk>/mark-as-viewed/", mark_viewed, name="mark-viewed"),
    path("projects/archive/", project_archive_view, name="projects-archive"),
    path("stats/", stats_view, name="stats"),
]
