import os

from dotenv import load_dotenv
from elasticapm.contrib.starlette import ElasticAPM, make_apm_client

from logging_config import get_logger

load_dotenv()

logger = get_logger("app.apm")


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
    app.add_middleware(ElasticAPM, client=apm_client)
    logger.info(
        "Elastic APM enabled (service=%s, server=%s)",
        config["SERVICE_NAME"],
        server_url,
    )
    return apm_client
