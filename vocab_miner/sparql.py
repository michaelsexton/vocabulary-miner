import requests
import string
from nltk import word_tokenize
from nltk.corpus import stopwords
import json
from json import JSONDecodeError

from nltk.tokenize import WordPunctTokenizer


LOGICAL_JOIN = {"and" : " && ", "or" : " || "}

EXACT_URI = "http://vocabs.ga.gov.au/cgi/sissvoc/commodity-code/concept.json?anylabel={0}"
def generate_query(terms=None, join = "and", query_by = "definition"):
  QUERY_TYPE = {"definition" : "?d", "preflabel" : "?p", "altlabel" : "?a" }
  
  qt = QUERY_TYPE[query_by]
  
  join = LOGICAL_JOIN[join]
  raw_query_string = '''PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    CONSTRUCT {{ ?u skos:prefLabel ?p .
            ?u skos:altLabel ?a .
            ?u skos:definition ?d}}
    WHERE
      {{ ?u skos:prefLabel ?p .
      optional {{ ?u skos:altLabel ?a }} .
        ?u  skos:definition ?d
        {0}
      }}
    '''
  if terms:
    contains = ['contains(lcase({0}), "{1}")'.format(qt,term) for term in terms]
    definition_filter = "FILTER({0})".format(join.join(contains))
    return raw_query_string.format(definition_filter)
  else:
    return raw_query_string.format("")

def query_by_definition(terms = None, join = "and"):

  
  query_string = generate_query(terms, join)

  headers = {"Accept" : "application/rdf+json"}
  params = {
    'query': query_string,
  }
  r = requests.get('http://vocabs.ands.org.au/repository/api/sparql/ga_commodity-code_v0-2', params=params, headers=headers)

  obj = json.loads(r.text)
  return obj
  
  #if len(obj.keys()) == 1:
  #    uri = list(obj.keys())[0]
  #    preflabel = obj[uri][PREFLABEL][0]['value']
  #    return uri, preflabel
  #return None, None

def stop_words():
  return stopwords.words('english') + list(string.punctuation)


def tokenize(name):
  wp = WordPunctTokenizer()

  name = name.lower()

  tokens = wp.tokenize(name)
  tokens = [t for t in tokens if t not in set(stop_words())]
  return tokens

def list_vocab_definitions():
  vocabs = query_by_definition()
  skos = [vocabs[vocab] for vocab in  vocabs]
  definitions = [definition["http://www.w3.org/2004/02/skos/core#definition"] for definition in skos]
  def_texts = [lang["value"] for definition in definitions for lang in definition if lang["lang"] == 'en']
  return def_texts

def get_by_definition(name = None):
  terms = None
  if name is not None:
    terms = tokenize(name)
  
  obj = query_by_definition(terms,"and")
  defs = uri_defs(obj)
  if len(defs) == 1:
    uri = list(defs.keys())[0]
    preflabel = preflabel_from_uri(uri)
    return uri, preflabel, None
  else:
    uris = list(defs.keys())
    return None, None, uris
  
def uri_defs(obj):
  return {key:lang["value"] for key, skos in obj.items() for key1, definition in skos.items()  if key1 == 'http://www.w3.org/2004/02/skos/core#definition' for lang in definition if lang["lang"] == "en"}

def preflabel_from_uri(uri):
  url = uri + '.json'
  obj =  json.loads(requests.get(url).text)
  try:
    preflabel = obj["result"]["primaryTopic"]["prefLabel"]["_value"]
    return preflabel
  except (JSONDecodeError):
    return None

def get_exact(name):
    name = name.lower()
    url = EXACT_URI.format(name)
    try: 
        obj =  json.loads(requests.get(url).text)

        items = obj["result"]["items"]
        if len(items) == 1:
            uri = obj["result"]["items"][0]["_about"]
            preflabel = obj["result"]["items"][0]["prefLabel"]["_value"]
            return uri, preflabel, None
        else:
            return None, None, None
    except (JSONDecodeError):
        return None, None, None
        
FUNCTION_SET = [get_exact, get_by_definition]


def process_labels(name):
  for fs in FUNCTION_SET:
    uri, preflabel, alts = fs(name)
    if uri is not None and preflabel is not None:
      print(name, uri, preflabel, alts)
      if alts is list:
        alts = ','.join(alts)
      return uri, preflabel, alts
  print(name, "No URI", alts)
  
## VOCAB PART BELOW

# vocabulary = set()
#
# for definition in vocabs:
#     words = sparql.tokenize(definition)
#     vocabulary.update(words)
# tfidf = TfidfVectorizer(stop_words=sparql.stop_words(), tokenizer=sparql.tokenize, vocabulary=vocabulary)
# tfidf.fit([definition for definitions in vocabs])
# transformed = {key:tfidf.transform([value]) for key, value in dict_defs.items()}
# transformed.keys()
# transformed["http://resource.geosciml.org/classifier/cgi/commodity-code/aggregate"][0,tfidf.vocabulary_["aggregates"]]
# dict_defs["http://resource.geosciml.org/classifier/cgi/commodity-code/pyrite"]
# EXACT_URI = "http://vocabs.ga.gov.au/cgi/sissvoc/commodity-code/concept.json?anylabel={0}"
# PREFLABEL = "http://www.w3.org/2004/02/skos/core#prefLabel"
# commodities = pd.read_excel('GS_MINEDEX_dbo_COMMODITIES.xlsx')
