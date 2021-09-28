import os
import re
import argparse
from pydriller import Repository
from sq_effect_study.config import PROJECTS_SQ
import pandas as pd


PATTERN = "[Ss]onar"


def collect_sq_commits(projs_to_check, outpath):
    rows = []
    gh_repos = [f"https://github.com/apache/{el}.git" for el in projs_to_check]
    pattern = re.compile(PATTERN)

    repo_path = os.path.join(os.environ["HOME"], "case_systems")

    for commit in Repository(
        path_to_repo=gh_repos, clone_repo_to=repo_path
    ).traverse_commits():
        if re.search(pattern, commit.msg):
            rows.append(
                (
                    commit.project_name,
                    commit.hash,
                    commit.author_date,
                    commit.msg,
                )
            )

    df = pd.DataFrame(rows, columns=["project", "c_hash", "date", "msg"])
    df.to_csv(os.path.join(outpath, "commits.csv"), index=False)
    return df


def main(outpath):

    projs_to_check = list(PROJECTS_SQ.keys())
    commits_df = collect_sq_commits(projs_to_check, outpath)
    commits_df.to_csv(os.path.join(outpath, "commits.csv"), index=False)

    # commits_df.groupby("project").date.min()
    # Out[99]:
    # project
    # project
    # ant             2016-12-18 16:11:31+01:00
    # cxf             2009-08-20 02:36:47+00:00
    # daffodil        2020-02-07 10:11:23-05:00
    # gora            2014-08-29 11:13:06-07:00
    # groovy          2020-03-22 07:05:26+08:00
    # hadoop-ozone    2019-11-14 09:20:54-08:00
    # iotdb           2019-01-18 15:36:50+01:00
    # isis            2013-03-04 23:30:13+00:00
    # jmeter          2016-12-18 11:12:17+00:00
    # jspwiki         2012-07-04 20:21:09+00:00
    # karaf           2020-10-04 14:07:45+02:00
    # knox            2018-12-12 11:28:40-05:00
    # openmeetings    2017-09-28 10:56:13+07:00
    # pdfbox          2015-01-29 18:08:54+00:00
    # plc4x           2017-12-22 22:53:55+01:00
    # poi             2013-10-14 19:44:30+00:00
    # ratis           2020-05-27 09:49:25-04:00
    # roller          2013-07-18 11:34:56+00:00
    # shiro           2016-11-10 13:41:25-05:00
    # struts          2013-09-10 12:12:37+00:00

    # commits_df = collect_sq_commits(PROJECTS_SQ.keys(), outpath)
    # PROJECTS_SQ.keys()
    # cdf[cdf.project == "ant"]


if __name__ == "__main__":
    msg = "."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument(
        "outpath",
        metavar="outpath",
        type=str,
        help="Path",
    )

    args = parser.parse_args()
    main(args.outpath)
