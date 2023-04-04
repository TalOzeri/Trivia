##############################################################################
# server.py
##############################################################################

import socket
import chatlib
import select
import random
import json
import requests
import html

# GLOBALS
users = {}
questions = {}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
messages_to_send = []
client_sockets = []

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"
MAX_MSG_LENGTH = 1024

#PATHS
USERS_PATH = "../data/users.txt"
QUESTIONS_PATH = "../data/questions.txt"
QUESTIONS_PATH_WEB = "https://opentdb.com/api.php?amount=50&type=multiple"
#QUESTIONS_PATH = r"D:\Studies\cyber\Ya\Networking\netCampCourse\trivia\data\questions.txt"



# HELPER SOCKET METHODS


def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    global messages_to_send

    full_msg = chatlib.build_message(code, msg)
    messages_to_send.append((conn, full_msg.encode()))

    print("[SERVER] ", full_msg)  # Debug print


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """

    full_msg = conn.recv(MAX_MSG_LENGTH).decode()
    cmd, data = chatlib.parse_message(full_msg)
    print("[CLIENT] ", full_msg)  # Debug print
    return cmd, data


# Data Loaders + Data Dumpers


def replace_hash_with_star(json_dict):
    if isinstance(json_dict, list):
        return [replace_hash_with_star(item) for item in json_dict]
    elif isinstance(json_dict, dict):
        return {key: replace_hash_with_star(value) for key, value in json_dict.items()}
    elif isinstance(json_dict, str):
        return json_dict.replace("#", "*")
    else:
        return json_dict



def decode_html_entities(json_dict):
    if isinstance(json_dict, list):
        return [decode_html_entities(item) for item in json_dict]
    elif isinstance(json_dict, dict):
        return {key: decode_html_entities(value) for key, value in json_dict.items()}
    elif isinstance(json_dict, str):
        return html.unescape(json_dict)
    else:
        return json_dict


def load_questions_from_web():
    try:
        jsonQuestions = replace_hash_with_star(decode_html_entities(requests.get(QUESTIONS_PATH_WEB).json()))
    except requests.exceptions.RequestException:
        dump_questions()
        return load_questions()
    else:
        dictQuestions = dict()
        for i in range(1, len(jsonQuestions["results"]) + 1):
            dictQuestions[i] = jsonQuestions['results'][i - 1]

        dump_questions()
        return decode_html_entities(dictQuestions)


def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    # questions = {
    #     2313: {"question": "How much is 2+2", "answers": ["3", "4", "2", "1"], "correct": 2},
    #     4122: {"question": "What is the capital of France?", "answers": ["Lion", "Marseille", "Paris", "Montpellier"],
    #            "correct": 3}
    # }

    # Open the file for reading
    with open(QUESTIONS_PATH, "r") as f:
        # Load the JSON object from the file into a dictionary
        questions = json.load(f)

    return questions


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    # users = {
    #     "test"	:	{"password" :"test" ,"score" :0 ,"questions_asked" :[]},
    #     "yossi"		:	{"password" :"123" ,"score" :50 ,"questions_asked" :[]},
    #     "master"	:	{"password" :"master" ,"score" :200 ,"questions_asked" :[]}
    # }

    # Open the file for reading
    with open(USERS_PATH, "r") as f:
        # Load the JSON object from the file into a dictionary
        users = json.load(f)

    return users


def dump_questions():
    global questions
    with open(QUESTIONS_PATH, "w") as f:
        # Write the dictionary to the file as a JSON object
        json.dump(questions, f)


def dump_user_database():
    global users
    with open(USERS_PATH, "w") as f:
        # Write the dictionary to the file as a JSON object
        json.dump(users, f)


def dumpAndLoad():
    # dump_questions()
    dump_user_database()
    return load_user_database()


def delete_questions_asked():
    global users
    for userName in users.keys():
        users[userName]["questions_asked"] = []
    dump_user_database()

# SOCKET CREATOR


def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    # Implement code ...
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.listen()

    return sock


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_failed_msg"], error_msg)


def start_connection(conn):
    global client_sockets
    client_socket, client_address = conn.accept()
    print("New client joined! ", client_address)
    client_sockets.append(client_socket)
    return client_socket, client_address


##### MESSAGE HANDLING


def handle_getscore_message(conn, username):
    global users

    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["score_msg"], f"{users[username]['score']}")


def handle_highscore_message(conn):
    global users
    sorted_users = dict(sorted(users.items(), key=lambda x: x[1]["score"], reverse=True))
    dataToSend = ""
    for name, data in sorted_users.items():
        dataToSend += f"{name}: {data['score']}\n"
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["allScore_msg"], dataToSend)


def handle_logged_message(conn):
    global logged_users
    dataToSend = ", ".join(logged_users.keys())
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["logged_answer_msg"], dataToSend)


def handle_logout_message(conn):
    """
    Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: None
    """
    global logged_users
    global client_sockets
    global users
    global questions
    userName = get_key_by_value(logged_users, conn.getpeername())
    conn.close()
    print("Connection closed")
    del logged_users[userName]
    client_sockets.remove(conn)
    print_client_sockets(client_sockets)

    users = dumpAndLoad()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users	 # To be used later

    splitted_data = chatlib.split_data(data, 1)
    if splitted_data != [None]:
        userName = splitted_data[0]
        password = splitted_data[1]
        if userName in users.keys() and password in users[userName].values() and password == users[userName]["password"]:
            if userName in logged_users.keys():
                send_error(conn, "There is already a client connected to this user right now")
            else:
                build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"],"")
                logged_users[userName] = conn.getpeername()
        else:
            if userName not in users.keys():
                send_error(conn, "Error! Username does not exist")
            else:
                send_error(conn, "Error! Password does not match!")
    else:
        send_error(conn, "Amount of parameters entered is smaller or larger than expected")


def is_socket_connected(conn):
    global logged_users
    return conn.getpeername() in logged_users.values()


def get_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None


def handle_question_message(conn, userName):

    question = create_random_question(userName)
    if question == None:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["no_question_msg"], "")
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["the_question_from_the_server"], question)


def handle_answer_message(conn, userName, data):
    global questions
    idOfQuestion, choice = chatlib.split_data(data, 1)
    idOfQuestion = int(idOfQuestion)
    if choice.isnumeric():
        choice = int(choice)
        correct, realAnswerIfNeeded = check_answer(idOfQuestion, choice)
        if correct:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["correct_answer_msg"],"")
            update_score(userName)
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["wrong_answer_msg"],str(realAnswerIfNeeded))
    else:
        send_error(conn, f"you didn't enter valid choice, the answer is {questions[idOfQuestion]['correct_answer']}")



def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users	 # To be used later
    connected = is_socket_connected(conn)

    if connected:
        if cmd in chatlib.PROTOCOL_CLIENT.values():
            if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
                handle_logout_message(conn)
            elif cmd == chatlib.PROTOCOL_CLIENT["score_msg"]:
                handle_getscore_message(conn, get_key_by_value(logged_users, conn.getpeername()))
            elif cmd == chatlib.PROTOCOL_CLIENT["high_score_msg"]:
                handle_highscore_message(conn)
            elif cmd == chatlib.PROTOCOL_CLIENT["logged_msg"]:
                handle_logged_message(conn)
            elif cmd == chatlib.PROTOCOL_CLIENT["get_question_msg"]:
                handle_question_message(conn, get_key_by_value(logged_users, conn.getpeername()))
            elif cmd == chatlib.PROTOCOL_CLIENT["send_answer_msg"]:
                handle_answer_message(conn, get_key_by_value(logged_users, conn.getpeername()), data)
        else:
            if cmd == "" or cmd == None:
                handle_logout_message(conn)
            else:
                send_error("The command is not recognized")
    else:
        if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
            handle_login_message(conn, data)
        else:
            send_error("There is no connection, before you need to LOGIN")


# QUESTIONS

def create_random_question(userName):
    global questions
    global users
    possible_questions = []
    if len(questions) != 0:
        possible_questions = [q for q in questions.keys() if q not in users[userName]["questions_asked"]]
        idOfQuestion, data =  random.choice(list(questions.items()))
        if len(possible_questions) == 0:
            return None
        else:
            users[userName]["questions_asked"].append(idOfQuestion)
            users = dumpAndLoad()
            questionToReturn = [str(idOfQuestion)] # id    --> id#question#answer1#answer2#answer3#answer4
            questionToReturn += [data["question"]] # question
            incorrect_answers = data["incorrect_answers"]
            correct_answer = [data["correct_answer"]]
            combined = incorrect_answers + correct_answer
            choices = random.sample(combined, len(combined))
            data["correct_answer_number"] = choices.index(data["correct_answer"]) + 1
            questionToReturn += choices  # choices
            #DEBUG print
            # print(f'index: {data["correct_answer_number"]}\n'
            #       f'list: {choices}\n'
            #       f'correct_answer = {correct_answer}')
            return chatlib.join_data(questionToReturn)
    else:
        return None


def update_score(userName):
    global users
    global questions
    users[userName]["score"] += 5
    users = dumpAndLoad()

def check_answer(idOfQuestion, choice):
    global questions
    z = questions[idOfQuestion]["correct_answer_number"]
    y = choice
    return (questions[idOfQuestion]["correct_answer_number"] == int(choice)), questions[idOfQuestion]["correct_answer"]

# OTHER HELPERS

def print_client_sockets(client_sockets):
    for c in client_sockets:
        print("\t", c.getpeername())



def main():
    # Initializes global users and questions dictionaries using load functions, will be used later
    global users
    global questions
    global messages_to_send
    global logged_users
    global client_sockets

    questions, users = load_questions_from_web(), load_user_database()
    delete_questions_asked() # Because the questions refreshed

    print("Welcome to Trivia Server!")
    print("starting up on port", SERVER_PORT)

    server_socket = setup_socket()
    # client_socket, client_address = start_connection(server_socket)


    while True:
        ready_do_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
        for current_socket in ready_do_read:
            if current_socket is server_socket:
                (client_socket, client_address) = start_connection(current_socket)
                print_client_sockets(client_sockets)
            else:
                try:
                    (cmd, data) = recv_message_and_parse(current_socket)
                except:
                    handle_logout_message(current_socket)
                    users = dumpAndLoad()
                else:
                    if data == "LOGOUT":
                        handle_logout_message(current_socket)
                    else:
                        handle_client_message(current_socket, cmd, data)
                        # print(data)
                        # messages_to_send.append((current_socket, data))

        for message in messages_to_send:
            current_socket, data = message
            if current_socket in ready_to_write:
                current_socket.send(data)
                messages_to_send.remove(message)




        # for message in messages_to_send:
        #     current_socket, fullMsg = message
        #     print(type(fullMsg))
        #     if current_socket in [conn.getpeername() for conn in ready_to_write]:
        #         current_socket.send(fullMsg)
        #         messages_to_send.remove(message)



        # (cmd, data) = recv_message_and_parse(client_socket)
        # handle_client_message(client_socket, cmd, data)
        # if cmd == "LOGOUT":
        #     client_sockets.remove(client_socket)
        #     client_socket, client_address = start_connection(server_socket)







if __name__ == '__main__':
    main()





# def main():
#     # Initializes global users and questions dictionaries using load functions, will be used later
#     global users
#     global questions
#     global messages_to_send
#     global logged_users
#     global client_sockets
#
#     questions = load_questions()
#     users = load_user_database()
#
#
#     print("Welcome to Trivia Server!")
#     print("starting up on port", SERVER_PORT)
#
#     server_socket = setup_socket()
#     # client_socket, client_address = start_connection(server_socket)
#
#
#     while True:
#         ready_do_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
#         for current_socket in ready_do_read:
#             if current_socket is server_socket:
#                 (client_socket, client_address) = start_connection(server_socket)
#                 print_client_sockets(client_sockets)
#             # print("New data from Client")
#             try:
#                 (cmd, data) = recv_message_and_parse(client_socket)
#             except:
#                 client_sockets.remove(current_socket)
#                 current_socket.close()
#                 print("this socket was closed")
#                 client_sockets.remove(current_socket)
#                 print_client_sockets(client_sockets)
#             else:
#                 if data == "z":
#                     print("Connection closed")
#                     client_sockets.remove(current_socket)
#                     current_socket.close()
#                     print_client_sockets(client_sockets)
#                 else:
#                     handle_client_message(client_socket, cmd, data)
#
#
#         for message in messages_to_send:
#             current_socket, fullMsg = message
#             if current_socket in ready_to_write:
#                 current_socket.send(fullMsg)
#                 messages_to_send.remove(message)
#
#
#
#
#         # for message in messages_to_send:
#         #     current_socket, fullMsg = message
#         #     print(type(fullMsg))
#         #     if current_socket in [conn.getpeername() for conn in ready_to_write]:
#         #         current_socket.send(fullMsg)
#         #         messages_to_send.remove(message)
#
#
#
#         # (cmd, data) = recv_message_and_parse(client_socket)
#         # handle_client_message(client_socket, cmd, data)
#         # if cmd == "LOGOUT":
#         #     client_sockets.remove(client_socket)
#         #     client_socket, client_address = start_connection(server_socket)




#1



# def main():
#     # Initializes global users and questions dictionaries using load functions, will be used later
#     global users
#     global questions
#
#     questions = load_questions()
#     users = load_user_database()
#
#     print("Welcome to Trivia Server!")
#     print("starting up on port", SERVER_PORT)
#
#     server_socket = setup_socket()
#     client_socket, client_address = start_connection(server_socket)
#
#
#     while True:
#         (cmd, data) = recv_message_and_parse(client_socket)
#         handle_client_message(client_socket, cmd, data)
#         if cmd == "LOGOUT":
#             client_socket, client_address = start_connection(server_socket)
