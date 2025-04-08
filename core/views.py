from datetime import timedelta

from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import F
from django.db.models import TextChoices
from django.db.models import Value
from django.db.models.functions import StrIndex
from django.db.models.functions import Substr
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.models import Project
from core.services import get_new_projects


def home(request):
    get_new_projects()
    new_projects = Project.objects.filter(viewed=False)
    new_projects_stats = {
        "Total": new_projects.count(),
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
    ALL_TIME = "all_time"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_3_MONTHS = "last_3_months"


def stats(request):
    return render(
        request,
        "core/stats.html",
        {
            "projects_per_source": Project.objects.annotate(
                protocol_pos=StrIndex("url", Value("://")),
                after_protocol=Substr("url", 3 + F("protocol_pos")),
                slash_pos=StrIndex(F("after_protocol"), Value("/")),
                domain=Substr(F("after_protocol"), 1, F("slash_pos") - 1),
            )
            .values("domain")
            .annotate(count=Count("domain"))
            .order_by("-count"),
            "project_count": Project.objects.count(),
            "PeriodOption": PeriodOption,
        },
    )


def get_project_count_card(request):
    qs = Project.objects.all()
    now = timezone.now()
    context = {
        "PeriodOption": PeriodOption,
    }
    match request.GET.get("period"):
        case PeriodOption.LAST_7_DAYS.value:
            context["project_count"] = qs.filter(published_at__date__gte=now - timedelta(days=7)).count()
            context["selected_period"] = PeriodOption.LAST_7_DAYS.label
        case PeriodOption.LAST_30_DAYS.value:
            context["project_count"] = qs.filter(published_at__date__gte=now - timedelta(days=30)).count()
            context["selected_period"] = PeriodOption.LAST_30_DAYS.label
        case PeriodOption.LAST_3_MONTHS.value:
            context["project_count"] = qs.filter(published_at__date__gte=now - timedelta(days=90)).count()
            context["selected_period"] = PeriodOption.LAST_3_MONTHS.label
        case _:
            context["project_count"] = qs.count()
            context["selected_period"] = PeriodOption.ALL_TIME.label

    return render(request, "core/includes/project-count-card.html", context)


def project_archive_view(request):
    qs = Project.objects.filter(viewed=True)
    template = "core/projects-archive.html"
    paginator = Paginator(qs, 500)
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
    project.viewed = True
    project.save()
    return HttpResponse(status=204)
