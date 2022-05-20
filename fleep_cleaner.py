import json
import argparse
import requests


id_to_name = dict()


def ids_to_names(ids):
    output = list()

    for i in ids:
        output.append(id_to_name[i])

    return output


def parse_file(file_path):
    """ Parse file
    :param file_path: path to dict file
    :return files list
    """

    # 1. Read and parse dict file
    with open(file_path, 'r', encoding='utf-8') as fin:
        data = json.load(fin)

        files = []
        for contact in data['contacts']:
            id_to_name[contact['account_id']] = contact['_formatted_name']

        for conversation in data['conversations']:
            user_name = id_to_name[conversation['profile_id']]

            for big_message in conversation['messages']:
                try:
                    message = json.loads(big_message['message'])
                    if 'attachments' in message.keys():
                        author = id_to_name[big_message['account_id']]
                        for att in message['attachments']:

                            if author != user_name:
                                continue

                            files.append({'url': 'https://fleep.io' + att['file_url'],
                                          'conversation_id': att['conversation_id'],
                                          'message_nr': att['message_nr'],
                                          'attachment_id': att['attachment_id'],
                                          'size': round(att['file_size']/1024/1024, 1)})

                except:
                    pass

    # 2. Return files list
    return files


def auth(email, password):
    """ Auth to Fleep
    :param email: Fleep email
    :param password: Fleep password
    :return Fleep TicketId, Fleep TokenId
    """
    r = requests.post("https://fleep.io/api/account/login", json={'email': email, 'password': password})
    assert r.status_code == 200, r.text
    ticket_id = r.json()['ticket']
    token_id = r.cookies['token_id']
    return ticket_id, token_id


def delete_file(conversation_id, token_id, ticket_id, message_nr, attachment_id):
    """ Delete file from Fleep
    :param conversation_id: Fleep Conversation Id
    :param token_id: Fleep Token Id
    :param ticket_id: Fleep Ticked Id
    :param message_nr: message number
    :param attachment_id: attachment Id """
    r = requests.post(f'https://fleep.io/api/message/delete/{conversation_id}', cookies={'token_id': token_id}, json={'ticket': ticket_id, 'message_nr': message_nr, 'attachment_id': attachment_id})
    assert r.status_code == 200, r.text


def main(email, password, file_path, file_size):
    """ Remove files from Fleep with defined file size
    :param email: Fleep email
    :param password: Fleep password
    :param file_path: Path to json file
    :param file_size: File size in MB """

    # 1. Auth to Fleep
    print('1. Auth to Fleep')
    ticket_id, token_id = auth(email, password)

    # 2. Parse json  file
    print('2. Parse json file')
    files = parse_file(file_path)

    # 3. Find files to delete
    print('3. Find files to delete')
    i = 0
    size = 0
    files_selected = []
    for file in files:
        if file['size'] >= file_size:
            i += 1
            size += file["size"]
            files_selected.append(file)
            print(f'{i} — {file["size"]} MB — {file["url"]}')
    if i == 0:
        print('Files not found! Exit script')
        return

    # 4, Delete files
    print(f'Files found: {i}. Total files size: {int(size)} MB.')
    while True:
        action = input('Delete files? Type "y" to delete, type "n" to abort: ')
        if action == 'n':
            print('Abort deletion')
            return
        elif action == 'y':
            break
        else:
            print(f'Unknown operation: "{action}".')

    # 4. Delete files
    print('4. Delete files')
    for file in files_selected:
        print(f'Delete file [{file["size"]} MB] — {file["url"]}')
        delete_file(conversation_id=file['conversation_id'], token_id=token_id, ticket_id=ticket_id, message_nr=file['message_nr'], attachment_id=file['attachment_id'])
    print(f'Cleanup completed. Deleted files: {i}. Total files size: {int(size)} MB.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fleep Cleaner')
    parser.add_argument('-e', '--email', help='Fleep email', required=True)
    parser.add_argument('-p', '--password', help='Fleep password', required=True)
    parser.add_argument('-f', '--file', help='Path to exported json file', required=True)
    parser.add_argument('-s', '--size', help='File size in MB to remove', required=True, type=int)
    args = parser.parse_args()
    main(args.email, args.password, args.file, int(args.size))
