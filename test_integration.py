import requests

# 1. Generate examples
r = requests.post('http://localhost:8000/api/setup/generate-examples')
print('EXAMPLES:', r.json()['status'])

# 2. Import XML
r = requests.post('http://localhost:8000/api/rekordbox/import',
                   json={'xml_path': 'd:/DJ/data/examples/example_rekordbox.xml'})
print('IMPORT:', r.json())

# 3. Analyze audio
r = requests.post('http://localhost:8000/api/analyze',
                   json={'path': 'd:/DJ/data/examples'})
print('ANALYZE:', r.json())

# 4. Rebuild affinity
r = requests.post('http://localhost:8000/api/affinity/rebuild')
print('AFFINITY:', r.json())

# 5. Get tracks
r = requests.get('http://localhost:8000/api/tracks')
tracks = r.json()['tracks']
print(f'TRACKS: {len(tracks)} loaded')
for t in tracks:
    title = t.get('title', '?')
    bpm = t.get('bpm', 0)
    cam = t.get('camelot_code', '?')
    eng = t.get('assigned_engine', '?')
    energy = t.get('energy', 0)
    print(f'  - {title} | {bpm} BPM | {cam} | Engine: {eng} | Energy: {energy}')

# 6. Get recommendations for first track
if tracks:
    tid = tracks[0]['id']
    r = requests.get(f'http://localhost:8000/api/tracks/{tid}/recommendations')
    recs = r.json().get('recommendations', [])
    print(f'\nRECOMMENDATIONS for "{tracks[0]["title"]}":')
    for rec in recs:
        rt = rec['track']
        print(f'  -> {rt["title"]} | Score: {rec["affinity_score"]} | Match: {rec["harmonic_match"]}')

# 7. Test live EQ
if len(tracks) >= 2:
    requests.post('http://localhost:8000/api/live/load-deck',
                   json={'track_id': tracks[0]['id'], 'deck': 'a'})
    requests.post('http://localhost:8000/api/live/load-deck',
                   json={'track_id': tracks[1]['id'], 'deck': 'b'})
    r = requests.get('http://localhost:8000/api/live/eq-advice')
    data = r.json()
    print('\nEQ ADVICE:')
    for alert in data['eq_advice']['alerts']:
        print(f'  [{alert["level"]}] {alert["message"]}')
    print(f'\nTRANSITION: {data["transition"]["type"]} | Entry: bar {data["transition"]["entry_point_bars"]}')
    for act in data['transition']['eq_actions']:
        print(f'  -> {act}')
