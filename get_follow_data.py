import requests
import json
import concurrent.futures
import time
import pandas as pd
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import config

client_id = config.client_id
bearer_token = config.bearer_token
user_agent = config.user_agent

# establish headers and session
HEADERS = {"client-id":client_id, "authorization":"Bearer %s" % bearer_token, "User-agent": user_agent}
s = requests.Session()
retry = Retry(connect=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
s.mount('http://', adapter)
s.mount('https://', adapter)
s.headers.update(HEADERS)

# job parameters
N_JOBS = 5 # number of parallel jobs to run
RATE_LIMIT = 800 # 800 requests per minute
SLEEP_TIME = 1.15*(N_JOBS*60)/RATE_LIMIT # sleep time to avoid rate-limiting

def safe_API_request(url, sleep_time):
	"""	Make API request and subsequently: (i) sleep to avoid rate-limit,
		(ii) check response for "Bad Request" or "Too Many Request"

		Inputs:
			url (str): url for API request
			sleep_time (float): amount of seconds to sleep for
		Outputs:
			r2j (dict): API response as a Python dictionary
	"""
	response = s.get(url)
	r2j = json.loads(response.text) # response to json
	time.sleep(sleep_time) # sleep to avoid hitting rate-limit

	# If no data was returned, identify error
	# {"error":"Bad Request", "status":400, "message":"..."}
	# {"error":"Too Many Requests", "status":429, "message": "..."}
	if "data" not in r2j:
		if r2j["error"].lower() == "bad request":
			# tqdm.write("Bad request for: " + user)
			# tqdm.write(response.text)
			pass

		elif r2j["error"].lower() == "too many requests":
			tqdm.write("Too many requests. Waiting 60 seconds and then retrying...")
			time.sleep(60)

			# retry
			response = s.get(url)
			r2j = json.loads(response.text)
			time.sleep(sleep_time)

	return r2j

def get_user_id(user):
	""" Get integer user ID corresponding to Twitch username.
		Why do we need this? -- because the API call "Get Users Follows"
		requires to_id or from_id and does not accept usernames.

		Inputs:
			user (str): Twitch username
		Outputs:
			ID (int): Twitch ID
	"""
	url = "https://api.twitch.tv/helix/users?login=%s" % user
	r2j = safe_API_request(url, sleep_time=SLEEP_TIME)

	# check for data again
	if "data" in r2j and r2j["data"]: # r2j["data"] may be empty, i.e. if streamer is banned
		ID = int(r2j["data"][0]["id"])
		return ID
	else:
		return None

def get_follow_data(ID, kind="followers", cursor=None, return_pagination=False, max_results=100, fmt=None):
	""" Make 1 API request to get a user's follow data. 
		Can either collect (i) followers, (ii) follows/following.
		Inputs:
			ID (int): Twitch ID for user to be collected
			kind (str): must be "followers" or "following"
			cursor (str): optional argument which specifies where to start when the response
				is multiple pages
			return_pagination (bool): if True, returns the cursor for the next page 
			max_results (int): maximum results to return in API request -- can be in range [1,100]	 
			fmt (int): fmt==1 is designed for getting streamers followers, fmt==2 is 
			designed for getting users follows, and fmt==3 only returns a list.
		Outputs:
			follow_data (dict or list): followers or follows data for Twitch user/streamer
	"""
	if kind == "followers":
		url_field, opp = "to", "from"
	else: # following
		url_field, opp = "from", "to"
	if cursor:
		url = "https://api.twitch.tv/helix/users/follows?%s_id=%i&first=%i&after=%s" % (url_field, ID, max_results, cursor)
	else:
		url = "https://api.twitch.tv/helix/users/follows?%s_id=%i&first=%i" % (url_field, ID, max_results)
		
	data = safe_API_request(url, sleep_time=SLEEP_TIME)
	
	if not data or not data["data"]:
		if return_pagination:
			return None, None
		else:
			return None

	# FORMAT
	# 1. Get streamer followers
	# {"ID":streamer_ID, "followers":[follower_id1, follower_id2, ...]}
	# 2. Get user follows
	# {"following":[[streamer_name1, time_followed1] , [streamer_name2, time_followed2] , ...]  }
	# 3. Generic get list of follows
	# [follow1, follow2, ...]
	if fmt == 1:
		follow_data = {"ID":ID, "followers":[x["%s_id" % opp] for x in data["data"]]}
	elif fmt == 2:
		follow_data = {ID: {"total":data["total"], "following": [[x["%s_name" % opp], x["followed_at"]] for x in data["data"]]}}
	else:
		follow_data = [x["%s_id" % opp] for x in data["data"]]
	
	if return_pagination:
		pagination = data["pagination"]
		if "cursor" in pagination:
			pagination = pagination["cursor"]
		return follow_data, pagination
	else:  
		return follow_data

def get_all_follow_data(ID, kind="followers", cursor=None, fmt=None):
	""" Get all follow data for a user. This function recursively calls get_follow_data
		to get multiple pages of results.
	"""
	# make 1 query and return cursor (in case no cursor was specified)
	follow_data, cursor = get_follow_data(ID, kind, cursor, return_pagination=True, max_results=100, fmt=fmt)
	
	# could not find data (i.e. user was banned or account was deleted)
	if not follow_data:
		return None

	# if there are < 1 full page of results, we can stop here
	if not cursor:
		return follow_data
	
	# else we recursively get each page
	count = 100 
	while cursor and count < 1000: # we choose to cap at 1000 total results (10 pages)
		results, cursor = get_follow_data(ID, kind, cursor, return_pagination=True, max_results=100, fmt=fmt)
		if fmt == 1:
			follow_data["followers"] = follow_data["followers"] + results["followers"]
		elif fmt == 2:
			follow_data[ID]["following"] = follow_data[ID]["following"] + results[ID]["following"]
		else:
			follow_data.extend(results)

		count += 100
		
	return follow_data

def get_streamer_followers_job(name):
	# tqdm.write(name)
	fmt=1
	# spaces allowed in usernames but not API queries, let's remove them.
	ID = get_user_id(name.replace(" ", ""))
	if ID:
		return {name: get_follow_data(ID, kind="followers", fmt=fmt)}
	else:
		return {}

def get_user_follows_job(ID):
	# tqdm.write(str(ID))
	fmt=2	
	return get_all_follow_data(ID, kind="following", fmt=fmt)

data = [] # global variable

def start_processing(job_func, my_iter, n_jobs):
	with tqdm(total=len(my_iter)) as pbar:
		with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as executor:
			future_proc = {executor.submit(job_func, x): x for x in my_iter}
			for future in concurrent.futures.as_completed(future_proc):
				if future.result():
					data.append(future.result())
				pbar.update(1)

def reformat_data(dat, outfile):
	data_fmt = {}
	for d in dat:
		if d: # if result is non-null
			key = next(iter(d))
			data_fmt[key] = d[key]

	with open(outfile, "w") as f:
		json.dump(data_fmt, f)

if __name__ == "__main__":
	# # ------- 1. GET STREAMER FOLLOWERS -------------
	# df = pd.read_csv("data/streamer_info_eng.csv")
	# # names = df["name"].values.tolist()
	# names = df.nlargest(200, "rec_hours_watched", keep="all")["name"].values.tolist() # top 200

	# start_processing(get_streamer_followers_job, names, n_jobs=N_JOBS)

	# reformat_data(data, "data/streamer_followers.json")

	# # ------- 2. GET USER FOLLOWS -------------
	# agg_followers_IDs = []
	# with open("data/streamer_followers.json", "r") as f:
	# 	streamer_followers_dict = json.load(f)
	# 	for streamer_followers in streamer_followers_dict.values():
	# 		agg_followers_IDs.extend(streamer_followers["followers"])
	# agg_followers_IDs = set(map(int, agg_followers_IDs))

	# # split the jobs up -- change n each run
	# agg_followers_IDs = list(agg_followers_IDs)
	# l = len(agg_followers_IDs)
	# n = 0
	# START, STOP = min(4000*n, l-1) , min(4000*(n+1), l)
	# agg_followers_IDs = agg_followers_IDs[START:STOP]
	
	# start_processing(get_user_follows_job, agg_followers_IDs, n_jobs=N_JOBS)

	# # reformat_data(data, "data/user_follows.json")
	# reformat_data(data, "data/user_follows-%i.json" % n)
	
	# ------- 3. AGGREGATE USER FOLLOWS -------------
	data = {}
	for n in range(4):
		with open("data/user_follows-%i.json" % n, "r") as f:
			data.update(json.load(f))

	with open("data/user_follows-full.json", "w") as out:
		json.dump(data, out)


