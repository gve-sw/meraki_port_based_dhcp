# Meraki Port Based DHCP


A customer is looking for an IOS feature called DHCP Server Port-Based Address Allocation.  This feature allows the user to preassign an IP address to a port from the DHCP pool.  Once a device is pulled into the port, the device will get the assigned IP address.  

Our project uses the following logic flow to simulate the same feature on the Meraki platform utilizing the Dashboard APIs.

![/IMAGES/logic_flow.png](/IMAGES/logic_flow.png)


## Contacts
* Jorge Banegas
* Jason Mah

## Solution Components
* Python
* Meraki Dashboard API Python Library - https://github.com/meraki/dashboard-api-python/
* Flask

## Installation/Configuration

Option 1: 

1. Pull down the project into a python virtual environment

```
git clone https://wwwin-github.cisco.com/gve/meraki_port_based_dhcp.git
```

2. Install required packages

```
pip install -r requirements.txt
```

3. Launch flask application

```
python app.py
```

Option 2:

1. Install Docker - https://docs.docker.com/get-docker/

2. Pull down the project
```
git clone https://wwwin-github.cisco.com/gve/meraki_port_based_dhcp.git
```

3. Build the project Docker image
```
docker build --tag merakidhcp:1.0 .
```

4. Run Docker image
```
docker run --publish 5000:5000 --detach --name dhcp merakidhcp:1.0
```




## Usage

Open your browser to http://0.0.0.0:5000

Enter a Meraki API Key from the Meraki API dashboard - https://documentation.meraki.com/zGeneral_Administration/Other_Topics/The_Cisco_Meraki_Dashboard_API#:~:text=Enable%20API%20access,-For%20access%20to&text=After%20enabling%20the%20API%2C%20go,API%20key%20on%20your%20profile.

Enter or create a Webex Teams Bot key - https://developer.webex.com/docs/bots

Enter or create the Webex Teams Room ID - https://developer.webex.com/docs/api/v1/rooms/list-rooms

![/IMAGES/login.png](/IMAGES/login.png)


To setup Meraki Webhook notifications.  Navigate in the Meraki Dashboard to Network-wide -> Configure -> Alerts

Under the Switch section of Alerts, select "any port goes down for more than 5 minutes" add your webhook name to the additional recipients.  

Under the Webhooks section add the corresponding Http server that will receive the Webhook notification.

![/IMAGES/dashboard_webhook.png](/IMAGES/dashboard_webhook.png)


## App Usage

In the Meraki Dashboard tag all switches that wish to use with the "media" tag to allow the application to inspect that device.  

On the port, add the IP tag that you would like to assign to the port.  

![/IMAGES/tagging.png](/IMAGES/tagging.png)


To initiate a device capture for the last device plugged into the switch.  Navigate to "Initiate Device Capture" on the sidebar.  

![/IMAGES/gui_interface.png](/IMAGES/gui_interface.png)


To scan a network for all switches that may have a "miss match" of tagged IP to current device IP.  Navigate to "Scan for New Devices"

Once you select a specific organization and network, the app wil display the mismatched port and client and offer the ability to change the desired ip address of the client

![/IMAGES/gui_interface.png](/IMAGES/scan.png)


### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
