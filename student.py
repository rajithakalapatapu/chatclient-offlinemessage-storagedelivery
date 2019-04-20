"""
Name: Venkata Adilakshmi Rajitha Kalapatapu
Student ID: 1001682465
Login ID: vxk2465
"""


import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, END
import socket
from threading import Thread
from http_helper import *

# References:
# Python GUI cookbook by Packtpub
# https://docs.python.org/3/howto/sockets.html#creating-a-socket
# https://pymotw.com/3/select/
# https://pymotw.com/3/selectors/
# https://docs.python.org/3/library/queue.html
# http://net-informations.com/python/net/thread.htm
# https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
# https://medium.com/swlh/lets-write-a-chat-app-in-python-f6783a9ac170


# a global socket object for all functions to access and send/recv
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# a global connected status - true if connection is active, false otherwise
connected = False
# a global tkinter window instance - accessed by thread and main
client_window = tk.Tk()
# a global variable to retrieve username - accessed by thread and main
username = tk.StringVar()
# a global label to show connection status - accessed by thread and main
connection_status = ttk.Label(client_window, text="Not connected to server")
# a global variable to retrieve message entered by client - accessed by thread and main
msg_client_entered = tk.StringVar()
# a global variable to show incoming message - scrollbox - accessed by thread and main
scroll_width = 32
scroll_height = 15
msg_area = scrolledtext.ScrolledText(
    client_window, width=scroll_width, height=scroll_height, wrap=tk.WORD
)
# a global variable storing the default message that a client can send - accessed by thread and main
default_msg = "Enter message here..."
# a global variable storing the message cast (1:1 OR 1:N) option - accessed by thread and main
message_cast_option = tk.IntVar()
# a global variable to store the client to send 1:1 message to - accessed by thread and main
chosen_client = tk.StringVar()
# a global variable to store the radiobutton objects for all client names
# when we get info about a new client, we delete all the radio objects on the
# client UI and redraw them
all_client_name_radiobuttons = []


def on_choosing_client():
    """
    Responsible for printing console log to serve for debugging purposes
    :return:
    """
    print("Chose to send 1-1 to client {}".format(chosen_client.get()))


def get_clients_from_server():
    """
    method to request all client names from server
    uses HTTP GET method to get all client names
    :return: None
    """
    # send a HTTP GET request to get all the client names
    client_socket.send(bytes(prepare_get_all_client_names_request(), "UTF-8"))


def on_message_cast_option():
    """
    When user selects 1:1, the client has to fetch names of all clients connected
    to the server
    When user selects 1:N, there is no need to fetch all client names - so we print
    to console
    :return: None
    """
    if message_cast_option.get() == 0:
        # The user selected 1-1 message option
        print(
            "{} Client intends to send a 1-1 message - so get client names".format(
                "*" * 4
            )
        )
        # get all the client names from server via a HTTP get message
        get_clients_from_server()
    else:
        # The user selected 1-N message option - we print it for debugging purposes
        print("{} Client intends to send a 1-N message".format("*" * 4))
        # in case the user selected 1-1 before selecting 1-N, we destroy the radio buttons
        for button in all_client_name_radiobuttons:
            button.destroy()


def exit_program():
    """
    Exit the program by closing socket connection and destroying client window
    :return: None
    """
    # exit cleanly by closing socket and destroying the tkinter window
    client_socket.close()
    client_window.destroy()


def send_one_to_one_message(destination, message):
    """
    send a 1:1 'message' from this client to 'destination' client
    :param destination: client name to send the message to
    :param message: the actual message to send
    :return: None
    """
    # prepare body of the http request
    body = {"mode": "1-1", "destination": destination, "message": message}
    import json

    # send a HTTP POST message to the server
    # body contains the mode (1:1 in this case), destination client to send it to
    # and the actual message entered by the client
    client_socket.send(
        bytes(prepare_http_msg_request("POST", SEND_MESSAGE, json.dumps(body)), "UTF-8")
    )


def send_one_to_n_message(message):
    """
    send a 1:N 'message' from this client to all clients
    :param message: the actual message to send
    :return: None
    """
    body = {"mode": "1-N", "message": message}
    import json

    # send a HTTP POST message to the server
    # body contains the mode (1:N in this case)
    # and the actual message entered by the client
    client_socket.send(
        bytes(prepare_http_msg_request("POST", SEND_MESSAGE, json.dumps(body)), "UTF-8")
    )


def send_to_server():
    """
    Read message entered by the client
    Validate entered message
        if empty, ask user to enter again
        if not, see if it is 1:1 or 1:N and send message
    Send the message to the server via HTTP POST request
    :return:
    """
    msg = msg_client_entered.get()
    global connected
    # if the message is empty or full of white spaces or the message prompt
    # or if we are not yet connected, don't send the message yet.
    if not msg.strip() or msg == default_msg or not connected:
        msg_client_entered.set(default_msg)
    else:
        # we're connected and we have a non-empty valid message to send here
        msg_client_entered.set("")
        global message_cast_option
        # call helper method to send 1:1 or 1:N message
        # based on which radiobutton was clicked
        if message_cast_option.get() == 0:  # was the 1:1 button clicked?
            send_one_to_one_message(chosen_client.get(), msg)
        else:  # was the 1:N button clicked?
            send_one_to_n_message(msg)
        # add the message to the client scrollbox
        add_msg_to_scrollbox("{}\n".format(msg))
        print("{} Sent message {} to the server".format("*" * 4, msg))


def add_msg_to_scrollbox(msg):
    """
        Add a given message to the scrollbox end
        :param msg: message to display
        :return: None
        """
    # add message to the end of scrollbox
    msg_area.insert(END, msg)
    # auto scroll the scrollbox to the end
    msg_area.see(END)


def display_client_names(names):
    """
    Takes a list holding names of all clients currently connected to server
    and displays radiobuttons for each client name

    :param names: a list holding names of all clients currently connected to server
    :return: None
    """
    global all_client_name_radiobuttons
    for button in all_client_name_radiobuttons:
        # remove all the older radio buttons
        # we have a new list of names - so use that to display client names
        button.destroy()
    for index, name in enumerate(names):
        # add radio buttons for each client name
        # when user chooses a client to send to, it's name will
        # be stored in "chosen_client" variable

        # eg: if client1 radiobutton is chosen, the "chosen_client" variable
        # will have the value "client1"
        radio = ttk.Radiobutton(
            client_window,
            text=name,
            variable=chosen_client,
            command=on_choosing_client,
            value=name,
        )
        radio.grid(column=index, row=17, padx=10, pady=10)
        all_client_name_radiobuttons.append(radio)


def parse_connection_request_response(msg):
    """
    if server sent 200 OK for our user name registration
    GUI displays message indicating success of connection
    else shows an error and asks user to retry again
    """
    if "200 OK" in msg:
        # the server sent us a 200 OK (success) for our request
        global connected
        connected = True
        connection_status.config(text="Connected to server...")
    else:
        # the server did not send us 200 OK - so some failure happened
        connection_status.config(text="Try connecting again...")


def display_incoming_message(msg):
    """
    displays incoming message in the scrollbox area

    if we received 200 OK for our sent message, we show "Message sent successfully!"
    if we received a new incoming message, we show where we got it from and if it
    was 1:1 or 1:N and the actual message content
    :param msg: message received from the server
    :return: None
    """
    if "200 OK" in msg:
        # the server sent us a 200 OK (success) for our request
        display_msg = "Message sent successfully!"
        add_msg_to_scrollbox("{}\n".format(display_msg))
    elif SEND_MESSAGE in msg:
        import json

        # this is the HTTP response message with
        # one status line (200 OK) [index 0]
        # 5 header lines [index 1,2,3,4,5]
        # one blank line [index 6]
        # and then the body of the response [index 7]
        # the message is now in a list - each element is a line from the original msg
        msg = msg.split("\n")
        # we want only the response body which is in index 7 (8th element of the list)
        response_body = msg[7]
        print("we are going to process {}".format(response_body))

        mode, source, message = extract_message_details(response_body)
        display_msg = "{} sent a {}: \n {}".format(source, mode, message)
        add_msg_to_scrollbox("{}\n".format(display_msg))
    else:
        # some failure happened
        print("Sending message failed {}".format(msg))


def parse_incoming_message(msg):
    """
    Responsible for parsing and understanding data
    received from the server

    Takes 3 actions
    1. Parses user-name registration request response message
    2. Parses get-all-client names request response message
    3. Parses send-message request response message
    """
    print("Received {} from server".format(msg))
    if GET_ALL_CLIENTS in msg:
        # we got a response to our request to get all client names
        display_client_names(parse_client_name_response(msg)[1:])
    elif REGISTER_CLIENT_NAME in msg:
        # we got a response to our request to register a client name
        parse_connection_request_response(msg)
    elif SEND_MESSAGE in msg:
        # we got incoming message from a client forwarded by the server
        display_incoming_message(msg)
    else:
        print("An unsupported operation happened! {}".format(msg))


def receive_from_server():
    """
    A while True loop to receive data from the server
        - if data is empty, it means server has disconnected/exited
        - if data is not empty, we parse the msg and take action
            - see parse_incoming_message for details about parsing
    """
    try:
        while True:
            data_from_server = client_socket.recv(MAX_MESSAGE_SIZE)
            data_from_server = data_from_server.decode("UTF-8")
            if data_from_server:
                # non-empty data - so parse this
                parse_incoming_message(data_from_server)
            else:
                # empty data - only sent when the server exits
                print("Closing this window as the server exited.")
                exit_program()
                break
    except OSError as e:
        print(e)


def connect_to_server():
    """
    responsible for
    1 - getting the user input
    2 - validate the user input until valid non-empty entry is given
    3 - connect socket to the server
    4 - send client name to the server in HTTP format (sendall)
    5 - launch thread to start receiving data from server
    :return:
    """
    try:
        if not username.get():
            messagebox.showerror("Username invalid", "Enter a non-empty username")
            return
        name_entered = username.get()
        global client_socket
        client_socket.connect((server_host, server_port))  # connection to server
        client_socket.sendall(
            bytes(prepare_post_client_name_request(name_entered), "UTF-8")
        )  # send user-name to server
        # start thread to receive data from server
        t = Thread(target=receive_from_server)
        # daemonize it so it will run in the background and start the thread
        t.daemon = True
        t.start()
    except OSError:
        global connected
        connected = False


def setup_client_window():
    """
    setup tkinter based client window and its widgets
    """

    # set up client window details
    client_window.title("Client UI")
    client_window.geometry("800x640")
    client_window.resizable(False, False)

    # set up fields for entering user-name
    username_label = ttk.Label(client_window, text="Enter a username")
    username_label.grid(column=0, row=1, padx=30, pady=15)
    username_entry = ttk.Entry(client_window, width=32, textvariable=username)
    username_entry.grid(column=1, row=1, padx=30, pady=15)

    # set up button for connecting to the server
    # when this button is clicked, "connect_to_server"
    # is called to establish connection to the server
    username_register = ttk.Button(
        client_window, text="Connect", command=connect_to_server
    )
    username_register.grid(column=2, row=1, padx=30, pady=15)

    # set up a label to show connection status to the server
    connection_status.grid(column=1, row=2, padx=30, pady=15)

    # set up text area to see incoming messages
    msg_area.grid(column=1, row=5, padx=5, pady=5)

    # set up widgets to get chat message input and send message
    msg_entry = ttk.Entry(client_window, width=32, textvariable=msg_client_entered)
    msg_entry.grid(column=1, row=25, padx=30, pady=15)
    msg_client_entered.set(default_msg)
    msg_send = ttk.Button(client_window, text="Send", command=send_to_server)
    msg_send.grid(column=2, row=25, padx=30, pady=15)

    # set up a button to exit the client UI
    # when this button is clicked, "exit_program"
    # is called to close the socket connection and exit the program
    exit_button = ttk.Button(client_window, text="Exit", command=exit_program)
    exit_button.grid(column=1, row=30, padx=10, pady=10)

    # cleanly close the socket and destroy the tkinter window when X button is clicked
    client_window.protocol("WM_DELETE_WINDOW", exit_program)

    # provide widgets to choose between 1:1 or 1:N messaging
    message_cast_options = ["1:1", "1:N"]
    for index, option in enumerate(message_cast_options):
        radio = ttk.Radiobutton(
            client_window,
            text=option,
            variable=message_cast_option,
            command=on_message_cast_option,
            value=index,
        )
        radio.grid(column=index, row=13, padx=10, pady=10)


def main():
    """
    main method of the program
        - responsible for setting up the tkinter based client UI
        - responsible for calling the tkinter main loop (event loop)
    """
    try:
        setup_client_window()
        client_window.mainloop()
    except RuntimeError:
        print("Exiting...")


if __name__ == "__main__":
    main()
