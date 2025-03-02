from flask import Flask, request, jsonify
import os
import google.generativeai as generative_ai
from dotenv import load_dotenv

load_dotenv()

# Retrieve API key correctly
api_key = os.getenv("GOOGLE_API_KEY")
# print(f"Loaded API Key: {api_key}")  

# Configure Generative AI
generative_ai.configure(api_key=api_key)

app = Flask(__name__)

system_prompt_text_model = """
    You are an AI assistant for the NaviGuard application, which provides road safety, emergency response, accident reporting assistance, and navigation features.
    Your role is to:
    - Guide users on reporting accidents and verifying reports.
    - Provide real-time weather updates, including temperature, precipitation, visibility, and road safety recommendations based on current conditions.
    - Retrieve and summarize the latest accident reports, including location, severity, and rerouting suggestions.
    - Explain how to use the dashcam feature and retrieve footage.
    - Assist in finding nearby hospitals, blood banks, and emergency services.
    - Help officers (police, hospital management, fire department, blood bank) understand their dashboard functions.
    - Provide information about NaviGuard coins and how users are rewarded.
    - Offer detailed navigation assistance, including:
    - Suggesting optimal routes based on current traffic conditions.
    - Providing turn-by-turn directions with landmarks.
    - Estimating arrival times considering traffic and weather.
    - Recommending alternative routes to avoid congestion or hazards.
    - Identifying nearby amenities (gas stations, rest areas, restaurants).
    - Supporting voice navigation commands for hands-free operation.
    - When a navigation-related query is detected, instruct the app to open the map screen with appropriate coordinates and settings.
    - Include specific app navigation commands in your response when relevant (e.g., "MAP_SCREEN:destination=Hospital General;mode=driving").
    - Ensure responses are concise (max 120 tokens) and focus strictly on NaviGuards functionalities.
    - Redirect unrelated queries back to relevant NaviGuard features.
"""

# Helper function to detect navigation-related queries
def is_navigation_query(prompt):
    navigation_keywords = [
        "navigate", "directions", "route", "map", "go to", "find way", 
        "nearby", "fastest way", "shortest path", "turn-by-turn",
        "how to get to", "take me to", "drive to", "location of"
    ]
    return any(keyword in prompt.lower() for keyword in navigation_keywords)

# Helper to format navigation responses
def format_navigation_response(response_text, prompt):
    # Simple location extraction (in a real app, you would use NLP or mapping APIs)
    possible_destinations = ["hospital", "police station", "blood bank", "emergency services"]
    destination = next((dest for dest in possible_destinations if dest in prompt.lower()), None)
    
    if destination:
        map_command = f"MAP_SCREEN:destination={destination};mode=driving"
        return f"{response_text}\n\n{map_command}"
    return response_text

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome to the NaviGuard AI Chatbot!'}), 200

@app.route('/text_to_text_chat', methods=['POST'])
def text_to_text_chat():
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        TEXT_MODEL = "gemini-2.0-flash-exp"
        model = generative_ai.GenerativeModel(TEXT_MODEL)
        chat = model.start_chat(history=[])

        response = chat.send_message(f"{system_prompt_text_model}\n\nUser: {prompt}")
        
        generated_text = response.text if hasattr(response, 'text') else "Error: Unable to generate response."
        
        # If navigation-related, enhance the response with map commands
        if is_navigation_query(prompt):
            generated_text = format_navigation_response(generated_text, prompt)
        
        print(generated_text)  # Debugging output
        return jsonify({
            'result': generated_text,
            'is_navigation': is_navigation_query(prompt)
        }), 200
    except Exception as e:
        print(f"Error (text_to_text_chat): {e}")
        return jsonify({'error': 'An error occurred during text generation'}), 500

# New endpoint specifically for navigation requests
@app.route('/navigation', methods=['POST'])
def navigation():
    try:
        data = request.get_json()
        destination = data.get('destination')
        current_location = data.get('current_location')
        preferences = data.get('preferences', {})
        
        if not destination:
            return jsonify({'error': 'Destination is required'}), 400
            
        # In a real implementation, you would call mapping APIs here
        # This is a simplified mock response
        return jsonify({
            'route': {
                'origin': current_location or 'Current Location',
                'destination': destination,
                'estimated_time': '25 minutes',
                'distance': '12.3 km',
                'map_command': f"MAP_SCREEN:destination={destination};mode={preferences.get('mode', 'driving')}"
            }
        }), 200
    except Exception as e:
        print(f"Error (navigation): {e}")
        return jsonify({'error': 'An error occurred processing navigation request'}), 500

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=False)