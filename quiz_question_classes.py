#Sample questions (in German).
QUIZ_FRAGEN = {
        'Wie viele WM-Titel hat Brasilien?': '5',
        "Welches Team hat insgesamt die meisten WM-Spiele gewonnen?": "brasilien",
        "Welche Mannschaft hat insgesamt die meisten WM-Spiele gespielt?": "deutschland",
        "Welche der Mannschaften, die noch keinen WM-Titel haben, wurde am häufigsten Vizemeister?": ("OR","die niederlande","holland", "niederlanden", "niederlande"),
        "Wann wurde Argentinien zum letzten Mal Fußball-Weltmeister: 1982, 1986, 1994 oder 2002?": ("OR", "1986", "86"),
        "Wann wurde Brasilien zum letzten Mal Fußball-Weltmeister: 1990, 1998, 2002 oder 2006?": "2002",
        "Wie viele von den 21 bisherigen WM-Titeln wurden von europäischen Teams gewonnen?": "12",        
        "Wie oft wurde eine Weltmeisterschaft im Elfmeterschießen entschieden: nie, einmal, zweimal oder dreimal?": ("OR", "zweimal", "2"),
        "Wie viele von den 21 bisherigen WM-Titeln haben Deutschland, Brasilien und Italien zusammen: 7, 9, 13 oder 16?": "13",
        "Wie viele WM-Finale wurden in der Verlängerung entschieden: 3, 5, 7 oder 9?": "5",
        "Wann hat Deutschland seinen ersten WM-Titel gewonnen: 1934, 1950, 1954 oder 1970?": ("OR", "1954", "54"),
}

class Frage(object):
    """
    Class to handle questions and answers.
    """
    def __init__(self, frage, antwort):
        self.frage = frage
        self.antwort = antwort
        self.lese_antwort = ""

    def evaluate(self, answer):
        return True if answer == self.antwort else False
    
    def get_frage(self):
        return self.frage
    
    def get_ans_str(self):
        """
        Returns answer in string format.
        """
        if self.lese_antwort != "":
            return self.lese_antwort
        elif isinstance(self.antwort,str):
            return self.antwort
        else:
            return self.antwort[0]

    def set_lese_antwort(self, lese_antwort):
        self.lese_antwort = lese_antwort
    
    def __str__(self):
        return self.frage    
    
class Frage_Mult(Frage):
    """
    Class for handling questions with multiple answers.
    """
    def __init__(self, frage, antwort):
        Frage.__init__(self, frage, antwort)
        
    def evaluate(self, answer):
        for e in self.antwort:
            if e == answer:
                return True
        return False
 
list_fragen = []    
for e in QUIZ_FRAGEN.items():
    if isinstance(e[1],tuple):
        list_fragen.append(Frage_Mult(e[0],e[1][1:]))
    else:
        list_fragen.append(Frage(e[0],e[1]))