print("Loading Real time QA system...")
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
from nltk.corpus import wordnet
import spacy
from spacy import displacy
nlp = spacy.load('en_core_web_sm')
import pandas as pd
from spacy.matcher import Matcher 
from spacy.tokens import Span 
from tqdm import tqdm
import wikipedia
import wikipediaapi
import re
def get_entities(sent):
 
  ent1 = ""
  ent2 = ""

  prv_tok_dep = ""    
  prv_tok_text = ""   

  prefix = ""
  modifier = ""
  
  for tok in nlp(sent):
    if tok.dep_ != "punct":
      if tok.dep_ == "compound":
        prefix = tok.text
        if prv_tok_dep == "compound":
          prefix = prv_tok_text + " "+ tok.text
      
      if tok.dep_.endswith("mod") == True:
        modifier = tok.text
        if prv_tok_dep == "compound":
          modifier = prv_tok_text + " "+ tok.text
      
      if tok.dep_.find("subj") == True:
        ent1 = modifier +" "+ prefix + " "+ tok.text
        prefix = ""
        modifier = ""
        prv_tok_dep = ""
        prv_tok_text = ""      

      if tok.dep_.find("obj") == True:
        ent2 = modifier +" "+ prefix +" "+ tok.text
        
      prv_tok_dep = tok.dep_
      prv_tok_text = tok.text
 

  return [ent1.strip(), ent2.strip()]
def get_relation(sent):

  doc = nlp(sent)

  # Matcher class object 
  matcher = Matcher(nlp.vocab)

  #define the pattern 
  pattern = [{'DEP':'ROOT'}, 
            {'DEP':'prep','OP':"?"},
            {'DEP':'agent','OP':"?"},  
            {'POS':'ADJ','OP':"?"},] 

  matcher.add("matching_1", None, pattern) 

  matches = matcher(doc)
  k = len(matches) - 1
  if(k>0):
    span = doc[matches[k][1]:matches[k][2]] 
    return(span.text)
print("Enter your question.")
sent=input()
verb=get_relation(sent)
actors=get_entities(sent)
whwords = ['what', 'which', 'how', 'why', 'when', 'where', 'who']
concept=""
if(actors[0] in whwords):
    concept=actors[1]
else:
    concept=actors[0]
search_results=wikipedia.search(concept, results=3)
wiki_wiki = wikipediaapi.Wikipedia(language='en',extract_format=wikipediaapi.ExtractFormat.WIKI)
p_wiki = wiki_wiki.page(search_results[0])
text_data=p_wiki.text
li=text_data.split(".")
sentences = []
for i in li:
    l = i.split('.')
    for j in l:
        sentences.append(j)
filtered_sentences=[]
for sentence in sentences:
    count = 0
    for words in sentence:
        if(words==" "):
            count = count+1
    if(count>=3):
        filtered_sentences.append(sentence)
sentences=filtered_sentences
for val in range(len(sentences)):
    sentences[val]=re.sub("\[(.*?)\]","",sentences[val])
df=pd.DataFrame(sentences)
df['sentence']=df[0]
df=df.drop([0],axis=1)
candidate_sentences=df
entity_pairs = []
for i in tqdm(candidate_sentences["sentence"]):
  entity_pairs.append(get_entities(i))
relations = [get_relation(i) for i in tqdm(candidate_sentences['sentence'])]
pd.Series(relations).value_counts()[:50]
# extract subject
source = [i[0] for i in entity_pairs]

# extract object
target = [i[1] for i in entity_pairs]

kg_df = pd.DataFrame({'source':source, 'target':target, 'edge':relations})
tokens=nltk.pos_tag(verb.split(" "))
nominees=[]
for i in tokens:
    if(i[1]!='IN'):
        nominees.append(i[0])
checks=set()
for i in nominees:    
    syns = wordnet.synsets(i)
    for j in syns:
        checks.add(j.lemmas()[0].name())
checks=list(checks)
suspect_relations=set()
for j in checks:
    for i in kg_df['edge']:
        if(i and j in i):
            suspect_relations.add(i)
for i in suspect_relations:
    print(kg_df[kg_df['edge']==i])