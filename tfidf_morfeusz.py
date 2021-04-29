from multiprocessing import Pool, cpu_count
import morfeusz2
import nltk

class MorfeuszAnalyser():
    morf = morfeusz2.Morfeusz(generate=False)
    tokenizer = nltk.data.load('tokenizers/punkt/polish.pickle')
    
    def __init__(self, ngram_range = (1,3), split_to_sentences=True, use_multiprocessing=True):
        self.ngram_range = ngram_range
        self.split_to_sentences = split_to_sentences
        self.use_multiprocessing = use_multiprocessing

        with open('polish_stopwords.txt') as f:
            self.stop_words = [x.strip() for x in f]
            
        self.ignore_tags = ['interp','interj','part','conj','comp','pred']

    def _ngrams(self, tokens):
        min_n, max_n = self.ngram_range
        ngrams = []
        n_tokens = len(tokens)

        ngrams_append = ngrams.append
        space_join = " ".join

        for n in range(min_n, max_n + 1):
            for i in range(n_tokens - n + 1):
                ngrams_append(space_join(tokens[i: i + n]))

        return ngrams

    def _analyse(self, text):
        analysis = [x for x in self.morf.analyse(text) if x[2][1].split(':')[0] not in self.stop_words and x[2][2] not in self.ignore_tags]
        org_tokens = []
        lem_tokens = []
        curr_index = -1

        for word_index, _, tup in analysis:
            if curr_index == word_index:
                continue
            
            curr_index = word_index
            org_tokens.append(tup[0])
            lem_tokens.append(tup[1].split(':')[0])

        return lem_tokens + self._ngrams(org_tokens)

    def __call__(self, text):
        if self.split_to_sentences:
            sentences = self.tokenizer.tokenize(text)
            if self.use_multiprocessing:
                with Pool(cpu_count() - 1) as p:
                    sentence_tokens = p.map(self._analyse, sentences)
            else:
                sentence_tokens = [self._analyse(sentence) for sentence in sentences]

            return [token for tokens in sentence_tokens for token in tokens]
        else:
            return self._analyse(text)
