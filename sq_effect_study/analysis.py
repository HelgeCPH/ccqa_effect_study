import pandas as pd
from pydriller import Repository
from sq_effect_study.analyse_sq_history import get_start_weeks_per_proj


cdf = pd.read_csv("experiment/data/input/commits.csv")
cdf[cdf.project == "ratis"]

start_df = get_start_weeks_per_proj("experiment/data/input")

start_df[
    start_df.project_gh.isin(
        ["daffodil", "groovy", "hadoop-ozone", "karaf", "ratis"]
    )
]


sdf = pd.read_csv("experiment/data/input/ratis_jira.csv")

sdf.created = pd.to_datetime(sdf.created, utc=True)


start_df[start_df.project_gh == "ratis"]

sdf[sdf.created >= pd.to_datetime("2020-05-28 10:30:20+00:00")]


sdf[sdf.created >= start_df[start_df.project_gh == "ratis"].date.iloc[0]]
# 428 issues since then

# Find commits that close an issue regarding SQ
q = sdf.description.str.contains("(S|s)onar", na=False, regex=True) & (
    sdf.status == "Resolved"
)
sdf[q].key
# 20 issues that refer to Sonar
# 12 of these are resolved


repo_path = os.path.join(os.environ["HOME"], "case_systems", "ratis")

rows = []
for iss_key in reversed(list(sdf[q].key.values)):
    for commit in Repository(path_to_repo=repo_path).traverse_commits():
        if commit.msg.startswith(f"{iss_key}. "):
            rows.append(
                (
                    commit.hash,
                    commit.author_date,
                    commit.msg,
                )
            )
# There is no commit for [RATIS-1054](https://issues.apache.org/jira/browse/RATIS-1054) since it is a super-task, which is resolved via the four sub-tasks RATIS-1051, RATIS-1052, RATIS-1053, RATIS-1055
# Add commits for these to the analysis, since they do not mention `Sonar`
# Manually check the other issues if they contain subtasks that I am missing so far:
# ['RATIS-1367', 'RATIS-1366', 'RATIS-1365', 'RATIS-1364',
#        'RATIS-1311', 'RATIS-1306', 'RATIS-1075', 'RATIS-1054',
#        'RATIS-953', 'RATIS-950', 'RATIS-948', 'RATIS-940']
# After manual check, the final list is:


iss_keys = [
    "RATIS-940",  # SQ infra
    "RATIS-948",  # SQ infra
    "RATIS-949",
    "RATIS-950",
    "RATIS-952",
    "RATIS-953",
    "RATIS-1051",
    "RATIS-1052",
    "RATIS-1053",
    "RATIS-1054",
    "RATIS-1055",
    "RATIS-1075",
    "RATIS-1306",  # SQ infra
    "RATIS-1311",  # SQ infra
    "RATIS-1364",
    "RATIS-1365",
    "RATIS-1366",
    "RATIS-1367",
]
rows = []
for iss_key in iss_keys:
    for commit in Repository(path_to_repo=repo_path).traverse_commits():
        if commit.msg.startswith(f"{iss_key}. "):
            rows.append(
                (
                    commit.hash,
                    commit.author_date,
                    commit.msg,
                )
            )
# 15 commits are in rows
# [('00f1747a1915f42fd256e9a5b7b8e0131cd06c2c',
#   datetime.datetime(2020, 5, 27, 9, 49, 25, tzinfo=<git.objects.util.tzoffset object at 0x1117f2040>),
#   'RATIS-940. Add sonar check for ratis (#108)'),
#  ('a2f3895396a81ee6e31d6fd1a8a6c8a7bf121dd6',
#   datetime.datetime(2020, 6, 2, 13, 57, 9, tzinfo=<git.objects.util.tzoffset object at 0x101d75d30>),
#   'RATIS-948. Update Sonar statistics only from the apache repo, not from the forks (#114)'),
#  ('43a042a8bbe123bcb5e567af0aeced12eb299290',
#   datetime.datetime(2020, 11, 5, 0, 54, 3, tzinfo=<git.objects.util.tzoffset object at 0x102489fd0>),
#   'RATIS-950. Handle Exceptions appropriately (#115)'),
#  ('02caace296f4414de3eda9f4469dbd806ca594b1',
#   datetime.datetime(2020, 12, 3, 2, 14, 20, tzinfo=<git.objects.util.tzoffset object at 0x1024de190>),
#   'RATIS-953. XML Parsers should not be vulnerable to XXE attacks (#126)\n\n* RATIS-953. XML Parsers should not be vulnerable to XXE attacks\r\n\r\n* RATIS-953. Also explicitly disable external DTD/schema\r\n\r\n* trigger new CI check'),
#  ('cf9ed0864615e82083f6be5f4f958563dbf242ad',
#   datetime.datetime(2020, 9, 8, 21, 10, 32, tzinfo=<git.objects.util.tzoffset object at 0x1015bb130>),
#   'RATIS-1051. Use try-resource-block when saveMd5File (#190)'),
#  ('0d964950e8fdf6887e53e8eb53695a14d29314c9',
#   datetime.datetime(2020, 9, 8, 19, 26, 45, tzinfo=<git.objects.util.tzoffset object at 0x1103653a0>),
#   'RATIS-1052. Fix the testDisconnectLeader assertion'),
#  ('6dd51454994a843fde10933d2ec3daedd6fb36de',
#   datetime.datetime(2020, 9, 8, 21, 12, 29, tzinfo=<git.objects.util.tzoffset object at 0x113a535e0>),
#   'RATIS-1052. Math operands should be cast before assignment (#192)'),
#  ('61f038b6bea2934e910e8504df0d8c79d6d34799',
#   datetime.datetime(2020, 9, 9, 13, 53, 45, tzinfo=<git.objects.util.tzoffset object at 0x10f94e580>),
#   'RATIS-1055. Switch cases should end with an unconditional "break" statement (#193)\n\n* Update GrpcLogAppender.java\r\n\r\nSwitch cases should end with an unconditional "break" statement\r\n\r\n* Add log for UNRECOGNIZED case'),
#  ('9b1d2c18f5677f3d443344e69f98e6c3ac953835',
#   datetime.datetime(2020, 9, 24, 22, 58, 10, tzinfo=<git.objects.util.tzoffset object at 0x113a2bf10>),
#   'RATIS-1075. Classes that implement AutoCloseable should call "close()" when it should be terminated (#208)\n\n* RATIS-1075. Class that implements AutoCloseable should call "close()" when it should be terminated\r\n\r\n* fixup! use try-with-resources\r\n\r\n* address more cases\r\n\r\n* fixup! fix test\r\n\r\n* fixup! fix test\r\n\r\n* fixup! fix test'),
#  ('9d1b711f9d4606145e19a28270b0c50b04dc869b',
#   datetime.datetime(2021, 2, 5, 0, 44, 43, tzinfo=<git.objects.util.tzoffset object at 0x1117e4d90>),
#   'RATIS-1306. Eliminate duplicated GitHub Actions workflow (#415)'),
#  ('87bd1fd1df9f02e83b973291d507ad002bd9d3f4',
#   datetime.datetime(2021, 2, 17, 8, 19, 35, tzinfo=<git.objects.util.tzoffset object at 0x1117be370>),
#   'RATIS-1311. Upgrade Java for Sonar check (#419)'),
#  ('9577d564eeac36cf449843d34b7010b33d634818',
#   datetime.datetime(2021, 5, 5, 14, 31, 11, tzinfo=<git.objects.util.tzoffset object at 0x10267fe20>),
#   'RATIS-1364. Fix Sonar Qube issues in IOUtils (#468).'),
#  ('ff8aa668f1a0569ba5e6b0f30dbd51a673913344',
#   datetime.datetime(2021, 4, 26, 12, 34, 12, tzinfo=<git.objects.util.tzoffset object at 0x1117aa8b0>),
#   'RATIS-1365. Add message for potential NPE in CombinedClientProtocolServerSideTranslatorPB (#467)'),
#  ('d65ca26a0291fc6067f860eff4ff3092d25c0aec',
#   datetime.datetime(2021, 5, 14, 5, 3, 10, tzinfo=<git.objects.util.tzoffset object at 0x102481580>),
#   'RATIS-1366. Fix NPE issues in MetaStateMachine (#471)'),
#  ('040bc52e19a5e36f5710ccd4fc1981e862e691e8',
#   datetime.datetime(2021, 5, 5, 14, 35, 48, tzinfo=<git.objects.util.tzoffset object at 0x10276c4f0>),
#   'RATIS-1367. Add null check for RaftConfigurationImpl (#469)')]


for commit in Repository(path_to_repo=repo_path).traverse_commits():
    if "indbugs" in commit.msg:

        print(
            (
                commit.hash,
                # commit.author_date,
                commit.msg,
            )
        )

# Daffodil has two resolved issues that mention "sonar" (DAFFODIL-2291, DAFFODIL-2300) both are only concerning the setup of the tool
# https://issues.apache.org/jira/browse/DAFFODIL-2291?jql=project%20%3D%20DAFFODIL%20AND%20text%20~%20%22sonar%22%20ORDER%20BY%20priority%20DESC%2C%20updated%20DESC
# There are eight commits that mention "sonar" but only one commit (https://github.com/apache/daffodil/commit/075ed018d786d332deddc5e20169939f95470fef) is addressing issues reported by SQ, where empty methods are filled with comments first after the drop in smells

repo_path = os.path.join(os.environ["HOME"], "case_systems", "daffodil")
for commit in Repository(path_to_repo=repo_path).traverse_commits():
    if "smell" in commit.msg:

        print(
            (
                commit.hash,
                # commit.author_date,
                commit.msg,
            )
        )

# I only find one commit in Daffodil that mentions fixing a code smell


# Check Hadoop Ozone
#
cdf[cdf.project == "hadoop-ozone"]
# There are 39 commits mentioning "sonar"

sdf2 = pd.read_csv("experiment/data/input/hadoop-ozone_jira.csv")
sdf2.created = pd.to_datetime(sdf2.created, utc=True)
q = sdf2.description.str.contains("(S|s)onar", na=False, regex=True) & (
    sdf2.status == "Resolved"
)
sdf2[q]
# There are 96 resolved issues that mention "sonar"
