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

import logging
import socket
from datetime import datetime

import Globals
from Products.ZenModel.actions import IActionBase
from Products.ZenModel.interfaces import IAction
from Products.ZenUtils.Utils import unused
from Products.Zuul.infos import InfoBase
from Products.Zuul.infos.actions import ActionFieldProperty
from .client import EventsApiClient
from .interfaces import IBoundaryEventContentInfo
from zope.interface import implements

unused(Globals)

LOG = logging.getLogger('zen.boundary.actions')

STATUS_MAP = {
    0: "OPEN",
    1: "ACKNOWLEDGED",
    2: "OPEN",  # No mapping for suppressed state
}

SEVERITY_MAP = {
    0: "INFO",
    1: "INFO",
    2: "INFO",
    3: "WARN",
    4: "ERROR",
    5: "CRITICAL",
}

OPTIONAL_EVENT_FIELDS = [
    'current_user_uuid',
    'current_user_name',
    'cleared_by_event_uuid',
]

OPTIONAL_OCCURRENCE_FIELDS = [
    'fingerprint',
    'event_class',
    'event_class_key',
    'event_class_mapping_uuid',
    'event_key',
    'event_group',
    'agent',
    'syslog_priority',
    'syslog_facility',
    'nt_event_code',
    'monitor',
]

FQDN = socket.getfqdn()


def truncate_to_length(value, length):
    if len(value) > length:
        value = value[:length-3] + "..."
    return value


def convert_time(zenoss_event_time):
    """
    Converts a Zenoss event time (represented as milliseconds since Unix epoch)
    to a UTC ISO date/time.

    >>> convert_time(1387407078321)
    '2013-12-18T22:51:18.321Z'
    """
    dt = datetime.utcfromtimestamp(zenoss_event_time/1000.0)
    return "%s.%03dZ" % (dt.strftime("%Y-%m-%dT%H:%M:%S"), dt.microsecond/1000)


class BoundaryEventAction(IActionBase):
    implements(IAction)

    id = "boundary_event_adapter"
    name = "Boundary"
    actionContentInfo = IBoundaryEventContentInfo
    shouldExecuteInBatch = False

    def __init__(self):
        self.dmd = None

    def setupAction(self, dmd):
        self.dmd = dmd

    def convert_zenoss_event(self, signal):
        zenoss_event = signal.event
        occurrence = zenoss_event.occurrence[0]
        actor = occurrence.actor
        source_ref = actor.element_uuid if actor.element_uuid else actor.element_identifier
        source_name = actor.element_title if actor.element_title else actor.element_identifier
        status = 'CLOSED' if signal.clear else STATUS_MAP.get(zenoss_event.status, 'OPEN')
        event = {
            'title': truncate_to_length(occurrence.summary, 255),
            'source': {
                'ref': source_ref,
                'type': 'host',  # TODO: Support additional Zenoss types?
                'name': source_name,
            },
            'sender': {
                'ref': FQDN,
                'type': 'zenoss',
                'properties': {
                    'version': getattr(self.dmd, 'version', 'Zenoss (unknown)'),
                },
            },
            'properties': {
                'uuid': zenoss_event.uuid,
                'status_change_time': convert_time(zenoss_event.status_change_time),
                'first_seen_time': convert_time(zenoss_event.first_seen_time),
                'last_seen_time': convert_time(zenoss_event.last_seen_time),
                'update_time': convert_time(zenoss_event.update_time),
            },
            'fingerprintFields': ['uuid'],
            'status': status,
            'severity': SEVERITY_MAP.get(occurrence.severity, 'INFO'),
            'createdAt': convert_time(occurrence.created_time),
        }
        if occurrence.HasField('message'):
            event['message'] = truncate_to_length(occurrence.message, 255)

        # Add fields from top-level event
        for optional_event_field in OPTIONAL_EVENT_FIELDS:
            if zenoss_event.HasField(optional_event_field):
                event['properties'][optional_event_field] = getattr(zenoss_event, optional_event_field)

        # Add fields from event actor
        for optional_actor_field in actor.DESCRIPTOR.fields_by_name.keys():
            if actor.HasField(optional_actor_field):
                event['properties'][optional_actor_field] = getattr(actor, optional_actor_field)

        # Add fields from event occurrence
        for optional_occurrence_field in OPTIONAL_OCCURRENCE_FIELDS:
            if occurrence.HasField(optional_occurrence_field):
                event['properties'][optional_occurrence_field] = getattr(occurrence, optional_occurrence_field)

        # Add event details
        for event_detail in occurrence.details:
            name, value = event_detail.name, event_detail.value
            if len(value) == 1:
                event['properties'][name] = value[0]
            else:
                event['properties'][name] = list(value)

        # TODO: tags/notes/audit_log?
        return event

    def execute(self, notification, signal):
        LOG.info("Notification: %s, Signal: %s", notification, signal)
        organization_id = notification.content.get('organization_id')
        if not organization_id:
            raise ValueError(
                'Boundary Organization ID not specified on notification: %s' % notification.getPrimaryId())

        api_key = notification.content.get('api_key')
        if not api_key:
            raise ValueError(
                'Boundary API Key not specified on notification: %s' % notification.getPrimaryId())

        client = EventsApiClient(organization_id, api_key)
        boundary_event = client.send_event(self.convert_zenoss_event(signal))
        LOG.info("Created event '%s' in Boundary for Zenoss event '%s'", boundary_event, signal.event.uuid)

    def updateContent(self, content=None, data=None):
        LOG.info("Update Content: %s, %s", content, data)
        updates = {}
        for k in ('organization_id', 'api_key'):
            v = data.get(k)
            updates[k] = v.strip() if v else v

        content.update(updates)


class BoundaryEventContentInfo(InfoBase):
    implements(IBoundaryEventContentInfo)

    organization_id = ActionFieldProperty(IBoundaryEventContentInfo, 'organization_id')
    api_key = ActionFieldProperty(IBoundaryEventContentInfo, 'api_key')
