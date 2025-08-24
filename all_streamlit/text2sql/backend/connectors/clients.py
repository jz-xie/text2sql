import boto3
from functools import lru_cache
from openai import AzureOpenAI
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection
import snowflake.connector
from text2sql.backend.config import settings


@lru_cache
def get_openai_chat_client():
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai.endpoint,
        api_key=settings.azure_openai.api_key.get_secret_value(),
        azure_deployment=settings.azure_openai.deployment_chat,
        api_version=settings.azure_openai.api_version,
    )


@lru_cache
def get_openai_embedding_client():
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai.endpoint,
        api_key=settings.azure_openai.api_key.get_secret_value(),
        azure_deployment=settings.azure_openai.deployment_embedding,
        api_version=settings.azure_openai.api_version,
    )


@lru_cache
def get_opensearch_client():
    if settings.env == "local":
        return OpenSearch(
            hosts=[
                {"host": settings.opensearch.host, "port": settings.opensearch.port}
            ],
            http_auth=(
                settings.opensearch.user,
                settings.opensearch.password.get_secret_value(),
            ),
            http_compress=True,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    else:
        boto3_session = boto3.Session()
        region = boto3_session.region_name
        credentials = boto3_session.get_credentials()
        auth = AWSV4SignerAuth(credentials, region, "es")

        return OpenSearch(
            hosts=[{"host": settings.opensearch.host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
            timeout=60,
        )


@lru_cache
def get_snowflake_connection(username: str, access_token: str):
    if settings.env == "local":
        account = "gxs-dev"
    else:
        account = f"gxs-{settings.env}"

    return snowflake.connector.connect(
        authenticator="oauth",
        user=username,
        account=account,
        database="gold",
        token=access_token,
        client_session_keep_alive=True,
        session_parameters={
            "QUERY_TAG": "Text2SQL",
        },
    )
