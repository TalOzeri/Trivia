# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

LIST_OF_ACTIONS = ["LOGIN", "LOGOUT"]

# Protocol Messages
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
    "login_msg": "LOGIN",
    "logout_msg": "LOGOUT",
    "score_msg": "MY_SCORE",
    "high_score_msg": "HIGHSCORE",
    "get_question_msg": "GET_QUESTION",
    "send_answer_msg": "SEND_ANSWER",
    "logged_msg": "LOGGED"
}  # .. Add more commands if needed

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK",
    "login_failed_msg": "ERROR",
    "score_msg": "YOUR_SCORE",
    "allScore_msg": "ALL_SCORE",
    "the_question_from_the_server": "YOUR_QUESTION",
    "no_question_msg" : "NO_QUESTIONS",
    "correct_answer_msg":"CORRECT_ANSWER",
    "wrong_answer_msg": "WRONG_ANSWER",
    "logged_answer_msg": "LOGGED_ANSWER"

}  # ..  Add more commands if needed

# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
    """
    Gets command name (str) and data field (str) and creates a valid protocol message
    Returns: str, or None if error occured
    """

    action = cmd.replace(" ", "")
    if action in PROTOCOL_CLIENT.values() or action in PROTOCOL_SERVER.values():
        return action.ljust(16, " ") + DELIMITER + str(len(data)).zfill(4) + DELIMITER + data
    else:
        return None




    # return full_msg


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occured, returns None, None
    """
    if data.count(DELIMITER) == 2:
        data_splited = data.split(DELIMITER)
        cmd = data_splited[0].replace(" ", "")
        length = data_splited[1].replace(" ", "").zfill(4)
        msg = data_splited[-1]
        if length.isnumeric() and length == str(len(msg)).zfill(4):
            return cmd, msg
        else:
            return None, None
    else:
        return None, None


# def parse_message(data):
#     """
#     Parses protocol message and returns command name and data field
#     Returns: cmd (str), data (str). If some error occured, returns None, None
#     """
#     if data.count(DELIMITER) == 2:
#         data_splited = data.split(DELIMITER)
#         cmd = data_splited[0].replace(" ", "")
#         if data_splited[1] != "0000":
#             length = data_splited[1].replace("0", "").replace(" ", "")
#         else:
#             length = "0"
#         msg = data_splited[-1]
#         if length.isnumeric() and length == str(len(msg)):
#             return cmd, msg
#         else:
#             return None, None
#     else:
#         return None, None



def split_data(msg, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's data field delimiter (|#) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occured, returns None
    """
    if msg.count(DATA_DELIMITER) == expected_fields:
        return msg.split(DATA_DELIMITER)
    else:
        return [None]


def join_data(msg_fields):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
    Returns: string that looks like cell1#cell2#cell3
    """
    return DATA_DELIMITER.join(msg_fields)


def main():
    x = parse_message("LOGIN           |   9|aaaa#bbbb")
    print(x)

if __name__ == '__main__':
    main()