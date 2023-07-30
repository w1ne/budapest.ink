import argparse
import json
from datetime import datetime, timedelta
import re
import openai
import os

def extract_number(s):
    if not isinstance(s, str):
        print(f"Unexpected data for 'response_info': {s}")
        return 0

    match = re.search(r'\d+', s)
    return int(match.group()) if match else 0

def generate_description(event):
    openai.api_key = os.getenv("OPENAI_BUDAPEST_INK_API_KEY")
    messages = [
        {"role": "system", "content": "Act As A Event Explorer. Very Proficient SEO in Fluently English. Write in Your Own Words Rather Than Copy From Other Sources. Consider perplexity and burstiness when creating content, ensuring high levels of both without losing specificity or context. Use detailed paragraphs that engage the reader. Write In A Conversational Style As Written By A Human (Use An Informal Tone, Utilize Personal Pronouns, Keep It Simple, Engage The Reader, Use The Active Voice, Keep It Brief, Use Rhetorical Questions, and Incorporate Analogies And Metaphors). Put short description of the event so people know where, when, what. Format in MD. If you do not know something, do not put explanations or empty links. For location in coordinates paste maps link. Time is Budapest local time. The article should be ready to publish as event announcment.:\n"},
	    {"role": "user", "content": f"Details of the event:\n\nName: {event['name']}\nDate and Time: {event['date_time']}\nLocation: {event['address']}\nOrganizer: {event['organizer_name']}\nText: {event['text']}"}
    ]

    for i in range(3):  # Retry up to 3 times
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.APIError as e:
                print(f"OpenAI API request failed for event '{event['name']}' on attempt {i+1}: {e}")
                time.sleep(5)  # Wait for 5 seconds before retrying
    return None  # Return None if all retries failed

def process_events_from_file(file_path):
    with open(file_path, 'r') as f:
        events = json.load(f)

    for event in events:
        response_info = event.get('response_info')
        if response_info is None:
            print(f"Missing 'response_info' in event: {event}")
            event['people_responded'] = 0
        else:
            event['people_responded'] = extract_number(response_info)

    events.sort(key=lambda x: -x['people_responded'])

    return events[:10]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", help="Path to the JSON file containing events")
    args = parser.parse_args()

    top_ten_events = process_events_from_file(args.file_path)

    # Create a new markdown file with today's date
    filename = datetime.now().strftime("%Y-%m-%d") + "-events.md"
    filepath = os.path.join("..", "content", "posts", filename)  # adjust the path according to your Hugo project's structure

    with open(filepath, "w") as f:
        # Write the required Hugo front matter
        f.write("---\n")
        f.write("title: Top 10 events for today in Budapest\n")
        f.write("date: " + datetime.now().strftime("%Y-%m-%d") + "\n")
        f.write("draft: false\n")
        f.write("---\n\n")

        for event in top_ten_events:
            name = event.get('name')
            if name is None:
                print(f"Missing 'name' in event: {event}")
                name = "Untitled Event"
            
            description = generate_description(event)
            if description is None:
                print(f"Failed to generate description for event: {event}")
                continue
            f.write(f"![Event Image]({event['image']})\n\n ### {name}\n\n{description}\n[Event Link](https://facebook.com{event['url']})\n")
            f.write("\n") 
            f.write("---") 
            f.write("\n") 

if __name__ == "__main__":
    main()

