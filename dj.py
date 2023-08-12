# ===========================================================================

import json
import sys 
import os
from datetime import datetime
from subprocess import call

# ===========================================================================

cli_args = sys.argv[1:] 
testing = False #  testing mode - changes runtime stuff

#  enable testing mode
if cli_args:
    if "t" in cli_args:
        testing = True

#  config file stuff
data_file = "data.json"
data_default = {
    "last_used_id":0,
    "media_types":[
        "CD",
        "DVD"
    ],
    "disks":[]
}

config_file = "config.json"
config_default = {
    "scan_directory":f"/run/media/{os.getlogin()}"
    }

#  testing mode runtime stuff
if testing:
    print("-> started in testing mode")
    config_file = "testing_config.json"
    data_file = "testing_data.json"

# ===========================================================================

#  used when FileNotFound is caught
def create_file(path, data):
    '''used for creating the config/data files when not present'''
    with open(path, 'w') as file:
        file.write(json.dumps(data, indent=4))

#  check if files are there, create them if not
def validate_files():
    '''check if files are there, create them if not'''
    if not os.path.exists(config_file):
        print("-> created config file:", config_file)
        create_file(config_file, config_default)
    if not os.path.exists(data_file):
        print("-> created data file:", data_file)
        create_file(data_file, data_default)


def load_file(file):
    if not os.path.exists(file):
        validate_files()
    with open(file, 'r') as f:
        return json.load(f)


def save_file(file, data):
    with open(file, 'w') as file:
        file.write(json.dumps(data, indent=4))

# ===========================================================================

def get_today():
    date_fmt = "%m/%d/%y"
    now = datetime.now()
    return now.strftime(date_fmt)


def clear():
    call('clear')

# ===========================================================================

def increase_id():
    data = load_file(data_file)
    data["last_used_id"] += 1 
    save_file(data_file, data)
    return data["last_used_id"]
    

def pull_id():
    new_id = str(increase_id())
    while len(new_id) < 3:
        new_id = "0" + new_id
    return new_id

# ===========================================================================

class Disk:
    def __init__(self, path):
        self.path = path
        self.id = None
        self.label = None
        self.write_date = None
        self.is_encrypted = False
        self.storage_location = None
        self.capacity = None
        self.tags = []
        self.contents = []

    def data(self):
        return self.__dict__

    def dump(self):
        return json.dumps(self.data(), indent=4)

    def strip_root_dir(self, full_path):
        #  strips the /run/media/{username} from the path
        root_len = len(self.path)
        return full_path[root_len:]

    def scan_disk(self, reset_contents=True):
        #  return a list of all paths found on the disk
        if reset_contents:
            self.contents = []
        for root, dirs, files in os.walk(self.path):
            for file in files:
                full_path = os.path.join(root, file)
                stripped = self.strip_root_dir(full_path)
                self.contents.append(stripped)
            for dir in dirs:
                full_path = os.path.join(root, dir)
                stripped = self.strip_root_dir(full_path)
                self.contents.append(stripped)
        return self.contents

# ===========================================================================

def find_disks(media_path):
    '''scan the media path for directories'''
    #! should really just tack this onto load_disks(), it isn't called
    #! anywhere else
    try: 
        return os.listdir(media_path)
    except FileNotFoundError:
        print("-> scan directory doesn't exist")
        print("-> you can change the scan dir path in the settings.")
        return -1
    

# ===========================================================================


#  save the disk dictionary to the json db
def save_disk(disk_data):
    data = load_file(data_file)
    data["disks"].append(disk_data)
    save_file(data_file, data)


def load_disk():
    """
    disk is loaded from scan directory. user selects disk if multiple
    directories are found.
    """
    selected_disk = None    
    while True:
        clear()
        # heading
        print("  ->  Load Disks  <-")
        # load config, scan for disks
        print()
        print("-> loading information...")
        config = load_file(config_file)
        print("-> current scan directory: " + scan_dir)

        try: 
            disks = os.listdir(media_path)
        except FileNotFoundError:
            print("-> scan directory doesn't exist")
            print("-> you can change the scan dir path in the settings.")
            disks = -1

        print()
        #  stop if scan diretory doesn't exist
        if disks == -1: # -1 if FileNotFound error occured
            input("-> press enter to continue ")
            return

        #  stop if len(disks) == 0
        if len(disks) == 0:
            print("-> no disks found")
            print("-> ensure the disk is mounted on the correct path.\n")
            input("-> press enter to continue ")

        #  auto select disk if len(disks) == 0
        elif len(disks) == 1:
            selected_disk = disks[0]
        #  user selects disk from list if len(disks) > 1
        elif len(disks) > 1:
            print("-> disks found: " + str(len(disks)))
            print("-> select a disk from the list\n")
            for d in disks:
                i = disks.index(d)
                print(f"--> {str(i + 1)} {d}")
            print()
            while True:
                try:
                    select = input("-> ")
                    selected_disk = disks[int(select)]
                    break
                except:
                    print("-x select a disk from the list by number")

        print()
        print("-> loaded disk: ", + selected_disk)
        input("-> press enter to continue ")
        return selected_disk
        
# ===========================================================================

def clear():
    call('clear')


def report_disk_data(dd):
    file_count = len(dd["files"])
    print()
    print("=" * 50)
    print()
    print("disk label    ->   ", dd["title"])
    print("media id      ->   ", dd["media_id"])
    print("date created  ->   ", dd["date_created"])
    print("file count    ->   ", str(file_count))
    if dd["tags"]:
        print("tags: ", end='')
        print(dd["tags"])
    print()
    print("=" * 50)
    print()


def ask_tags():
    print("-> enter tags separated by a space")
    tags = input("-> ")
    return tags.split()

# ===========================================================================

def main():
    media_path = load_file(config_file)["scan_directory"]
    disk_name = find_disks(media_path)
    disk_path = os.path.join(media_path, disk_name)
    print("-> scanning disk...")
    found_files = scan_disk(disk_path)
    disk_data = {
        "title":disk_name,
        "media_id":pull_id(),
        "date_created":get_today(),
        "tags":None,
        "files":found_files,
    }
    clear()
    report_disk_data(disk_data)
    while True:
        command = input("-> ")
        if command == "tag":
            disk_data["tags"] = ask_tags()
            clear()
            report_disk_data(disk_data)
        elif command == "save":
            save_disk(disk_data)
            print("-> saved disk data")
            return

# ===========================================================================
#  UI functions



def search_nav():
    while True:
        clear()
        print("[]. Search for a specific file")
        print("[]. View disks")
        print("[]. Database statistics")
        print("[Q]. Return to the main menu")
        print()
        select = input("-> ")
        if select.lower() == 'q':
            return
        elif select == "1":
            pass 
        elif select == '2':
            pass 
        elif select == '3':
            pass 


def settings_nav():
    while True:
        clear()
        input("UwU")


def scan_nav():
    disk_path = load_disk()
    if not disk_path:
        return
    print("-> loading new disk: disk_path")
    try:
        disk = Disk(disk_path)
    except Exception as error:
        print("\n-> failed creating disk object")
        print("-> error: " + error)
        input("-> press enter to continue ")
        return 
    while True: 
        clear()
        # header info 
        print("> Disk: " + disk.label)
        print()
        # options 
        print("[1]. Scan disk contents")
        print("[2]. ")
        
    


def main_nav():
    while True:
        clear()
        print("[1]. Scan disk")
        print("[2]. Search database")
        print("[3]. Settings")
        print("[Q]. Exit")
        print()
        select = input("-> ")
        if select.lower() == 'q':
            break 
        elif select == '1':
            pass
        elif select == '2':
            search_nav() 
        elif select == '3':
            settings_nav() 

# ===========================================================================

#main()
x = Disk("/home/jakers/Documents")
x.scan_disk()
print(x.contents)

# ===========================================================================
