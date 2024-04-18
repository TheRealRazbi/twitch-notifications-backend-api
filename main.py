import requests
from flask import request, jsonify, Flask

app = Flask(__name__)

tracked_streamers = []
twitch_api_base_url = "https://api.twitch.tv/helix/"
headers = {
    'Client-ID': client_id,
    'Authorization': f'Bearer {bearer_token}'
}


@app.route('/api/streamers/list', methods=['GET'])
def list_streamers():
    """Endpoint to list all tracked streamers."""
    return jsonify(tracked_streamers)


@app.route('/api/streamers/add', methods=['POST'])
def add_streamers():
    """Endpoint to add streamers to the tracking list."""
    data = request.get_json()
    streamers = data.get('streamers', [])
    for streamer in streamers:
        if streamer not in tracked_streamers:
            tracked_streamers.append(streamer)
    return jsonify({'message': 'Streamers added', 'tracked_streamers': tracked_streamers})


@app.route('/api/streamers/remove', methods=['DELETE'])
def remove_streamers():
    """Endpoint to remove streamers from the tracking list."""
    data = request.get_json()
    streamers = data.get('streamers', [])
    for streamer in streamers:
        if streamer in tracked_streamers:
            tracked_streamers.remove(streamer)
    return jsonify({'message': 'Streamers removed', 'tracked_streamers': tracked_streamers})


@app.route('/api/streamers/live', methods=['GET'])
def live_streamers():
    """Endpoint to list currently live streamers from the tracked list."""
    live_streamers_info = []
    if tracked_streamers:
        query = 'user_login=' + '&user_login='.join(tracked_streamers)
        url = twitch_api_base_url + 'streams?' + query
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            live_streams = response.json().get('data', [])
            live_streamers_info = [stream for stream in live_streams if stream['user_login'] in tracked_streamers]
    return jsonify(live_streamers_info)
