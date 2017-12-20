
import os
import subprocess
import xml.etree.ElementTree as ET
import time
import sys
import urllib2

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".cache")
CONF_FOLDER = os.path.join(SCRIPT_FOLDER, "conf")


def main(command_word):
    keys = parse_properties_file()
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    broker_version = keys["BROKER_VERSION"]
    destination_url = keys["DESTINATION_URL"]
    print "Requiring ActiveMq version: " + broker_version
    activemq_home = os.path.join(CACHE_FOLDER, broker_version)
    activemq_bin = os.path.join(activemq_home, "bin/activemq")

    if not os.path.isfile(activemq_bin):
        downloaded_artifact = os.path.join(CACHE_FOLDER, "last_download.tar.gz")
        print "artifact: " + downloaded_artifact
        print "Version not found in local cache. Downloading from: " + destination_url

        download_file(destination_url, downloaded_artifact)
        subprocess.call(["tar", "-xvf", downloaded_artifact, "-C", CACHE_FOLDER, "--transform", "s/apache-activemq-//"])

    os.chmod(activemq_bin, 0x755)
    print "Execute: " + activemq_bin
    conf_file = os.path.join(CONF_FOLDER, "activemq.xml")

    extra_opts = "xbean:file:" + conf_file
    if command_word == "stop":
        extra_opts = ""

    activemq_opts = parse_activemq_xml(conf_file)
    os.system("export ACTIVEMQ_OPTS=\"" + activemq_opts + "\"")
    os.system(activemq_bin + " " + command_word + " " + extra_opts)

    if command_word == "start":
        jetty_xml = os.path.join(CONF_FOLDER, "jetty.xml")
        admin_port = parse_jetty_xml(jetty_xml)
        wait_until_port_is_open(admin_port, 5)


def parse_properties_file():
    separator = "="
    keys = {}

    with open(os.path.join(SCRIPT_FOLDER, 'activemq-wrapper.properties')) as f:
        for line in f:
            if separator in line:
                name, value = line.split(separator, 1)
                value = value.replace("${SCRIPT_FOLDER}", SCRIPT_FOLDER)
                if not name.startswith("#"):
                    keys[name.strip()] = value.strip()

    return keys


def download_file(url, file_name):
    output = urllib2.urlopen(url)
    with open(file_name, 'wb') as f:
        f.write(output.read())


def parse_activemq_xml(conf_file):
    tree = ET.ElementTree(file=conf_file)
    root = tree.getroot()

    for managementContext in root.findall('.//{http://activemq.apache.org/schema/core}managementContext'):
        if "connectorHost" in managementContext.attrib:
            jmx_host = managementContext.attrib.get("connectorHost")
            jmx_port = managementContext.attrib.get("connectorPort")
            return "-Dactivemq.jmx.url=service:jmx:rmi:///jndi/rmi://" + jmx_host + ":" + jmx_port + "/jmxrmi"


def parse_jetty_xml(jetty_xml):
    tree = ET.parse(jetty_xml)
    root = tree.getroot()

    for bean in root.findall('.//{http://www.springframework.org/schema/beans}bean'):
        if bean.get("id") == "jettyPort":
            for prop in bean.findall(".//{http://www.springframework.org/schema/beans}property"):
                if prop.get("name") == "port":
                    return prop.get("value")


def wait_until_port_is_open(port, delay):
    n = 0
    while n < 5:
        print "Is application listening on port " + str(port) + "? "
        returncode = subprocess.call("lsof -P -i TCP:" + str(port) + " > /dev/null", shell=True)
        if returncode == 0:
            print "Yes"
            return
        print "No. Retrying in " + str(delay) + " seconds"
        n = n + 1
        time.sleep(delay)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print "run again with the command \"start\" or \"stop\""
