import os
import re
import pandas as pd
from pydriller import Repository
from sq_effect_study.analyse_sq_history import get_start_weeks_per_proj


PATTERN = "[Ss]onar"


def identify_sonar_issues(sys_name):
    issues_path = f"experiment/data/input/{sys_name}_jira.csv"
    sdf = pd.read_csv(issues_path)
    sdf.created = pd.to_datetime(sdf.created, utc=True)

    q = sdf.description.str.contains(PATTERN, na=False, regex=True) & (
        sdf.status == "Resolved"
    )

    rsdf = sdf[q][:]
    rsdf["project"] = [sys_name] * rsdf.shape[0]
    return rsdf


def identify_sonar_commits(sys_name):
    rows = []
    pattern = re.compile(PATTERN)

    repo_path = os.path.join(os.environ["HOME"], "case_systems", sys_name)

    for commit in Repository(path_to_repo=repo_path).traverse_commits():
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
    return df


def identify_commits_for_issue(iss_key, sys_name):
    repo_path = os.path.join(os.environ["HOME"], "case_systems", sys_name)

    if sys_name == "daffodil":
        # Daffodil puts ticket references in the end of the message, if at all
        pattern = re.compile(f"{iss_key}$")
    elif sys_name in ["hadoop-ozone", "ratis"]:
        pattern = re.compile(f"{iss_key}\. ")
    elif sys_name == "groovy":
        pattern = re.compile(f"{iss_key}[:,]")
    elif sys_name == "karaf":
        pattern = re.compile(f"\[{iss_key}\]")

    rows = []
    for commit in Repository(path_to_repo=repo_path).traverse_commits():
        if re.search(pattern, commit.msg):
            rows.append(
                (
                    sys_name,
                    iss_key,
                    commit.hash,
                    commit.author_date,
                    commit.msg,
                )
            )
    cols = ["project", "iss_key", "c_hash", "date", "msg"]
    df = pd.DataFrame(rows, columns=cols)
    return df


def print_start_days():
    start_df = get_start_weeks_per_proj("experiment/data/input")

    start_df[
        start_df.project_gh.isin(
            ["daffodil", "groovy", "hadoop-ozone", "karaf", "ratis"]
        )
    ]
    print(start_df)


def main():
    systems = ["daffodil", "groovy", "hadoop-ozone", "karaf", "ratis"]
    sdfs = []
    for sys_name in systems:
        sdf = identify_sonar_issues(sys_name)
        no_resolved_sonar_iss = sdf.shape[0]
        print(
            f"Number of resolved issues that mention `[Ss]onar for {sys_name}: {no_resolved_sonar_iss}"
        )
        sdfs.append(sdf)
    sdf = pd.concat(sdfs)

    cdfs = []
    for _, (proj, iss_key) in sdf[["project", "key"]].iterrows():
        print(proj, iss_key)
        cdf = identify_commits_for_issue(iss_key, proj)
        cdfs.append(cdf)
    cdf = pd.concat(cdfs)

    for proj, groupcdf in cdf.groupby("project"):
        print(proj, groupcdf.shape[0])

    # For Ratis do a more thorough analysis
    iss_keys = list(sdf[sdf.project == "ratis"].key.values) + [
        "RATIS-1051",
        "RATIS-1052",
        "RATIS-1053",
        "RATIS-1055",
        "RATIS-949",  # The latter two issues are still open (14. Jun. 21)
        "RATIS-952",  # Therefore, do not add them to this list
    ]
    # [f"https://issues.apache.org/jira/browse/{i}" for i in iss_keys]

    ratis_cdfs = []
    for iss_key in iss_keys:
        ratis_cdf = identify_commits_for_issue(iss_key, "ratis")
        ratis_cdfs.append(ratis_cdf)
    ratis_cdf = pd.concat(ratis_cdfs)

    ratis_cdf["gh_url"] = [
        f"https://github.com/apache/ratis/commit/{c}"
        for c in ratis_cdf.c_hash.values
    ]

    # Serialize Ratis_Results.csv

    c_ratio, cdf_after_sq = compute_sonar_commit_ratio(
        ratis_cdf, proj_name="ratis"
    )


def compute_sonar_commit_ratio(cdf, proj_name="ratis"):
    start_df = get_start_weeks_per_proj("experiment/data/input")
    start_dt = start_df[start_df.project_gh == proj_name].iloc[0].date

    repo_path = os.path.join(os.environ["HOME"], "case_systems", proj_name)

    rows = []
    for commit in Repository(path_to_repo=repo_path).traverse_commits():
        if commit.author_date >= start_dt:
            rows.append(
                (
                    commit.hash,
                    commit.author_date,
                    commit.msg,
                )
            )
    cols = ["c_hash", "date", "msg"]
    df = pd.DataFrame(rows, columns=cols)
    sonar_commit_ratio = cdf.shape[0] / df.shape[0]

    return sonar_commit_ratio, df


if __name__ == "__main__":
    main()
