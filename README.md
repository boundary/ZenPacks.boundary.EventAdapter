# Zenoss 4.x Boundary Event Adapter

This ZenPack provides the ability to forward selected events from a Zenoss 4.x system to Boundary's Events API.

## Installation

All commands below should be run as the `zenoss` user on the Zenoss master.

From a packaged ZenPack .egg:

```sh
$ zenpack --install ZenPacks.boundary.EventAdapter-[version].egg
```

From source:

```sh
$ git clone git@github.com:boundary/ZenPacks.boundary.EventAdapter.git
$ zenpack --install ZenPacks.boundary.EventAdapter
```

After installing the ZenPack, restart Zenoss as the zenoss user:

```sh
$ zenoss restart
```

## Configuration

To configure the ZenPack, perform the following steps:

 * Log into Zenoss and navigate to Events -> Triggers.
 * If you have not defined a Trigger (to match events to forward to Boundary), create one now. The examples below describe how to create a trigger that forwards all events with severity >= WARNING to Boundary. 

![add trigger](https://github.com/boundary/ZenPacks.boundary.EventAdapter/raw/master/img/add_trigger.png)
![edit trigger](https://github.com/boundary/ZenPacks.boundary.EventAdapter/raw/master/img/edit_trigger.png)

 * Click the 'Notifications' link on the left-hand side.
 * Click the '+' icon to create a new Notification.
 * Give the notification a unique name (i.e. 'BoundaryEvent'). Choose 'Boundary' in the 'Action' drop-down.

![add trigger](https://github.com/boundary/ZenPacks.boundary.EventAdapter/raw/master/img/add_notification.png)
 
 * Click 'Submit' to create the notification.
 * Double click on the notification to open the detailed preferences window. Make the following changes:
   * Notification Tab:
     * Check the 'Enabled' checkbox.
     * Check the 'Send Clear' checkbox.
     * Add one or more 'Triggers' which control the types of events to forward to Boundary. ![edit notification](https://github.com/boundary/ZenPacks.boundary.EventAdapter/raw/master/img/edit_notification.png)
   * Content Tab:
     * Enter the Boundary Organization and Boundary API Key (both fields are required). ![edit notification content](https://github.com/boundary/ZenPacks.boundary.EventAdapter/raw/master/img/edit_notification_content.png)
 * Click 'Submit' to save the settings for the notification.

## Release Notes

1.0.0 - [ZenPacks.boundary.EventAdapter-1.0.0-py2.7.egg](https://s3.amazonaws.com/boundary-utils/boundary-event-adapters/zenoss/ZenPacks.boundary.EventAdapter-1.0.0-py2.7.egg)
* Initial Release
