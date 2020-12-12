from bs4 import BeautifulSoup
from collections import Counter
from glob import glob
import matplotlib.pyplot as plt
import os
import requests
import re
import spacy
from time import sleep
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# All you have to do is run this python file once. :)
# Ignoring the flake8 errors for readability


def get_html():
    '''This function requests from `https://transcripts.fandom.com/wiki/` and
    saves the file in the local folder `strangerthings/`. The function doesn't
    return a value (so by default, it will automatically return `None`).'''

    # Get episode title names in order to create links
    url = "https://transcripts.fandom.com/wiki/Stranger_Things"
    h = {'user-agent': 'Tiara Johnson (tiaramj@byu.edu)'}
    response = requests.get(url, headers=h)
    links_regex = r'<a href=\"/wiki/(.*?)\" title=\"Ch'
    links = re.findall(links_regex, response.text, flags=re.IGNORECASE)

    for link in links:
        # Add link to the base url
        url = "https://transcripts.fandom.com/wiki/" + link
        response = requests.get(url, headers=h)

        htmlfilename = "strangerthings/" + link + ".html"
        with open(htmlfilename, 'w') as html_file:
            print(response.text, file=html_file)  # save html to file

        # tells the scraper to sleep for 1 sec per loop/request
        sleep(1)


def get_dialogue_locations():
    '''The function extracts the locations and dialogues from the saved
    html files and saves it in a text file per episode'''

    for htmlfile in glob("strangerthings/*.html"):
        with open(htmlfile, 'r') as f:
            content = f.read()
            regex = r'<p>(.*)\s<\/p>'  # Dialogue regex
            dialogues = re.findall(regex, content, flags=re.IGNORECASE)

            # Use BeautifulSoup to get locations from span class
            soup = BeautifulSoup(content, 'html.parser')
            locations = [spans.text for spans in soup.find_all('span', {'class': 'mw-headline'})]  # Ignoring flake8 error

        with open(htmlfile.replace(".html", ".txt"), 'w') as textfile:
            print("Locations: ", file=textfile)
            for location in locations:
                # Remove extra time & sub-location info
                simple_loc = re.sub(r'\s-\s.*', "", location)

                # create dictionary with location counts for analysis
                if simple_loc not in location_dict.keys():
                    # adds the key for the first time
                    location_dict[simple_loc] = 1
                else:
                    location_dict[simple_loc] += 1

                # Save full location info to text file
                print(location, file=textfile)

            print("\nScript: ", file=textfile)
            for dialogue in dialogues:
                # clean up extra bold tags in S1 dialogues
                # remove html entity names
                clean = dialogue.replace("<b>", "").replace("</b>", "").replace("&amp;", "and").replace("&#160;", "")  # Ignore flake8 error
                print(clean, file=textfile)


def get_characters():
    '''This function reads through each episodes dialogues and
    populates a set of unique characters and the number of times they
    appear as the speaker.'''

    for textfile in glob("strangerthings/*.txt"):
        with open(textfile, 'r') as f:
            content = f.read()
            regex = r'\n\b(.*?):\s.*'  # Character regex
            characters_list = re.findall(regex, content, flags=re.IGNORECASE)
            for person in characters_list:
                # add to set to get unique characters
                characters.add(person)
                # add to dictionary to get speaker counts
                if person not in char_frequencies.keys():
                    char_frequencies[person] = 1
                else:
                    char_frequencies[person] += 1


def character_analysis():
    '''This function creates text files with just the dialogues for the
    10 most common characters and then uses spacy for word frequency,
    entity recognition, and sentiment analysis'''

    # Create text files with just the dialogues for the
    # 10 most common characters
    for charc in common_chars:
        with open("strangerthings/characters/"+charc+".txt", 'w') as charcfile:
            for textfile in glob("strangerthings/*.txt"):
                with open(textfile, 'r') as f:
                    content = f.read()
                    regex = re.escape(charc) + r":\s?(.*)"  # dialgoue regex
                    dialogues = re.findall(regex, content, flags=re.IGNORECASE)
                    for dialogue in dialogues:
                        print(dialogue, file=charcfile)

    # Custom list to filter stop words
    custom_stop_words = ["okay", "yeah", "know", "go", "oh", "like", "hey",
                         "to", "uh", "um"]
    labels = ['DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL',
              'CARDINAL', 'PERSON']
    for textfile in glob("strangerthings/characters/*.txt"):
        print(textfile)
        ent_dict = {}
        with open(textfile, 'r') as f:
            content = f.read()
            doc = nlp(content)

            # Find common words per character
            word_counter = Counter()
            for token in doc:
                # not including stop words and punctuations in my counts
                if token.is_stop is False and token.is_punct is False and token.lemma_ not in custom_stop_words:
                    word_counter[token.lemma_] += 1
            word_counter.pop('\n')

            # Named entity recognition - pop culture code
            for ent in doc.ents:
                if ent.text not in characters and ent.label_ not in labels and ent.text not in ent_dict.keys():
                    ent_dict[ent.text] = ent.label_
                # print(ent.text, ent.label_)

            # Sentiment analysis print to terminal
            ps = hal.polarity_scores(content)
            for name, score in sorted(ps.items()):
                print(f'\t{name}: {score:> .3}', end='  ')
            print()

        name = os.path.splitext(os.path.basename(textfile))[0]

        # Print NER stuff to its own file
        with open('strangerthings/characters/NER/' + name +
                  "NER.txt", 'w') as entfile:
            for key, value in ent_dict.items():
                print(key + '\t\t' + value, file=entfile)

        # print(word_counter.most_common(10))
        # start buliding word frequency plot
        common = dict(word_counter.most_common(10))
        plt.bar(common.keys(), common.values())
        plt.title('Top Common Words - ' + name)
        plt.xlabel('Words')
        plt.ylabel('Frequency')
        fig = plt.gcf()
        fig.savefig(textfile[:-4])
        plt.clf()


# Creates directory 'strangerthings'
try:
    os.mkdir('strangerthings')
except FileExistsError:
    pass  # if it already exists, do nothing

# Creates directory 'characters'
try:
    os.mkdir('strangerthings/characters')
except FileExistsError:
    pass  # if it already exists, do nothing

# Creates directory 'NER'
try:
    os.mkdir('strangerthings/characters/NER')
except FileExistsError:
    pass  # if it already exists, do nothing

nlp = spacy.load('en_core_web_md')
hal = SentimentIntensityAnalyzer()


# Step 1: Scrape all html for each episode from fandom.com
get_html()  # This should return 25 html files


# Step 2: Parse out dialogues and locations from html files to text files
location_dict = {}
get_dialogue_locations()  # This should return 25 txt files


# Step 3: Get all the characters and how many times they appear as the speaker
char_frequencies = {}
characters = set()
get_characters()

# print(len(characters))
# print("\nWord frequencies:\n")
# print(sorted(char_frequencies.items(), key=lambda x: x[1], reverse=True))
# print(sorted(location_dict.items(), key=lambda x: x[1], reverse=True))


# Step 4: Plot 10 most common characters
# Characters plot
common_chars = dict(Counter(char_frequencies).most_common(10))
keys = common_chars.keys()
values = common_chars.values()

plt.bar(keys, values)
plt.xlabel('Characters')
plt.ylabel('Count')
plt.title('10 Most Common Characters By Dialogue')
plt.show()


# Step 5: Plot 5 most common locations
# Location plot
common_locations = dict(Counter(location_dict).most_common(5))
keys = common_locations.keys()
values = common_locations.values()

plt.bar(keys, values)
plt.xlabel('Locations')
plt.ylabel('Count')
plt.title('5 Most Common Stranger Things Locations')
plt.xticks(fontsize=8, rotation=10)
plt.show()


# Step 6: Find common words said by the 10 most common characters
# and perform sentiment analysis and NER on each character
character_analysis()
# Look in strangerthings/characters for word freq results
# Look in strangerthings/characters/NER for named ent recog results
