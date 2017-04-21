import codecs
file = "F:/University/EE239AS TA - Big Data/project 2/codes/answers_text.txt"

answer_count = 1
with codecs.open(file, encoding='utf8') as f:
    for line in f:
        if line[0:8] == "Answer: ":
            fw = codecs.open("docs/answer" + str(answer_count) + ".txt", mode='w' , encoding='utf8')
            fw.write(line[8:])
            answer_count += 1
            fw.close()


