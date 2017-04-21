import nltk
import string
import json
from gensim import corpora, models
from time import time, strftime
from pprint import pprint
from os import path, listdir, makedirs, rename
from re import compile
from argparse import ArgumentParser
from random import choice, randint
from hashlib import md5
from matplotlib import pyplot
from operator import itemgetter
from collections import Counter
stopwords = set(nltk.corpus.stopwords.words())
morestopwords = set(['one', 'would', 'like', 'im', 'us', 'dont', 'may', 'good', 'well', 'make'])
singleletters = set(list(string.lowercase))
urlwords = set(['http', 'www', 'en', 'com', 'co', 'org', 'nbsp'])
quorawords = set(['embed', 'quote', 'quoteviaanonymous', 'quoteanswered', 'answered', 'minutes'])
excludewords = stopwords | morestopwords | singleletters | urlwords | quorawords
punctuation = string.punctuation.replace("'", "")
def getCorpusDictionary(filename):
    memory = True
    if not path.isfile(filename):
        print 'Run first with -g flag'
        exit()
    dictName = filename[:-4] + '.dict'
    if path.isfile(dictName):
        print 'Loading ' + dictName
        dictionary = corpora.Dictionary.load(dictName)
    else:
        dictionary = corpora.Dictionary(line.split() for line in open(filename))
        dictionary.save(dictName)
    if memory:
        with open(filename) as file:
            lines = json.load(file)
            QA=[]
            for line in lines:
                QA=line['answers']+line['question']
                texts = [ word.split() for word in QA ]
                print(QA)
                #pprint(texts)
            #pprint(lines)
            #pprint(QA)
            #pprint(texts)
            #texts = [ line.split() for line in QA ]
            #texts=QA.split()
            corpus = [ dictionary.doc2bow(text) for text in texts ]

    else:
        class Corpus(object):
            def __iter__(self):
                for line in open(filename):
                    yield dictionary.doc2bow(line.split())
        corpus = Corpus()
    return corpus, dictionary, lines
corpus, dictionary, lines = getCorpusDictionary('nani.json')
def LDA(corpus, dictionary, k, alpha):
    print 'Running LDA', k, alpha
    lda = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=k, alpha=alpha) # passes=25
    lda.save(path.join('lda', str(k) + '-' + str(alpha) + '.lda'))
    topics = lda.show_topics(formatted=False)
    with open(path.join('lda', 'lda_' + str(k) + '_topics.txt' + '_' + str(alpha)), 'w') as file: # remove '_' + str(alpha) from filename
        for i, topic in enumerate(topics):
            file.write('Topic ' + str(i+1) + ': ' + ' '.join(t[1] for t in topic) + '\n')
            # t[1] is word, t[0] is probability
    with open(path.join('lda', 'lda_models.log'), 'a') as file:
        file.write(strftime('%Y/%m/%d %H:%M:%S') + '\n')
        file.write(str(lda) + '\n\n')
    return lda
def processAnswer(line):
    line = line[8:].lower() # slice off 'Answer: '
    line = line.translate(string.maketrans(punctuation, ' '*len(punctuation))) # replace everything except ' with space
    line = line.translate(None, "'") # replace ' with no space
    words = nltk.word_tokenize(line)
    words = [ w for w in words if w not in excludewords ]
    return words
def createAllAnswersDoc():
    with open('answers_text.txt', 'r') as file1, open('answers_all.txt', 'w') as file2:
        lines_seen = set() # holds lines already seen
        for i, line in enumerate(file1):
            if line.startswith('Answer') and len(line) > 8 and \
               md5(line).hexdigest() not in lines_seen: # only add if not a duplicate
                lines_seen.add(md5(line).hexdigest())
                words = processAnswer(line)
                file2.write(' '.join(words) + '\n')
def part1():
    corpus, dictionary, lines = getCorpusDictionary('nani.json')
    if not path.exists('lda'):
        makedirs('lda')
    k =  2
    lda_times = []
    #for k in ks:
    start = time()
    LDA(corpus, dictionary, k, 'auto')
    lda_times.append((k, time() - start))
    #for k in ks:
    start = time()
    LDA(corpus, dictionary, k, 50.0/k)
    lda_times.append((k, time() - start))
    return lda_times
def main():
    LDA_R=part1()
    createAllAnswersDoc()
if __name__ == "__main__":
    main()