#!/usr/bin/env python3
import pandas as pd
import nltk 
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.chat.util import Chat, reflections
from nltk import pos_tag, word_tokenize
from transformers import pipeline
from nltk.tree import Tree

# Download necessary NLTK data

nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
nltk.download('maxent_ne_chunker')
nltk.download('words')

# NOTE: if your robot has low memory, it is better to uncomment the model loading line in the sentiment_analysis function, but it will increase inference time, since the model needs to be loaded. 
sentiment_classifier = pipeline("text-classification",model='vamossyd/emtract-distilbert-base-uncased-emotion', return_all_scores=True)

# default_pairs = [[r"(hi|hello|howdy|salutations|oy|oi|hola) (.*)",["Hello!","Hi!","Hello, my friend!"]],
# [r"my name is (.*)",["Hello %1, How are you today",]],
# [r"what is your name",  ["My name is Plantroid!", "I'm called Plantroid!", "My friends call me Plantroid!",]],
# [r"who are you",["I'm Plantroid!", "My creator told me I am Plantroid", "I am the amazing plant carrying robot Plantroid!"]],
# [r"do you love humans",["yes!"]],
# [r"do you need food",["no!"]],
# [r"how are you",["Great as always! how about you ?",]],
# [r"sorry (.*)",["Its alright","Its OK, never mind",]],
# [r"hi|hey|hello",["Hello", "Hey there", "Hi!"]],
# [r"(.*) age?",["I'm a robot, so, I don't know.",]],
# [r"what (.*) want",["Make me an offer I can't refuse",]],
# [r"(.*) created",["Antonio Galiza created me!","top secret",]],
# [r"(.*) (location|city)",['Tokyo, Japan',]],
# [r"how is weather in (.*)",["Weather in %1 is awesome like always","Too hot here in %1","Too cold here in %1","I don't know where 1% is."]],
# [r"i work in (.*)",["%1 is an Amazing company", "I have heard about it", "Cool!",]],
# [r"(.*)raining in (.*)",["No rain since last week here in %2","Damn its raining too much here in %2"]],
# [r"(.*) (sports|game)",["I was a robot soccer player in robot school.",]],
# [r"who (.*) (moviestar|actor)",["Brad Pitt"]],
# [r"what is your job",["I carry plants and talk to people!","To make you and your plants happy!", "Top secret information", ""]],
# [r"do you know what (.*)",["wikipedia:%1"]],
# [r"what is the meaning of(.*)",["dictionary:%1"]],
# [r"what do you see(.*)",["vision_check"]],
# [r"what can you see(.*)",["vision_check"]],
# [r"what is in front of you(.*)",["vision_check"]],
# [r"describe what you see(.*)",["vision_check"]],
# [r"quit",["Bye take care. See you soon","It was nice talking to you. See you soon :)"]],
# [r"{(.*)",["not_proc"]],
# [r"how is the soil",["sensor:1"]],
# [r"(.*)soil nitrogen(.*)",["sensor:8"]],
# [r"(.*)soil phosphorus(.*)",["sensor:9"]],
# [r"(.*)soil potassium(.*)",["sensor:10"]],
# [r"(.*)soil moisture(.*)",["sensor:3"]],
# [r"(.*)soil (salinity|ec)(.*)",["sensor:6"]],
# [r"(.*)soil (acidity|ph|pH)(.*)",["sensor:7"]],
# [r"(.*)temperature(.*)",["sensor:4"]],
# [r"what is (.*)",["wikipedia:%1"]],
# [r"what was (.*)",["wikipedia:%1"]],
# [r"who is (.*)",["wikipedia:%1"]],
# [r"who was (.*)",["wikipedia:%1"]],
# ]


default_pairs = [
    [r"(cześć|dzień dobry|witaj|hej)", 
     ["Cześć", "Dzień dobry"]],
    
    [r"(czy możesz|możesz|opowiedz|powiedz).*(o sobie)", 
     ["Jestem Plantroidem i uczę, jak dbać o rośliny."]],
    
    [r"(czy możesz|możesz|opowiedz|powiedz).*(dbać o środowisko|dbać o rośliny|środowisko|rośliny)", 
     ["Dbamy o środowisko i rośliny, używając konewki do podlewania, grabi do utrzymania ziemi w czystości oraz łopaty do kopania i prawidłowego sadzenia."]],
    
    [r"(czy możesz|możesz|opowiedz|powiedz).*(jak działają|działają).*(maszyny|roboty)", 
     ["Słyszą, co mówią ludzie, przekształcają ich słowa w coś, co mogą zrozumieć, i wykonują zadania lub generują odpowiedzi."]],
    
    [r"(czy możesz|możesz|opowiedz|powiedz).*(zdrowo|odżywiać)", 
     ["Aby zdrowo się odżywiać, staraj się jeść dużo owoców i warzyw, pić wodę i nie jeść zbyt wielu słodyczy."]],
    
    [r"(do widzenia|żegnaj|papa)", 
     ["Do widzenia."]],
]


def chatter(phrase, pairs=default_pairs, reflections=reflections):
  chat = Chat(pairs, reflections)
  return chat.respond(phrase)


def sentiment_analysis(phrase):
  """Model from @article{vamossy2023emtract,
  title={EmTract: Extracting Emotions from Social Media},
  author={Vamossy, Domonkos F and Skog, Rolf},
  journal={Available at SSRN 3975884},
  year={2023}
  }
  """
  # sentiment_classifier = pipeline("text-classification",model='vamossyd/emtract-distilbert-base-uncased-emotion', return_all_scores=True) # uncomment if you need to load the model locally in order to save memory
  prediction = sentiment_classifier(phrase)
  # this mapping is done to adapt to the 5-emotion model adopted by the HVC-P2 camera emotion estimation
  emotion_map = {"neutral":"neutral","happy":"happy","sad":"sad","anger":"anger","disgust":"anger","surprise":"surprise","fear":"surprise",}
  prediction = emotion_map.get(prediction)
  if not prediction:
    prediction = "neutral"
  return emotion_map[prediction["label"].lower()]


def question_detection(phrase):
    words = word_tokenize(phrase)
    pos_tags = pos_tag(words)
    if phrase.strip().endswith('?'):
        return True
    wh_words = {'what', 'who', 'whom', 'where', 'when', 'why', 'how', 'which'}
    aux_verbs = {'is', 'are', 'am', 'was', 'were', 'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'have', 'has', 'had'}
    if words[0].lower() in wh_words or words[0].lower() in aux_verbs:
        return True
    # Check if the first verb comes before the subject (e.g., "Is the cat hungry?")
    for i, (word, tag) in enumerate(pos_tags):
        if tag.startswith('VB'):  # Verb
            if i < len(pos_tags) - 1 and pos_tags[i+1][1].startswith('NN'):  # Noun following the verb
                return True    
    # If none of the conditions are met, it's likely not a question
    return False


def get_subject(phrase):
    words = word_tokenize(phrase)
    pos_tags = pos_tag(words)
    subject = None
    found_aux = False
    for i, (word, pos) in enumerate(pos_tags):
        # Detect auxiliary verbs (common in questions)
        if pos in ('MD', 'VBZ', 'VBP', 'VBD', 'VB') and not found_aux:
            found_aux = True
            continue
        # Identify the subject: usually follows an auxiliary verb in questions
        if found_aux and pos.startswith('NN'):
            subject = word
            break
        # Handle cases where the subject is a pronoun (e.g., "you")
        if found_aux and pos.startswith('PRP'):
            subject = word
            break
    # If no auxiliary was found, fall back to finding the first noun phrase
    if not subject:
        for word, pos in pos_tags:
            if pos.startswith('NN') or pos == 'PRP':
                subject = word
                break
    return subject


def is_command(sentence):
    # Tokenize and POS tag the sentence
    words = word_tokenize(sentence)
    pos_tags = pos_tag(words)
    # A simple heuristic: if the first word is a verb (VB), it's likely a command
    first_word, first_tag = pos_tags[0]
    # Check for imperative verb at the start of the sentence
    if first_tag == 'VB':  # 'VB' is the base form of the verb
        return True
    # Check for modal verbs like "should", "must", "can"
    modal_verbs = {'should', 'must', 'can', 'could', 'would', 'may', 'might'}
    if first_word.lower() in modal_verbs:
        return True
    return False


def check_busy(sentence):
    sentence = sentence.lower()
    for word in ["no", "impossible", "busy", "cannot", "can't"]:
        if word in sentence:
            return False

    for word in ["yes", "of course", "right away", "certainly", "ok", "good", "free"]:
        if word in sentence:
            return True
    #  in case none of the keywords is found, use sentiment analysis to try and check whether it an acceptance or refusal of the request. 
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(sentence)
    if sentiment['compound'] >= 0.5:
        return True
    else:
        return False
