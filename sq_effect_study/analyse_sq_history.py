import os
import math
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sq_effect_study.config import PROJECTS_SQ
from sq_effect_study.collect_jira_issues import filter_projects


DATA_COLS = ["date", "no_bugs", "no_code_smells", "no_vulnerabilities"]


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


def get_sq_data_as_df(path, projects):
    """Returns a list of DataFrames with a DataFrame for each project, for
    which a SonarCloud history exists.
    """
    dfs = []
    for proj_gh_name, proj_sq_id in projects.items():
        if proj_sq_id:
            df = pd.read_csv(
                os.path.join(path, f"{proj_gh_name}.csv"),
                parse_dates=["date"],
                infer_datetime_format=True,
            )
            # The above date parsing does not seem to work properly, therefore
            # cast it to datetimes
            df.date = pd.to_datetime(df.date, utc=True)
            df["project_gh"] = np.full(df.shape[0], proj_gh_name)
            dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    return df


def plot_sq_analysis(df, figsize=(25, 25)):
    no_cols = 5
    no_projs = df.project_gh.unique().size
    no_rows = int(np.ceil((no_projs / 5)))
    fig, axes = plt.subplots(
        nrows=no_rows, ncols=no_cols, figsize=figsize, dpi=80
    )

    idx = 0
    for project_gh, df_proj in df.groupby("project_gh"):
        if no_projs > 5:
            axs = axes[idx // no_cols, idx % no_cols]
        else:
            axs = axes[idx]
        ax = df_proj[["date", "no_code_smells"]].plot(
            x="date",
            ax=axs,
            title=project_gh.replace("-", " ").title(),
            legend=False,
            color="green",
        )
        if idx == 0:
            ax.set_ylabel("#code smells")
        ax.tick_params(axis="y", rotation=30)
        ax.set_ylim(
            0,
            df_proj.no_code_smells.max() + (df_proj.no_code_smells.max() / 10),
        )
        # ax.set_yticklabels(
        #     range(0, df_proj.no_code_smells.max()),
        #     fontsize=5,
        # )
        ax.tick_params(axis="both", which="major", labelsize=7)

        ax2 = ax.twinx()
        if idx == 4:
            ax2.set_ylabel("#bugs, #vulnerabilities")
        ax2.tick_params(axis="y", rotation=30)
        ax2.tick_params(axis="both", which="major", labelsize=7)

        df_proj[["date", "no_bugs", "no_vulnerabilities"]].plot(
            x="date", ax=ax2, legend=False
        )

        ax.xaxis.set_label_text("")
        ax2.xaxis.set_label_text("")

        # df_proj[DATA_COLS].plot(
        #     x="date", ax=axes[idx // no_cols, idx % no_cols], title=project_gh
        # )
        idx += 1

    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]

    lines = lines_labels[0][0] + lines_labels[-1][0]
    labels = ["#code smells", "#bugs", "#vulnerabilities"]

    fig.legend(
        lines,
        labels,
        loc="lower center",
        ncol=3,
        bbox_to_anchor=[0.5, -0.08],
    )

    plt.tight_layout()
    return fig


def get_start_weeks_per_proj(inpath):
    df = get_sq_data_as_df(inpath, PROJECTS_SQ)
    start_df = df.groupby("project_gh").date.min().reset_index()
    start_df["week"] = start_df.date.dt.strftime("%Y%W")
    return start_df


# def compute_lin_regression_for(df):

#     try:
#         bug_slope, bug_intercept = np.polyfit(df.index, df.no_bugs, 1)
#         smell_slope, smell_intercept = np.polyfit(
#             df.index, df.no_code_smells, 1
#         )
#         vuln_slope, vuln_intercept = np.polyfit(
#             df.index, df.no_vulnerabilities, 1
#         )
#     except Exception:
#         print("No data...")
#     return (
#         bug_slope,
#         bug_intercept,
#         smell_slope,
#         smell_intercept,
#         vuln_slope,
#         vuln_intercept,
#     )


def main(inpath, outpath):
    projs = {
        k: v for k, v in PROJECTS_SQ.items() if k in filter_projects(inpath)
    }

    df = get_sq_data_as_df(inpath, projs)
    fig = plot_sq_analysis(df, figsize=(15, 3))

    fname = "sq_evolve.png"
    fig.savefig(os.path.join(outpath, fname), bbox_inches="tight")


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
