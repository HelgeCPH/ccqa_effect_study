"""This script collects automatically analyzes repositories from the Apache 
Software Foundation for signs of use of SonarQube or SonarCloud

Potential projects are printed to stdout in the form of:

```
thrift https://github.com/apache/thrift
jmeter https://github.com/apache/jmeter
sirona https://github.com/apache/sirona
helix https://github.com/apache/helix
struts https://github.com/apache/struts
ant https://github.com/apache/ant
kylin https://github.com/apache/kylin
samza https://github.com/apache/samza
rocketmq https://github.com/apache/rocketmq
daffodil https://github.com/apache/daffodil
rocketmq-spring https://github.com/apache/rocketmq-spring
iotdb https://github.com/apache/iotdb
servicecomb-toolkit https://github.com/apache/servicecomb-toolkit
```

These, are analyzed manually for inclusion in `config.py`
"""
import sys
from os import getenv
from github import Github
from dateutil.parser import parse


INCLUSION_DATE = parse("1. Jan 2020")


def filter_criteria(repo):
    if "incubator" in repo.name:
        # No incubator project
        return False
    if repo.updated_at < INCLUSION_DATE:
        # Is still active, which means it has an update in 2020
        return False
    if "-site" in repo.name:
        # No website project
        return False
    if "-website" in repo.name:
        # No website project
        return False
    if repo.stargazers_count < 50:
        # Project has to be reasonable popular
        return False

    sonar_file = False
    try:
        # Check if the project contains a SonarQube configuration
        # Check it at the end as it is expensive
        repo.get_contents("sonar-project.properties")
        sonar_file = True
    except:
        pass

    try:
        # Check if the project contains a Maven Configuration that points
        # to something SonarQube related
        pom_contents = repo.get_contents("pom.xml").decoded_content
        if b"<sonar.host.url>" in pom_contents:
            sonar_file = True
    except:
        pass

    try:
        # Check if the project contains a Maven Configuration that points
        # to something SonarQube related
        travis_contents = repo.get_contents(".travis.yml").decoded_content
        if b"sonarcloud:" in travis_contents:
            sonar_file = True
    except:
        pass

    try:
        # Check if the project contains a Maven Configuration that points
        # to something SonarQube related
        gradle_contents = repo.get_contents("gradle.properties").decoded_content
        if b"org.sonarqube.version" in gradle_contents:
            sonar_file = True
    except:
        pass

    if not sonar_file:
        return False
    return True


def collect_possible_repos():
    if not getenv("GITHUB_API_KEY"):
        sys.exit("GITHUB_API_KEY must be set as environment variable")
    g = Github(login_or_token=getenv("GITHUB_API_KEY"))
    repos = [r for r in g.get_organization("apache").get_repos()]

    return list(filter(filter_criteria, repos))


def main():
    repos = collect_possible_repos()
    for r in repos:
        print(r.name, r.html_url)


if __name__ == "__main__":
    main()
