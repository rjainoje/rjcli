# rjcli v1.0.0 for Dell EMC Power Protect Data Manager - Github @ rjainoje
__author__ = "Raghava Jainoje"
__version__ = "1.0.2"
__email__ = "raghavachary_j@yahoo.com"

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
		filter = 'name lk "%{}%"'.format(asset)
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
		filter = 'name lk "%{}%"'.format(policies)
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

def get_activities(ppdmuri, token, jobs, window):
	'''This function returns activities based on filters in JSON'''
	uri = ppdmuri + 'activities'
	headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
	filter = 'classType in ("JOB", "JOB_GROUP") and createdTime gt "{}"'.format(window)
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
		print("The call {}{} failed with exception:{} and {}".format(response.request.method, response.url, err, r))
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
		window = gettime.isoformat()
	elif period == '1week-ago':
		gettime = datetime.now() - timedelta(days = 7)
		window = gettime.isoformat()
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
def show(jobs, period, storage, asset, policies):
	"""This command displays information about jobs, storage, assets and policies \n
	Example commands: \n
	show --jobs summary --period <1day-ago | 1week-ago> \n
	show --jobs <successful | failed | all> --period <> \n
	show --storage details \n
	show --asset <asset-name | all> \n
	show --policies <policy-name | all>
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
		for activity in activities:
			try:
				activitylist.append([activity['protectionPolicy']['name'], activity['classType'], activity['result']['status'], activity['createTime']])
			except Exception:
				print ("Some jobs couldn't fetch")
				continue
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
		for storage in stgtargets:
			try:
				print("                                                         ")
				print("---------------------------------------------------------")
				print("Storage Name:", storage["name"])
				print("Storage Type:", storage["type"])
				print("Storage Model:", storage["details"]["dataDomain"]["model"])
				print("OS Version:   ", storage["details"]["dataDomain"]["version"])
				print("Total Size (GB):", "%.2f" %(int(storage["details"]["dataDomain"]["totalSize"])/1024/1024/1024))
				print("Used Percentage:", "%.2f" %(int(storage["details"]["dataDomain"]["percentUsed"])))
				print("Last Discovered:", storage["lastDiscoveryStatus"])
			except Exception:
				print ("Some storage couldn't fetch")
				continue
	elif asset:
		allassets = get_assets(ppdmuri, token, asset)
		if len(allassets) == 0:
			print('The asset could not be found')
		elif len(allassets) == 1:
			for asset in allassets:
				print("---------------------------------------------------------")
				print("Asset Name:", asset["name"])
				print("Asset Type:", asset["type"])
				print("Last Backup:", asset["lastAvailableCopyTime"])
				print("OS Version :", asset["details"]["vm"]["guestOS"])
		else:
			assetlist = []
			for asset in allassets:
				try:
					assetlist.append([asset["name"], asset["type"], asset["lastAvailableCopyTime"]])
				except Exception:
					print ("Some assets couldn't fetch")
			print(tabulate(assetlist, headers=["Client Name", "Client Type", "Last BackupCopy", "Guest OS"], tablefmt="pretty"))
	elif policies:
		allpolicies = get_policies(ppdmuri, token, policies)
		policylist = []
		for policy in allpolicies:
			try:
				policylist.append([policy["name"], policy["assetType"], policy["type"], policy['stages'][0]['operations'][0]['schedule']['frequency'], policy['stages'][0]['operations'][0]['schedule']['startTime']])
			except Exception:
				print ("Some policies coudn't fetch")
				continue
		print(tabulate(policylist, headers=["Policy Name", "Policy Type", "Status", "Frequency", "Next Schedule"], tablefmt="pretty"))
	else:
		print ("Select correcct option to display jobs, storage or policies, try show --help")

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
	"""This will monitor active jobs \n
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

if __name__ == '__main__':
    my_app()