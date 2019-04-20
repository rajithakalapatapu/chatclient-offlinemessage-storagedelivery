"""
Name: Venkata Adilakshmi Rajitha Kalapatapu
Student ID: 1001682465
Login ID: vxk2465
"""


import tkinter as tk
from tkinter import ttk, scrolledtext, END
import socket
from threading import Thread
import selectors
import pprint

from http_helper import *

PPRINTER = pprint.PrettyPrinter(indent=4)
# References:
# Python GUI cookbook by Packtpub
# https://docs.python.org/3/howto/sockets.html#creating-a-socket
# https://pymotw.com/3/select/
# https://pymotw.com/3/selectors/
# https://docs.python.org/3/library/queue.html
# http://net-informations.com/python/net/thread.htm
# https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
# https://medium.com/swlh/lets-write-a-chat-app-in-python-f6783a9ac170

# global variable for storing server tkinter window - accessed by thread and main
server_window = tk.Tk()
# global variable for storing server socket - accessed by thread and main
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# a global data structure for storing the connected clients
#   connected_clients is a dict of tuples
#       keys are the address tuple containing host and port
#       values are a tuple which contains (client_socket, client_address, client_name)
#   {
#       (address_tuple): (client_socket, client_address_tuple, client_name)
#   }
# EXAMPLE:
# the example below shows 2 clients
# client 1 is called 'c1' and has the address ('127.0.0.1', 36852)
# client 2 is called 'c2' and has the address ('127.0.0.1', 36854)
#   {
#       ('127.0.0.1', 36852): (   <socket.socket fd=8, family=AddressFamily.AF_INET, type=2049, proto=0, laddr=('127.0.0.1', 9997), raddr=('127.0.0.1', 36852)>,
#                               ('127.0.0.1', 36852),
#                               'c1'),
#       ('127.0.0.1', 36854): (   <socket.socket fd=9, family=AddressFamily.AF_INET, type=2049, proto=0, laddr=('127.0.0.1', 9997), raddr=('127.0.0.1', 36854)>,
#                               ('127.0.0.1', 36854),
#                               'c2')
#   }
#   To send data to client c1, we use the client socket object with fd=8
#   To know what is the name of the client, we use the value tuple to find that.
#   The name of the client is in the second index (third element) of the tuple -
#   in this case, it is "c1"
#
connected_clients = {}
# a list to store client labels - used to show client names in the server UI
client_labels = [None, None, None]

# a global variable that shows unparsed incoming and outgoing HTTP messages - accessed by thread and main
scroll_width = 70
scroll_height = 10
scr = scrolledtext.ScrolledText(
    server_window, width=scroll_width, height=scroll_height, wrap=tk.WORD
)
# a global variable that tracks activities on several client sockets
# this is used from "selectors" module of python [https://pymotw.com/3/selectors/]
def_selector = selectors.DefaultSelector()


def get_address_from_name(name):
    """
    given the client name, extract client address from the connected_clients global dict
    :param name: client name
    :return: address tuple storing (host, port)
    """
    for address, client in connected_clients.items():
        # loop through each client where address is key and client variable is value
        if client[2] == name:
            # The client value tuple has name in the second index (or third position)
            # if it matches the input name, then we return address (key of the dictionary)
            return address


def add_msg_to_scrollbox(msg):
    """
    Add a given message to the scrollbox end
    :param msg: message to display
    :return: None
    """
    # add message to the end of scrollbox
    scr.insert(END, msg)
    # auto scroll the scrollbox to the end
    scr.see(END)


def parse_data_from_client(client_address, data_from_client):
    """
    Parse incoming data from the client
    :param client_address: client from which we got the message from
    :param data_from_client: HTTP data that we received from the client
    :return: None
    """
    # the HTTP request has client message details in json dictionary format
    # so we use this helper method to extract that into 3 variables
    # mode, destination and message
    # the number 7 indicates we want the 8th line of the original message
    # the 8th line is the body of the message
    #   recollect HTTP header has 1 request line + 5 headers + 1 blank line before the body
    mode, destination, message = extract_message_details(
        data_from_client.split("\n")[7]
    )
    print("Message {} destined to {} via mode {}".format(message, destination, mode))

    # create a HTTP message to send to the destination client
    response_message = prepare_fwd_msg_to_client(
        mode, connected_clients[client_address][2], message
    )

    if mode == "1-1":
        # if the client sent a 1-1 message, this code will run
        print(
            "{} Sending message to {}".format(
                "*" * 8, connected_clients[get_address_from_name(destination)]
            )
        )
        # show the message on the server scrollbox
        add_msg_to_scrollbox("{}\n".format(response_message))

        # access the destination socket and send the HTTP message to it
        connected_clients[get_address_from_name(destination)][0].sendall(
            bytes(response_message, "UTF-8")
        )
        print("{} Sending ack back to source {}".format("*" * 8, client_address))
        # now send ACK to the originating client
        add_msg_to_scrollbox("{}\n".format(prepare_ack_message()))
        connected_clients[client_address][0].sendall(
            bytes(prepare_ack_message(), "UTF-8")
        )
    elif mode == "1-N":
        # if the client sent a 1-N message, this code will run
        print("{} Sending message to all clients".format("*" * 8))

        # show the message on the server scrollbox
        add_msg_to_scrollbox("{}\n".format(response_message))

        for address, client in connected_clients.items():
            # for each client, send the message
            client[0].sendall(bytes(response_message, "UTF-8"))
        print("{} Sending ack back to source {}".format("*" * 8, client_address))
        # now send ACK to the originating client
        add_msg_to_scrollbox("{}\n".format(prepare_ack_message()))
        connected_clients[client_address][0].sendall(
            bytes(prepare_ack_message(), "UTF-8")
        )
    else:
        pass


def read_from_client(client_connection, event_mask):
    """
    this method is responsible for reading data from a client
    :param client_connection: connection that we have activity on
    :param event_mask: READ or WRITE event
    :return:
    """
    print(
        "{} Client activity on {} with event mask {}".format(
            "*" * 4, client_connection, event_mask
        )
    )

    # get the client address we got this message from
    client_address = client_connection.getpeername()
    # read data from the client
    data_from_client = client_connection.recv(MAX_MESSAGE_SIZE).decode("UTF-8")
    if data_from_client:
        # we have valid data from the client
        print("\t Received '{}' from '{}'".format(data_from_client, client_address))
        # show what we received on the scrollbox
        if client_address in connected_clients.keys():
            # if it is existing client, just show the name
            add_msg_to_scrollbox("{}: \t {}\n".format(connected_clients[client_address][2], data_from_client))
        else:
            # if it is a new client, show the address for now
            # in the next message, we'll show the name on the scrollbox
            add_msg_to_scrollbox("{}: \t {}\n".format(client_address, data_from_client))

        if REGISTER_CLIENT_NAME in data_from_client:
            # A new client just connected - so we register it's name and update the UI
            register_client_name(client_connection, client_address, data_from_client)
        elif GET_ALL_CLIENTS in data_from_client:
            # A client wants to know all the clients the server is tracking - so send that data
            names = [GET_ALL_CLIENTS]
            # go through all clients one by one
            for address, client in connected_clients.items():
                # append the client name that we have stored in memory to a list called "names"
                names.append(client[2])
            # create a HTTP GET response to hold the client names
            response_message = prepare_get_all_client_names_response(names)
            # show the unparsed HTTP data on the server scrollbox
            add_msg_to_scrollbox("{}\n".format(response_message))
            # send the data to the requesting client
            connected_clients[client_address][0].sendall(
                bytes(response_message, "UTF-8")
            )
        else:
            # A client wants to send message to another client
            parse_data_from_client(client_address, data_from_client)
    else:
        # the client exited here - so unregister the client name and update UI
        print("Closing socket to {}".format(client_connection))
        unregister_client_name(client_connection)


def unregister_client_name(client_connection):
    """
    When a client disconnects, we need to update our in-memory dictionary
    AND also update the client labels
    :param client_connection: connection object from client
    :return: None
    """
    # unregister from monitoring the client socket
    def_selector.unregister(client_connection)
    # get client address from connection
    client_address = client_connection.getpeername()
    # get client name from the given client address - it is the third element of the value tuple
    client_name = connected_clients[client_address][2]
    # delete the entry from the dictionary
    del connected_clients[client_address]
    # update the UI with the remaining client names
    update_client_labels(connected_clients)
    # close socket connection to the client that shutdown
    client_connection.close()
    # update UI to show that the client has disconnected
    add_msg_to_scrollbox("Client {} has disconnected \n".format(client_name))


def update_client_labels(clients):
    """
    Update the client names on the server UI
    :param clients: list of client names
    :return: None
    """
    # first delete all entries from the server UI
    for i in range(len(client_labels)):
        client_labels[i]["text"] = ""
    index = 0
    for address, client in clients.items():
        # for each client key, value of the clients dictionary
        # extract just the name part of the value
        # it is in the second index of the value tuple - see top of file for more details
        client_labels[index]["text"] = client[2].strip()
        index += 1


def register_client_name(client_sock, client_address, data_str):
    """
    Responsible for storing the client details in a in-memory data structure
    :param client_sock: socket that the activity happened
    :param client_address: the address (host, port) tuple from where the activity came
    :param data_str: data
    :return: None
    """
    # data_str is the incoming HTTP request - we want to extract the name from that blob.
    # see http_helper for more details on how this works
    client_name = extract_client_name(data_str)
    print(
        "Client {} connected with name {}".format(
            (client_sock, client_address), client_name
        )
    )
    global connected_clients
    # add the incoming connection details to the global
    # connected_clients dictionary storing all the clients we have
    connected_clients[client_address] = (client_sock, client_address, client_name)
    print("List of all connected_clients")
    PPRINTER.pprint(connected_clients)

    # update the client list on the server UI
    update_client_labels(connected_clients)

    # prepare the response for the HTTP request that came in
    response_message = prepare_post_client_name_response()
    add_msg_to_scrollbox("{}\n".format(response_message))
    # send the response we generated
    sent = connected_clients[client_address][0].send(bytes(response_message, "UTF-8"))
    # show the unparsed HTTP response on the server scrollbox
    add_msg_to_scrollbox("Client {} registered \n".format(client_name))
    print("Client registered name {} Sent 200 OK in {} bytes".format(client_name, sent))


def accept_new_client(server, event_mask):
    """
    When a new client connects to the server this method is called
    This method is responsible for
    1. accepting new connections
    2. making the socket connection non-blocking
    3. registering the EVENT_READ event on this socket to call "read_from_client" callback
    :param server: the server socket that is listening for incoming connections
    :param event_mask: is this a READ or WRITE event
    :return: None
    """
    print(
        "A new client {} with event mask {} is connecting...".format(server, event_mask)
    )
    client_sock, client_address = server.accept()
    # client_sock is a python socket object instance
    # client address is a tuple which contains the (host, port) from which the connection came
    client_sock.setblocking(False)
    # when a new message comes from the client, call the "read_from_client" method
    def_selector.register(client_sock, selectors.EVENT_READ, read_from_client)


def run_select_thread():
    """
    A while true loop that wakes up whenever there is socket activity
    Based on what activity occurred, the corresponding callback is initiated
    for example,
    READ event server_socket calls accept_new_client function
    READ event on any client socket calls read_from_clietn
    :return:
    """
    while True:
        for key, mask in def_selector.select(timeout=None):
            # call the callback with the required data
            # key.fileobj has the socket where the activity happened
            # mask indicates if the event was READ or WRITE event
            key.data(key.fileobj, mask)


def setup_server_socket():
    """
    responsible for setting up server socket
    if it fails, the program will exit
    if it succeeds, it will launch a thread to receive and process new clients
    :return: None
    """
    try:
        # set the socket to not block
        server_socket.setblocking(False)
        # bind the socket to given port and listen
        server_socket.bind((server_host, server_port))
        server_socket.listen(5)
        # when a new client opens connection, call "accept_new_client" callback
        def_selector.register(server_socket, selectors.EVENT_READ, accept_new_client)
        print("Server started...")
        # we now run a select loop that listens for activity on all sockets
        # this loop is run in a thread which is daemonized
        select_loop = Thread(target=run_select_thread)
        select_loop.daemon = True
        select_loop.start()  # start the thread for responding to new clients and existing clients

    except OSError as e:
        print("An error occurred {}. \n".format(str(e)))
        print("Please fix before relaunching.")
        import sys

        sys.exit(1)


def exit_program():
    """
    Exit the program by closing socket connection and destroying client window
    :return: None
    """
    print("Existing clients are {}".format(connected_clients))
    for name, client in connected_clients.items():
        print("Closing connection to client {}".format(name))
        def_selector.unregister(client[0])
        client[0].close()
    server_window.destroy()


def setup_server_window():
    """
    setup tkinter based server window and its widgets
    :return: None
    """

    # create server window
    server_window.title("Server UI")
    server_window.geometry("800x640")
    server_window.resizable(False, False)

    # create widget to show a list of active clients
    label_frame = ttk.LabelFrame(server_window, text="List of active clients")
    label_frame.grid(column=0, row=0, padx=320, pady=100)
    global client_labels
    for i in range(len(client_labels)):
        client_labels[i] = ttk.Label(label_frame)
        client_labels[i].grid(column=0, row=i)
    for child in label_frame.winfo_children():
        child.grid_configure(padx=8, pady=4)

    # create scrollbox to show a list of incoming message
    scr.grid(column=0, columnspan=20, padx=10, pady=10)

    # set up a button to exit the UI
    # when this button is clicked, "exit_program"
    # is called to close the socket connection and exit the program
    exit_button = ttk.Button(server_window, text="Exit", command=exit_program)
    exit_button.grid(column=0, columnspan=2, padx=10, pady=10)

    # cleanly close the socket and destroy the tkinter window when X button is clicked
    server_window.protocol("WM_DELETE_WINDOW", exit_program)


def main():
    """
    main method of the program
        - responsible for setting up the tkinter based server UI
        - responsible for setting up the server socket connection
        - responsible for calling the tkinter main loop (event loop)
    """
    setup_server_window()
    setup_server_socket()
    server_window.mainloop()


if __name__ == "__main__":
    main()
