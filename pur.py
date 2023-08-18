import json
import requests
import time

# ANSI escape codes for text colors
YELLOW = '\033[93m'
GREEN = '\033[92m'
RESET = '\033[0m'

def load_config():
    with open("config.json", "r") as config_file:
        return json.load(config_file)

def load_latest_message(channel_id, bot_token):
    headers = {
        'Authorization': bot_token
    }
    url = f'https://discord.com/api/v8/channels/{channel_id}/messages'
    response = requests.get(url, headers=headers, params={'limit': 1})
    messages = response.json()
    return messages[0] if messages else None

def load_user_messages(channel_id, user_id, bot_token, limit=50):
    headers = {
        'Authorization': bot_token
    }
    params = {
        'limit': limit
    }
    url = f'https://discord.com/api/v8/channels/{channel_id}/messages'
    response = requests.get(url, headers=headers, params=params)
    messages = response.json()
    user_messages = [message for message in messages if message.get('author', {}).get('id') == user_id]
    return user_messages

def delete_message(message_id, channel_id, bot_token):
    headers = {
        'Authorization': bot_token
    }
    url = f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}'
    response = requests.delete(url, headers=headers)
    return response.status_code

def main():
    config = load_config()
    channel_ids = config.get('channel_ids')
    user_id = config.get('user_id')
    bot_token = config.get('bot_token')

    if not channel_ids or not user_id or not bot_token:
        print("Error: channel_ids, user_id, or bot_token not found in config.json")
        return

    print(YELLOW + "Purger by Felix started" + RESET)

    last_message_ids = {channel_id: None for channel_id in channel_ids}

    while True:
        for channel_id in channel_ids:
            headers = {
                'Authorization': bot_token
            }
            latest_message = load_latest_message(channel_id, bot_token)
            if latest_message:
                last_message_id = last_message_ids[channel_id]
                if latest_message['id'] != last_message_id:
                    last_message_ids[channel_id] = latest_message['id']

                    if latest_message['author']['id'] == user_id:
                        if latest_message.get('content', '').lower().startswith('!purge'):
                            content_parts = latest_message['content'].split()
                            if len(content_parts) >= 3 and content_parts[1].isdigit() and content_parts[2].isdigit():
                                amount_to_purge = int(content_parts[1])
                                amount_to_load = int(content_parts[2])
                                print(f"Purge command detected in channel {channel_id}. Loading {amount_to_load} messages and deleting {amount_to_purge}...")
                                user_messages = load_user_messages(channel_id, user_id, bot_token, amount_to_load)
                                for user_message in user_messages:
                                    delete_status_code = delete_message(user_message['id'], channel_id, bot_token)
                                    if delete_status_code == 204:
                                        print(f"{GREEN}Message with ID {user_message['id']} deleted successfully in channel {channel_id}.{RESET}")
                                        amount_to_purge -= 1
                                        if amount_to_purge <= 0:
                                            break
                                        time.sleep(0.5)  # Add a delay of 0.5 seconds between deletions
                                    else:
                                        print(f"Failed to delete message with ID {user_message['id']} in channel {channel_id}. Status code: {delete_status_code}")
                                print(f"Deletion completed in channel {channel_id}. Back to monitoring latest messages.")

            time.sleep(0.05)  # Adjust this sleep interval for faster checking, but be cautious of rate limits

if __name__ == "__main__":
    main()
