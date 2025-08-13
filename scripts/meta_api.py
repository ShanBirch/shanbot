from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import re
import logging

app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


gemini_api_key = None


def setup_gemini(api_key):
    global gemini_api_key
    gemini_api_key = api_key
    genai.configure(api_key=gemini_api_key)


@app.route('/summarize-code', methods=['POST'])
def summarize_code():
    data = request.get_json()
    if not data or 'code' not in data or 'output' not in data:
        logging.error("No code or output provided in the request.")
        return jsonify({'error': 'No code or output provided'}), 400

    code = data['code']
    output = data['output']
    pastebin_links = data.get('pastebin_links', {})
    logging.debug(f"Received output:\n{output}")
    logging.debug(f"Received links:\n{pastebin_links}")

    prompt = f"""
        You are an AI coding assistant that helps debug selenium scripts.
        Your role is to provide a high level overview of the python code provided, highlighting areas that could be improved, or that might be causing problems.

        Here is the output from a selenium script:
        {output}
         Here is the code from the script:
         {code}
        Here are links to the log files:
        {pastebin_links}
        
        Please provide a summary of the code, with feedback on how to improve the code, and what areas of the code should be prioritized for debugging.
        Do not provide code changes, only high level feedback.
       """
    logging.debug(f"Generated Prompt:\n{prompt}")

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        logging.debug(f"Gemini Response:\n{response.text}")
        summary = response.text
        return jsonify({'summary': summary})
    except Exception as e:
        logging.exception(f"Error processing with Gemini: {str(e)}")
        return jsonify({'error': f"Error processing with Gemini: {str(e)}"}), 500


if __name__ == '__main__':
    setup_gemini("AIzaSyA3bMRGd2KfTrf_G6YuUIDiq7F94w1EDFw")
    app.run(debug=False, port=5002, use_reloader=False)  # Changed port to 5002
