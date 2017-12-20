
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
    n = 0
    while n < 5:
        print "Is application listening on port " + str(port) + "? "
        returncode = subprocess.call("lsof", "-P", "-i", "TCP:" + str(port), ">", "/dev/null")
        if returncode == 0:
            print "Yes"
            return
        print "No. Retrying in " + str(delay) + "seconds"
        n = n + 1
        time.sleep(delay)


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

    tree = ET.parse(conf_file)
    root = tree.getroot()

    for managementContext in root.iter('managementContext'):
        jmx_host = managementContext.attrib.connectorHost
        jmx_port = managementContext.attrib.connectorPort
        activemq_opts = "-Dactivemq.jmx.url=service:jmx:rmi:///jndi/rmi://" + jmx_host + ":" + jmx_port + "/jmxrmi"
        os.system("export ACTIVEMQ_OPTS=\"" + activemq_opts + "\"")

    print activemq_bin + " " + command + " " + extra_opts
    os.system(activemq_bin + " " + command + " " + extra_opts)

    if command == "start":
        jetty_xml = os.path.join(CONF_FOLDER, "jetty.xml")
        tree = ET.parse(jetty_xml)
        root = tree.getroot()
        for bean in root.iter("bean"):
            if bean.id == "jettyPort":
                for prop in bean.iter("property"):
                    if prop.name == "port":
                        admin_port = prop.value
                        wait_until_port_is_open(admin_port)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print "run again with the command \"start\" or \"stop\""
