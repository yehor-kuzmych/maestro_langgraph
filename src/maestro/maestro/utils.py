#!/usr/bin/env python3
from random import choice
from wikipedia import summary, suggest
from PyDictionary import PyDictionary
import sqlite3 as sql


def now():
    import datetime
    now = datetime.datetime.today()
    return (now.year, now.month, now.day, now.hour, now.minute, now.second,now.microsecond)


def write_sql(dbLoc, sql_command, values):
    db = sql.connect(dbLoc)
    cursor = db.cursor()
    cursor.execute(sql_command, values)
    db.commit()
    db.close()


def gibberish():
    min_len_words=1
    max_len_words=10
    min_len_phrase=1
    max_len_phrase=1
    consonants=["m", "M", "n[","n","n.","n^","N",'n"',"p","b","t[","d[","t","d","t.","d.","c","J","k","g","q","G","?","s","z","S","Z","s.","z.","P","B","f","v","T","D","C","C<vcd>","x","Q","X",'g"',"H","H<vcd>","h","h<?>","s<lat>","z<lat>", "r<lbd>","r[","r","r.","j","j<vel>",'g"', "l[","l","l.","l^","L","*","*.","*<lat>","b<trl>","r<trl>",'r"',"p!","t!","c!","k!","l!","b`","d`","J`","g`","G`","p`","t[`","t`","c`","k`","q`"]
    otherSymbols=["n<lbv>","t<lbv>","d<lbv>","w<vls>","w"]
    vowels=["i","y",'i"','u"',"u-","u","I","I.","U","e","Y","@<umd>","o-","o","@","@.","E","W",'V"','O"',"V","O","&","a","a.","A","A."]
    empty = [""]

    counter0 = 0
    max_len_phrase = choice(range(min_len_phrase, max_len_phrase+1))
    phrase = ""
    t0 = 0
    tries = 0

    while counter0 <= max_len_phrase:
        counter1 = 0
        wordlen = choice(range(min_len_words, max_len_words+1))
        word = ""
        while counter1 < wordlen:
            phoneme = choice(choice([vowels,consonants]))
            phoneme +=  choice(choice([vowels,consonants,otherSymbols,[""]]))
            if len(phoneme)>1:
                if phoneme[0] in consonants and phoneme[1] in consonants:
                    phoneme += choice(vowels)
                elif phoneme[1] in otherSymbols:
                    phoneme +=  choice(choice([vowels,consonants]))
                else:
                    phoneme +=  choice(choice([vowels,consonants,[""],[""],[""],[""],[""],[""]]))

            word+= phoneme+" "
            counter1+=1

        phrase += word+" "
        counter0 += 1
    return phrase


def wikipedia_query(title):
    ans = "Sorry, I don't know what "+title+" is."
    try:
        ans = summary(title, sentences=2)
    except: pass
    #    try:
    #        ans = summary(suggest(title),sentences=2)
    #    except:
    #        pass
    return ans


def dictionary_query(word):
    dictionary=PyDictionary()
    ans = "Sorry, I don't know what " + word + " means."
    try:
        temp = "The "
        d = dictionary.meaning(word)
        for grammar in list(d.keys()):
            temp += grammar + " " + word + " means " + d[grammar][0]
            if grammar != list(d.keys())[-1]:
                temp += " and the "
        ans = temp
    except:
        pass
    return ans
