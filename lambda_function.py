import random
import re
import quiz_question_classes as quiz

TOTAL_ROUNDS = 3

TEXT_BREAK = "<break/>"

TICK_BEEP_SOUND = "<audio src='https://s3-eu-west-1.amazonaws.com/weltmeisterquiz-audio/tick_beep.mp3'/>"

TICK_HELP_MESSAGE = "<s>Beantworte jede Frage nach dem Piepton. </s>\
<s>Wenn du eine Frage nochmal hören willst, sag Frage wiederholen.</s> "

WELCOME_MESSAGE = "Hallo! Willkommen im Weltmeisterquiz. Wie viele Spieler seid ihr? \
                   Sag eine Nummer zwischen 1 und 4."

SPIELER_PROMPT_TEXT = "<s>Wie viele Spieler seid ihr?</s> Sag eine Nummer zwischen 1 und 4."


ABSCHIED_CARD_TEXT = "Spiel beendet. Danke fürs Mitspielen!"

HELP_MESSAGE = "Dies ist ein inoffizielles Quiz zur Fußball-Weltmeisterschaft. \
                Bis zu 4 Spieler können gleichzeitig an einem \
                Spiel teilnehmen. Es werden jeweils {0}\
                Fragen an jeden Spieler gestellt. ".format(TOTAL_ROUNDS) + TICK_HELP_MESSAGE

NEG_SPEECHCONS = ["oh nein! ", "oh oh! ", "oje! ", "hm! "]

POS_SPEECHCONS = ["sehr gut! ", "wunderbar! ", "bingo! ", "genau! "]

NEG_ANS = ["Das stimmt leider nicht." + TEXT_BREAK,
           "Das ist leider Falsch." + TEXT_BREAK,
           "Falsche Antwort." + TEXT_BREAK
          ]

POS_ANS = ["Richtig beantwortet." + TEXT_BREAK,
           "Richtige Antwort." + TEXT_BREAK,
           "Richtige antwort." + TEXT_BREAK
          ]

def lambda_handler(event, context):
    """ App entry point  """
    
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
    try:
        if event['request']['type'] == "LaunchRequest":
            return on_launch()
        elif event['request']['type'] == "IntentRequest":
            return on_intent(event['request'], event['session'])
        elif event['request']['type'] == "SessionEndedRequest":
            return on_session_ended(event['request'], event['session'])
    except Exception as e:
        print(e)
        text = "Fehler. Skill wird beendet."
        return response(text, True)

def on_session_started(session_started_request, session):
    """Called when the session starts."""

    print("on_session_started requestId=" +
          session_started_request['requestId'] + ", sessionId=" +
          session['sessionId'])

def on_launch():
    """ called on Launch reply with a welcome message """
    return get_welcome_message()

def on_intent(request, session):
    """ Called on receipt of an Intent  """

    intent = request['intent']

    print("on_intent:", intent)

    if intent["name"] == "AntwortIntent":
        return handle_answer_request(intent, session)
    elif intent["name"] == "DontKnowIntent":
        return handle_answer_request(intent, session)
    elif intent['name'] == "AMAZON.RepeatIntent":
        return handle_repeat_request(intent, session)
    elif intent['name'] == "AMAZON.StopIntent" or intent['name'] == "AMAZON.CancelIntent":
        return handle_finish_session_request(intent, session)
    elif intent['name'] == "AMAZON.HelpIntent":
        return get_help(intent, session)
    elif intent['name'] == "StartQuizIntent" or intent['name'] == "AMAZON.StartoverIntent":
        if session["new"] == False:
            return get_welcome_message(restart=True)
    #if no intent is identified:
    return get_help(intent, session)


def on_session_ended(session_ended_request, session):
    """
    Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

def handle_repeat_request(intent, session):
    
    print("handle_repeat_request: ", intent)

    if "attributes" not in session:
        return get_welcome_message()
    elif "speech_output" in session["attributes"]:
        attributes = session["attributes"]
        speech_output = attributes.get("current_question", "reprompt_text")
        reprompt_text = attributes.get("current_question", "reprompt_text")
        
        attributes["speech_output"] = speech_output
        attributes["reprompt_text"] = reprompt_text

        return response(speech_output, False, reprompt_text, attributes)

    else:
        #If all fails:
        return get_help(intent, session)
    
def get_help(intent, session):
    """ return a help response  """
   
    print("get_help: ", intent)

    text = HELP_MESSAGE
    if "attributes" in session and "current_question" in session["attributes"]:
        attributes = session["attributes"]
        frage_text = attributes["current_question"]
        text += "Ich wiederhole die letzte Frage: " + frage_text
    else:
        frage_text = SPIELER_PROMPT_TEXT
        text += SPIELER_PROMPT_TEXT
        attributes = reset_attributes()
    
    attributes["current_question"] = frage_text
    attributes["speech_output"] = text
    attributes["reprompt_text"] = frage_text

    return response(text, False, frage_text, attributes, card_text=clear_tags(HELP_MESSAGE)+\
                    "\n" + build_card_content(attributes))

def handle_answer_request(intent, session):
    """ calls appropriate function for the intent """

    eins_list = ["eins", "ein", "einer", "eine", "einen", "eines", "einem"]
    
    if intent["name"] == "DontKnowIntent":
        answer = "weiß nicht"
    elif "Nummer" in intent["slots"].keys() and "value" in intent["slots"]["Nummer"]:
        answer = intent["slots"]["Nummer"]["value"]
    elif "Antworten" in intent["slots"].keys() and "value" in intent["slots"]["Antworten"]:
        answer = intent["slots"]["Antworten"]["value"]
    else:
        answer = "Fehler"
        
    #Necessary to recognize "1":
    if answer in eins_list:
        answer = "1"
    elif answer == "ein mal":
        answer = "einmal"
    answer = answer.lower()

    print("handle_answer_request: ", intent, "answer: ", answer)

    if "attributes" not in session:
        return start_game(answer, session)
    elif session["attributes"]["state"] == "Gameon":
        return check_answer(answer, session)
    elif session["attributes"]["state"] == "Start":
        return start_game(answer, session)

    return start_game(answer, session)


def check_answer(answer, session):
    """checks if quiz answer is correct, returns speech value"""
    
    print("check_answer: ", answer)

    attributes = session["attributes"]
    print("atts\n", attributes)
    scores = attributes["scores"]
    curr_round = attributes["current_round"]
    curr_player = attributes["current_player"]
    quest_index = attributes["question_index"]
    sess_questions = attributes["sess_questions"]
    print("before curr item")
    curr_item = quiz.list_fragen[sess_questions[quest_index]]
    print("curr_item created")

    if curr_item.evaluate(answer):
        text = get_reaction("pos")
        result = 1
    else:
        text = get_reaction("neg")
        result = 0
        text += "<s>Die richtige Antwort war " + curr_item.get_ans_str() + "</s>"
    print("evaluation done")
    print("scores ", scores)
    print("curr_player ", curr_player)

    scores[str(curr_player)] += result
    print("score updated")
    if curr_round == TOTAL_ROUNDS and curr_player == len(scores):
        text += get_final_score(scores)
        print(scores)
        attributes["scores"] = scores
        return response(speech_response=text,should_end_session=True,\
                        card_text= ABSCHIED_CARD_TEXT +"\n" + \
                        build_card_content(attributes=attributes, add_frage=False))

    curr_player += 1
    print("player updated")
    if curr_player > len(scores):
        curr_player = 1
        curr_round += 1
    quest_index += 1
    
    attributes["scores"] = scores 
    attributes["current_round"] = curr_round
    attributes["current_player"] = curr_player
    attributes["question_index"] = quest_index

    frage = ask_question(quest_index, attributes)
    text += frage
    
    attributes["current_question"] = frage
    attributes["speech_output"] = text
    attributes["reprompt_text"] = frage

    return response(text, should_end_session=False, reprompt_text=frage, \
                    attributes=attributes)

def ask_question(index, attributes):
    """gets question Frage object in SESS_FRAGEN index as a string value"""
    
    print("ask_question, index: ", str(index))

    curr_question = quiz.list_fragen[attributes["sess_questions"][index]].get_frage()
    print("@ask_question: ", curr_question)

    print("@ask_question before if ")
    if len(attributes["scores"]) > 1:
        print("@ask_question if > 1")
        text = "<s>Frage {0} an Spieler {1}:</s> <s>{2}</s>".format(int(attributes["current_round"]),\
                     attributes["current_player"], curr_question)
    else:
        print("@ask_question else")
        text = "<s>Frage {0}:</s> <s>{1}</s>".format(int(attributes["current_round"]),\
                         curr_question)
    
    text = slower_speech(text)
    text += TICK_BEEP_SOUND
    
    print("@ask_question before setatts")
    attributes["current_question"] = curr_question
    print("@ask_question before setatts")

    #returns string here excepcionally because response is formed elsewhere
    return text

def reset_attributes():
    """resets and returns attributes dict"""
    
    print("reset_attributes")

    attributes = {
        "scores": {},
        "state": "Start",
        "current_player": 0,
        "current_round": 0,
        "current_question": "",
        "sess_questions":[],
        "question_index": 0,
        "speech_output": WELCOME_MESSAGE,
        "reprompt_text": HELP_MESSAGE}
    
    return attributes
    

def start_game(answer, session):
    """
    starts a new quiz with num players according to answer, resets global values,
    returns speech text including first question from ask_question()
    """

    print("start_game, answer: ", answer)

    attributes = reset_attributes()

    if answer == "einem spieler":
        answer = "1"
    if answer == "vier spieler":
        answer = "4"

    if answer in [str(x) for x in range(1, 5)]:
        curr_round = 1
        curr_player = 1
        state = "Gameon"
        scores = {x:0 for x in range(1, int(answer)+1)}
        sess_fragen = populate_questions(scores)
        
        attributes["question_index"] = 0
        attributes["current_round"] = curr_round
        attributes["current_player"] = curr_player
        attributes["state"] = state
        attributes["scores"] = scores
        attributes["sess_questions"] = sess_fragen

        if answer == "1":
            text = "<s>Alles klar. "+ TEXT_BREAK + "Wir beginnen ein Spiel mit einem Spieler."+\
            "</s> <s>Das Quiz enthält {} Fragen.\
            </s>".format(TOTAL_ROUNDS)
        else:
            text = "<s>Alles klar." + TEXT_BREAK + "Wir beginnen ein Spiel mit {} Spielern"\
            .format(answer) +\
            "</s><s> Es werden jeweils {} Fragen an jeden Spieler gestellt.\
            </s>".format(TOTAL_ROUNDS)

        frage1 = ask_question(0, attributes)
        text += TICK_HELP_MESSAGE
        text += frage1
        card_text = "Spiel mit {0} Spielern begonnen.\n".format(len(scores)) + clear_tags(frage1)

    else:
        richtige_zahl_prompt = "Sag eine Nummer zwischen 1 und 4."
        text = "Ungültige Spielerzahl. " + richtige_zahl_prompt
        frage1 = SPIELER_PROMPT_TEXT
        card_text = text

    attributes["current_question"] = frage1
    attributes["speech_output"] = text
    attributes["reprompt_text"] = frage1
    
    return response(text, should_end_session=False, reprompt_text=frage1, \
                    attributes=attributes, card_text=card_text)

def populate_questions(scores):
    """returns a list of random questions according to num of players"""
    
    print("populate_questions, scores: ", str(scores))

    try:
        return random.sample(range(len(quiz.list_fragen)), TOTAL_ROUNDS*len(scores))
    except ValueError:
        print("List of questions is too short.")

def get_welcome_message(restart=False):
    """resets globals, returns welcome message"""
    print("get_welcome_message, restart: ", str(restart))

    if restart == True:
        message = "OK, wir starten ein neues Spiel." + SPIELER_PROMPT_TEXT
    else:
        message = WELCOME_MESSAGE
    
    reprompt_text = SPIELER_PROMPT_TEXT

    return response(speech_response=message, should_end_session=False,\
                    reprompt_text=reprompt_text, card_text=WELCOME_MESSAGE)

def get_final_score(scores):
    """returns final score message as a string value"""
    
    print("get_final_score")
    
    print("scores:", scores)
    
    max_score = max(scores.values())
    print("max_score:", max_score)
    sieger = [x for x in scores.keys() if scores[x] == max_score]
    
    print("sieger:", sieger)

    if len(scores) == 1:
        print("if1")
        text = "<s>Spiel beendet. </s>Du hast {0} von {1} Fragen richtig beantwortet."\
        .format(scores["1"], TOTAL_ROUNDS)
    elif len(sieger) == 1:
        sieger = sieger[0]
        text = "<s>Spiel beendet.</s> Der Sieger ist Spieler {0} mit {1} von {2} Punkten."\
        .format(sieger, scores[sieger], TOTAL_ROUNDS)

    elif len(sieger) == len(scores):
        text = "<s>Spiel beendet.</s> <s>Es gab keinen Sieger;</s> alle Spieler haben\
        {0} von {1} Fragen richtig beantwortet.".format(max_score, TOTAL_ROUNDS)
    else:
        scores_text = ""
        for e in sieger[:-1]:
            scores_text += "<break/> Spieler {0}".format(e)
        scores_text += " und Spieler {0} mit {1} von {2} Fragen richtig beantwortet."\
        .format(sieger[-1], max_score, TOTAL_ROUNDS)
        text = "<s>Spiel beendet.</s> Das beste Ergebnis hatten" + scores_text

    text += "<s> Danke fürs Mitspielen!</s>"

    return text

def handle_finish_session_request(intent, session):
    """returns goodbye speech message, ends session"""
    
    print("handle_finish_session_request", intent)

    return response(speech_response="Danke fürs mitspielen!", should_end_session=True,
                    card_text=ABSCHIED_CARD_TEXT)

def slower_speech(text):
    return "<prosody rate = '90%'>" + text + "</prosody>"

def get_reaction(reaction_type):
    """returns negative or positive speech message according to reaction_type"""

    if reaction_type == "neg":
        speechcon = "<say-as interpret-as='interjection'>" \
        + random.choice(NEG_SPEECHCONS) + "</say-as>"
        ans = random.choice(NEG_ANS)
    elif reaction_type == "pos":
        speechcon = random.choice(POS_SPEECHCONS)
        ans = random.choice(POS_ANS)
    else:
        raise ValueError

    return speechcon + ans

def clear_tags(raw_text):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_text)
  return cleantext

def build_card_content(attributes={}, add_frage=True):
    text = ""
    if add_frage == True:
        if "current_question" in attributes:
            text += attributes["current_question"] + "\n"
    if "scores" in attributes:
        for e in attributes["scores"].items():
            text += "Spieler {0}: {1} Punkte\n".format(e[0], e[1])

    text = clear_tags(text)

    return text

def response(speech_response, should_end_session, \
             reprompt_text=HELP_MESSAGE, attributes={}, card_text=""):
    """ create a simple json response """
    
    if not card_text:
        card_text = build_card_content(attributes)
        
    response = {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml": "<speak>" + speech_response + "</speak>"
            },
            "card": {
                "type": "Simple",
                "title": "Weltmeisterquiz",
                "content": card_text
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "SSML",
                    "ssml": "<speak>" + reprompt_text + "</speak>"
                    }
                },
            "shouldEndSession": should_end_session
        }
    }
    return response