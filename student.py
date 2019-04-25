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
student_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# a global connected status - true if connection is active, false otherwise
connected = False
# a global tkinter window instance - accessed by thread and main
client_window = tk.Tk()
# a global variable to retrieve username - accessed by thread and main
student_name = tk.StringVar()
# a global variable to retrieve course name - accessed by thread and main
course_name = tk.StringVar()
# a global label to show connection status - accessed by thread and main
connection_status = ttk.Label(client_window, text="Not connected to server")
# a global variable to retrieve message entered by client - accessed by thread and main
student_course_entered = ()
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
# a global variable to store the radiobutton objects for all client names
# when we get info about a new client, we delete all the radio objects on the
# Student UI and redraw them
all_client_name_radiobuttons = []


def get_clients_from_server():
    """
    method to request all client names from server
    uses HTTP GET method to get all client names
    :return: None
    """
    # send a HTTP GET request to get all the client names
    student_socket.send(bytes(prepare_get_all_client_names_request(), "UTF-8"))


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
    student_socket.close()
    client_window.destroy()


def send_student_course_clearance_message(student_course_tuple):
    """
    send message to the MQS that a student is requesting clearance for course
    :param student_course_tuple: a tuple containing the student name and course name
    :return: None
    """
    # prepare body of the http request
    body = {
        "action": REQUEST_COURSE_CLEARANCE,
        "student": student_course_tuple[0],
        "course": student_course_tuple[1],
    }
    import json

    # send a HTTP POST message to the server
    # body contains the action (requesting course clearance in this case), student name and course name
    sent_bytes = student_socket.send(
        bytes(
            prepare_http_msg_request(
                "POST", REQUEST_COURSE_CLEARANCE, json.dumps(body)
            ),
            "UTF-8",
        )
    )
    if sent_bytes:
        # add the student-course combo to the student scrollbox
        add_msg_to_scrollbox(
            "Sent clearance request for for {} and course {}\n".format(
                student_course_tuple[0], student_course_tuple[1]
            )
        )
    else:
        # else show that error occured - so that student can retry
        add_msg_to_scrollbox(
            "Error sending clearance request for {} and course {}\n".format(
                student_course_tuple[0], student_course_tuple[1]
            )
        )


def send_to_server():
    """
    - getting the user input
    - validate the user input until valid non-empty entry is given
    - Read message entered by the client
    - Validate entered message
        - if empty, ask user to enter again
        - if not, see if it is 1:1 or 1:N and send message
    - Send the message to the server via HTTP POST request
    :return:
    """
    if not student_name.get():
        messagebox.showerror("Student name invalid", "Enter a non-empty student name")
        return
    if not course_name.get():
        messagebox.showerror(
            "Course name invalid", "Enter a non-empty valid course name"
        )
        return
    global connected
    if not connected:
        connect_to_server()
    # if the course name is empty or full of white spaces or the message prompt
    # or if we are not yet connected, don't send the message yet.
    if not course_name.get() or not course_name.get().strip():
        messagebox.showerror(
            "Course name invalid", "Enter a non-empty valid course name"
        )
        return
    # we're connected and we have a non-empty valid message to send here
    global student_course_entered
    student_course_entered = (student_name.get(), course_name.get())

    send_student_course_clearance_message(student_course_entered)


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
            data_from_server = student_socket.recv(MAX_MESSAGE_SIZE)
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
        global student_socket
        student_socket.connect((server_host, server_port))  # connection to server
        student_socket.sendall(
            bytes(prepare_post_client_name_request("student"), "UTF-8")
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
    client_window.title("Student UI")
    client_window.geometry("800x640")
    client_window.resizable(False, False)

    # set up fields for entering student-name
    username_label = ttk.Label(client_window, text="Enter a student name")
    username_label.grid(column=0, row=1, padx=30, pady=15)
    username_entry = ttk.Entry(client_window, width=32, textvariable=student_name)
    username_entry.grid(column=1, row=1, padx=30, pady=15)

    # set up fields for entering course name
    course_label = ttk.Label(client_window, text="Enter a course name")
    course_label.grid(column=0, row=2, padx=30, pady=15)
    course_entry = ttk.Entry(client_window, width=32, textvariable=course_name)
    course_entry.grid(column=1, row=2, padx=30, pady=15)

    # set up a label to show connection status to the server
    connection_status.grid(column=1, row=4, padx=30, pady=15)

    # set up text area to see incoming messages
    msg_area.grid(column=1, row=5, padx=5, pady=5)

    # set up widget to send message
    msg_send = ttk.Button(client_window, text="Send", command=send_to_server)
    msg_send.grid(column=1, row=3, padx=30, pady=15)

    # set up a button to exit the Student UI
    # when this button is clicked, "exit_program"
    # is called to close the socket connection and exit the program
    exit_button = ttk.Button(client_window, text="Exit", command=exit_program)
    exit_button.grid(column=1, row=30, padx=10, pady=10)

    # cleanly close the socket and destroy the tkinter window when X button is clicked
    client_window.protocol("WM_DELETE_WINDOW", exit_program)


def main():
    """
    main method of the program
        - responsible for setting up the tkinter based Student UI
        - responsible for calling the tkinter main loop (event loop)
    """
    try:
        setup_client_window()
        client_window.mainloop()
    except RuntimeError:
        print("Exiting...")


if __name__ == "__main__":
    main()
