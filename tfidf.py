from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import numpy as np
import pickle
import morfeusz2
from multiprocessing import Pool
from tqdm import tqdm

morf = morfeusz2.Morfeusz(generate=False)

model_path = '/data/model/'
doc_file = model_path + 'iii.csv'

total = 291415

df_reader = pd.read_csv(doc_file, usecols=['text'], chunksize=10000)
docs_gen = [x for df in df_reader for x in df.text][:1000]

with open('polish_stopwords.txt') as f:
    stop_words = [x.strip() for x in f]

def ngrams(tokens):
    min_n, max_n = 2, 3
    ngrams = []
    n_tokens = len(tokens)

    ngrams_append = ngrams.append
    space_join = " ".join

    for n in range(min_n, max_n + 1):
        for i in range(n_tokens - n + 1):
            ngrams_append(space_join(tokens[i: i + n]))

    return ngrams

def analyse(text):
    ignore_tags = ['interp','interj','part','conj','comp','pred']
    analysis = [x for x in morf.analyse(text) if x[2][1].split(':')[0] not in stop_words and x[2][2] not in ignore_tags]
    org_tokens = []
    lem_tokens = []
    curr_index = -1

    for word_index, _, tup in analysis:
        if curr_index == word_index:
            continue
        
        curr_index = word_index
        org_tokens.append(tup[0])
        lem_tokens.append(tup[1].split(':')[0])

    return lem_tokens + ngrams(org_tokens)

print("generating lemmatized ngrams..")
with Pool(8) as p:
    docs = list(tqdm(p.imap(analyse, docs_gen), total=total))

print('analysed docs', len(docs))
with open(model_path + 'tfidf-morf-tokens.pkl', "wb") as fOut:
    pickle.dump(docs, fOut)

print("calculating tf-idf..")
tfidf_vectorizer = TfidfVectorizer(analyzer=lambda x: x, min_df=5)
embeddings_tfidf = tfidf_vectorizer.fit_transform(tqdm(docs, total=total))

print("Saving embeddings..")

with open(model_path + 'embeddings-tfidf-morf.pkl', "wb") as fOut:
    pickle.dump(embeddings_tfidf, fOut)

print("done")

feature_names = np.array(tfidf_vectorizer.get_feature_names())

def get_top_tf_idf_words(response, top_n=5):
    sorted_emb = np.argsort(response.data)[:-(top_n+1):-1]
    return feature_names[response.indices[sorted_emb]]

tfidf_words = [get_top_tf_idf_words(x) for x in embeddings_tfidf]

print("Saving words..")
with open(model_path + 'tfidf-morf-top-words.pkl', "wb") as fOut:
    pickle.dump(tfidf_words, fOut)
