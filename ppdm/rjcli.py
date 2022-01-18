# rjcli v1.0.5 for Dell EMC Power Protect Data Manager - Github @ rjainoje
__author__ = "Raghava Jainoje"
__version__ = "1.0.5"
__email__ = " "

import requests
import json
import click
import urllib3
import sys
import time
import pyfiglet
from tabulate import tabulate
from click_shell import shell
from datetime import datetime, timedelta
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# PPDM Uri and api end-point
ppdmsrv = 'ppdmserver'
ppdmuri = "https://{0}".format(ppdmsrv) + ":8443/api/v2/"
token = 'temp'

def get_assets(ppdmuri, token, asset):
	'''This function returns assets in JSON'''
	uri = ppdmuri + 'assets'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	pageSize = '10000'
	if asset != 'all':
		filter = 'name lk "%{0}%" or details.fileSystem.hostName lk "%{0}%"'.format(asset)
	else:
		filter = 'createdAt gt "2010-05-06T11:20:21.843Z"'
	params = {'filter': filter, 'pageSize': pageSize}
	try:
		response = requests.get(uri, headers=headers, params=params, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
	if (response.status_code != 200):
		raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
	return response.json()['content']

def get_policies(ppdmuri, token, policies):
	'''This function returns policies in JSON'''
	uri = ppdmuri + 'protection-policies'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	pageSize = '10000'
	if policies != 'all':
		filter = 'type eq "ACTIVE" and name lk "%{}%"'.format(policies)
	else:
		filter = 'type eq "ACTIVE" and createdAt gt "2010-05-06T11:20:21.843Z"'
	params = {'filter': filter, 'pageSize': pageSize}
	try:
		response = requests.get(uri, headers=headers, params=params, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
	if (response.status_code != 200):
		raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
	return response.json()['content']

def get_activities(ppdmuri, token, jobs, window):
	'''This function returns JSON with all the activities based on the selected filters'''
	uri = ppdmuri + 'activities'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	print (window)
	filter = 'classType in ("JOB", "JOB_GROUP") and category eq "PROTECT" and createdTime gt "{}"'.format(window)
	orderby = 'createTime DESC'
	pageSize = '10000'
	if jobs == 'running':
		filter +=' and state in ("RUNNING","QUEUED")'
	elif jobs == 'failed':
		filter +=' and state in ("COMPLETED") and result.status in ("FAILED", "CANCELED")'
	elif jobs == 'successful':
		filter +=' and state in ("COMPLETED") and result.status eq "OK"'
	elif jobs == 'ALL-FAILED':
		filter +=' and state in ("COMPLETED") and result.status in ("FAILED", "CANCELED") and actions.retryable eq "true"'
	else:
		print ('Proceeding with listing all the jobs since {}'.format(window))
	params = {'filter': filter, 'orderby': orderby, 'pageSize': pageSize}
	try:
		response = requests.get(uri, headers=headers, params=params, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
	if (response.status_code != 200):
		raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
	if 'activityId' in response.json():
		return response.json()['activityId']
	if 'taskId' in response.json():
		return response.json()['taskId']
	if 'jobId' in response.json():
		return response.json()['jobId']
	return response.json()['content']

def get_stg_targets(ppdmuri, token):
	'''This function returns storage devices in JSON'''
	uri = ppdmuri + 'storage-systems'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	pageSize = '10000'
	params = {'pageSize': pageSize}
	try:
		response = requests.get(uri, headers=headers, params=params, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
	if (response.status_code != 200):
		raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
	return response.json()['content']

def countList(lst, x):
	'''This function returns sum of list element count'''
	return sum(x in item for item in lst) 

def getwindow(period):
	'''This function returns time with the delta'''
	if period == '1day-ago':
		gettime = datetime.now() - timedelta(days = 1)
		window = gettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
	elif period == '1week-ago':
		gettime = datetime.now() - timedelta(days = 7)
		window = gettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
	else:
		raise Exception ("Please select the period either 1day-ago or 1week-ago")
	return window

def adhoc_backup(ppdmuri, token, id, full):
	'''This function performs backup and returns activityid'''
	uri = ppdmuri + 'asset-backups'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	if not full:
		backuptype = "FULL"
	else:
		backuptype = "AUTO_FULL"
	payload = json.dumps({
        'assetId' : '{}'.format(id),
		'backupType' : backuptype
		})
	try:
		response = requests.post(uri, data=payload, headers=headers, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
	if response.status_code not in [200, 201, 202]:
		print('Failed to run ad-hoc backup on asset ID {}, code: {}, body: {}'.format(id, response.status_code, response.text))
	if 'activityId' in response.json():
		return response.json()['activityId']
	if 'taskId' in response.json():
		return response.json()['taskId']
	if 'jobId' in response.json():
		return response.json()['jobId']
	return None

def monitor_activity(ppdmuri, token, activityid):
	'''This function returns activityid status'''
	timeout = 300
	interval = 15
	uri = ppdmuri + 'activities/' + str(activityid)
	start = time.time()
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	while True:
		if (time.time() - start) > timeout:
			break
		try:
			response = requests.get(uri, headers=headers, verify=False)
			response.raise_for_status()
		except requests.exceptions.RequestException as err:
			print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
		if (response.status_code != 200):
			print('Failed to query {}, code: {}, body: {}'.format(
                uri, response.status_code, response.text))
			return None
		print('Activity {} {}'.format(activityid, response.json()['state']))
		if response.json()['state'] == 'COMPLETED':
			return response.json()['result']['status']
		time.sleep(interval)
	return 'TIMEOUT'

def backup_retry(ppdmuri, token, actid, joblist):
	'''This function takes activityid and jobgroupid to retry failed jobs'''
	uri = ppdmuri + 'activities/'+actid+'/retry'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	payload = json.dumps({'retryJobIds' : joblist})
	try:
		response = requests.post(uri, data=payload, headers=headers, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
	if response.status_code not in [200, 201, 202]:
		print('Failed to run ad-hoc backup on asset ID {}, code: {}, body: {}'.format(id, response.status_code, response.text))
	retrylist = []
	for activityids in response.json()['retryResults']:
		retrylist.append(activityids['newJobId'])
	return retrylist

def get_creds(ppdmuri, token, cred):
	'''This function returns credentials in JSON'''
	uri = ppdmuri + 'credentials'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	pageSize = '10000'
	if cred != 'all':
		filter = 'name eq "{0}" '.format(cred)
		params = {'filter': filter, 'pageSize': pageSize}
		try:
			response = requests.get(uri, headers=headers, params=params, verify=False)
			response.raise_for_status()
		except requests.exceptions.RequestException as err:
			print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
		if (response.status_code != 200):
			raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
		if response.json()['page']['totalElements'] != 0:
			return response.json()['content'][0]['id']
		else:
			return response.json()['content']
	else:
		params = {'pageSize': pageSize}
		try:
			response = requests.get(uri, headers=headers, params=params, verify=False)
			response.raise_for_status()
		except requests.exceptions.RequestException as err:
			print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
		if (response.status_code != 200):
			raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
		return response.json()['content']

def delete_cred(ppdmuri, token, credid, cred):
	'''This function takes credentials ID and credentials name to delete'''
	uri = ppdmuri + 'credentials/'+credid+'/'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	try:
		response = requests.delete(uri, headers=headers, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
	if (response.status_code != 204):
		raise Exception('Failed to delete {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
	print ("Deleted credential name {} successfully".format(cred))

def get_alerts(ppdmuri, token, alerttype):
	'''This function returns alerts based on filters in JSON'''
	uri = ppdmuri + 'alerts'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	orderby = 'postedTime DESC'
	pageSize = '10000'
	if alerttype in ("warning", "critical", "informational"):
		filter ='severity eq "{}"'.format(alerttype)
		params = {'filter': filter, 'orderby': orderby, 'pageSize': pageSize}
	else:
		params = {'orderby': orderby, 'pageSize': pageSize}
	try:
		response = requests.get(uri, headers=headers, params=params, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
	if (response.status_code != 200):
		raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
	return response.json()['content']

def ack_alerts(ppdmuri, token, alertslist):
	'''This function acknowledges all the alerts'''
	uri = ppdmuri + 'alerts/acknowledgements'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	payload = json.dumps({"acknowledgement": {"acknowledgeState": "ACKNOWLEDGED"}, "messageIds": alertslist})
	try:
		response = requests.post(uri, data=payload, headers=headers, verify=False)
		response.raise_for_status()
	except requests.exceptions.RequestException as err:
		print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
	if response.status_code not in [200, 201, 202]:
		print('Failed to acknowledge ID {}, code: {}, body: {}'.format(id, response.status_code, response.text))
	return response.json()['acknowledgementCount']

@shell(prompt='dellemc-ppdm-cli > ', intro='')
def my_app():
	'''This is the banner'''
	banner = pyfiglet.figlet_format("RJ CLI", font = "slant" )
	print (banner)
	print ("-------------------------------------------------------")
	print ("Welcome to RJCli for Dell EMC PowerProtect Data Manager")
	print ("Please login to PPDM with a command login")
	print ("-------------------------------------------------------")

@my_app.command()
@click.option('--ppdmsrv', prompt='PPDM IP or Hostname')
@click.option('--uname', prompt='Username')
@click.option('--password', prompt=True, hide_input=True)
def login(ppdmsrv, uname, password):
	"""Enter PPDM username and password to login"""
	global token
	global ppdmuri
	uri = "https://{0}".format(ppdmsrv) + ":8443/api/v2/" + 'login'
	payload = '{"username": "%s", "password": "%s"}' % (uname, password)
	headers = {'content-type': 'application/json'}
	try:
		response = requests.post(uri, data=payload, headers=headers, verify=False)
		response.raise_for_status()
	except requests.exceptions.ConnectionError as err:
		print('Error Connecting to {}: {}'.format(ppdmsrv, err))
		sys.exit(1)
	except requests.exceptions.Timeout as err:
		print('Connection timed out {}: {}'.format(ppdmsrv, err))
		sys.exit(1)
	except requests.exceptions.RequestException as err:
		print("Login failed! {}".format(err))
		sys.exit(1)
	except requests.exceptions.HTTPError as err:
		print("Login failed in the loop {}".format(err))
	if (response.status_code != 200):
		raise Exception('Login failed for user: {}, code: {}, body: {}'.format(uname, response.status_code, response.text))
	print('Logged in with user: {} to PowerProtect Data Manager: {}'.format(uname, ppdmsrv))
	print ("Type help for available commands and options")
	ppdmuri = "https://{0}".format(ppdmsrv) + ":8443/api/v2/"
	token = response.json()['access_token']
	return token

@my_app.command()
@click.option('--jobs', required=False, help="Displays jobs, takes arguments failed, success or all")
@click.option('--period', required=False, help="It takes arguments 1day-ago or 1week-ago")
@click.option('--storage', required=False, help="Displays storage, accepts option 'details'")
@click.option('--asset', required=False, help="Displays assets, filter by client name or 'all'")
@click.option('--policies', required=False, help="Displays policy information, it accepts option 'all' ")
@click.option('--cred', required=False, help="Lists all the credentails")
def show(jobs, period, storage, asset, policies, cred):
	"""This command displays information about jobs, storage, assets and policies \n
	Example commands: \n
	show --jobs summary --period <1day-ago | 1week-ago> \n
	show --jobs <successful | failed | all> --period <> \n
	show --storage details \n
	show --asset <asset-name | all | summary> \n
	show --policies <policy-name | all> \n
	show --cred <all>
	"""
	if (jobs == 'failed' or jobs == 'successful' or jobs == 'all'):
		window = getwindow(period)
		activities = get_activities(ppdmuri, token, jobs, window)
		activitylist = []
		if len(activities) == 0:
			print ("There are no jobs to display, change the criteria and try again")
		else:
			for activity in activities:
				try:
					activitylist.append([activity['protectionPolicy']['name'], activity['classType'], activity['result']['status'], activity['createTime']])
				except Exception:
					print ("Some jobs couldn't fetch")
					continue
			print(tabulate(activitylist, headers=["Activity Name","Job Type", "Job Status", "Start Time"], tablefmt="pretty"))
	elif jobs == 'summary':
		activitylist = []
		window = getwindow(period)
		activities = get_activities(ppdmuri, token, jobs, window)
		if len(activities) == 0:
			print ("No activities found!")
		else:
			for activity in activities:
				try:
					activitylist.append([activity['protectionPolicy']['name'], activity['classType'], activity['result']['status'], activity['createTime']])
				except Exception:
					print ("Some activities couldn't fetch")
			ok = countList(activitylist, 'OK')
			failed = countList(activitylist, 'FAILED')
			canceled = countList(activitylist, 'CANCELED')
			totaljobs = (ok+failed+canceled)
			sumlist = [(ok, failed, canceled, totaljobs)]
			print("															")
			print("JOB SUMMARY REPORT                  ")
			print(tabulate(sumlist, headers=["Successful Jobs", "Failed Jobs", "Canceled Jobs", "Total Jobs"], tablefmt="pretty"))
	elif (storage == 'details'):
		stgtargets = get_stg_targets(ppdmuri, token)
		if len(stgtargets) == 0:
			print ("No storage devices found!")
		else:
			for storage in stgtargets:
				try:
					print("                                                         ")
					print("---------------------------------------------------------")
					print("Data Domain Name:", storage["name"])
					print("DD Type:         ", storage["type"])
					print("DD Model:        ", storage["details"]["dataDomain"]["model"])
					print("DD Serial Number:", storage["details"]["dataDomain"]["serialNumber"])
					print("DDOS Version:    ", storage["details"]["dataDomain"]["version"])
					print("Total Size (GB): ", "%.2f" %(int(storage["details"]["dataDomain"]["totalSize"])/1024/1024/1024))
					print("Used Size (GB):  ", "%.2f" %(int(storage["details"]["dataDomain"]["totalUsed"])/1024/1024/1024))
					print("Dedupe Factor(x):", "%.1f" %(storage["details"]["dataDomain"]["compressionFactor"]))
					print("Used Percentage: ", "%.2f" %(int(storage["details"]["dataDomain"]["percentUsed"])))
					print("Last Status:     ", storage["lastDiscoveryStatus"])
					print("Last Discovered: ", storage["lastDiscovered"])
				except Exception:
					print ("Some storage devices couldn't display")
					continue
	elif asset:
		if asset == 'summary':
			assetDict = {}
			allassets = get_assets(ppdmuri, token, 'all')
			for asset in allassets:
				atype = asset["type"]
				aname = asset["name"]
				if (atype in assetDict.keys()):
					assetDict.get(atype).append(aname)
				else:
					newlist=[]
					newlist.append(aname)
					assetDict[atype]=newlist
			sumtable = []
			for key, value in assetDict.items():
				atype = key
				acount = len([item for item in value if item])
				sumtable.append([atype, acount])
			print(tabulate(sumtable, headers=["Asset Type", "Asset Count"], tablefmt='pretty'))	
		else:
			allassets = get_assets(ppdmuri, token, asset)
			if len(allassets) == 0:
				print('The asset could not be found')
			elif len(allassets) == 1:
				for asset in allassets:
					print("---------------------------------------------------------")
					print("Asset Name:", asset["name"])
					print("Asset Type:", asset["type"])
					print("Last Backup:", asset["lastAvailableCopyTime"])
			else:
				assetlist = []
				for asset in allassets:
					try:
						if asset["type"] == "VMWARE_VIRTUAL_MACHINE":
							assetlist.append([asset["name"], asset["type"], asset["lastAvailableCopyTime"], asset["details"]["vm"]["guestOS"]])
						elif asset["type"] == "KUBERNETES":
							assetlist.append([asset["name"], asset["type"], asset["lastAvailableCopyTime"], asset["details"]["k8s"]["subType"]])
						elif asset["type"] == "ORACLE_DATABASE":
							assetlist.append([asset["name"], asset["type"], asset["lastAvailableCopyTime"], asset["details"]["database"]["clusterName"]])
						elif asset["type"] == "MICROSOFT_SQL_DATABASE":
							assetlist.append([asset["name"], asset["type"], asset["lastAvailableCopyTime"], asset["details"]["database"]["clusterName"]])
						elif asset["type"] == "FILE_SYSTEM":
							assetlist.append([asset["details"]["fileSystem"]["hostName"], asset["type"], asset["lastAvailableCopyTime"], asset["details"]["fileSystem"]["hostOS"]])
						elif asset["type"] == "SAP_HANA_DATABASE":
							assetlist.append([asset["name"], asset["type"], asset["lastAvailableCopyTime"], asset["details"]["database"]["clusterName"]])
						elif asset["type"] == "VMAX_STORAGE_GROUP":
							assetlist.append([asset["name"], asset["type"]])
						elif asset["type"] == "XTREMIO_CONSISTENCY_GROUP":
							assetlist.append([asset["name"], asset["type"]])
						else:
							assetlist.append(["NA"])
					except Exception:
						print ("Some assets couldn't fetch")
				print(tabulate(assetlist, headers=["Client Name", "Client Type", "Last BackupCopy", "Details"], tablefmt="pretty"))
	elif policies:
		allpolicies = get_policies(ppdmuri, token, policies)
		policylist = []
		for policy in allpolicies:
			try:
				policylist.append([policy["name"], policy["assetType"], policy["type"], policy['stages'][0]['operations'][0]['schedule']['frequency'], policy['stages'][0]['operations'][0]['schedule']['startTime']])
			except Exception:
				print ("Some policies coudn't fetch")
				continue
		if len(policylist) == 0:
			print ("No policies found!")
		else:
			print(tabulate(policylist, headers=["Policy Name", "Policy Type", "Status", "Frequency", "Next Schedule"], tablefmt="pretty"))
	elif cred:
		if cred == 'all':
			allcreds = get_creds(ppdmuri, token, 'all')
			for credid in allcreds:
				print("---------------------------------------------------------")
				print("Credential Name:", credid["name"])
				print("Credential Username:", credid["username"])
				print("Credential ID:", credid["id"])
				print("Credential Type:", credid["type"])				
		else:
			print ("Select option all to display all the credentials")
	else:
		print ("Select correct option to display jobs, storage or policies, try show --help")

@my_app.command()
@click.option('--client', required=False, help="Specify a client name to backup")
@click.option('--backuptype', required=False, default="FULL", help="backup type is FULL by default")
@click.option('--retry', required=False, help="Retries failed jobs, takes ALL-FAILED argument")
@click.option('--period', required=False, help="Period of scope to list, takes 1day-ago or 1week-ago")
def backup(client, backuptype, retry, period):
	"""This command has options to perform Ad-hoc backup of a client or retry failed jobs\n
	backup --client <asset-name> --backuptype full (Full backup only)\n
	backup --retry ALL-FAILED --period <1day-ago | 1week-ago>
	"""
	if client:
		vms = get_assets(ppdmuri, token, client)
		if len(vms) == 0:
			print("Client Name {} could not be found".format(client))
		elif (len(vms) > 1):
			print ("Client Name {} yielded in more than 1 result".format(client))
			print("Specify the exact client name")
		elif (len(vms) == 1):
			print("Performing Ad-hoc backup for Client", vms[0]["name"])
			activityid = adhoc_backup(ppdmuri, token, vms[0]["id"], backuptype)
			print ("Backup has been triggered for {}, check the status with a command monitor --activityid ".format(client) + activityid)
	elif retry:
		if retry == 'ALL-FAILED':
			window = getwindow(period)
			retryDict = {}
			activities = get_activities(ppdmuri, token, 'ALL-FAILED', window)
			try:
				for activity in activities:
					if activity['classType'] == 'JOB':
						childid = activity['id']
						jobgroupid = activity['parentId']
						if (jobgroupid in retryDict.keys()):
							retryDict.get(jobgroupid).append(childid)
						else:
							newlist=[]
							newlist.append(childid)
							retryDict[jobgroupid]=newlist
					else:
						pass
			except Exception:
				pass
			if len(retryDict) == 0:
				print ("There are no failed jobs that are retryable")
			else:
				for actid, joblist in retryDict.items():
					retryfailed = backup_retry(ppdmuri, token, actid, joblist)
					print ("Backup has been triggered, monitor the backup using monitor --activityid {}".format(retryfailed))
		else:
			print ("Please select the correct option, type command --help for more information")
	else:
		print ("Please select the correct option, type command --help for more information")

@my_app.command()
@click.option('--activityid', required=False, help="Specify an activity id to monitor")
@click.option('--jobs', required=False, help="It takes 'running' as an argument")
@click.option('--period', required=False, help="The period of scope to list, default 1day-ago")
def monitor(activityid, jobs, period):
	"""This command monitors active jobs \n
	monitor --activityid <activity-id> \n
	monitor --jobs running [--period 1day-ago | 1week-ago. --period is optinal]\n
	"""
	if activityid:
		monitor_activity(ppdmuri, token, activityid)
	elif (jobs == 'running'):
		window = getwindow(period)
		activities = get_activities(ppdmuri, token, jobs, window)
		activitylist = []
		if len(activities) == 0:
			print ("There are no jobs to display, change the criteria and try again")
		else:
			for activity in activities:
				try:
					activitylist.append([activity['protectionPolicy']['name'], activity['classType'], activity['asset']['name'], activity['state']])
				except Exception:
					print ("Some jobs couldn't fetch")
					continue
			print(tabulate(activitylist, headers=["Policy Name", "Job Type", "Asset Name", "Status"], tablefmt="pretty"))
	else:
		print ("Please select the correct option, type --help")

@my_app.command()
@click.option('--backupsize', required=False, help="Displays backup size of asset or assets")
def report(backupsize):
	"""This command displays backup size of an asset or combined backup size of all the assets \n
	Example commands: \n
	report --backupsize <assetname> or <keyword> \n
	report --backupsize all
	"""
	if backupsize:
			allassets = get_assets(ppdmuri, token, backupsize)
			assetlist = []
			if len(allassets) == 0:
				print('The asset could not be found')
			elif (backupsize == 'all'):
				for asset in allassets:
					try:
						assetlist.append([asset["name"], asset["protectionCapacity"]["size"]])
					except Exception:
						print ("Some assets couldn't fetch")
				df = pd.DataFrame(assetlist)
				print("-----------------------------------------------------")
				print ("This report shows the single largest backup size")
				print("-----------------------------------------------------")				
				print ("Total number of assets: ", df[0].count())
				print ("Total Largest Backup (GB):", "%.2f" %((df[1].sum())/1024/1024/1024))
				# print(tabulate(df, headers=["Clients", "Total Backup (GB)"], tablefmt="pretty", showindex="False"))
			else:
				for asset in allassets:
					try:
						assetlist.append([asset["name"], asset["protectionCapacity"]["size"]])
					except Exception:
						print ("Some assets couldn't fetch")
				print(tabulate(assetlist, headers=["Client Name", "Largest Backup (Bytes)"], tablefmt="pretty"))
	else:
		print ("Please specify a correct option, type --help")

@my_app.command()
@click.option('--assetgroup', required=False, help="Displays backup size of asset or assets")
def create(assetgroup):
	"""This command displays i"""

@my_app.command()
@click.option('--cred', required=False, help="Deletes selected credentials")
def delete(cred):
	"""This command deletes selected credentials \n
	Example commands: \n
	delete --cred <user>
	"""
	if cred:
		credid = get_creds(ppdmuri, token, cred)
		if len(credid) == 0:
			print('The credentials could not be found')
		else:
			delete_cred(ppdmuri, token, credid, cred)


@my_app.command()
@click.option('--display', required=False, help="Lists all the alerts")
@click.option('--ack', required=False, help="Acknowledges all the alerts")
def alerts(display, ack):
	"""This command displays and acknowledges alerts \n
	Example commands: \n
	alerts --display <warning | critical | informational | summary> \n
	alerts --ack <warning | critical | informational | all>
	"""
	if display in ["warning", "critical", "informational"]:
		allalerts = get_alerts(ppdmuri, token, display)
		alertslist = []
		if len(allalerts) == 0:
			print ("There are no alerts to display, change the criteria and try again")
		else:
			for alert in allalerts:
				try:
					alertslist.append([alert['messageID'], alert['category'], alert['severity'], alert['responseAction'], alert['postedTime']])
				except Exception:
					print ("Some jobs couldn't fetch")
					continue
			print(tabulate(alertslist, headers=["messageID","Category", "Severity", "Response Action", "Posted Time"], tablefmt="pretty"))
	elif display == 'summary':
		alertslist = []
		allalerts = get_alerts(ppdmuri, token, display)
		if len(allalerts) == 0:
			print ("No alerts found!")
		else:
			for alert in allalerts:
				try:
					alertslist.append([alert['severity']])
				except Exception:
					print ("Some alerts couldn't fetch")
			print ()
			ok = countList(alertslist, 'WARNING')
			failed = countList(alertslist, 'CRITICAL')
			canceled = countList(alertslist, 'INFORMATIONAL')
			totaljobs = (ok+failed+canceled)
			sumlist = [(ok, failed, canceled, totaljobs)]
			print("															")
			print("ALERT SUMMARY REPORT                  ")
			print(tabulate(sumlist, headers=["Warning", "Critical", "Informational", "Total Alerts"], tablefmt="pretty"))
	elif ack in ["warning", "critical", "informational", "all"]:
		alertslist = []
		allalerts = get_alerts(ppdmuri, token, ack)
		for alert in allalerts:
			alertslist.append(alert['id'])
		# print ("Acknowledging the following {} alerts".format(ack))
		# print (alertslist)
		ackalerts = ack_alerts(ppdmuri, token, alertslist)
		print ("Acknowledged {} {} alerts".format(ackalerts, ack))

	else:
		print ("Please select the correct option, type command --help for more information")

if __name__ == '__main__':
	my_app()