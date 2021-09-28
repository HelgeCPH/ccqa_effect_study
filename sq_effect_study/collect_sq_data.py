import os
import argparse
import requests
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from datetime import timezone
from selenium import webdriver
from dateutil.parser import parse
from sq_effect_study.config import PROJECTS_SQ

BROWSER = webdriver.Firefox()
TIME_FMT_STR = "%Y-%m-%dT%H%%3A%M%%3A%S%%2B0000"
SQ_API_BASE_URL = "https://sonarcloud.io/api/project_analyses/search"
SQ_WEB_BASE_URL = "https://sonarcloud.io/project/activity"
COLUMNS = (
    "project",
    "date",
    "no_bugs",
    "bugs_rating",
    "no_code_smells",
    "code_smells_rating",
    "no_vulnerabilities",
    "vulnerabilities_rating",
    # "lines_to_cover",
    # "covered_lines",
    # "uncovered_lines",
    # "coverage_perc",
    # "loc",
    # "dupl_lines",
    # "dupl_lines_perc",
)


def get_activity_from_sq_api(project):
    idx = 1
    responses = []
    """Collects especially the dates when a project was analyzed. In essence,
    it collects everything that is in the left pane, for example of:
    https://sonarcloud.io/project/activity?id=simgrid_simgrid
    """
    while True:
        # Collecting pages from the `project_analyses` API
        url = SQ_API_BASE_URL + f"?project={project}&ps=500&p={idx}"
        r = requests.get(url)
        proj_activity = r.json()

        responses.append(proj_activity)
        if proj_activity["paging"]["total"] < (
            proj_activity["paging"]["pageIndex"]
            * proj_activity["paging"]["pageSize"]
        ):
            # Leave the loop once all values are collected
            break
        sleep(2)  # Be kind to the sonarcloud server and prevent being banned

    analysis_rows = []
    for response in responses:
        for ana in response["analyses"]:
            # Looks like: '2020-06-11T06:38:24+0200'
            data_str = parse(ana["date"])
            try:
                proj_version_str = ana["projectVersion"]
            except KeyError:
                proj_version_str = None
            events_lst = [(e["category"], e["name"]) for e in ana["events"]]

            analysis_rows.append((data_str, proj_version_str, events_lst))

    return analysis_rows


def scrape_analysis_event(project, ana_row):
    vals = []

    html_src = get_analysis_page_src(project, ana_row, kind="ISSUES")
    issue_vals = scrape_analysis_value(html_src, ana_row, kind="ISSUES")
    # html_src = get_analysis_page_src(project, ana_row, kind="COVERAGE")
    # cov_vals = scrape_analysis_value(html_src, ana_row, kind="COVERAGE")
    # html_src = get_analysis_page_src(project, ana_row, kind="DUPLICATIONS")
    # dupl_vals = scrape_analysis_value(html_src, ana_row, kind="DUPLICATIONS")

    vals = issue_vals
    # + cov_vals + dupl_vals
    # flatten the values into a list per row
    row = []
    for val in vals:
        if type(val) == tuple:
            for v in val:
                row.append(v)
        else:
            row.append(val)
    return row


def scrape_analysis_values(project, analysis_rows):
    rows = []
    for ana in analysis_rows:
        try:
            row = scrape_analysis_event(project, ana)
            # print(project, ana[0], *row)
            if len(row) < 6:  # 13:
                # print(row)
                # print("oioioi!")
                raise Exception("oioioi!")
            rows.append((project, ana[0], *row))
        except IndexError as e:
            date_str = ana[0].strftime("%Y-%m-%d:%H:%M")
            print(f"Skipped {project} {date_str}")
    return rows


def get_analysis_page_src(project, analysis_row, kind="ISSUES"):
    # print(analysis_row[0])
    utc_datetime = (
        analysis_row[0]
        .astimezone()
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )
    time_str = utc_datetime.strftime(TIME_FMT_STR)

    if kind == "ISSUES":
        url = SQ_WEB_BASE_URL + f"?id={project}&selected_date={time_str}"
    elif kind == "COVERAGE":
        url = (
            SQ_WEB_BASE_URL
            + f"?graph=coverage&id={project}&selected_date={time_str}"
        )
    elif kind == "DUPLICATIONS":
        url = (
            SQ_WEB_BASE_URL
            + f"?graph=duplications&id={project}&selected_date={time_str}"
        )

    print(url)
    # if (
    #     url
    #     == "https://sonarcloud.io/project/activity?graph=duplications&id=apache_ofbiz-plugins&selected_date=2020-05-14T12%3A13%3A19%2B0000"
    # ):
    #     print("oioioi")

    BROWSER.get(url)
    # Be kind to the sonarcloud server and prevent being banned. Additionally,
    # wait for the page to be loaded
    sleep(3)

    return BROWSER.page_source


def scrape_issues(src):
    # Order is: Bugs, Code Smells, Vulnerabilities
    typ = src.find_all("td")[-1].text
    value, rating = src.find_all("span")
    value, rating = int(value.text.replace(",", "")), rating.text

    return typ, value, rating


def scrape_others(src):
    tds = src.find_all("td")
    typ = tds[-1].text.strip()
    if typ == "Events:":
        return typ, None
    else:
        val_str = tds[-2].text

        if "k" in val_str:
            val_str = val_str.replace("k", "000").replace(".", "")
            value = int(val_str)
        if "," in val_str:
            val_str = val_str.replace(",", "")
            value = int(val_str)
        if "%" in val_str:
            val_str = val_str.replace("%", "")
            value = float(val_str)
        else:
            value = int(val_str)

        return typ, value


def scrape_analysis_value(page_source, analysis_row, kind="ISSUES"):
    soup = BeautifulSoup(page_source, "html5lib")

    if kind == "ISSUES":
        attributes = {"class": "project-activity-graph-tooltip-issues-line"}
    elif (kind == "COVERAGE") or (kind == "DUPLICATIONS"):
        attributes = {"class": "project-activity-graph-tooltip-line"}

    assessment = soup.find_all("tr", attrs=attributes)
    if kind == "ISSUES":
        results = {"Bugs": None, "Code Smells": None, "Vulnerabilities": None}
    elif kind == "COVERAGE":
        results = {
            "Lines to Cover": None,
            "Covered Lines": None,
            "Uncovered Lines": None,
            "Coverage": None,
        }
    elif kind == "DUPLICATIONS":
        results = {
            "Lines of Code": None,
            "Duplicated Lines": None,
            "Duplicated Lines (%)": None,
        }

    for a in assessment:
        if kind == "ISSUES":
            typ, value, rating = scrape_issues(a)
            # print(typ, (value, rating))
            results[typ] = (value, rating)
        else:
            # try:
            typ, value = scrape_others(a)
            # print(typ, (value,))
            if typ == "Events:":
                continue
            results[typ] = value

    # print(results)
    return tuple(results.values())


def main(outpath):
    try:
        for proj_gh_name, proj_sq_id in PROJECTS_SQ.items():
            fname = os.path.join(outpath, f"{proj_gh_name}.csv")
            if proj_sq_id and not os.path.isfile(fname):
                print(f"Collecting info for {proj_gh_name} from Sonarcloud.")
                analysis_rows = get_activity_from_sq_api(proj_sq_id)
                # Make first analysis come first
                analysis_rows = list(reversed(analysis_rows))
                data = scrape_analysis_values(proj_sq_id, analysis_rows)

                df = pd.DataFrame(data, columns=COLUMNS)
                df.to_csv(fname, index=False)
            else:
                print(f"Collecting nothing for {proj_gh_name} from Sonarcloud.")
    except Exception as e:
        BROWSER.close()
        raise e

    BROWSER.close()


if __name__ == "__main__":

    msg = "Collect project statistics from Sonarcloud."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument(
        "outpath",
        metavar="outpath",
        type=str,
        help="Path",
    )

    args = parser.parse_args()
    main(args.outpath)
