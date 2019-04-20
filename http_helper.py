"""
Name: Venkata Adilakshmi Rajitha Kalapatapu
Student ID: 1001682465
Login ID: vxk2465
"""


# global variable to limit the maximum message size
MAX_MESSAGE_SIZE = 2048

# server details
server_host = "127.0.0.1"
server_port = 9999

# resource names for client actions
GET_ALL_CLIENTS = "all/client/names"
REGISTER_CLIENT_NAME = "register/client/name"
SEND_MESSAGE = "send/message"
COURSE_CLEARANCE = "student/course/clearance"


def extract_client_name(http_request):
    """
    extract client name from string containing http_request data
    :param http_request: string containing http request
    :return: string containgin client name

    The register/client/name request has the name in the following format
    "name:<client_name>"

    so parse the http request line by line and see if name: occurs in the line
    if so we extract it (using split()) and return just the name part

    so - "name:<client_name>".split(":") returns ['name', '<client_name>']
    and we return the second element (using index 1)
    """
    client_name = ""
    lines = http_request.split("\n")
    for line in lines[1:]:
        if "name" in line:
            client_name = line.split(":")[1]
    return client_name


def extract_message_details(
    line, field1="mode", field2="destination", field3="message"
):
    """
    Given a line of text containing message details
    we extract the required fields
    :param line: text containing message details


    :return: tuple holding (mode, destination, message)

    examples:
    if the input is:
    {"mode" : "1:1", "destination" : "client-name", "message": "sample message"}
    the output is ("1:1", "client-name", "sample message")

    if the input is:
    {"mode" : "1:1", "source" : "client-name", "message": "sample message"}
    the output is ("1:1", "client-name", "sample message")

    NOTE: the second element could have the label as either "destination" or "source"
    """
    print("Line to process {}".format(line))
    import json

    try:
        line = json.loads(line)
        mode = line.get(field1, None)
        source_or_destination = line.get(field2, None) or line.get("source", None)
        message = line.get(field3, None)
        return (mode, source_or_destination, message)
    except json.decoder.JSONDecodeError as e:
        # we received ACK message for a message we sent earlier
        return "ACK", None, None


def prepare_http_msg_request(verb, resource, body=""):
    """
    helper method to format the http request
    :param verb: GET or POST
    :param resource: which resource is the request going to
    :param body: content of the http request
    :return: formatted string containing the following

    <verb> <resource> HTTP/1.0
    header1
    header2
    .
    .
    .
    .
    headern

    body
    """
    import datetime

    request = []
    headers = {
        "Content-Type": "Application/json",
        "Content-Length": len(body),
        "Host": "{}".format(server_host),
        "Date": datetime.datetime.utcnow(),
        "User-Agent": "Custom HTTP endpoint written for CSE5306 lab",
    }
    for key, value in headers.items():
        request.append("{}:{}".format(key, value))

    http_msg_to_send = "{} {} HTTP/1.0\n{}\n\n{}\n".format(
        verb, resource, "\n".join(request), body
    )
    return http_msg_to_send


def prepare_get_all_client_names_request():
    """
    returns a http get message that contains request to get client names
    :return: string containing http GET request

    example return string format:

    GET all/client/names HTTP/1.0
    Content-Type:Application/json
    Content-Length:0
    Host:127.0.0.1
    Date:2019-02-27 04:06:11.685443
    User-Agent:Custom HTTP endpoint written for CSE5306 lab
    """
    return prepare_http_msg_request("GET", GET_ALL_CLIENTS)


def prepare_post_client_name_request(name_entered):
    """

    :param name_entered:
    :return: string containing http POST request to server

    example return string format...

    POST register/client/name HTTP/1.0
    Content-Type:Application/json
    Content-Length:12
    Host:127.0.0.1
    Date:2019-02-27 03:11:12.574242
    User-Agent:Custom HTTP endpoint written for CSE5306 lab

    name:<client_name>
    """
    body = "name:{}".format(name_entered)
    return prepare_http_msg_request("POST", REGISTER_CLIENT_NAME, body)


def prepare_http_msg_response(status, body=""):
    """
    helper method to create a HTTP response string
    :param status: what should the http response status be? - 200 OK etc
    :param body: what body should be added to the response
    :return: HTTP response string
    example

    HTTP/1.0 <status>
    header1
    header2
    ...
    ...
    headern

    <body>
    """
    import datetime

    first_line = "HTTP/1.0 {}".format(status)
    headers = {
        "Content-Type": "Application/json",
        "Content-Length": len(body),
        "Host": "{}".format(server_host),
        "Date": datetime.datetime.utcnow(),
        "User-Agent": "Custom HTTP endpoint written for CSE5306 lab",
    }
    response_headers = []
    for key, value in headers.items():
        response_headers.append("{}:{}".format(key, value))
    import json

    http_msg_response = "{}\n{}\n\n{}\n".format(
        first_line, "\n".join(response_headers), json.dumps(body)
    )
    return http_msg_response


def prepare_get_all_client_names_response(names):
    """
    Given a list of names, prepares a HTTP response message containing
    the names
    :param names: list of client name
    :return: string holding HTTP 200 OK response

    example
    HTTP/1.0 200 OK
    header1
    header2
    ...
    ...
    header5

    [json list of names]
    """
    return prepare_http_msg_response("200 OK", names)


def prepare_post_client_name_response():
    """
    Prepares a HTTP response message for sending 200 OK to the client
    This is in response to HTTP POST message to register client name
    :return: string holding HTTP 200 OK response

    example
    HTTP/1.0 200 OK
    header1
    header2
    ...
    ...
    header5

    REGISTER_CLIENT_NAME
    """
    return prepare_http_msg_response("200 OK", REGISTER_CLIENT_NAME)


def parse_client_name_response(http_response):
    """
    Given a HTTP 200 OK response containing a list of names in json
    format in the body area, convert it to a list of strings
    :param http_response: string storing 200 OK HTTP response
    :return: a list of strings each holding the client name
    """

    names = http_response.split("\n")[7]
    import json

    return json.loads(names)


def prepare_fwd_msg_to_client(mode, source, message):
    """
    Given client details, prepare a HTTP message to send to the client
    :param mode: is either 1:1 or 1:N
    :param destination: the destination client we want to send the message to
    :param message: the message the destination client should receive
    :return: string containing HTTP message with the body containing mdoe, destination and mode

    example:
    POST send/message HTTP/1.0
    Content-Type:Application/json
    Content-Length:92
    Host:127.0.0.1
    Date:2019-02-27 23:49:46.496350
    User-Agent:Custom HTTP endpoint written for CSE5306 lab

    {"resource": "send/message", "mode": "1-1", "source": "rajitha", "message": "Hello Srinath"}
    """
    import json

    body = {
        "resource": SEND_MESSAGE,
        "mode": mode,
        "source": source,
        "message": message,
    }
    return prepare_http_msg_request("POST", SEND_MESSAGE, json.dumps(body))


def prepare_ack_message():
    """
    Prepare a HTTP ACK message (200 OK) to send to the client
    :return: string containing HTTP message with the body
    containing send message resource

    example:
    HTTP/1.0 200 OK
    Content-Type:Application/json
    Content-Length:12
    Host:127.0.0.1
    Date:2019-02-27 23:08:48.108944
    User-Agent:Custom HTTP endpoint written for CSE5306 lab

    "send/message"
    """
    return prepare_http_msg_response("200 OK", SEND_MESSAGE)
