import asyncio
import json
import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from quart import request, jsonify, Quart

from api import API
from constants import SAVED_STREAMERS_FILE_NAME, SAVED_STREAMERS_FILE_NAME_BACKUP

load_dotenv()

app = Quart(__name__)

tracked_streamers = []
api = API(client_id=os.getenv('client_id'), client_secret=os.getenv('client_secret'))


def save_streamers():
    streamers_file_path = Path(SAVED_STREAMERS_FILE_NAME)
    if streamers_file_path.exists():
        streamers_file_path.rename(SAVED_STREAMERS_FILE_NAME_BACKUP)
    with open(SAVED_STREAMERS_FILE_NAME, 'w') as f:
        json.dump(tracked_streamers, f)


def load_streamers():
    global tracked_streamers
    streamers_file_path = Path(SAVED_STREAMERS_FILE_NAME)
    if streamers_file_path.exists():
        with open(SAVED_STREAMERS_FILE_NAME, 'r') as f:
            tracked_streamers = json.load(f)
        print('Loaded streamers from file')
    else:
        backup_streamers_file_path = Path(SAVED_STREAMERS_FILE_NAME_BACKUP)
        if backup_streamers_file_path.exists():
            with open(SAVED_STREAMERS_FILE_NAME_BACKUP, 'r') as f:
                tracked_streamers = json.load(f)
            print('Loaded streamers from backup file')
        else:
            print('No streamers available load')


@app.route('/')
async def index():
    return 'Twitch Streamers API '


@app.route('/api/streamers/list', methods=['GET'])
async def list_streamers():
    """Endpoint to list all tracked streamers."""
    return jsonify(tracked_streamers)


@app.route('/api/streamers/add', methods=['POST'])
async def add_streamers():
    """Endpoint to add streamers to the tracking list."""
    data = await request.get_json()
    streamers = data.get('streamers', [])
    has_changed = False
    for streamer in streamers:
        streamer = streamer.lower()
        if streamer not in tracked_streamers and len(streamers) < 100:
            tracked_streamers.append(streamer)
            has_changed = True

    if has_changed:
        save_streamers()
    return jsonify({'message': 'Streamers added', 'tracked_streamers': tracked_streamers})


@app.route('/api/streamers/remove', methods=['DELETE'])
async def remove_streamers():
    """Endpoint to remove streamers from the tracking list."""
    data = await request.get_json()
    streamers = data.get('streamers', [])
    has_changed = False
    for streamer in streamers:
        streamer = streamer.lower()
        if streamer in tracked_streamers:
            tracked_streamers.remove(streamer)
            has_changed = True

    if has_changed:
        save_streamers()
    return jsonify({'message': 'Streamers removed', 'tracked_streamers': tracked_streamers})


@app.route('/api/streamers/live', methods=['GET'])
async def live_streamers():
    """Endpoint to list currently live streamers from the tracked list."""
    if not tracked_streamers:
        return jsonify({'message': 'No streamers being tracked'})
    response = await api.get_live_streamers(tracked_streamers)
    return jsonify(response)


async def setup():
    load_streamers()
    await api.setup()


async def main():
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = ["0.0.0.0:9620"]
    config.certfile = "certificate-stuff/cert.pem"
    config.keyfile = "certificate-stuff/key.pem"
    await serve(app, config)


if __name__ == '__main__':
    asyncio.run(setup())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        traceback.print_exc()
        print('Program stopped')
