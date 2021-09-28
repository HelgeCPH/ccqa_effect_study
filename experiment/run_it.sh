# Collect Apache projects that potentially use SonarQube
# python sq_effect_study/collect_apache_repos.py


# Firefox webdriver for Selenium has to be installed
# Since the data is collected via webscraping, the process of data collection 
# takes some time
python sq_effect_study/collect_sq_data.py data/input



mkdir $HOME/case_systems
# This will clone the repositories to $HOME/case_systems
python sq_effect_study/collect_gh_repos.py data/input


# This takes some minutes to complete
python sq_effect_study/collect_jira_issues.py --filter data/input

# This creates an overview plot `sq_evolve.png`
python sq_effect_study/analyse_sq_history.py data/input data/output
# This creates an overview plot `bug_evolve.png`
python sq_effect_study/analyse_issue_tracker.py data/input data/output


echo "Analyzed version of daffodil:" > data/output/daffodil_scc.txt
git -C $HOME/case_systems/daffodil/ rev-parse HEAD >> data/output/daffodil_scc.txt
echo "-----------------------------" >> data/output/daffodil_scc.txt
scc $HOME/case_systems/daffodil/ >> data/output/daffodil_scc.txt

echo "Analyzed version of groovy:" > data/output/groovy_scc.txt
git -C $HOME/case_systems/groovy/ rev-parse HEAD >> data/output/groovy_scc.txt
echo "-----------------------------" >> data/output/groovy_scc.txt
scc $HOME/case_systems/groovy/ >> data/output/groovy_scc.txt

echo "Analyzed version of hadoop-ozone:" > data/output/hadoop-ozone_scc.txt
git -C $HOME/case_systems/hadoop-ozone/ rev-parse HEAD >> data/output/hadoop-ozone_scc.txt
echo "-----------------------------" >> data/output/hadoop-ozone_scc.txt
scc $HOME/case_systems/hadoop-ozone/ >> data/output/hadoop-ozone_scc.txt

echo "Analyzed version of karaf:" > data/output/karaf_scc.txt
git -C $HOME/case_systems/karaf/ rev-parse HEAD >> data/output/karaf_scc.txt
echo "-----------------------------" >> data/output/karaf_scc.txt
scc $HOME/case_systems/karaf/ >> data/output/karaf_scc.txt

echo "Analyzed version of ratis:" > data/output/ratis_scc.txt
git -C $HOME/case_systems/ratis/ rev-parse HEAD >> data/output/ratis_scc.txt
echo "-----------------------------" >> data/output/ratis_scc.txt
scc $HOME/case_systems/ratis/ >> data/output/ratis_scc.txt

