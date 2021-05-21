from data import model_path, load_embeddings
import pandas as pd
import numpy as np
from tqdm import tqdm
from glob import glob
from scoring import score_consistency, score_coherence
from os import environ, path
import logging
logging.basicConfig(level = logging.INFO)

environ['TOKENIZERS_PARALLELISM']="true"

df = pd.read_csv(model_path + '/iii.csv', usecols=['id', 'date', 'text'])
docs = df.text.to_list()

output_file='scores.csv'

if path.exists(output_file):
    with open(output_file, 'r') as f:
        scored = [tuple(line.split(',')[:4]) for line in f]
    completed = [x[0] for x in scored if x[1:] == ('20','100','100')]
else:
    scored, completed = [], []
    with open(output_file, 'w') as f:
        f.write('embedding,n_neighbors,min_cluster_size,min_samples,topics_num,not_found,support,c_v,u_mass,c_su,c_cu\n')

with open(output_file, 'a+') as file_out:
    for emb_file in tqdm(sorted(glob(model_path + 'embeddings/*.pkl')), position=0):
        emb = emb_file.split('/')[-1][:-4]
        if emb in completed:
            continue

        for n_neighbors in [5, 10, 15, 20]:
            if (emb, str(n_neighbors), 'None', 'None') in scored:
                continue

            embeddings = load_embeddings(emb, dim=5, n_neighbors=n_neighbors)
            if embeddings is None:
                logging.warning(f'SEGFAULT during UMAP for {emb} ({n_neighbors}) ;c')
                file_out.write(f'{emb},{n_neighbors}' + ',None'*9 + '\n')
                continue
        
            for min_cluster_size, min_samples in tqdm([(10, 10), (20, 10), (20, 20), (50,10), (50, 25), (50, 50), (100, 1), (100, 10), (100, 50), (100, 100)], position=1, leave=False):
                current = (emb, str(n_neighbors), str(min_cluster_size), str(min_samples))
                if current in scored:
                    continue

                logging.info('scoring.. ' + ','.join(current))
                score_c_v, score_u_mass, topics, not_found, support = score_coherence(docs, embeddings, min_cluster_size, min_samples)

                file_out.write(','.join(current) + f',{len(np.unique(topics))},{not_found},{support},{score_c_v},{score_u_mass}')

                score_c_su = score_consistency(df, topics, mode='skip_unknown')
                score_c_cu = score_consistency(df, topics, mode='count_unknown')
                file_out.write(f',{score_c_su},{score_c_cu}\n')
                file_out.flush()

