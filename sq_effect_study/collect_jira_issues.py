import os
import re
import argparse
import requests
import pandas as pd
from time import sleep
from io import StringIO
from dateutil.parser import parse
from sq_effect_study.config import PROJECTS_JIRA, PROJECTS_BUGZILLA


JIRA_API_BASE_URL = "https://issues.apache.org/jira/"
BUGZILLA_BASE_URL = "https://bz.apache.org/bugzilla/buglist.cgi"
BUGZILLA_BUG_URL = "https://bz.apache.org/bugzilla/show_bug.cgi"
PAGE_LENGTH = 500

JIRA_COLUMNS = (
    "issue_type",
    "issue_component",
    "creator_name",
    "creator_display_name",
    "reporter_name",
    "reporter_display_name",
    "priority",
    "description",
    "labels",
    "created",
    "resolution",
    "updated",
    "status",
    "id",
    "key",
)

PROJECT_KEYS = list(PROJECTS_JIRA.keys()) + list(PROJECTS_BUGZILLA.keys())


def filter_projects(data_path):
    from sq_effect_study.analyse_sq_history import get_start_weeks_per_proj

    commits_csv = os.path.join(data_path, "commits.csv")
    commits_df = pd.read_csv(commits_csv)
    # Just to be sure that these are really dates
    commits_df.date = pd.to_datetime(commits_df.date, utc=True)

    fst_commits_df = commits_df.groupby("project").date.min().reset_index()
    sq_start_df = get_start_weeks_per_proj(data_path)

    # Get only those systems that do not have a commit that mentions SonarQube
    # more than a month before it was actually used
    q = (sq_start_df.date - fst_commits_df.date).astype("timedelta64[D]") < 30
    return list(fst_commits_df[q].project)


def collect_from_jira(outpath, force_recollections=False):
    print(PROJECT_KEYS)
    for proj_gh_name, proj_jira_id in PROJECTS_JIRA.items():
        if (proj_gh_name not in PROJECT_KEYS) or (not proj_jira_id):
            continue
        fname = os.path.join(outpath, f"{proj_gh_name}_jira.csv")
        if not force_recollections:
            if os.path.isfile(fname):
                print(f"Found {fname}, will not recreate it...")
                continue

        print(f"Collecting data from {proj_gh_name}...")
        sleep(5)

        rows = []
        start_idx = 0
        url = (
            JIRA_API_BASE_URL
            + f"rest/api/2/search?jql=project={proj_jira_id}+order+by+created"
            + f"&issuetypeNames=Bug&maxResults={PAGE_LENGTH}&"
            + f"startAt={start_idx}&fields=id,key,priority,labels,versions,"
            + "status,components,creator,reporter,issuetype,description,"
            + "summary,resolutiondate,created,updated"
        )

        print(f"Getting data from {url}...")
        r = requests.get(url)
        r_dict = r.json()

        while start_idx < r_dict["total"]:
            sleep(2)

            # The above `issuetypeNames=Bug` should limit the response to bugs
            # only but the response for `WW` contains more issue types. So I
            # have to filter later ...
            for idx in range(len(r_dict["issues"])):
                fields = r_dict["issues"][idx]["fields"]

                # fields["issuetype"]["description"]
                issue_type = fields["issuetype"]["name"]

                issue_component = [
                    c["name"] for c in fields["issuetype"].get("components", [])
                ]
                creator = fields["creator"]
                if creator:
                    creator_name = creator.get("name", None)
                    creator_display_name = creator.get("displayName", None)
                else:
                    creator_name = None
                    creator_display_name = None

                reporter = fields["reporter"]
                if reporter:
                    reporter_name = reporter.get("name", None)
                    reporter_display_name = reporter.get("displayName", None)
                else:
                    reporter_name = None
                    reporter_display_name = None

                priority = fields["priority"]
                if priority:
                    priority = priority.get("name", None)

                description = fields["description"]
                labels = fields["labels"]

                created = fields["created"]
                if created:
                    created = parse(created)
                resolution = fields["resolutiondate"]
                if resolution:
                    resolution = parse(resolution)
                updated = fields["updated"]
                if updated:
                    updated = parse(updated)
                status = fields["status"]["name"]

                id_val = r_dict["issues"][idx]["id"]
                key_val = r_dict["issues"][idx]["key"]

                rows.append(
                    (
                        issue_type,
                        issue_component,
                        creator_name,
                        creator_display_name,
                        reporter_name,
                        reporter_display_name,
                        priority,
                        description,
                        labels,
                        created,
                        resolution,
                        updated,
                        status,
                        id_val,
                        key_val,
                    )
                )

            start_idx += PAGE_LENGTH
            url = re.sub(r"startAt=\d+&", f"startAt={start_idx}&", url)
            inner_idx = start_idx + PAGE_LENGTH
            print(f"Getting data for index {start_idx} to {inner_idx}...")
            r = requests.get(url)
            r_dict = r.json()

        print(f"Writing {fname} for {proj_gh_name}...")
        df = pd.DataFrame(rows, columns=JIRA_COLUMNS)
        df.to_csv(fname, index=False)


def collect_from_bz(outpath, force_recollections=False):
    # Export the data from Bugzilla
    for proj_gh_name, proj_bz_id in PROJECTS_BUGZILLA.items():
        if (proj_gh_name not in PROJECT_KEYS) or (not proj_bz_id):
            continue

        fname = os.path.join(outpath, f"{proj_gh_name}_bugzilla.csv")
        if not force_recollections:
            if os.path.isfile(fname):
                print(f"Found {fname}, will not recreate it...")
                continue

        print(f"Collecting data from {proj_gh_name}...")

        url = (
            BUGZILLA_BASE_URL
            + f"?limit=0&product={proj_bz_id}&query_format=advanced&limit=0"
            + "&ctype=csv&human=1&columnlist=bug_id,bug_severity,bug_status,"
            + "component,reporter,reporter_realname,assigned_to,priority,"
            + "short_desc,keywords,resolution,status_whiteboard,opendate,"
            + "changeddate"
        )

        r = requests.get(url)
        csv_str = StringIO(r.text)
        df = pd.read_csv(csv_str)

        print(f"Writing {fname} for {proj_gh_name}...")
        df.to_csv(fname, index=False)
        sleep(30)


def update_keys(data_path):
    global PROJECT_KEYS
    PROJECT_KEYS = filter_projects(data_path)


if __name__ == "__main__":
    msg = "Collect issues from JIRA and from Bugzilla."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument(
        "outpath",
        metavar="outpath",
        type=str,
        help="Path",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite previously collected issue dumps.",
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help="Only download the issue tracker data for relevant projects.",
    )

    args = parser.parse_args()
    if args.filter:
        update_keys(args.outpath)

    collect_from_jira(args.outpath, force_recollections=args.force)
    collect_from_bz(args.outpath, force_recollections=args.force)
