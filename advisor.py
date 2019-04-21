"""
Name: Venkata Adilakshmi Rajitha Kalapatapu
Student ID: 1001682465
Login ID: vxk2465
"""


import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, END
import socket
from threading import Thread, Timer
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
advisor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# a global connected status - true if connection is active, false otherwise
connected = False
# a global tkinter window instance - accessed by thread and main
advisor_window = tk.Tk()
# a global label to show connection status - accessed by thread and main
connection_status = ttk.Label(advisor_window, text="Not connected to server")
# a global variable to show incoming message - scrollbox - accessed by thread and main
scroll_width = 32
scroll_height = 15
msg_area = scrolledtext.ScrolledText(
    advisor_window, width=scroll_width, height=scroll_height, wrap=tk.WORD
)


def exit_program():
    """
    Exit the program by closing socket connection and destroying client window
    :return: None
    """
    # exit cleanly by closing socket and destroying the tkinter window
    advisor_socket.close()
    advisor_window.destroy()


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


def parse_get_all_pending_clearance_response(msg):
    """
    parses response containing all pending clearance requests
    :return: None
    """
    add_msg_to_scrollbox("TODO {}\n".format(msg))


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
        print("An unsupported operation happened! {}".format(msg))
    elif REGISTER_CLIENT_NAME in msg:
        # we got a response to our request to register a client name
        parse_connection_request_response(msg)
    elif SEND_MESSAGE in msg:
        # we got incoming message from a client forwarded by the server
        display_incoming_message(msg)
    elif GET_PENDING_STUDENT_CLEARANCE_REQUESTS in msg:
        # we got a response to our request to get all pending clearance requests
        parse_get_all_pending_clearance_response(msg)
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
            data_from_server = advisor_socket.recv(MAX_MESSAGE_SIZE)
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
    - connect socket to the server
    - send client name to the server in HTTP format (sendall)
    - launch thread to start receiving data from server
    :return:
    """
    try:
        advisor_name = "advisor"
        global advisor_socket
        advisor_socket.connect((server_host, server_port))  # connection to server
        advisor_socket.sendall(
            bytes(prepare_post_client_name_request(advisor_name), "UTF-8")
        )  # send user-name to server
        # start thread to receive data from server
        t = Thread(target=receive_from_server)
        # daemonize it so it will run in the background and start the thread
        t.daemon = True
        t.start()
    except OSError:
        global connected
        connected = False


def setup_advisor_window():
    """
    setup tkinter based client window and its widgets
    """

    # set up client window details
    advisor_window.title("Advisor Window")
    advisor_window.geometry("800x640")
    advisor_window.resizable(False, False)

    # set up a label to show connection status to the server
    connection_status.grid(column=1, row=4, padx=30, pady=15)

    # set up text area to see incoming messages
    msg_area.grid(column=1, row=5, padx=5, pady=5)

    # set up a button to exit the client UI
    # when this button is clicked, "exit_program"
    # is called to close the socket connection and exit the program
    exit_button = ttk.Button(advisor_window, text="Exit", command=exit_program)
    exit_button.grid(column=1, row=30, padx=10, pady=10)

    # cleanly close the socket and destroy the tkinter window when X button is clicked
    advisor_window.protocol("WM_DELETE_WINDOW", exit_program)


def send_request_to_get_all_pending_clearances():
    """
    Send the HTTP request to MQS to get all pending clerances
    :return:
    """
    # prepare body of the http request
    body = {"action": GET_PENDING_STUDENT_CLEARANCE_REQUESTS}
    import json

    # send a HTTP POST message to the server
    # body contains the action (requesting course clearance in this case), student name and course name
    sent_bytes = advisor_socket.send(
        bytes(
            prepare_http_msg_request(
                "GET", GET_PENDING_STUDENT_CLEARANCE_REQUESTS, json.dumps(body)
            ),
            "UTF-8",
        )
    )
    if sent_bytes:
        # add the student-course combo to the student scrollbox
        add_msg_to_scrollbox(
            "Sent request to get all pending course clearance requests"
        )
    else:
        add_msg_to_scrollbox(
            "Error sending request to get all pending course clearance requests"
        )


def get_all_pending_clerance_requests():
    """
    Get all pending messages from the MQS
    Restart the timer once again for 3 seconds
    :return: None
    """
    add_msg_to_scrollbox("Getting all pending student-course clearance requests\n")

    send_request_to_get_all_pending_clearances()

    # Restart the timer again to one second - at the end of the second, we call
    # clock_tick again which increments the value by 1
    t = Timer(3.0, get_all_pending_clerance_requests)
    t.daemon = True
    t.start()


def main():
    """
    main method of the program
        - responsible for setting up the tkinter based client UI
        - responsible for calling the tkinter main loop (event loop)
    """
    try:
        setup_advisor_window()
        connect_to_server()
        # Instantiate a timer for one second - at the end of one second call "clock_tick"
        t = Timer(3.0, get_all_pending_clerance_requests)
        # make the timer a background thread
        t.daemon = True
        # Start the timer object
        t.start()

        advisor_window.mainloop()
    except RuntimeError:
        print("Exiting...")


if __name__ == "__main__":
    main()
