import umap
from embeddings_util import load_embeddings,save_file,filename, LEXRANK_TOP1,LEXRANK_TOP3,LEXRANK_WEIGHTED, TFIDF_MORF

print('loading embeddings..')

embeddings = load_embeddings(TFIDF_MORF)

print('embeddings shape', embeddings.shape)

for dim in [3, 2]:
    print('reducing to dim', dim)
    embeddings_map = umap.UMAP(n_neighbors=15,
                        n_components=dim,
                        min_dist=0.0,
                        metric='hellinger').fit(embeddings)

    for combine in [LEXRANK_TOP1, LEXRANK_TOP3, LEXRANK_WEIGHTED]:
        print('combining with', combine)
        map_combined = embeddings_map * load_embeddings(combine, dim, map=True)
        save_file(map_combined.embedding_, filename(combine + '-xtfidf', dim))