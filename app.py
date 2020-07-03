#Copyright (c) 2020 Cisco and/or its affiliates.

#This software is licensed to you under the terms of the Cisco Sample
#Code License, Version 1.1 (the "License"). You may obtain a copy of the
#License at
#
#               https://developer.cisco.com/docs/licenses
#
#All use of the material herein must be in accordance with the terms of
#the License. All rights not expressly granted by the License are
#reserved. Unless required by applicable law or agreed to separately in
#writing, software distributed under the License is distributed on an "AS
#IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#or implied.

from pprint import pprint
from flask import Flask, json, request, render_template
import json, sys, requests, jsonify, re
from env import *
import meraki
import datetime
from pytz import timezone
import dateutil.parser
from webexteamssdk import WebexTeamsAPI
import re

app = Flask(__name__)


#Initialize varibles
set_combinedhw = False
meraki_key = ""
webex_botkey = ""
webex_roomid = ""
dashboard = []
teamsapi = []
# Make a regular expression 
# for validating an Ip-address 
network = " "
organization = " "
regex = '''^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$'''
      
# Define a function for 
# validate an Ip addess 
def check(Ip):  
  
    # pass the regular expression 
    # and the string in search() method 
    if(re.search(regex, Ip)):  
        return True  
          
    else:  
        return False  

def get_system_time():
    current_time=datetime.datetime.now().strftime("The current system time and date is %I:%M%p on %A, %B %d, %Y.")
    return current_time

def convert_my_iso_8601(iso_8601, tz_info):
    assert iso_8601[-1] == 'Z'
    iso_8601_dt = dateutil.parser.parse(iso_8601)
    print(iso_8601_dt)
    return iso_8601_dt.replace(tzinfo=timezone('UTC')).astimezone(tz_info)


def send_info_to_webex_teams(sentfrom, switchname, switchserial, clientocc, clientport, cclientip, newclientip, clientmac, clientdnsname, clientdesc):

    teamsapi.messages.create(
        webex_roomid, 
        text="Meraki Alert: \nSent from: " + sentfrom + 
        "\n" + switchname + 
        "\n" + switchserial +
        "\n" + clientdnsname +
        "\n" + cclientip +
        "\n" + newclientip +
        "\n" + clientmac + 
        "\n" + clientport +
        "\n" + clientdesc +
        "\n" + clientocc 
    )

     # Return success message
    return "WebHook POST Received"


def find_port_tag_vlan(network_id, switch_serial, client_port):
    port_list=[]
    devices = dashboard.networks.getNetworkDevices(networkId=network_id)
    for device in devices:
            if device['serial'].startswith(switch_serial):
                if device['tags'] is not None:
                    for switch_tag in device['tags']:
                        if switch_tag == 'media':
                            print('switch found!','---',device['name'])
                            ports = dashboard.switch.getDeviceSwitchPorts(device['serial'])
                            for port in ports:
                                if port['portId'] == client_port:
                                   port_list.append(port)
    return port_list
                                   

def change_ip_address(network_id, vlan_id, port_ip, client_mac, description):
   
    vlan = dashboard.appliance.getNetworkApplianceVlan(networkId=network_id, vlanId=vlan_id)
    fixed_assignments = vlan["fixedIpAssignments"]
    mac_address = client_mac
    fixed_assignments[mac_address] = {'ip': port_ip,'name': description}
    dashboard.appliance.updateNetworkApplianceVlan(networkId=network_id,vlanId=vlan_id,fixedIpAssignments=fixed_assignments)
    
    return

@app.route('/')
def index():
    return render_template("login.html")


@app.route("/", methods=["POST"])
def get_webhook_json():


    # Webhook Receiver
    webhook_data = request.json
    pprint(webhook_data)
    #webhook_data = json.dumps(webhook_data)

    # Capture Webhook info
    if re.search(r"port connected", webhook_data["alertType"]):
        wbh_port_num = webhook_data["alertData"]["portNum"]
        wbh_switch_serial = webhook_data["deviceSerial"]
        wbh_switch_mac = webhook_data["deviceMac"] 
        wbh_switch_name = webhook_data["deviceName"]
        wbh_org_id = webhook_data["organizationId"]
        wbh_net_id = webhook_data["networkId"]
        wbh_occ_time = webhook_data["occurredAt"]
        #occuredtime
        print(wbh_switch_serial)
    else:
        return "Webhook received but not accepted"

    device_clients = dashboard.devices.getDeviceClients(wbh_switch_serial)
    print(device_clients)

    try:
        for item in device_clients:
            while item["switchport"] == str(wbh_port_num):
                currentclientip = item["ip"]
                clientmac = item["mac"]
                clientdnsname = item["dhcpHostname"]
                clientdesc = item["description"]
                break

    except:
        raise Exception ("could not find the client in that port")

    port_vlan_tag = find_port_tag_vlan(wbh_net_id, wbh_switch_serial, str(wbh_port_num))
    print(port_vlan_tag)
    change_ip_address(wbh_net_id, port_vlan_tag[0]['vlan'], port_vlan_tag[0]['tags'][0], clientmac, clientdnsname)
    cycle = dashboard.switch.cycleDeviceSwitchPorts(serial=wbh_switch_serial,ports=[str(wbh_port_num)])

    swname = "Switch Name - " + wbh_switch_name
    swserial = "Switch Serial Number - " + wbh_switch_serial
    my_dt = convert_my_iso_8601(wbh_occ_time, timezone('MST'))
    clocc = "Occurred at - " + str(my_dt)
    clport = "Client Port - " + str(wbh_port_num)
    currentclientip = "Current Client IP - " + currentclientip
    newclientip = "Port Tag IP - " + port_vlan_tag[0]['tags'][0]
    clientmac = "Client MAC - " + clientmac
    if clientdnsname is not None:
        clientdnsname = "Client DNS - " + clientdnsname
    else:
        clientdnsname = "Client DNS - NA"

    if clientdesc is not None:
        clientdesc = "Client Description - " + clientdesc
    else:
        clientdesc = "Client Description - NA"

    send_info_to_webex_teams("Webhook", swname, swserial, clocc, clport, currentclientip, newclientip, clientmac, clientdnsname, clientdesc)
    return "WebHook POST Received"



@app.route("/apikey", methods=['POST'])
def apikey():
    global meraki_key
    global webex_botkey
    global webex_roomid
    global dashboard
    global teamsapi

    code = request.form.get("code")
    print("this is the code",code)
    if code == '1':
        meraki_key = request.form.get("key")
        webex_botkey = request.form.get("botkey")
        webex_roomid = request.form.get("roomid")

    dashboard = meraki.DashboardAPI(api_key=meraki_key, base_url=get_meraki_base_url())
    teamsapi = WebexTeamsAPI(access_token=webex_botkey)

    organizations = dashboard.organizations.getOrganizations()
    return render_template("capture.html", orgs = organizations)

@app.route("/capture")
def capture():

    organizations = dashboard.organizations.getOrganizations()
    return render_template("capture.html", orgs = organizations)

@app.route("/capture", methods=['POST'])
def capture_post():
    global set_combinedhw
    

    select = request.form.get("select")
    print("Select: ", select)
    if select == '1':
        org_select = request.form['org']
        networks = dashboard.organizations.getOrganizationNetworks(org_select)
        print(networks)
        netwks = []
        try:
            for item in networks:
                print (len(item["productTypes"]))
                if len(item["productTypes"]) > 1:
                    set_combinedhw = True

                for device in item["productTypes"]:
                    if device == "switch":
                        netwks.append(item)
        except:
            raise Exception ("could not find switch")

        return json.dumps(netwks)

    if select == '2':
        net_select = request.form['net']
        print(bool(set_combinedhw))
        print(net_select)
        if set_combinedhw:
            hwtype = "switch"
        else:
            hwtype = ""

        print(hwtype)
        network_events = dashboard.networks.getNetworkEvents(net_select,productType=hwtype)
        print(network_events)
        try:
            for item in network_events["events"]:
                if re.search(r"role_change", item["type"]):
                    switchname = item["deviceName"]
                    switchserial = item["deviceSerial"]
                    clientport = item["eventData"]["port"]
                    clientoccurred = item["occurredAt"]
                    break

            print(switchname)
            print(switchserial)
            print(clientport)
            print(clientoccurred)
            print(net_select)
            return json.dumps({"switch_name": switchname, "switch_serial": switchserial, "client_port": clientport, "client_occurred": clientoccurred, "network": net_select})

        except:
            #raise Exception ("could not find any new event")
            return json.dumps({'error' : 'Device Not Found!!'})

    if select == '3':
        

        swname = request.form['swname']
        swserial = request.form['swserial']
        clport = request.form['clport']
        clocc = request.form['clocc']
        netid = request.form['netid']


        device_clients = dashboard.devices.getDeviceClients(swserial)
        print(device_clients)

        try:
            for item in device_clients:
                while item["switchport"] == clport:
                    currentclientip = item["ip"]
                    clientmac = item["mac"]
                    clientdnsname = item["dhcpHostname"]
                    clientdesc = item["description"]
                    break

        except:
            #raise Exception ("could not find the client on that port")
            return json.dumps({'error' : 'Device Not Found!!'})

        port_vlan_tag = find_port_tag_vlan(netid, swserial, clport)
        print(port_vlan_tag)
        change_ip_address(netid, port_vlan_tag[0]['vlan'], port_vlan_tag[0]['tags'][0], clientmac, clientdnsname)
        cycle = dashboard.switch.cycleDeviceSwitchPorts(serial=swserial,ports=[clport])

        swname = "Switch Name - " + swname
        swserial = "Switch Serial Number - " + swserial
        my_dt = convert_my_iso_8601(clocc, timezone('MST'))
        clocc = "Occurred at - " + str(my_dt)
        clport = "Client Port - " + clport
        currentclientip = "Current Client IP - " + currentclientip
        newclientip = "Port Tag IP - " + port_vlan_tag[0]['tags'][0]
        clientmac = "Client MAC - " + clientmac

        if clientdnsname is not None:
            clientdnsname = "Client DNS - " + clientdnsname
        else:
            clientdnsname = "Client DNS - NA"

        if clientdesc is not None:
            clientdesc = "Client Description - " + clientdesc
        else:
            clientdesc = "Client Description - NA"

        print(swname)
        print(swserial)
        print(clocc)
        print(clport)
        print(currentclientip)
        print(newclientip)
        print(clientmac)
        print(clientdnsname)
        print(clientdesc)
        print(netid)

        

        send_info_to_webex_teams("Portal", swname, swserial, clocc, clport, currentclientip, newclientip, clientmac, clientdnsname, clientdesc)

        return json.dumps({"switch_name": swname, "switch_serial": swserial, "client_occ": clocc, "client_port": clport, "cclient_ip": currentclientip, "newclient_ip": newclientip, "client_dnsname": clientdnsname, "client_description": clientdesc, "client_mac": clientmac})



@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/scan")
def scan():
    organizations = dashboard.organizations.getOrganizations()
    return render_template("scan.html",orgs=organizations)


@app.route("/scan", methods=['POST'])
def scan_post():
    global network
    global organization
    port_list = []
    unmatched_tags = []

    code = request.form['code']

    if code == '1':
        request1 = request
        orgranization = request.form['org-select']
        network = request.form['net-select']

        print('Org ID selected:',organization)
        print('Net ID selected:',network)

        devices = dashboard.networks.getNetworkDevices(networkId=request.form['net-select'])
        # check for only switches then check their tag
        for device in devices:
            if device['model'].startswith('MS'):
                if device['tags'] is not None:
                    for switch_tag in device['tags']:
                        if switch_tag == 'media':
                            print('switch found!','---',device['name'])
                            ports = dashboard.switch.getDeviceSwitchPorts(device['serial'])
                            for port in ports:
                                if port['tags'] is not None:
                                    for port_tag in port['tags']:
                                        if check(port_tag):
                                            print('port tags ip address',port_tag)
                                            device_clients = dashboard.devices.getDeviceClients(device['serial'])
                                            for device_client in device_clients:
                                                if port['portId'] == device_client['switchport']:
                                                    print('client connected to port ',port['portId'],':',device_client)
                                                    if device_client['ip'] == port_tag: 

                                                        print("client ip and port tag matches!")
                                                        print("client ip:",device_client['ip'])
                                                        print("port tag:",port_tag)
                                                        continue
                                                    else:
                                                        port_temp = {}
                                                        port_temp['client'] = device_client['dhcpHostname']
                                                        port_temp['description'] = device_client['description']
                                                        port_temp['number'] = port['portId']
                                                        port_temp['port_tag'] = port_tag
                                                        port_temp['client_mac'] = device_client['mac']
                                                        port_temp['client_ip'] = device_client['ip']
                                                        port_temp['device_name'] = device['name']
                                                        port_temp['vlan'] = device_client['vlan']
                                                        port_temp['network_id'] = device['networkId']
                                                        port_temp['serial'] = device['serial']
                                                        port_list.append(port_temp)

                                                        print("client ip and port tag do not match!")
                                                        print("client ip:",device_client['ip'])
                                                        print("port tag:",port_tag)

                                                        port_temp['mac'] = device_client['mac']
                                                        unmatched_tags.append(port_temp)                      
                                        else:
                                            print("Unacceptable ip address")
        
        organizations = dashboard.organizations.getOrganizations()
        print(unmatched_tags)



        return render_template("scan.html",orgs=organizations,ports=port_list)

    if code == '2':

        request1 = request
        ports = request.form.getlist("port")

        for port in ports:
            temp = port.split('|')
            port_num = temp[0]
            port_tag = temp[1]
            client_mac = temp[2]
            port_ip = temp[3]
            vlan_id = temp[4]
            network_id = temp[5]
            device_serial = temp[6]

            if port_tag == port_ip:
                continue
            else:
                vlans = dashboard.appliance.getNetworkApplianceVlans(networkId=network_id)
                for vlan in vlans:
                    vlan_temp = vlan
                    if vlan['networkId'] == network and str(vlan['id']) == vlan_id:
                        vlan_id = vlan['id']
                        vlan_temp = vlan
                        fixed_assignments = vlan_temp["fixedIpAssignments"]                        

                        if len(fixed_assignments) > 0:
                            temp = fixed_assignments
                            for key, value in temp.items():
                                mac = key
                                ip = value

                                if ip['ip'] == port_tag:
                                    print("removing ", mac," from static bind ",port_tag)
                                    del fixed_assignments[mac]
                                    break

                        mac_address = client_mac
                        fixed_assignments[mac_address] = {'ip':port_tag,'name':'script'}
                        
                        try:
                            response = dashboard.appliance.updateNetworkApplianceVlan(networkId=network,vlanId=vlan_id,fixedIpAssignments=fixed_assignments)
                        except:
                            print("ERROR IN CHANGING IP ADDRESS")
                    else:
                        continue
                
                send_info_to_webex_teams("Device Scan", "", "Switch Serial Number - " + str(device_serial), "", "Client Port - " + str(port_num), "Current Client IP - " + str(port_ip), "Port Tag IP - " + str(port_tag), "Client MAC - " + str(client_mac), "", "")
                cycle = dashboard.switch.cycleDeviceSwitchPorts(serial=device_serial,ports=[port_num])

        organizations = dashboard.organizations.getOrganizations()
        return render_template("scan.html",orgs=organizations)


if __name__ == "__main__":


    app.run(host="0.0.0.0", port=5000, debug=True)


