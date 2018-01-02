
import os
import subprocess
import xml.etree.ElementTree as ET
import time
import sys
import urllib2
import socket
import platform
import tarfile
import zipfile


SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".cache")
CONF_FOLDER = os.path.join(SCRIPT_FOLDER, "conf")

# ~~~~ The list of ports:  (see activemq.xml)
# Openwire: 21616
# AMQP:     25672
# STOMP:    21613
# MQTT:     21883
# WS:       21614
#
# WebConsole: 28161
# JMX port: 20011  jmxDomainName=activemq.test.instance -> TEST.BROKER


def main(command_word):
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    broker_version = "5.11.1"
    if "Windows" in platform.system():
        destination_url = "http://archive.apache.org/dist/activemq/5.11.1/apache-activemq-5.11.1-bin.zip"
        is_shell = True
    else:
        destination_url = "http://archive.apache.org/dist/activemq/5.11.1/apache-activemq-5.11.1-bin.tar.gz"
        is_shell = False

    print "Requiring ActiveMq version: " + broker_version
    activemq_home = os.path.join(CACHE_FOLDER, broker_version)
    activemq_bin = os.path.join(activemq_home, "bin", "activemq")

    if not os.path.isfile(activemq_bin):
        downloaded_file_name=destination_url[destination_url.rfind("/")+1:]
        downloaded_artifact = os.path.join(CACHE_FOLDER, downloaded_file_name)
        print "artifact: " + downloaded_artifact
        print "Version not found in local cache. Downloading from: " + destination_url

        download_and_show_progress(destination_url, downloaded_artifact)
        print "The contents of the cache folder: " + ', '.join(os.listdir(CACHE_FOLDER))

        # Extract
        extract_archive(downloaded_artifact, CACHE_FOLDER)
        os.rename(os.path.join(CACHE_FOLDER, "apache-activemq-"+broker_version), activemq_home)

    os.chmod(activemq_bin, 0x755)
    conf_file = os.path.join(CONF_FOLDER, "activemq.xml")

    conf_file_java_uri = conf_file.replace("\\", "/")
    extra_opts = "xbean:file:" + conf_file_java_uri
    if command_word == "stop":
        extra_opts = ""

    proc = execute({'ACTIVEMQ_OPTS': parse_activemq_xml(conf_file)},
            [activemq_bin, command_word, extra_opts], is_shell)

    if command_word == "start":
        jetty_xml = os.path.join(CONF_FOLDER, "jetty.xml")
        admin_port = parse_jetty_xml(jetty_xml)
        wait_until_port_is_open(admin_port, 5)
        proc.terminate()

    proc.wait()
    sys.exit()


def execute(my_env, command, is_shell):
    env_copy = os.environ.copy()
    env_copy.update(my_env)
    print "Execute: " + " ".join(command)
    return subprocess.Popen(command, env=env_copy, shell=is_shell)


def extract_archive(archive, to_folder):
    if archive.endswith("zip"):
        zip_ref = zipfile.ZipFile(archive, 'r')
        zip_ref.extractall(to_folder)
        zip_ref.close()
    else:
        tar = tarfile.open(archive)
        tar.extractall(to_folder)
        tar.close()


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

    # Force flush the file to ensure it is written
    f.flush()
    os.fsync(f.fileno())
    f.close()


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
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', int(port)))
        if result == 0:
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
