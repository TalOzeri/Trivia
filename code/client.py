import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

MAX_MSG_LENGTH = 1024
SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678

# HELPER SOCKET METHODS

def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    msg = chatlib.build_message(code, data)
    conn.send(msg.encode())



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
    return cmd, data



def connect():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print(f"connecting to {SERVER_IP} port {SERVER_PORT}")
    return client_socket


def error_and_exit(error_msg):
    exit(error_msg)


def login(conn):
    while True:
        username = input("Please enter username: \n")
        password = input("Please enter password: \n")

        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"],chatlib.join_data([username, password]))

        cmd, data = recv_message_and_parse(conn)

        if cmd == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print("Logged in!")
            return

        print(data)


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")


# Section 2:

def build_send_recv_parse(conn, code, data):
    build_and_send_message(conn, code, data)
    return recv_message_and_parse(conn)


def get_score(conn):
    cmd, score = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["score_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["score_msg"]:
        print("Your score is: " + score)
    else:
        print("ERROR! with Score")


def get_highscore(conn):
    cmd, scoreTable = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["high_score_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["allScore_msg"]:
        print("High-Score table:\n" + scoreTable)
    else:
        print("ERROR! with Score")


# Section 3:

def play_question(conn):
    #First step: asking for question from the server:
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question_msg"], "")
    if cmd != chatlib.PROTOCOL_SERVER["no_question_msg"]: # check if there is any questions
        splitted_data = data.split("#")
        id_of_the_question = splitted_data[0]
        question = splitted_data[1]
        options = splitted_data[2:]
        print(f"Q: {question}")
        for i in range(len(options)):
            print(f"\t\t{i+1}. {options[i]}")
        choice = input(f"Please choose an answer [1-{len(options)}]: ")
        isAnswerCorrect, realAnswerIfNeeded = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer_msg"], chatlib.join_data([id_of_the_question, choice]))
        answerCorrect = isAnswerCorrect == chatlib.PROTOCOL_SERVER["correct_answer_msg"]
        if answerCorrect:
            print("YES!!!")
        else:
            print(f"Nope, correct answer is {realAnswerIfNeeded}")
    else:
        print("No more questions, please choose another option")


def get_logged_users(conn):
    cmd, loggedUsers = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["logged_answer_msg"]:
        print("Logged users:\n" + loggedUsers)
    else:
        print("ERROR! with Logged Answer")


def main():
    conn = connect()
    login(conn)
    cmd = ""
    while cmd != "q":
        print("""p        Play a trivia question\ns        Get my score\nh        Get high score\nl        Get logged users\nq        Quit""")
        try:
            cmd = input("Please enter your choice: ")
        except KeyboardInterrupt:
            cmd = ""
        else:
            if cmd == "p":
                play_question(conn)
            elif cmd == "s":
                get_score(conn)
            elif cmd == "h":
                get_highscore(conn)
            elif cmd == "l":
                get_logged_users(conn)
        if cmd == "":
            break
    logout(conn)


    error_and_exit("Goodbye!")

if __name__ == '__main__':
        main()

