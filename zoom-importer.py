import base64
import os
import time
import urllib
from datetime import date, timedelta

import b2sdk
import b2sdk.v2 as b2
import requests
from environs import Env
from slugify import slugify


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
        return bucket.get_file_info_by_name(file).content_length
    except (b2sdk.exception.FileNotPresent):
        return 0


def delete_recording(uuid):
    try:
        uuid = urllib.parse.quote(urllib.parse.quote(uuid, safe=''))
        response = requests.delete(
            url=f"https://api.zoom.us/v2/meetings/{uuid}/recordings",
            headers={
                "Authorization": f"Bearer {ZOOM_KEY}",
            },
        )
    except requests.exceptions.RequestException:
        print(f"delete failed for {uuid}")


def process_file(file, name):
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
			print('    start download: ' + filename)
			download_file(file_url, filename)
			# Check if the file was downloaded successfully
			if not os.path.exists(filename):
				print(f"Failed to download file: {filename}")
				return
	print('    start upload: ' + filename)
	# Check if the file exists and is accessible before upload
	if os.path.exists(filename) and os.access(filename, os.R_OK):
		bucket.upload_local_file(filename, filename)
	else:
		print(f"File {filename} doesn't exist or isn't accessible")
		return

	try:
		os.remove(filename)
	except FileNotFoundError:
		pass

def process_meeting(meeting):
    print(f"	{meeting['start_time']} {meeting['topic']}")
    if meeting['recording_count'] > 0:
        files = meeting['recording_files']
        global processed_storage
        sizes = [x['file_size'] for x in files]

        processed_storage = processed_storage + sum(sizes)
        types = [x['recording_type'] for x in files]
        wanted_types = ['audio_only', 'chat_file']
        extra_wanted_types = [
            'shared_screen_with_gallery_view',
            'gallery_view',
            'shared_screen_with_speaker_view',
            'speaker_view',
            'shared_screen',
        ]
        for t in extra_wanted_types:
            if t in types:
                wanted_types.append(t)
                break
    print(f"		{wanted_types}")
    for file in files:
        if file['recording_type'] in wanted_types:
            name = meeting['start_time'] + '-' + meeting['topic']
            process_file(file, name)
    delete_recording(meeting['uuid'])
    time_elapsed = time.time() - time_start
    speed = processed_storage / (time_elapsed / 60)
    print(
        f"total processed {processed_storage:,} bytes, elapsed {time_elapsed:,.0f} sec, {speed:,.0f} bytes per minute")


def get_recordings(date_from, date_to):
    # The maximum date range for this endpoing can be a month
    print(f"getting recordings from {date_from} to {date_to}...")
    response = requests.get(
        url="https://api.zoom.us/v2/users/me/recordings",
        params={
            "from": date_from.strftime("%Y-%m-%d"),
            "to": date_to.strftime("%Y-%m-%d"),
            'page_size': 300,
        },
        headers={
            "Authorization": f"Bearer {ZOOM_KEY}",
        },
    )
    meetings = response.json()['meetings']
    return meetings


def date_span(date_start, date_end, delta=timedelta(days=30)):
    if date_start > date_end:
        raise RuntimeError('start date should be lower than end date!')

    current_date = date_start
    while current_date < date_end:
        yield (current_date, min(current_date + delta, date_end))
        current_date += delta


# Get Zoom access token using Server-to-Server OAuth app
def get_zoom_access_token():
    print('getting Zoom access token...')
    params = {
        'grant_type': 'account_credentials',
        'account_id': env('ACCOUNT_ID'),
    }
    credentials = base64.b64encode(f"{env('CLIENT_ID')}:{env('CLIENT_SECRET')}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = requests.post(
        "https://zoom.us/oauth/token",
        params=params,
        headers=headers,
    )
    data = response.json()
    if not 'access_token' in data:
        raise Exception(data)
    return data['access_token']


def get_cloud_bucket():
    print('preparing B2 bucket...')
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", env('B2_KEY_ID'), env('B2_KEY'))
    return b2_api.get_bucket_by_name(env('BUCKET'))


env = Env()
env.read_env()

bucket = get_cloud_bucket()
processed_storage = 0
time_start = time.time()

if __name__ == "__main__":
    date_start = date(
        env.int('DATE_FROM_Y'),
        env.int('DATE_FROM_M'),
        env.int('DATE_FROM_D')
    )
    date_end = date(
        env.int('DATE_TO_Y'),
        env.int('DATE_TO_M'),
        env.int('DATE_TO_D'),
    )

    ZOOM_KEY = get_zoom_access_token()

    meetings = []
    for period_start, period_end in date_span(date_start, date_end):
        period_meetings = get_recordings(period_start, period_end)
        meetings.extend(period_meetings)
        if period_end > date.today():
            break
    meetings.sort(key=lambda x: x['start_time'])

    print(f'Total meetings in cloud: {len(meetings)}')
    for i, meeting in enumerate(meetings):
        print(i, meeting['start_time'], meeting['topic'])
        process_meeting(meeting)
