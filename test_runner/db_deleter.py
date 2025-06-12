"""
Usage:
    <script> environment api_endpoint token

*WARNING*: this will delete the database, no questions asked

On success:
    Nothing is printed. The script does not wait for the DB to actually disappear.
"""

import os
import sys

from astrapy import DataAPIClient
from astrapy.admin.endpoints import parse_api_endpoint


if __name__ == "__main__":
    ENVIRONMENT, ENDPOINT, TOKEN = sys.argv[1:4]
    client = DataAPIClient(environment=ENVIRONMENT)
    astra_admin = client.get_admin(token=TOKEN)

    # parsing and validation of endpoint
    parsed_endpoint = parse_api_endpoint(ENDPOINT)
    if parsed_endpoint.environment != ENVIRONMENT:
        raise ValueError(
            "Endpoint environment differs from working environment set by invocation."
        )
    database_id = parsed_endpoint.database_id

    astra_admin.drop_database(
        id=database_id,
        wait_until_active=False,
    )
