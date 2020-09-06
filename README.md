# Multi-SIEM-Support-For-McAfee-ePO
 Multi SIEM support for McAfee ePolicy Orchestrator

## Purpose of this project
The purpose of this project is to propose a solution for enterprises that use a unique centrale ePO server to manage all endpoints across the entire Group/Enterprise including subsidiaries and are looking to offer a point of data collection for subsidiaries SIEM/SOC. While most of SIEMs are establishing a direct connection to ePO or its database or while ePO can redirect all events to a Syslog receiver, it forces each subsidiary to get a view/access to logs from all subsidiaries.<br>
I'm proposing a "Pull Request" approach through ePO WebAPI based on ePO User Account to filter/limit log access to only the scope that each subsidiary is participating/acting to.

![](./img/epo-management.png)
TO DO: Include a graphic to illustrate the current concept

## Designing the Threat Event query
As a standard approach, you can decide to start with all the columns available from the Threat Events table of the ePO database. It will be the best point to start as most SIEM are simply grabbing events from this table. Also, this is what McAfee decided to offer for his "Pull Events" API from the SaaS version of ePolicy Orchestrator, aka MVISION ePO. (Please read the following [documentation page](https://docs.mcafee.com/bundle/mvision-epolicy-orchestrator-product-guide/page/GUID-26C1A6F2-DEB6-48B6-80D6-509649C356BC.html) for more information about this service.)

If you don't want to import my query ("query-threat-events.xml"), you can build your own. From ePO console menu -> Queries & Reports, click "New Query".

![](./img/epo-create-query-01.png)
Select "Threat Events" as the source for the query, then click "Next".

![](./img/epo-create-query-02.png)
Choose the table "Chart Type", then click "Next".

![](./img/epo-create-query-03.png)
Then add all columns available from Threat Events. I like to add also the Assignement Path in this query because based on the ePO System Tree, the location of the system within the tree could definitely helps to understand the event or identify the targeted system.

| Included columns in the query:                                                             |||
| ------------------------------ | -------------------------- | ------------------------------ |
| Action Taken                   | Event Generated Time       | Threat Source URL              |
| Agent GUID                     | Event ID                   | Threat Source User Name        |
| Analyzer Detection Method      | Event Received Time        | Threat Target File Path        |
| DATVersion                     | Preferred Event Time       | Threat Target Host Name        |
| Detecting Product ID           | Server ID                  | Threat Target IP Address       |
| Detecting Product Host Name    | Threat Handled             | Threat Target IPV4 Address     |
| Detecting Product IP Address   | Threat Name                | Threat Target MAC Address      |
| Detecting Product IPV4 Address | Threat Severity            | Threat Target Network Protocol |
| Detecting Product MAC Address  | Threat Source Host Name    | Threat Target Port Number      |
| Detecting Product Name         | Threat Source IP Address   | Threat Target Process Name     |
| Detecting Product Version      | Threat Source IPV4 Address | Threat Target User Name        |
| Engine Version                 | Threat Source MAC Address  | Threat Type                    |
| Event Category                 | Threat Source Process Name | Assignement Path*              |

*Note:* Assignement Path is coded as "EPOBranchNode.NodeTextPath2".<br>

![](./img/epo-create-query-04.png)
As the goal is to run the pull events request every hour, here I'm filtering the events based on the last full received hour. (I'm not using the Event Generated Time because the agent may not present today and will report their events the day after, so if you don't want to miss events, you need to work based on the Event Received Time.)<br>
You can adapt the filter based on your needs (i.e: last 5 minutes or last day.) Then click "Next".

![](./img/epo-create-query-05.png)
Enter the name and description you want for this query and click "Save".
<br>
I also built another query where I  added the "Targeted File Hash' reported in the case of the ENS detection. Feel free to add any columns that could add value to your SIEM based on your needs. Then I decided to save those queries in a "Shared Group" that I plan to use in a dedicated Permission Set.

![](./img/epo-shared-queries.png)

## Provisionning Accounts and Permission Sets
Permission Set will allow ePO Administrator to set a hard-coded filter on the execution of the query by each subsidiary.

![](./img/epo-system-tree2.png)

Define a new ePO user and permission set per subsidiary with the following permissions:
- **Queries and Reports:** Use public groups, and these shared groups: Threat Events.
- **Systems:** View "System Tree" tab 
- **System Tree access:**  Can search on the following nodes and parts of the System Tree:*The-subsidary-folder*
- **Threat Event Log:** View events 
 
![](./img/epo-permission-set.png)

**Note:** The on-demand creation or the provisioning of all users and permission sets can be done through the WebAPI also. (That script is not part of the current project).

## Pull Request the Threat Events though the API
Use the Python script "[get_events.py](./get_events.py)" to pull events every hours, based on the query defined earlier.

![](./img/sequence-diagram.png)

[//]: # (Sequence Generator: https://bramp.github.io/js-sequence-diagrams/)
[//]: # (participant get_events.py)
[//]: # (participant Local File)
[//]: # (participant ePO Server)
[//]: # (get_events.py->ePO Server: core.executeQuery)
[//]: # (Note over ePO Server: Execute query based\n on Permission Set)
[//]: # (ePO Server->get_events.py: events.json)
[//]: # (Note over get_events.py: Write events)
[//]: # (get_events.py->Local File: json.dump)

Here the script is saving "pulled events" in a simple file. You can read the sample file "[events-sample.json](./events-sample.json)" grabbed from my testing lab with five events from McAfee Endpoint Security Threat Prevention and Adaptive Threat Prevention.

You can adapt that script the save event in a syslog stream instead and configure the syslogd to forward those events to a syslog receiver from your SIEM infrastructure.

![](./img/sequence-diagram-syslog.png)

[//]: # (Sequence Generator: https://bramp.github.io/js-sequence-diagrams/)
[//]: # (participant get_events.py)
[//]: # (participant syslogd)
[//]: # (participant ePO Server)
[//]: # (participant SIEM Rcv)
[//]: # (participant Syslog Rcv)
[//]: # (get_events.py->ePO Server: core.executeQuery)
[//]: # (Note over ePO Server: Execute query based\n on Permission Set)
[//]: # (ePO Server->get_events.py: events.json)
[//]: # (Note over get_events.py: Write events)
[//]: # (get_events.py->syslogd: json.dump)
[//]: # (Note over syslogd: Syslog forward)
[//]: # (syslogd->Syslog Rcv: Threat event A)
[//]: # (Syslog Rcv-> SIEM Rcv: push.event)
[//]: # (syslogd->Syslog Rcv: Threat event B)
[//]: # (Syslog Rcv-> SIEM Rcv: push.event)
[//]: # (syslogd->Syslog Rcv: Threat event ...)
[//]: # (Syslog Rcv-> SIEM Rcv: push.event)

I'm not going to cover the syslog forwarder in this project. If you want to do so I strongly recommand you to have a look at the [McAfee GitHub for McAfee MVISION EDR](https://github.com/mcafee/mvision-edr-activity-feed).

[//]: # (Benjamin Marandel - 2020-09-04)