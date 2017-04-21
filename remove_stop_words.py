import os
import codecs


filecount = 0
for file in os.listdir("docs_portion/"):
    if file.endswith(".txt"):
        with codecs.open("docs_portion/" + file, encoding = 'utf8') as f:
            line = f.readline()
            line = line.replace("the", "")
            line = line.replace("The", "")
            fw = codecs.open("docs_portion_2/" + file.strip('.txt') + "_2.txt" , mode='w' , encoding='utf8')
            fw.writelines(line)
            filecount += 1
            fw.close()
#            for line in f:
#                fw.write(line)



