import requests
import xml.etree.ElementTree as ET
import hashlib
from os import path
import os

verbose = False

agent_group = 'com.contrastsecurity'
agent_group_path = agent_group.replace('.', '/')
agent_artifact = 'contrast-agent'
artifact_root_url = 'https://repo1.maven.org/maven2/{}/{}/'.format(agent_group_path, agent_artifact)
metadata_url = artifact_root_url + 'maven-metadata.xml'
jar_url_format = artifact_root_url + '{0}/contrast-agent-{0}.jar'
sha1_url_format = artifact_root_url + '{0}/contrast-agent-{0}.jar.sha1'
jar_name_format = 'contrast-agent-{0}.jar'
jar_dir = 'data'

def get_response_or_raise(url):
    response = requests.get(url)
    if response.status_code == 200:
        if verbose:
            print('GET ' + url + ' returns:')
            print(response)
        return response
    else:
        msg = 'GET ' + url + ' returns HTTP status: ' + str(response.status_code)
        if verbose:
            print(msg)
        raise Exception(msg)

def agent_repo_metadata_xml():
    response = get_response_or_raise(metadata_url)
    return response.content

def agent_metadata_summary():
    metadata_xml = agent_repo_metadata_xml()
    if verbose:
        print(metadata_xml)
    metadata = ET.fromstring(metadata_xml)
    group = metadata.find('groupId').text
    artifact = metadata.find('artifactId').text
    versioning = metadata.find('versioning')
    latest = versioning.find('latest').text
    versions = [version.text for version in versioning.find('versions')]
    return group, artifact, latest, versions

def download_verified_agent(version, to_dir=''):
    sha1_url = sha1_url_format.format(version)
    sha1 = get_response_or_raise(sha1_url).content.decode();
    if verbose:
        print("sha1: " + str(sha1))

    jar_name = jar_name_format.format(version)
    jar_path = path.join(os.getcwd(), path.join(jar_dir, jar_name))
    existing_jar = existing_agent_download(jar_path)
    if existing_jar:
        if valid_content(sha1, existing_jar):
            if verbose:
                print("Valid jar {} already exists.".format(jar_path))
            return jar_path
        else:
            print("Removing invalid jar at {}".format(jar_path))
            os.remove(jar_path)

    jar_url = jar_url_format.format(version)
    jar_resp = get_response_or_raise(jar_url);
    if verbose:
        print("jar_resp: " + str(jar_resp))
    jar_content = jar_resp.content
    if not valid_content(sha1, jar_content):
        raise Exception("Downloaded JAR sha1 does not match published sha1")
    with open(jar_path, mode="wb") as jar:
        jar.write(jar_content)
        if verbose:
            print("Saved " + jar.name)
    return jar_path

def valid_content(sha1, jar_content):
    hasher = hashlib.sha1()
    hasher.update(jar_content)
    jar_hash = hasher.hexdigest()
    if jar_hash != sha1:
        print("Agent JAR validation failed!")
        print("published sha1: " + str(sha1))
        print("content   sha1: " + str(jar_hash))
    elif verbose:
        print("published sha1: " + str(sha1))
        print("content   sha1: " + str(jar_hash))
    return jar_hash == sha1

def existing_agent_download(jar_path):
    if not path.isfile(jar_path):
        return None
    with open(jar_path, mode="rb") as jar:
        jar_content = jar.read()
        if verbose:
            print("Found existing jar {} of size {}".format(jar_path, str(len(jar_content))))
        return jar_content

def get_latest_agent():
    group, artifact, latest, versions = agent_metadata_summary()
    jar_path = download_verified_agent(latest)
    return jar_path

if __name__ == '__main__':
    group, artifact, latest, versions = agent_metadata_summary()
    if verbose:
        print ('group: {}, artifact: {}, latest: {}'.format(group, artifact, latest))
        print('avalable versions: ' + str(versions))
    jar_path = get_latest_agent()
    print("Validated Agent JAR exists at " + jar_path)
