from django.conf import settings
from django.http import FileResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)
def favicon_file(request):
    name = "favicon-dev.png" if settings.DEBUG else request.path.lstrip("/")
    file = (settings.BASE_DIR / "static" / "img" / name).open("rb")
    return FileResponse(file)
