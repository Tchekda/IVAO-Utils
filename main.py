from ivao import Server, Pilot, Client
import os
import datetime
from pushbullet import PushBullet

server = Server()

tracked_users = [485573]
air_static = []

pb = False
PB_TITLE = "IVAO Tracker"


# noinspection PyBroadException
@server.event("update")
def get_data(clients):
    count = {
        'pilots': 0,
        'ground': 0,
        'air': 0,
        'atc': 0,
        'folme': 0
    }

    for _, client in clients.items():
        if client.client_type == "PILOT":
            count['pilots'] += 1
            if client.ground:
                count['ground'] += 1
            else:
                count['air'] += 1
        elif client.client_type == "ATC":
            count['atc'] += 1
        elif client.client_type == "":
            count['atc'] += 1

    data = "Current Data : {} pilots ({} ground / {} air) - {} ATC - {} Follow Me".format(count['pilots'],
                                                                                          count['ground'],
                                                                                          count['air'],
                                                                                          count['atc'], count['folme'])

    print(data)
    if pb:
        for push in pb.get_pushes():
            text = push['body'].lower()
            command = text.split()[0]
            commands = ['help', 'stop', 'data', 'list', 'add', 'del', 'moving']
            if command in commands and push['dismissed'] == False:
                print("Received command :", command)
                if command == "stop":
                    pb.push_note(PB_TITLE, "Stop Received")
                    server.stop_update_stream()
                elif command == "data":
                    pb.push_note(PB_TITLE, data)
                elif command == "list":
                    message = "Tracked : "
                    for vid in tracked_users:
                        message += str(vid) + " "
                    pb.push_note(PB_TITLE, message)
                elif command == "add":
                    try:
                        vid = int(text.split()[1])
                    except:
                        pb.push_note(PB_TITLE, "Invalid VID")
                    else:
                        if vid not in tracked_users:
                            tracked_users.append(vid)
                            pb.push_note(PB_TITLE, str(vid) + " has been added to the tracked list")
                        else:
                            pb.push_note(PB_TITLE, str(vid) + " was already in the tracked list")
                elif command == "del":
                    try:
                        vid = int(text.split()[1])
                    except:
                        pb.push_note(PB_TITLE, "Invalid VID")
                    else:
                        if vid in tracked_users:
                            tracked_users.remove(vid)
                            pb.push_note(PB_TITLE, str(vid) + " has been removed from the tracked list")
                        else:
                            pb.push_note(PB_TITLE, str(vid) + " wasn't in the tracked list")
                elif command == "help":
                    message = "Commands : "
                    for cmd in commands:
                        message += cmd + "\n"
                    pb.push_note(PB_TITLE, message)
                elif command == "moving":
                    try:
                        vid = int(text.split()[1])
                    except:
                        pb.push_note(PB_TITLE, "Invalid VID")
                    else:
                        if vid in server.clients:
                            if vid in air_static:
                                pb.push_note(PB_TITLE, str(vid) + " is currently static in the air")
                            else:
                                air_static.append(vid)
                                pb.push_note(PB_TITLE, str(vid) + " Will be checked on next update")
                        else:
                            pb.push_note(PB_TITLE, str(vid) + " is not connected")
            if push['dismissed'] == False:
                pb.dismiss_push(push['iden'])


@server.event("connect")
def connect(client: Client, first_run: bool):
    if client.vid in tracked_users:
        if first_run:
            if pb:
                pb.push_note(PB_TITLE,
                             get_short_client(
                                 client) + " was already connected since " + client.connection_time.strftime(
                                 "%H:%M:%S %b %d %Y", ))
        else:
            if pb:
                pb.push_note(PB_TITLE, get_short_client(client) + " just connected at " + get_time())


@server.event("disconnect")
def disconnect(client: Client):
    if client.vid in tracked_users:
        if pb:
            pb.push_note(PB_TITLE, get_short_client(client) + " just disconnected at " + get_time())


@server.event("static")
def static(client: Pilot):
    if client.ground == False and client.vid in tracked_users:
        if client.vid not in air_static:
            if pb:
                pb.push_note(PB_TITLE, get_short_client(client) + " got air-static at " + get_time())
            air_static.append(client.vid)


@server.event("moving")
def moving(client: Pilot):
    if client.vid in air_static:
        air_static.remove(client.vid)
        if pb:
            pb.push_note(PB_TITLE, get_short_client(client) + " is moving again at " + get_time())


@server.event("land")
def land(client: Pilot):
    if client.vid in tracked_users:
        if pb:
            pb.push_note(PB_TITLE, get_short_client(client) + " just landed at " + get_time())


@server.event("takeoff")
def land(client: Pilot):
    if client.vid in tracked_users:
        if pb:
            pb.push_note(PB_TITLE, get_short_client(client) + " just takeoff at " + get_time())


def get_time():
    return datetime.datetime.now().strftime("%H:%M:%S", )


def get_short_client(client: Client):
    return client.callsign + "(" + str(client.vid) + ")"


if __name__ == "__main__":
    if 'API_KEY' in os.environ:
        pb = PushBullet(os.environ['API_KEY'])
        pb.delete_pushes()
        pb.push_note(PB_TITLE, "Connected at " + datetime.datetime.now().strftime("%H:%M:%S %b %d %Y", ))
    try:
        server.run_update_stream(delay=0.5)
    except Exception as e:
        print("Error : " + str(e))
        if pb:
            pb.push_note(PB_TITLE, "Error : " + str(e))
    finally:
        print("Closing at " + datetime.datetime.now().strftime("%H:%M:%S %b %d %Y", ))
        if pb:
            pb.push_note(PB_TITLE, "Closing at " + datetime.datetime.now().strftime("%H:%M:%S %b %d %Y", ))
