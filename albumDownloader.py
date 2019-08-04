import argparse
import os
from progressbar import Bar, Percentage, ProgressBar
import time
import urllib.parse
import urllib.request
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError

client_id = 'YOUR-CLIENT-ID-HERE'
client_secret = 'YOUR-CLIENT-SECRET-HERE'

client = ImgurClient(client_id, client_secret)

parser = argparse.ArgumentParser()
parser.add_argument("username", nargs='?', default="Unknown_User")
parser.add_argument("-a", "--album", 
                    help="Specify an album to get only that albums images.")
parser.add_argument("-i", "--images", action="store_true",
                    help="Get the user's content by the images associated "\
                    "with their account rather than their albums. This will fail "\
                    "if the user's images are not publicly available. This option "\
                    "should not be used with the --album option.")
parser.add_argument("-c", "--credits", action="store_true",
                    help="View credit info for application after successful execution.")
args = parser.parse_args()

pbar = None
downloaded = 0

def show_progress(count, block_size, total_size):
    global pbar
    global downloaded
    if pbar is None:
        pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=total_size).start()
    if count > 0:
        downloaded += block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.finish()
        pbar = None
        downloaded = 0
		
def get_images_from_album(album_id):
    items = client.get_album_images(album_id)
    if not os.path.exists(args.username + "/" + album_id):
        os.makedirs(args.username + "/" + album_id)
    os.chdir(args.username + "/" + album_id)
    for item in items:
        print("Downloading " + item.link)
        urllib.request.urlretrieve(item.link, os.path.basename(urllib.parse.urlparse(item.link).path), show_progress)
    urllib.request.urlcleanup()
    os.chdir("../..")
	
def get_user_content_by_images(username):
    image_count = client.get_account_images_count(username)
    if image_count != 0:
        images = client.get_account_images(username)
        if len(images) != image_count:
            print("Image count does not equal number of images retrieved! Must implement paging!")
        if not os.path.exists(username):
            os.makedirs(username)
        os.chdir(username)
        for image in images:
            print("Downloading " + image.link)
            urllib.request.urlretrieve(image.link, os.path.basename(urllib.parse.urlparse(image.link).path), show_progress)
            time.sleep(2) # pause to keep from going over the rate limit
        urllib.request.urlcleanup()
        os.chdir("..")

try:
    if args.album and args.images:
        print("The --images and --album options should not be used together!")
        parser.print_help()
        quit()
    if args.images:
        if args.username == "Unknown_User":
            print("When using the --images option, a valid username must be provided!")
            parser.print_help()
            quit()
        get_user_content_by_images(args.username)
        quit()
    if not args.album:
        if args.username == "Unknown_User":
            print("If not specifying an album, a valid username must be provided!")
            parser.print_help()
            quit()
        # Try to get a user's content from their albums
        album_count = client.get_account_album_count(args.username)
        # If no albums, try to download they images associated with their account
        if album_count == 0:
            get_by_images = input("This user has no albums. "\
                                  "Would you like to try to get their content by their images? \n"\
                                  "Type 'Y' for yes or anything else to quit:\n")
            if get_by_images == 'Y':
                get_user_content_by_images(args.username)
            quit()
        else:
            albums = client.get_account_album_ids(args.username)
            if len(albums) != album_count:
                print("Album count does not equal number of albums retrieved! Must implement paging!")
            for album in albums:
                get_images_from_album(album)
                time.sleep(5) # pause to keep from going over the rate limit
    else:
        # Download a single album
        get_images_from_album(args.album)
    if args.credits:
        for k, v in client.credits.items():
            print(k, v)
        print("UserReset in local time: " + time.strftime('%Y-%m-%d %H:%M:%S',
              time.localtime(int(client.credits["UserReset"]))))
except ImgurClientError as e:
    print(e.error_message)
    print(e.status_code)
