import requests
import json

# Start a new game with custom word between 'elmo' and 'fulmine'
session = requests.Session()

# Set a word between elmo and fulmine
response = session.post('http://localhost:8080/set-custom-word',
                        json={'parola': 'facile'})
print("Set custom word 'facile':", response.status_code)

# Make some guesses to narrow the range
response = session.post('http://localhost:8080/guess', json={'parola': 'elmo'})
data = json.loads(response.text)
print(f"\nGuess 'elmo': {data['risultato']}")
print(f"Range: {data['parola_minima']} - {data['parola_massima']}")

response = session.post('http://localhost:8080/guess', json={'parola': 'fulmine'})
data = json.loads(response.text)
print(f"\nGuess 'fulmine': {data['risultato']}")
print(f"Range: {data['parola_minima']} - {data['parola_massima']}")

print("\n✓ The range is now: elmo - fulmine")
print("The alphabet helper should show el..., em..., en... etc. and fa..., fb..., fc... etc.")