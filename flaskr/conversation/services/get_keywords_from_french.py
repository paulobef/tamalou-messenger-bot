"""
Author: Romain Benassi
Date: 29/05/2020
"""
from googletrans import Translator
from collections import OrderedDict
import numpy as np
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from spellchecker import SpellChecker
from collections import OrderedDict

# définition des fonctions auxiliaires qui interviennent dans la fonction principale
nlp = spacy.load('en_core_web_sm')


class TextRank4Keyword():
    """Extract keywords from text"""

    def __init__(self):
        self.d = 0.85  # damping coefficient, usually is .85
        self.min_diff = 1e-5  # convergence threshold
        self.steps = 10  # iteration steps
        self.node_weight = None  # save keywords and its weight

    def set_stopwords(self, stopwords):
        """Set stop words"""
        for word in STOP_WORDS.union(set(stopwords)):
            lexeme = nlp.vocab[word]
            lexeme.is_stop = True

    def sentence_segment(self, doc, candidate_pos, lower):
        """Store those words only in cadidate_pos"""
        sentences = []
        for sent in doc.sents:
            selected_words = []
            for token in sent:
                # Store words only with cadidate POS tag
                if token.pos_ in candidate_pos and token.is_stop is False:
                    if lower is True:
                        selected_words.append(token.text.lower())
                    else:
                        selected_words.append(token.text)
            sentences.append(selected_words)
        return sentences

    def get_vocab(self, sentences):
        """Get all tokens"""
        vocab = OrderedDict()
        i = 0
        for sentence in sentences:
            for word in sentence:
                if word not in vocab:
                    vocab[word] = i
                    i += 1
        return vocab

    def get_token_pairs(self, window_size, sentences):
        """Build token_pairs from windows in sentences"""
        token_pairs = list()
        for sentence in sentences:
            for i, word in enumerate(sentence):
                for j in range(i + 1, i + window_size):
                    if j >= len(sentence):
                        break
                    pair = (word, sentence[j])
                    if pair not in token_pairs:
                        token_pairs.append(pair)
        return token_pairs

    def symmetrize(self, a):
        return a + a.T - np.diag(a.diagonal())

    def get_matrix(self, vocab, token_pairs):
        """Get normalized matrix"""
        # Build matrix
        vocab_size = len(vocab)
        g = np.zeros((vocab_size, vocab_size), dtype='float')
        for word1, word2 in token_pairs:
            i, j = vocab[word1], vocab[word2]
            g[i][j] = 1

        # Get Symmeric matrix
        g = self.symmetrize(g)

        # Normalize matrix by column
        norm = np.sum(g, axis=0)
        g_norm = np.divide(g, norm, where=norm != 0)  # this is ignore the 0 element in norm

        return g_norm

    def get_keywords(self, number=10):
        """Print top number keywords"""
        node_weight = OrderedDict(sorted(self.node_weight.items(), key=lambda t: t[1], reverse=True))
        for i, (key, value) in enumerate(node_weight.items()):
            print(key + ' - ' + str(value))
            if i > number:
                break

    # ---- fonction ajoutée par moi (Romain) pour recuperer les keywords sous forme de liste
    def get_keywords_list(self, number=10):
        list_out = list()
        """get top number keywords"""
        node_weight = OrderedDict(sorted(self.node_weight.items(), key=lambda t: t[1], reverse=True))
        for i, (key, value) in enumerate(node_weight.items()):
            # print(key + ' - ' + str(value))
            list_out.append(key)
            if i > number:
                break
        return (list_out)

    # --------

    def analyze(self, text,
                candidate_pos=['NOUN', 'PROPN'],
                window_size=4, lower=False, stopwords=list()):
        """Main function to analyze text"""

        # Set stop words
        self.set_stopwords(stopwords)

        # Pare text by spaCy
        doc = nlp(text)

        # Filter sentences
        sentences = self.sentence_segment(doc, candidate_pos, lower)  # list of list of words

        # Build vocabulary
        vocab = self.get_vocab(sentences)

        # Get token_pairs from windows
        token_pairs = self.get_token_pairs(window_size, sentences)

        # Get normalized matrix
        g = self.get_matrix(vocab, token_pairs)

        # Initionlization for weight(pagerank value)
        pr = np.array([1] * len(vocab))

        # Iteration
        previous_pr = 0
        for epoch in range(self.steps):
            pr = (1 - self.d) + self.d * np.dot(g, pr)
            if abs(previous_pr - sum(pr)) < self.min_diff:
                break
            else:
                previous_pr = sum(pr)

        # Get weight for each node
        node_weight = dict()
        for word, index in vocab.items():
            node_weight[word] = pr[index]

        self.node_weight = node_weight


# on définit des variables à vocation globales qui sont utilisées dans la fonction principale
translator = Translator()
tr4w = TextRank4Keyword()
spell = SpellChecker(language='fr')  # french dictionary
spell_en = SpellChecker(language='en')  # english dictionary


# fonction permettant de récupérer les mots clés pour un texte donné
# input : 
# - text : la chaîne de caractères correspondant au texte à analyser
# output :
# - la liste des mots-clés classés dans l'ordre du plus significatif au moins significatif
def get_keywords_from_french(text):
    # on traduit le texte en anglais afin d'utiliser la procédure d'extration des mots clés
    text_english = translator.translate(text, src="fr", dest="en").text
    # on extrait les mots clés (en anglais)
    tr4w.analyze(text_english, candidate_pos=['NOUN', 'PROPN'], window_size=4, lower=False)
    # on récupère les mots clés anglais
    keyw_en = tr4w.get_keywords_list()
    # ------ on filtre les mots qui ne sont pas reconnus dans un dictionnaire
    # Attention: deux possibilité  => soit on filtre les mots clés anglais avec un dictionnaire anglais
    # => soit on filtre les mots clés après traduction avec un dictionnaire français
    # Le dictionnaire anglais me semblant plus robuste j'ai choisi la première solution (en partant du principe que si le mot
    # anglais existe alors une traduction française existera aussi). Néanmoins la deuxième possibilité est aussi présente
    # plus bas dans le code dans un ligne commentée
    keyw_en = [keyw for keyw in keyw_en if keyw not in spell_en.unknown(keyw_en)]
    # -----
    # on les traduits en français
    # on initialise la liste qui va les contenir
    keyw_fr = list()
    # on traduits les mots clés en une commande (mais une traduction indépendante est faite pour chaque car on donne une liste en entrée)
    keyw_fr_aux = translator.translate(keyw_en, src="en", dest="fr")
    # on remplit la liste des mots clés français avec la traduction
    for key_fr in keyw_fr_aux:
        keyw_fr.append(key_fr.text)

    # on filtre les mots dont l'orthographe n'est pas reconnue => ligne commentée car le filtrage est effecuté directement
    # sur les mots clés anglais (voir plus haut).
    # keyw_fr = [keyw for keyw in keyw_fr if keyw not in spell.unknown(keyw_fr)]

    # on effectue quelques opérations de nettoyage (on enleve les doublons et les smiley qui apparaissent dans le corpus tamalou sous la forme "SMILEY_xxxx")
    keyw_fr = [key for key in keyw_fr if "SMILEY" not in key]
    # on enleve les doublons éventuels (provoqués possiblement par la traduction, tout en conservant l'ordre)
    keyw_fr = list(OrderedDict.fromkeys(keyw_fr))

    return keyw_fr


"""
# TODO: Write this as a test
# Exemple d'utilisation sur un texte issu du corpus Tamalou
text_in = "Bonjour, Pour ma part j'utilise de l'anti cernes uniquement en cas d'imperfections sut le visage. J'ai pourtant des cernes très marquées, avec en plus une peau très fine et des veines assez visibles. J'ai pourtant arrêté de les camoufler. Je trouve que finalement, elles donnent plus de caractère à mon visage. C'est peut être bizarre mais j'aime bien avoir des cernes. Bonne journée! "
get_keywords_from_french(text_in)

['visage',
 'anticernes',
 'Cas',
 'imperfections',
 'cercles',
 'peau',
 'veines',
 'personnage',
 'camouflage',
 'journée']

"""
