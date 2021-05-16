from morfeusz_spacy_analyser import SpacyMorfeuszAnalyser
import pandas as pd
import pickle
from tqdm import tqdm

model_path = '/data/model/iii/'
doc_file = model_path + 'iii.csv'
parsed_docs_file = model_path + 'iii-spacy-docs'

total = 291415

def generate(kad):
    df_reader = pd.read_csv(doc_file, usecols=['text', 'kad'], chunksize=10000)
    docs = [x.text for df in df_reader for _, x in df.iterrows() if x.kad == kad]

    analyser = SpacyMorfeuszAnalyser()

    analyse_gen = (analyser(doc) for doc in tqdm(docs))

    with open(f'{parsed_docs_file}-{kad}.pkl', 'wb') as f:
        for doc in analyse_gen:
            pickle.dump(doc, f)

kad = input('Kadencja: ')
generate(int(kad))
