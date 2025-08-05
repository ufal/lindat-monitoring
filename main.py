#!/usr/bin/python3
import urllib3
import requests
import json
from urllib.parse import urlsplit
from pprint import pprint
import os

SHORTREF_API_URL = "https://lindat.mff.cuni.cz/repository/server/api/services/handles/magic"
ICINGA_API = "https://localhost:5665/v1"

#/usr/lib/python3/dist-packages/urllib3/connectionpool.py:794: InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.org/en/latest/security.html
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_handles():
    with requests.session() as s:
        handles = []
        s.headers.update({'Accept': 'application/json'})
        r = s.get(SHORTREF_API_URL)
        for handle in r.json():
            handles.append(handle)
    return handles

def get_config():
    js = json.load(open(os.path.join(os.path.abspath(os.path.dirname(__file__))) + "/settings.json", mode="r"))
    return (js["username"], js["password"], False)


def addToMonitoring(handles):
    (login, password, verify) = get_config()
    with requests.session() as s:
        s.headers.update({'Accept': 'application/json'})
        s.auth = (login, password)
        s.verify = verify
        #r = s.get(ICINGA_API)
        #pprint(r.json())
        #r = s.get(ICINGA_API + '/objects/checkcommands')
        #pprint(list(map((lambda x: x["name"]), r.json()['results'])))
        hostname = 'shortref_handles'

        #It should be ok to delete and recreate, question is what does it do to check intervals...
	#seems it resets them
        #r = s.delete(ICINGA_API + '/objects/hosts/' + hostname, params={'cascade':1})
        #print(r.json())

        attrs = {'attrs': {'check_command': 'dummy'}}
        r = s.put(ICINGA_API + '/objects/hosts/' + hostname, data=json.dumps(attrs))
        if r.status_code != requests.codes.ok and "already exists" not in r.json()["results"][0]["errors"][0]:
            print(r.json())

        #also add ports, handle empty paths, etc.
        for handle in handles:
            handle_id = urlsplit(handle["handle"]).path[1:]
            id = handle_id.replace('/', '_')
            url = urlsplit(handle["url"])
            target_hostname = url.hostname
            path = url.path or "/"
            path = path + '?' + url.query if url.query else path
            path = path + '#' + url.fragment if url.fragment else path
            ssl = True if url.scheme == 'https' else ""
            port = url.port if url.port else ""
            auth = url.username + ':' + url.password if url.username and url.password else ""

            attrs ={'vars.http_vhost': target_hostname, 
                    'vars.http_uri': path,
                    'vars.http_ssl': ssl,
                    'vars.http_port': port,
                    'vars.http_auth': auth,
                    'vars.handle': '/' + handle_id,
                   }

            service_url = ICINGA_API + '/objects/services/' + hostname + '!' + id
            r = s.get(service_url)
            if r.status_code == requests.codes.ok:
                service_vars = r.json()["results"][0]["attrs"]["vars"]
                for var in ["vhost", "uri", "ssl", "port", "auth"]:
                        var = "http_" + var
                        if attrs['vars.' + var] != service_vars[var]:
                            data = {'attrs':attrs}
                            print("Updating " + handle_id)
                            r = s.post(service_url, data=json.dumps(data))
                            print(r.json())
                            break
            else:
                data = {'templates': ["shortref-handle-service"],
                        'attrs':attrs
                      }
            
                print("Creating " + handle_id)
                r = s.put(service_url, data=json.dumps(data))
                print(r.json())


if __name__ == '__main__':
    handles = get_handles()

    #pprint(handles)
    addToMonitoring(handles)
