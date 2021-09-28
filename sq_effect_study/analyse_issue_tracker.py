import os
import argparse
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from sq_effect_study.config import PROJECTS_SQ, PROJECTS_JIRA, PROJECTS_BUGZILLA
from sq_effect_study.analyse_sq_history import get_start_weeks_per_proj


DATA_COLS = ["created_week", "bugs_per_week"]


def create_bug_freq_df(data_path, project, kind="jira"):
    if kind == "jira":
        date_col = "created"
    elif kind == "bugzilla":
        date_col = "Opened"

    df = pd.read_csv(
        os.path.join(data_path, f"{project}_{kind}.csv"),
        parse_dates=[date_col],
        infer_datetime_format=True,
    )
    # The above date parsing does not seem to work properly, therefore
    # cast it to datetimes
    df[date_col] = pd.to_datetime(df[date_col], utc=True)

    if kind == "jira":
        # For JIRA there are labels that indicate if something is a bug
        bug_df = df[df.issue_type == "Bug"].copy()
    elif kind == "bugzilla":
        # In Bugzilla everything is considered a bug
        bug_df = df.copy()
    bug_df["created_week"] = bug_df[date_col].dt.strftime("%Y%W")

    # Returns the amount of bugs per week
    bug_freq = (
        bug_df.groupby("created_week").size().reset_index(name="bugs_per_week")
    )
    bug_freq["project_gh"] = np.full(bug_freq.shape[0], project)

    # TODO: fill week holes with zeros?
    return bug_freq


def plot_bug_freqs_per_proj(df, start_df, figsize=(25, 25)):
    no_projs = df.project_gh.unique().size
    if no_projs >= 5:
        no_cols = 5
    else:
        no_cols = no_projs
    no_rows = int(np.ceil((no_projs / 5)))

    # plt.subplots_adjust(
    #     left=None, bottom=1.5, right=None, top=1.9, wspace=0.2, hspace=0.2
    # )
    fig, axes = plt.subplots(
        nrows=no_rows, ncols=no_cols, figsize=figsize, dpi=80
    )

    idx = 0
    for project_gh, df_proj in df.groupby("project_gh"):
        if no_projs > 5:
            axs = axes[idx // no_cols, idx % no_cols]
        else:
            axs = axes[idx]
        ax = df_proj[DATA_COLS].plot(
            x="created_week",
            ax=axs,
            title=project_gh.replace("-", " ").title(),
            legend=False,
            linewidth=0.5,
        )
        ax.xaxis.set_label_text("")

        try:
            fst_use_dt = start_df[start_df.project_gh == project_gh].date.iloc[
                0
            ]
            ax.axvline(x=fst_use_dt, color="orange", linestyle="--")
        except:
            print(project_gh)

        idx += 1

    plt.tight_layout()
    return fig


def compute_stats(df, start_df):
    projs_to_check = []
    warnings.filterwarnings("ignore")
    for project_gh, df_proj in df.groupby("project_gh"):
        start_dt = pd.to_datetime(
            start_df[start_df.project_gh == project_gh].date.iloc[0]
        )
        lower_dt = np.datetime64(start_dt - pd.DateOffset(years=1))
        upper_dt = np.datetime64(start_dt + pd.DateOffset(years=1))

        # dt = pd.to_datetime(dt, utc=True)

        q = (
            (df.project_gh == project_gh)
            & (df.created_week >= lower_dt)
            & (df.created_week < np.datetime64(start_dt))
        )
        before = df[q].bugs_per_week
        q = (
            (df.project_gh == project_gh)
            & (df.created_week >= np.datetime64(start_dt))
            & (df.created_week < upper_dt)
        )
        after = df[q].bugs_per_week

        stat, p_val = stats.kruskal(before, after)
        significant = False
        if p_val < 0.05:
            significant = True

        change = "increase"
        if before.median() > after.median():
            change = "decrease"
        elif before.median() == after.median():
            change = "none"
        print(
            project_gh.replace("-", " ").title(),
            significant,
            change,
            before.median(),
            after.median(),
            stat,
            p_val,
        )
        if change == "decrease" and significant:
            projs_to_check.append(project_gh)
    return projs_to_check


def get_bug_frequencies_as_df(inpath):
    dfs = []
    for proj_gh in PROJECTS_JIRA.keys():
        try:
            df = create_bug_freq_df(inpath, proj_gh, kind="jira")
            dfs.append(df)
        except FileNotFoundError:
            pass
    for proj_gh in PROJECTS_BUGZILLA.keys():
        try:
            df = create_bug_freq_df(inpath, proj_gh, kind="bugzilla")
            dfs.append(df)
        except FileNotFoundError:
            pass

    df = pd.concat(dfs, ignore_index=True)

    # Convert created week to proper datetime for later plotting
    week_w_day = df.created_week.astype(str) + "1"
    df.created_week = pd.to_datetime(week_w_day, format="%Y%W%w")
    return df


def main(inpath, outpath):
    df = get_bug_frequencies_as_df(inpath)

    start_df = get_start_weeks_per_proj(inpath)
    # week_w_day = start_df.week.astype(str) + "1"
    # start_df.week = pd.to_datetime(week_w_day, format="%Y%W%w")
    fig = plot_bug_freqs_per_proj(df, start_df, figsize=(15, 3))
    fname = "bug_evolve.png"
    fig.savefig(os.path.join(outpath, fname), bbox_inches="tight")

    compute_stats(df, start_df)
    # q = (
    #     (df.project_gh == "daffodil")
    #     | (df.project_gh == "groovy")
    #     | (df.project_gh == "hadoop-ozone")
    # )
    # fig = plot_bug_freqs_per_proj(df[q], start_df, figsize=(15, 3))
    # fname = "bug_evolve_small.png"
    # fig.savefig(os.path.join(outpath, fname), bbox_inches="tight")


if __name__ == "__main__":
    msg = "."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument(
        "inpath",
        metavar="inpath",
        type=str,
        help="Path",
    )
    parser.add_argument(
        "outpath",
        metavar="outpath",
        type=str,
        help="Path",
    )

    args = parser.parse_args()
    main(args.inpath, args.outpath)

    # projects = collect_projects(args.inpath)
    # bug_freqs = get_bug_freqs_per_proj(projects)
    # bug_freqs.to_csv("output/bug_frequencies.csv", index=False)
