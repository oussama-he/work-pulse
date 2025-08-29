from datetime import timedelta

from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import F
from django.db.models import TextChoices
from django.db.models import Value
from django.db.models.functions import StrIndex
from django.db.models.functions import Substr
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from core.models import Project
from core.scrapers import SOURCES_CONFIG
from core.services import get_new_projects


def home(request):
    get_new_projects()
    new_projects = Project.objects.filter(viewed__isnull=True).order_by(F("published_at").desc(nulls_last=True))
    new_projects_stats = {
        "emploitic.com": new_projects.filter(url__icontains="https://emploitic.com/").count(),
        "nafezly.com": new_projects.filter(url__icontains="https://nafezly.com/").count(),
        "ouedkniss.com": new_projects.filter(url__icontains="https://ouedkniss.com/").count(),
        "baaeed.com": new_projects.filter(url__icontains="https://baaeed.com/").count(),
        "bahr.sa": new_projects.filter(url__icontains="https://bahr.sa/").count(),
        "mostaql.com": new_projects.filter(url__startswith="https://mostaql.com").count(),
    }
    return render(
        request,
        "core/home.html",
        {
            "projects": new_projects,
            "new_projects_stats": new_projects_stats,
        },
    )


class PeriodOption(TextChoices):
    LAST_7_DAYS = "7", "Last 7 days"
    LAST_30_DAYS = "30", "Last 30 days"
    LAST_3_MONTHS = "90", "Last 3 months"


class StatsView(TemplateView):
    SOURCES = sorted(SOURCES_CONFIG.keys())
    SOURCE_COLORS = [SOURCES_CONFIG[source]["color"] for source in SOURCES]

    def get_template_names(self):
        if self.request.htmx:
            return ["core/stats.html#daily-projects-card"]
        return ["core/stats.html"]

    def get_projects_by_source(self):
        return Project.objects.annotate(
            protocol_pos=StrIndex("url", Value("://")),
            after_protocol=Substr("url", 3 + F("protocol_pos")),
            slash_pos=StrIndex(F("after_protocol"), Value("/")),
            source=Substr(F("after_protocol"), 1, F("slash_pos") - 1),
        )

    def get_daily_stats(self, day_list):
        daily_stats = (
            self.get_projects_by_source()
            .filter(published_at__gte=day_list[0])
            .annotate(day=TruncDate("published_at"))
            .values("day", "source")
            .annotate(count=Count("id"))
        )
        return self._format_daily_counts(daily_stats, day_list)

    def _format_daily_counts(self, daily_stats, day_list):
        source_daily_count = []
        for source in self.SOURCES:
            counts = [
                next((item["count"] for item in daily_stats if item["source"] == source and item["day"] == day), 0)
                for day in day_list
            ]
            source_daily_count.append({"name": source, "data": counts})
        return source_daily_count

    def _calculate_source_totals(self, daily_stats):
        source_totals = {}
        for source_count in daily_stats:
            source = source_count["name"]
            source_totals[source] = sum(source_count["data"])
        return source_totals

    def get_day_list(self):
        period = self.request.GET.get("period")
        period = period if period in PeriodOption.values else PeriodOption.LAST_7_DAYS.value
        start_date = timezone.now().date() - timedelta(days=1)
        day_list = [start_date - timedelta(days=i) for i in range(int(period))]
        day_list.reverse()
        return day_list

    def get(self, request, *args, **kwargs):
        projects_by_source = (
            self.get_projects_by_source().values("source").annotate(total=Count("id")).order_by("source")
        )
        day_list = self.get_day_list()
        source_daily_count = self.get_daily_stats(day_list)
        source_total = self._calculate_source_totals(source_daily_count)
        context = {
            "source_daily_count": source_daily_count,
            "source_totals": source_total,
            "daily_total": sum(source_total.values()),
            "source_colors": self.SOURCE_COLORS,
            "day_list": day_list,
            "projects_per_source": list(projects_by_source),
            "project_count": Project.objects.count(),
            "PeriodOption": PeriodOption,
            "selected_period_label": dict(PeriodOption.choices).get(
                self.request.GET.get("period"),
                PeriodOption.LAST_7_DAYS.label,
            ),
        }
        return self.render_to_response(context)


stats_view = StatsView.as_view()


def project_archive_view(request):
    qs = Project.objects.filter(viewed__isnull=False)
    template = "core/projects-archive.html"
    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page") or 1
    try:
        page = paginator.page(int(page_number))
    except (ValueError, EmptyPage):
        page = paginator.page(1)

    if request.htmx:
        template = "core/projects-archive.html#project-list"

    return render(
        request,
        template,
        {
            "page": page,
        },
    )


@require_http_methods(["PUT"])
def mark_viewed(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.viewed = timezone.now()
    project.save()
    return HttpResponse(status=204)
