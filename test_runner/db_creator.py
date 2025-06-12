"""
Usage:
    <script> environment region keyspace token

On success:
    it prints exactly one line to stdout, the database API Endpoint.
"""

import os
import sys

from astrapy import DataAPIClient


if __name__ == "__main__":
    ENVIRONMENT, REGION, KEYSPACE, TOKEN = sys.argv[1:5]
    client = DataAPIClient(environment=ENVIRONMENT)
    astra_admin = client.get_admin(token=TOKEN)

    new_database_admin = astra_admin.create_database(
        name="perf_test_auto",
        cloud_provider="AWS",
        region=REGION,
        keyspace=KEYSPACE,
        wait_until_active=True,
    )

    api_endpoint = new_database_admin.api_endpoint
    print(api_endpoint)
