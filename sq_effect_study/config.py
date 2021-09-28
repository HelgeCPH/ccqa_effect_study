from collections import OrderedDict


# This is a mapping from project names on Github
# (https://github.com/apache/<proj_name>) to project names on SonarCloud (https://sonarcloud.io/dashboard?id=<sq_id>)
# The mapping was identified manually using the complete list of Apache Software
# Foundation projects that use SonarCloud:
# https://sonarcloud.io/organizations/apache/projects

# In order as displayed on the SonarCloud page
PROJECTS_SQ = {
    "ant": "ant-master",
    "cxf": "cxf",
    "gora": "apache_gora",
    "groovy": "apache_groovy",
    "iotdb": "apache_incubator-iotdb",
    "isis": "apache_isis",
    "jspwiki": "jspwiki-builder",
    "karaf": "apache_karaf",
    "hadoop-ozone": "hadoop-ozone",
    "pdfbox": "pdfbox-reactor",
    "ratis": "apache-ratis",
    "shiro": "apache_shiro",
    "daffodil": "apache-daffodil",
    # "dolphinscheduler": "apache-dolphinscheduler",
    "knox": "knox-gateway",
    "jmeter": "JMeter",
    "openmeetings": "apache_openmeetings",
    "plc4x": "apache_plc4x",
    "poi": "poi-parent",
    "roller": "roller-master",
    "struts": "apache_struts",
}
PROJECTS_SQ = OrderedDict(sorted(PROJECTS_SQ.items()))

PROJECTS_JIRA = {
    "cxf": "CXF",
    "gora": "GORA",
    "groovy": "GROOVY",
    "iotdb": "IOTDB",
    "isis": "ISIS",
    "jspwiki": "JSPWIKI",
    "karaf": "KARAF",
    "hadoop-ozone": "HDDS",
    "pdfbox": "PDFBOX",
    "ratis": "RATIS",
    "shiro": "SHIRO",
    "daffodil": "DAFFODIL",
    "knox": "KNOX",
    "openmeetings": "OPENMEETINGS",
    "plc4x": "PLC4X",
    "roller": "ROL",
    "struts": "WW",
}
PROJECTS_BUGZILLA = {
    "ant": "Ant",
    "jmeter": "JMeter",
    "poi": "POI",
}
PROJECTS_GH_ISSUES = {
    "dolphinscheduler": "dolphinscheduler",
}
