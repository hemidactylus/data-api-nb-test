import json
import os
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from zoneinfo import ZoneInfo

IMAGE_WIDTH_ON_PAGE_PX = 1024

# settings from env
ATLASSIAN_EMAIL = os.environ["ATLASSIAN_EMAIL"]
ATLASSIAN_API_TOKEN = os.environ["ATLASSIAN_API_TOKEN"]
ATLASSIAN_BASE_URL = os.environ["ATLASSIAN_BASE_URL"]
ATLASSIAN_PAGE_ID = os.environ["ATLASSIAN_PAGE_ID"]


def upsert_attachment_to_atlassian(f_title: str, f_path: str, mime_type: str = "image/png") -> None:
    atlassian_auth = HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)
    attach_url = f"{ATLASSIAN_BASE_URL}/content/{ATLASSIAN_PAGE_ID}/child/attachment"
    # Check if filename is there already
    file_get_response = requests.get(
        attach_url,
        params={"filename": f_title},
        auth=atlassian_auth,
        headers={"Accept": "application/json"},
    )
    data_file_get = file_get_response.json()
    attachment_id: str | None
    if data_file_get["results"]:
        attachment = data_file_get["results"][0]
        attachment_id = attachment["id"]
    else:
        attachment_id = None

    # if existing, delete it first
    if attachment_id is not None:
        delete_url = f"{ATLASSIAN_BASE_URL}/content/{attachment_id}"
        delete_response = requests.delete(
            delete_url,
            auth=atlassian_auth,
            headers={"X-Atlassian-Token": "no-check"},
        )
        print(
            f"    * deleting older '{f_title}' returned: {delete_response.status_code}."
        )

    with open(f_path, "rb") as f_data:
        files = {"file": (f_title, f_data, mime_type)}
        upload_response = requests.post(
            attach_url,
            auth=atlassian_auth,
            headers={"X-Atlassian-Token": "no-check"},
            files=files,
        )
    print(f"    * upload '{f_title}' returned: {upload_response.status_code}.")


def update_atlassian_page(
    tree: dict[
        str,
        dict[str, dict[str, dict[str, dict[str, tuple[dict[datetime, float], str]]]]],
    ],
    image_map: dict[str, dict[str, dict[str, dict[str, list[tuple[str, str]]]]]],
) -> None:
    print("\nAtlassian update starting.")
    generation_timestamp_str = datetime.now(ZoneInfo("UTC")).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    atlassian_auth = HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)

    # get current version of page
    getpage_response = requests.get(
        f"{ATLASSIAN_BASE_URL}/content/{ATLASSIAN_PAGE_ID}?expand=body.storage,version,space,title",
        auth=atlassian_auth,
        headers={"Accept": "application/json"},
    )
    getpage_data = getpage_response.json()
    page_current_version = getpage_data["version"]["number"]
    print(f"Current version detected on Atlassian: {page_current_version}")

    # prepare html while sending images along the way
    page_doc_parts = []
    page_doc_parts.append(f"<p>Generated at: {generation_timestamp_str}</p>\n")
    for _wl, wlmap in sorted(image_map.items()):
        if wlmap:
            # add h1 wl
            page_doc_parts.append(f"<h1>Workload '{_wl}'</h1>\n")
            for _sc, scmap in sorted(wlmap.items()):
                if scmap:
                    # add h2 sc
                    page_doc_parts.append(f"<h2>Scenario '{_sc}'</h2>\n")
                    for _ac, acmap in sorted(scmap.items()):
                        if acmap:
                            # add h3 ac
                            page_doc_parts.append(f"<h3>Activity '{_ac}'</h3>\n")
                            for _na, nalist in sorted(acmap.items()):
                                if nalist:
                                    # add a simple p with the na, followed by the plots
                                    page_doc_parts.append(f"<p>Name: '{_na}'</p>\n")
                                    # this is a list of plots to upload
                                    for img_title, img_path in nalist:
                                        # append image embed
                                        page_doc_parts.append(
                                            '<ac:image ac:custom-width="true" '
                                            f'ac:width="{IMAGE_WIDTH_ON_PAGE_PX}">'
                                        )
                                        page_doc_parts.append(
                                            f'  <ri:attachment ri:filename="{img_title}" />',
                                        )
                                        page_doc_parts.append("</ac:image>")
                                        # upload (upsert) attached image
                                        upsert_attachment_to_atlassian(
                                            img_title, img_path
                                        )

    # upload page (with version increase)
    print(f"Preparing page body from {len(page_doc_parts)} lines.")
    page_body = "\n".join(page_doc_parts)
    update_data = {
        "id": ATLASSIAN_PAGE_ID,
        "type": "page",
        "title": getpage_data["title"],
        "space": {"key": getpage_data["space"]["key"]},
        "body": {"storage": {"value": page_body, "representation": "storage"}},
        "version": {"number": page_current_version + 1},
    }
    update_response = requests.put(
        f"{ATLASSIAN_BASE_URL}/content/{ATLASSIAN_PAGE_ID}",
        data=json.dumps(update_data),
        auth=atlassian_auth,
        headers={"Content-Type": "application/json"},
    )
    print(f"Update returned status: {update_response.status_code}")
