import os

from dotenv import load_dotenv
from elasticapm.contrib.starlette import ElasticAPM, make_apm_client
from starlette.routing import Match, Mount

from logging_config import get_logger

load_dotenv()

logger = get_logger("app.apm")


class _CompatElasticAPM(ElasticAPM):
    """ElasticAPM middleware patched for FastAPI >= 0.139 routing.

    FastAPI 0.139 wraps included routers in an internal ``_IncludedRouter``
    route object that has no ``.path`` attribute. The stock elastic-apm
    resolver blindly reads ``route.path`` on any matched route, so every
    request raises ``AttributeError`` and 500s. Here we recurse into the
    wrapped router to recover the real route template, and never let route
    naming crash a request (falling back to the URL path instead).
    """

    def get_route_name(self, request):
        try:
            return super().get_route_name(request)
        except Exception:
            # Never let transaction naming break the actual request; the
            # caller falls back to request.url.path when this returns None.
            logger.debug("APM route-name resolution failed", exc_info=True)
            return None

    def _get_route_name(self, scope, routes, route_name=None):
        for route in routes:
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                merged = {**scope, **child_scope}
                path = getattr(route, "path", None)
                if path is not None:
                    route_name = path
                    if isinstance(route, Mount) and route.routes:
                        child = self._get_route_name(merged, route.routes, route_name)
                        route_name = None if child is None else route_name + child
                    return route_name
                # FastAPI >= 0.139: _IncludedRouter has no .path — descend into
                # the underlying router's routes to find the real APIRoute.
                sub_routes = getattr(
                    getattr(route, "original_router", None), "routes", None
                )
                if sub_routes:
                    prefix = getattr(
                        getattr(route, "include_context", None), "prefix", ""
                    ) or ""
                    child = self._get_route_name(merged, sub_routes, route_name)
                    return None if child is None else prefix + child
                return route_name
            elif match == Match.PARTIAL and route_name is None:
                route_name = getattr(route, "path", route_name)
        return route_name


def init_apm(app):
    """Attach the Elastic APM agent to the FastAPI app if configured.

    The agent is enabled only when ELASTIC_APM_SERVER_URL is set. Authenticate
    with Elastic Cloud using either ELASTIC_APM_SECRET_TOKEN or
    ELASTIC_APM_API_KEY. Returns the APM client, or None when disabled.
    """
    server_url = os.getenv("ELASTIC_APM_SERVER_URL")
    if not server_url:
        logger.info("Elastic APM disabled (ELASTIC_APM_SERVER_URL not set)")
        return None

    config = {
        "SERVICE_NAME": os.getenv("ELASTIC_APM_SERVICE_NAME", "fastapi-auth-mysql"),
        "SERVER_URL": server_url,
        "ENVIRONMENT": os.getenv("ELASTIC_APM_ENVIRONMENT", "production"),
        "SERVICE_VERSION": os.getenv("ELASTIC_APM_SERVICE_VERSION", "1.0.0"),
    }

    secret_token = os.getenv("ELASTIC_APM_SECRET_TOKEN")
    api_key = os.getenv("ELASTIC_APM_API_KEY")
    if secret_token:
        config["SECRET_TOKEN"] = secret_token
    elif api_key:
        config["API_KEY"] = api_key
    else:
        logger.warning(
            "Elastic APM: neither ELASTIC_APM_SECRET_TOKEN nor "
            "ELASTIC_APM_API_KEY is set; requests to Elastic Cloud may be rejected"
        )

    apm_client = make_apm_client(config)
    app.add_middleware(_CompatElasticAPM, client=apm_client)
    logger.info(
        "Elastic APM enabled (service=%s, server=%s)",
        config["SERVICE_NAME"],
        server_url,
    )
    return apm_client
