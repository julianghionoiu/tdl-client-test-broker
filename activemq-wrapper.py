
import os
import subprocess
import xml.etree.ElementTree as ET
import time
import urllib2
import sys

BROKER_VERSION = "5.11.1"
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
DESTINATION_URL = "file://" + SCRIPT_FOLDER + "/local-distributions/apache-activemq-" + BROKER_VERSION + "-bin.tar.gz"
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".cache")
CONF_FOLDER = os.path.join(SCRIPT_FOLDER, "conf")


def download_and_show_progress(url, file_name):
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print status,

    f.close()


def wait_until_port_is_open(port, delay):
    print "hit wait_until_port_is_open"
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


def main(command):
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    print "Requiring ActiveMq version: " + BROKER_VERSION
    activemq_home = os.path.join(CACHE_FOLDER, BROKER_VERSION)
    activemq_bin = os.path.join(activemq_home, "bin/activemq")

    if not os.path.isfile(activemq_bin):
        downloaded_artifact = os.path.join(CACHE_FOLDER, "last_download.tar.gz")
        print "artifact: " + downloaded_artifact
        print "Version not found in local cache. Downloading from: " + DESTINATION_URL

        download_and_show_progress(DESTINATION_URL, downloaded_artifact)
        subprocess.call(["tar", "-xvf", downloaded_artifact, "-C", CACHE_FOLDER, "--transform", "s/apache-activemq-//"])

    os.chmod(activemq_bin, 0x755)
    print "Execute: " + activemq_bin
    conf_file = os.path.join(CONF_FOLDER, "activemq.xml")

    extra_opts = "xbean:file:" + conf_file
    if command == "stop":
        extra_opts = ""

    activemq_opts = parse_activemq_xml(conf_file)
    os.system("export ACTIVEMQ_OPTS=\"" + activemq_opts + "\"")
    os.system(activemq_bin + " " + command + " " + extra_opts)

    if command == "start":
        jetty_xml = os.path.join(CONF_FOLDER, "jetty.xml")
        admin_port = parse_jetty_xml(jetty_xml)
        wait_until_port_is_open(admin_port, 5)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print "run again with the command \"start\" or \"stop\""
