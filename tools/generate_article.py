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
        {"role": "system", "content": "I Want You To Act As A Event Reviewer. Very Proficient SEO in Fluently English. Write in Your Own Words Rather Than Copying And Pasting From Other Sources. Consider perplexity and burstiness when creating content, ensuring high levels of both without losing specificity or context. Use detailed paragraphs that engage the reader. Write In A Conversational Style As Written By A Human (Use An Informal Tone, Utilize Personal Pronouns, Keep It Simple, Engage The Reader, Use The Active Voice, Keep It Brief, Use Rhetorical Questions, and Incorporate Analogies And Metaphors). Put short description on what event is exactly about with price(if any). Do not put empty placeholders for date or location. Format in MD Write a short paragraph about an event with the following details:\n"},
	    {"role": "user", "content": f"Here are the details of the event:\n\nName: {event['name']}\nDate and Time: {event['date_time']}\nOrganizer: {event['organizer_name']}"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=1000
    )

    return response['choices'][0]['message']['content'].strip()

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

    top_5_events = process_events_from_file(args.file_path)

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

        for event in top_5_events:
            name = event.get('name')
            if name is None:
                print(f"Missing 'name' in event: {event}")
                name = "Untitled Event"
            
            description = generate_description(event)
            f.write(f"![Event Image]({event['image']})\n\n ### {name}\n\n{description}\n[Event Link](https://facebook.com{event['url']})\n")

if __name__ == "__main__":
    main()

