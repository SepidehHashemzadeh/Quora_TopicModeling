import nltk
import string
from gensim import corpora, models
from time import time, strftime
from os import path, listdir, makedirs, rename
from re import compile
from argparse import ArgumentParser
from random import choice, randint
from hashlib import md5
from matplotlib import pyplot
from operator import itemgetter
from collections import Counter

# import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

stopwords = set(nltk.corpus.stopwords.words())
morestopwords = set(['one', 'would', 'like', 'im', 'us', 'dont', 'may', 'good', 'well', 'make'])
singleletters = set(list(string.lowercase))
urlwords = set(['http', 'www', 'en', 'com', 'co', 'org', 'nbsp'])
quorawords = set(['embed', 'quote', 'quoteviaanonymous', 'quoteanswered', 'answered', 'minutes'])
excludewords = stopwords | morestopwords | singleletters | urlwords | quorawords
punctuation = string.punctuation.replace("'", "")

def archiveFile(filename):
    print 'Archiving ', filename
    answers_pattern = compile(filename + '.bak(\d+)')
    if path.exists(filename):
        max = 0
        filenames = listdir('.')
        for f in filenames:
            m = answers_pattern.match(f)
            if m and int(m.group(1)) > int(max):
                max = m.group(1)
        rename(filename, filename + '.bak' + str(int(max)+1))

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

def createRandomAnswersDoc():
    with open('answers_all.txt') as file1, open('answers_random.txt', 'w') as file2:
        lines = file1.readlines()
        count = 0
        while count < 5:
            doc = choice(lines)
            if len(doc) > 100:
                file2.write(doc)
                count += 1

def getTopTopics():
    with open('answers_text.txt') as file:
        topics = []
        questions = []
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith('Topic') and len(line) > 7 and \
               lines[i-1].startswith('Question') and lines[i-1] not in questions and len(lines[i-1]) > 10:
                topics.append(line[7:-1])
                questions.append(lines[i-1])
        c = Counter(topics)
        mostCommonTopics = [ x[0] for x in c.most_common(5) ]
        return mostCommonTopics

def createTopAnswersDoc():
    mostCommonTopics = getTopTopics()

    with open("answers_text.txt") as file1, open("answers_top2.txt", 'w') as file2:
        lines = file1.readlines()
        for i, line in enumerate(lines):
            if line.startswith('Topic') and line[7:-1] in mostCommonTopics and \
               lines[i+1].startswith('Answer') and len(lines[i+1]) > 8:
                words = processAnswer(lines[i+1])
                file2.write(line[7:-1] + ',') # Write the topic without 'Topic: ' and ending newline
                file2.write(' '.join(words) + '\n')

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
            lines = file.readlines()
            texts = [ line.split() for line in lines ]
            corpus = [ dictionary.doc2bow(text) for text in texts ]
    else:
        class Corpus(object):
            def __iter__(self):
                for line in open(filename):
                    yield dictionary.doc2bow(line.split())
        corpus = Corpus()
    return corpus, dictionary, lines

def LDA(corpus, dictionary, k, alpha):
    print 'Running LDA', k, alpha
    lda = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=k, alpha=alpha) # passes=25
    lda.save(path.join('lda', str(k) + '-' + str(alpha) + '.lda'))
    topics = lda.show_topics(topics=k, topn=20, formatted=False)
    with open(path.join('lda', 'lda_' + str(k) + '_topics.txt' + '_' + str(alpha)), 'w') as file: # remove '_' + str(alpha) from filename
        for i, topic in enumerate(topics):
            file.write('Topic ' + str(i+1) + ': ' + ' '.join(t[1] for t in topic) + '\n')
            # t[1] is word, t[0] is probability
    with open(path.join('lda', 'lda_models.log'), 'a') as file:
        file.write(strftime('%Y/%m/%d %H:%M:%S') + '\n')
        file.write(str(lda) + '\n\n')
    return lda

def part1():
    corpus, dictionary, lines = getCorpusDictionary('answers_all.txt')
    if not path.exists('lda'):
        makedirs('lda')
    ks = [ 2, 10, 50, 20, 25, 30, 40, 75, 100 ]
    lda_times = []
    for k in ks:
        start = time()
        LDA(corpus, dictionary, k, 'auto')
        lda_times.append((k, time() - start))
    for k in ks:
        start = time()
        LDA(corpus, dictionary, k, 50.0/k)
        lda_times.append((k, time() - start))
    return lda_times

def part2(k):
    if path.isfile(path.join('lda', str(k) + '-auto.lda')):
        print 'Loading ' + str(k) + '-auto.lda'
        lda = models.ldamodel.LdaModel.load(path.join('lda', str(k) + '-auto.lda'))
    else:
        c, d, l = getCorpusDictionary('answers_all.txt')
        lda = LDA(c, d, k, 'auto')
    print lda
    topics = lda.show_topics(topics=k, topn=5, formatted=False)
    randomCorpus, randomDictionary, randomLines = getCorpusDictionary('answers_random.txt')
    colors = [ 'b', 'g', 'r', 'c', 'y' ]
    for i, (doc_bow, line) in enumerate(zip(randomCorpus, randomLines)):
        print i, doc_bow, line
        doc_lda = lda[doc_bow]
        pyplot.bar(*zip(*doc_lda), color = colors[i])
        # print doc_lda
        primary_topic = max(doc_lda, key=itemgetter(1))[0]
        # print primary_topic
        # print topics[primary_topic]
        print 'Doc', colors[i], 'Topic', primary_topic, '(' + ', '.join(t[1] for t in topics[primary_topic]) + '):', line
    pyplot.savefig(path.join('img', 'part-2-random-docs-topic-distribution-auto.png'))
    # TODO: what is the estimated value of alpha?
    pyplot.close()
    for i in range(3):
        r = randint(0, 99)
        pyplot.plot(lda.expElogbeta[r].T, color='b')
        pyplot.title('Betas for alpha=auto, topic=' + str(r))
        pyplot.savefig(path.join('img', 'part-2-beta-auto-' + str(r) + '.png'))
        pyplot.close()

    if path.isfile(path.join('lda', str(k) + '-' + str(50.0/k) + 'passes25.lda')):
        lda = models.ldamodel.LdaModel.load(path.join('lda', str(k) + '-' + str(50.0/k) + 'passes25.lda'))
    else:
        c, d, l = getCorpusDictionary('answers_all.txt')
        lda = LDA(c, d, k, 50.0/k)
    topics = lda.show_topics(topics=k, topn=5, formatted=False)
    for i, (doc_bow, line) in enumerate(zip(randomCorpus, randomLines)):
        # doc_bow = dictionary.doc2bow(doc.split())
        doc_lda = lda[doc_bow]
        pyplot.bar(*zip(*doc_lda), color = colors[i])
        primary_topic = max(doc_lda, key=itemgetter(1))[0]
        print 'Doc', colors[i], 'Topic', primary_topic, '(' + ', '.join(t[1] for t in topics[primary_topic]) + '):', line
    pyplot.savefig(path.join('img', 'part-2-random-docs-topic-distribution-manual.png'))
    for i in range(3):
        r = randint(0, 99)
        pyplot.plot(lda.expElogbeta[r].T, color='g')
        pyplot.title('Betas for alpha=50/k, topic=' + str(r))
        pyplot.savefig(path.join('img', 'part-2-beta-manual-' + str(r) + '.png'))
        pyplot.close()
    # pick 3 rows and print (each should be corpus-length)

def part3(k, alpha):
    corpus, dictionary, lines = getCorpusDictionary('answers_top.txt')
    mostCommonTopics = getTopTopics()
    print mostCommonTopics

    quoraToLdaTopics = [ [0]*k for i in range(5) ]

    if path.isfile(path.join('lda', str(k) + '-' + str(alpha) + 'passes25.lda')):
        lda = models.ldamodel.LdaModel.load(path.join('lda', str(k) + '-' + str(alpha) + 'passes25.lda'))
    else:
        c, d, lines = getCorpusDictionary('answers_all.txt')
        lda = LDA(c, d, k, alpha)
    lda_topics = lda.show_topics(topics=k, topn=10, formatted=False)

    with open('answers_top.txt') as file:
        for line in file:
            topic, answer = line.split(',')
            doc_bow = dictionary.doc2bow(answer.split())
            doc_lda = lda[doc_bow]
            primary_topic = max(doc_lda, key=itemgetter(1))[0] # get topic with max probability
            quoraToLdaTopics[mostCommonTopics.index(topic)][primary_topic] += 1
    with open('quora_topics_output.txt', 'w') as file:
        for i, topics in enumerate(quoraToLdaTopics):
            topTopicIndices = [ x[0] for x in sorted(enumerate(topics), key=lambda y:y[1], reverse=True) ]
            print mostCommonTopics[i].replace('"', '') + ':'
            file.write(mostCommonTopics[i].replace('"', '') + ':' + '\n')
            for j in range(5):
               print "top topic " + str(j+1) + " num docs: " + str(topics[topTopicIndices[j]])
               file.write("top topic " + str(j+1) + " num docs: " + str(topics[topTopicIndices[j]]) + '\n')
               lda_topics = lda.show_topics(topics=k, topn=10, formatted=False)
               print ' '.join(t[1] for t in lda_topics[topTopicIndices[j]])
               file.write(' '.join(t[1] for t in lda_topics[topTopicIndices[j]]) + '\n')
            print
            file.write('\n')

def part4(k, alpha):
    corpus, dictionary, lines = getCorpusDictionary('answers_all.txt')
    if path.isfile(path.join('lda', str(k) + '-' + str(alpha) + 'passes25.lda')):
        lda = models.ldamodel.LdaModel.load(path.join('lda', str(k) + '-' + str(alpha) + 'passes25.lda'))
    else:
        lda = LDA(corpus, dictionary, k, alpha)
    topics = [0]*k
    with open('answers_all.txt') as file:
        for line in file:
            doc_bow = dictionary.doc2bow(line.split())
            doc_lda = lda[doc_bow]
            primary_topic = max(doc_lda, key=itemgetter(1))[0] # get topic with max probability
            topics[primary_topic] += 1
    topics = [ float(t)/sum(topics) for t in topics ]
    pyplot.bar(*zip(*enumerate(topics)))
    pyplot.savefig(path.join('img', 'part-4-overall-prior-topic-distribution2.png'))

def part5(k, alpha):
    corpus, dictionary, lines = getCorpusDictionary('answers_all.txt')
    numRandDocsMax = 50
    numSuccessesNeeded = 5

    listRandDocs = ['']*numRandDocsMax
    with open('answers_random.txt', 'r') as infile:
        for i, line in enumerate(infile):
            #print str(i)+" "+ liockne
            listRandDocs[i] = line.strip('\n')
    for string in listRandDocs:
        print string
        print ""

    listOfProbsPerDoc =[[]]*numRandDocsMax

    numSuccessProcessed = 0

    if path.isfile(path.join('lda', str(k) + '-' + str(alpha) + 'passes25.lda')):
        print "loading lda"
        lda = models.ldamodel.LdaModel.load(path.join('lda', str(k) + '-' + str(alpha) + 'passes25.lda'))
    else:
        lda = LDA(corpus, dictionary, k, alpha)
    topicProbs = [0]*k
    print 'starting calculating topicProbs'
    with open('answers_all.txt') as file:
        for line in file:
            doc_bow = dictionary.doc2bow(line.split())
            doc_lda = lda[doc_bow]
            primary_topic = max(doc_lda, key=itemgetter(1))[0] # get topic with max probability
            topicProbs[primary_topic] += 1
    topicProbs = [ float(t)/sum(topicProbs) for t in topicProbs ]
    topics = lda.show_topics(topics=k, topn=len(dictionary), formatted=False)
    print "topic Probs finished finished"
    print topicProbs

    for currDocNum, document in enumerate(listRandDocs):
        if numSuccessProcessed >= numSuccessesNeeded:
            break;
        docProbPerTopic = [0]*k
        probEachTopic = [0]*k

        wordDistrs = {}
        for topicNum,topic in enumerate(topics):
            #load prob map of words in topic
            for t in topic:
                wordDistrs[t[1]] = t[0]

            #print wordDistrs
            docProb = 1
            for w in document.strip('\n').split(' '):
                probW = wordDistrs.get(w, -1)
                print "word prob: " + str(probW) + 'doc: '+str(currDocNum)+'topic: '+ str(topicNum)+'numprocessed: '+str(numSuccessProcessed)
                docProb *= probW
                print "docProb prob: " + str(docProb)+str(currDocNum)+str(currDocNum)+'topic: '+ str(topicNum)+'numprocessed: '+str(numSuccessProcessed)

            docProbPerTopic[topicNum] = docProb
            wordDistrs.clear()
            print "iterated"

        #probability of document is the sum of conditional prob of document for each topic
        docProb = 0
        for i in range(k):
            docProb += docProbPerTopic[i]*topicProbs[i]
        for i in range(k):
            probEachTopic[i] = topicProbs[i]* docProbPerTopic[i]/docProb
        #print probEachTopic
        print 'sum: ' + str(sum(probEachTopic))
        if(sum(probEachTopic) ==1):

            numSuccessProcessed += 1;
            print probEachTopic
            print str(currDocNum)
            print str(currDocNum)
            print str(currDocNum)

            print ""
            print ""
            print ""

        listOfProbsPerDoc[currDocNum]= probEachTopic

    colors = [ 'b', 'g', 'r', 'c', 'y','m', 'k' ]
    numSuccessGraphed = 0
    for i, listProbs in enumerate(listOfProbsPerDoc):
        if(numSuccessGraphed == numSuccessesNeeded):
            break;
        if sum(listProbs)== 1:
            print str(i) + ' ' + str(len(listProbs))
            pyplot.bar(range(k),listProbs, color = colors[numSuccessGraphed])
            numSuccessGraphed += 1
            print listProbs
        else:
            print ""
    pyplot.savefig('img\\part5.png')
    pyplot.close()

def main():
    parser = ArgumentParser()
    parser.add_argument('-g', '--generate-docs', action='store_true')
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-p', '--part', type=int)
    args = parser.parse_args()

    if args.test:
        c, d, l = getCorpusDictionary('test.txt')
        print c, d
        pass
    if args.generate_docs:
        archiveFile('answers_all.txt')
        createAllAnswersDoc()
        archiveFile('answers_random.txt')
        createRandomAnswersDoc()
        archiveFile('answers_top.txt')
        createTopAnswersDoc()
        return

    # TODO: BIG EFFING PROBLEM... USING THE WRONG DICTIONARY FOR PARTS 2, 3, AND 4
    k = 2
    if args.part == 1:
        lda_times = part1()
        print 'LDA:', lda_times
    elif args.part == 2:
        part2(k)
    elif args.part == 3:
        part3(k, 50.0/k)
    elif args.part == 4:
        part4(k, 50.0/k)
    elif args.part == 5:
        part5(k, 50.0/k )

if __name__ == "__main__":
    main()

