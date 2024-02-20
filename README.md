# Zoom-importer

Effortlessly move your [Zoom](https://zoom.us) recordings to [Backblaze](https://www.backblaze.com/b2/cloud-storage.html) for cheap storage and sharing

## Why?

Because money (USD / month):

| Storage / Platform	|	[Zoom](https://zoom.us/buy?plan=pro&period=annual&from=cmr30&addon_period=annual&usageType=business)	|	[Backblaze](https://www.backblaze.com/b2/cloud-storage-pricing.html) |
| --------| ------ | -------|
| **30GB**	|	10	|	0.21 |
| **200GB**	|	40	|	1.06 |
| **1TB**	|	100	|	7.00 |
| **5TB**	|	500	|	35.00 |

Yes, this is not a mistake.

And I am assuming 10% view rate here, which is very high for me, so it's even cheaper in Backblaze reality.

Use great [Cloud Storage Cost Calculator](http://coststorage.com) to check your savings with your cloud storage provider of choice.

## Quick start guide

1. Choose if you'd like to do it from your laptop or server. You'd need fast internet and free space on the disk to fit the largest of your recordings (files are deleted upon upload).
1. Clone or download the repo
2. Get all dependencies `pip3 install -r requirements.txt`
3. Rename `example.env` to `.env` and open it with an editor
4. Register for [Zoom Dev account](https://developers.zoom.us) and create a new app
    0. Create a Server-to-Server OAuth app:
    1. Navigate to the [Zoom Marketplace](https://marketplace.zoom.us/develop)
    2. Click on the `Develop` button in the top-right corner
    3. Select `Build App` from the dropdown menu
    4. Choose `Server-to-Server` as the app type
    5. Grant the app access to `Recording: Read` scope
    6. Get your API Key and Secret and paste them into `.env` file

5. [Register for Backblaze](https://www.backblaze.com/b2/sign-up.html), create a bucket, drop it's name into .env file
6. Create a new auth key in Backblaze, drop it's ID and the Key into .env file
7. Choose a range of dates you'd like to move. If not sure — export a list of all recording from zoom web interface and check it's first and last line — and drop them into `.env` file
8. Check that all dependencies are met and run the app `python3 zoom-importer.py`. It should show you the dates, meeting names and download/upload notifications along with some stats: time elapsed, data cleaned from Zoom and cleanup speed.
9. Add your credit card to Backblaze on [billing page](https://secure.backblaze.com/billing_card.htm), so you are not blocked when you hit 10GB free limit.
10. Profit

## Tuning

I do save audio track, chat transcripts and one video file recording per meeting. Video file is selected to retain maximum information with following priorities: `shared_screen_with_gallery_view`, `gallery_view`, `shared_screen_with_speaker_view`, `speaker_view`, `shared_screen`. First hit from the list is saved, other videos are discarded.

You might want to preserve different set of files, this can be tuned in lines 62-72. Complete list of recording file types can be found [here](https://marketplace.zoom.us/docs/api-reference/zoom-api/methods/#operation/recordingGet).

## Code quality, bugs and feature requests

I am not a professional python developer and code might be obscene without me realising it. Sorry about that, pull requests are very welcome.

This script worked for my 3 years worth of recordings: 3k meetings, 1,3TB of storage in Zoom, but might break in your case. Please open an issue via GitHub and include tracebacks, I will do my best to fix them.

## Automatically move new recordings

There are two approaches to move new recordings from Zoom to Backblaze automatically:

1. Run this script [periodically](https://en.wikipedia.org/wiki/Cron), on the end of the day, e. g.

2. Subscribe to a '[zoom recording completed](https://marketplace.zoom.us/docs/guides/guides/managing-recordings/)' webhook from zoom and run this script when said webhook is fired — I recommend this [excellent webhook server](https://github.com/adnanh/webhook) for that.

Alternatively, use some of this lively tools for AWS (I am personally too scared to ops AWS, but you might be more experienced or braver):
- https://github.com/danielsoneg/egd-zoom_aws_sync
- https://github.com/openlibraryenvironment/serverless-zoom-recordings
- https://github.com/Speeeddy/zoom-recording-s3-exporter
- https://github.com/ColoredCow/zoom-s3-recording-migrations-lambda
- https://github.com/loneJogger/zoom-archiver
- https://github.com/benniemosher/recordings-archiver