#
# Copyright 2013 Boundary, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import logging
import urllib2
from base64 import b64encode

LOG = logging.getLogger("zen.boundary.client")

API_ENDPOINT = "https://api.boundary.com"


class EventsApiClient(object):
    def __init__(self, organization_id, api_key, api_endpoint=API_ENDPOINT):
        self.organization_id = organization_id
        self.api_key = api_key
        self.api_endpoint = api_endpoint

    def send_event(self, event):
        url = "/".join((self.api_endpoint, self.organization_id, "events"))
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % b64encode("%s:" % self.api_key),
        }
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug("URL: %s, Headers: %s, Payload: %s", url, headers,
                      json.dumps(event, indent=4, sort_keys=True))
        request = urllib2.Request(url, json.dumps(event), headers=headers)
        try:
            response = urllib2.urlopen(request)
            response_data = response.read()
            if 'Location' not in response.headers:
                LOG.error("Failed to create event in Boundary API: %s (%d), Error: %s",
                          response.msg, response.code, response_data)
            event_id = response.headers['Location'].rsplit('/', 1)[-1]
            return event_id
        except urllib2.HTTPError as e:
            LOG.error("Error sending event to Boundary API: %s (%d), Error: %s\nPayload: %s",
                      getattr(e, "reason", "Unknown Reason"),
                      e.code, e.read(), json.dumps(event, indent=4, sort_keys=True))
            raise
