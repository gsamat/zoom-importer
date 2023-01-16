import requests
import json
from slugify import slugify 
from datetime import date, timedelta
import b2sdk.v2 as b2
import b2sdk
import os
import time
from environs import Env
import urllib

def download_file(url, filename):
	response = requests.get(
		url=url,
		headers={
			"Authorization": f"Bearer {ZOOM_KEY}",
		},
	)
	with open(filename, 'wb') as f:
		f.write(response.content)

def b2_file_size(file):
    try:
        return b.get_file_info_by_name(file).content_length
    except (b2sdk.exception.FileNotPresent):
        return 0

def delete_recordings(uuid):
	try:
		uuid = urllib.parse.quote(urllib.parse.quote(uuid, safe = ''))
		response = requests.delete(
			url=f"https://api.zoom.us/v2/meetings/{uuid}/recordings",
			headers={
				"Authorization": f"Bearer {ZOOM_KEY}",
			},
		)
	except requests.exceptions.RequestException:
		print(f"delete failed for {uuid}")

def send_request(date_from, date_to):
	try:
		response = requests.get(
			url="https://api.zoom.us/v2/users/me/recordings",
			params={
				"from": date_from,
				"to": date_to
			},
			headers={
				"Authorization": f"Bearer {ZOOM_KEY}",
			},
		)
		meetings = response.json()["meetings"]
		for meeting in meetings:
			name =  meeting['start_time'] + '-' + meeting['topic']
			print('	' + name)
			if meeting['recording_count'] > 0:
				files = meeting['recording_files']
				sizes = [x['file_size'] for x in files]
				global processed_storage
				processed_storage = processed_storage + sum(sizes)
				types = [x['recording_type'] for x in files]
				wanted_types = ['audio_only', 'chat_file']
				if 'shared_screen_with_gallery_view' in types:
					wanted_types.append('shared_screen_with_gallery_view')
				elif 'gallery_view' in types:
					wanted_types.append('gallery_view')
				elif 'shared_screen_with_speaker_view' in types:
					wanted_types.append('shared_screen_with_speaker_view')
				elif 'speaker_view' in types:
					wanted_types.append('speaker_view')
				elif 'shared_screen' in types:
					wanted_types.append('shared_screen')
				print(f"		{wanted_types}")
				for file in files:
					if file['recording_type'] in wanted_types:
						filename = slugify(name) + '.' + file['file_extension'].lower()
						size_zoom = file['file_size']
						size_bb = b2_file_size(filename)
						try:
							size_local = os.path.getsize(filename)
						except FileNotFoundError:
							size_local = 0
						if size_zoom > size_bb:
							if size_zoom > size_local:
								file_url = file['download_url']
								print('			start download: ' + filename)
								download_file(file_url, filename)
							print('			start upload: ' + filename)
							b.upload_local_file(filename, filename)
						try:
							os.remove(filename)
						except FileNotFoundError:
							pass
			delete_recordings(meeting['uuid'])
			time_elapsed = time.time() - time_start
			speed = processed_storage / (time_elapsed/60)
			print(f"total processed {processed_storage:,} bytes, elapsed {time_elapsed:,.0f} sec, {speed:,.0f} bytes per minute")
	except requests.exceptions.RequestException:
		print('HTTP Request failed')

def daterange(start_date, end_date):
    if start_date < end_date:
    	raise RuntimeError('start date should be > than end_date!')
    for n in range(int((start_date - end_date).days)):
        yield start_date - timedelta(n)

env = Env()
env.read_env()
B2_KEY_ID = env('B2_KEY_ID')
B2_KEY = env('B2_KEY')
BUCKET = env('BUCKET')
ZOOM_KEY = env('ZOOM_KEY')
DATE_FROM_Y = env.int('DATE_FROM_Y')
DATE_FROM_M = env.int('DATE_FROM_M')
DATE_FROM_D = env.int('DATE_FROM_D')
DATE_TO_Y = env.int('DATE_TO_Y')
DATE_TO_M = env.int('DATE_TO_M')
DATE_TO_D = env.int('DATE_TO_D')


info = b2.InMemoryAccountInfo()
b2_api = b2.B2Api(info)
b2_api.authorize_account("production", B2_KEY_ID, B2_KEY)
b = b2_api.get_bucket_by_name(BUCKET)
processed_storage = 0
time_start = time.time()

if __name__ == "__main__":
	start_date = date(DATE_FROM_Y, DATE_FROM_M, DATE_FROM_D)
	end_date = date(DATE_TO_Y, DATE_TO_M, DATE_TO_D)
	for single_date in daterange(start_date, end_date):
		print(f"{single_date.strftime('%Y-%m-%d')}")
		send_request(single_date.strftime("%Y-%m-%d"), single_date.strftime("%Y-%m-%d"))