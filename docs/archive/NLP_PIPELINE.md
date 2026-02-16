# NLP Pipeline - Advanced Linguistic Analysis Module

## Overview

The **NLPPipeline** module provides comprehensive natural language processing capabilities for the SimpleMem toolkit. It integrates NLTK with semantic analysis to deliver deep linguistic understanding for all layers of the system.

### Key Capabilities

- **Multi-level Tokenization**: Word and sentence tokenization with semantic awareness
- **Part-of-Speech (POS) Tagging**: Detailed grammatical role identification
- **Named Entity Recognition (NER)**: Automatic extraction of persons, organizations, locations, and more
- **Phrase Chunking**: Identification of noun phrases, verb phrases, and prepositional phrases
- **Lemmatization & Stemming**: Word normalization to canonical forms
- **Semantic Integration**: Connects to WordNet and SemanticGraph for conceptual analysis
- **Complexity Metrics**: Linguistic feature extraction for text analysis
- **Key Term Extraction**: Automatic identification of domain-relevant terms

## Architecture

```
NLPPipeline (Main Interface)
    ├── NLTK Components
    │   ├── Tokenizers (sent_tokenize, word_tokenize)
    │   ├── POS Tagger (pos_tag)
    │   ├── NER (ne_chunk)
    │   └── Chunk Parser (RegexpParser)
    │
    ├── Integration Layer
    │   ├── DataManager (corpus access)
    │   └── SemanticGraph (semantic analysis)
    │
    └── Analysis Output
        ├── Token (individual words + features)
        ├── Phrase (multi-word chunks)
        ├── NamedEntity (recognized entities)
        └── NLPAnalysis (complete analysis)
```

## Data Structures

### Token
```python
@dataclass
class Token:
    text: str                  # Original word
    pos: str                   # Part-of-speech tag (NN, VB, JJ, etc)
    lemma: str                 # Lemmatized form
    stem: str                  # Stemmed form
    is_stopword: bool          # Common word flag
    entity_type: Optional[str] # NER label
    semantic_type: Optional[str] # From semantic graph
```

### NLPAnalysis
Complete analysis result with:
- `sentences`: List of sentences
- `tokens`: Token-level analysis
- `pos_tags`: Part-of-speech tags
- `lemmas`: Lemmatization mapping
- `stems`: Stemming mapping
- `entities`: Named entities
- `phrases`: Identified phrases
- `stopwords`: Common words
- `vocabulary`: Unique terms
- `key_terms` property: Non-stopword nouns/verbs

## Usage Examples

### Basic Analysis
```python
from src import NLPPipeline

nlp = NLPPipeline()

# Analyze text
analysis = nlp.analyze("Apple CEO Tim Cook announced new AI features in San Francisco.")

# Access results
print(analysis.pos_tags)
# [('Apple', 'NNP'), ('CEO', 'NNP'), ('Tim', 'NNP'), ('Cook', 'NNP'), ...]

print(analysis.entities)
# [NamedEntity(text='Apple', entity_type='ORG'),
#  NamedEntity(text='Tim Cook', entity_type='PERSON'),
#  NamedEntity(text='San Francisco', entity_type='LOC')]

print(analysis.key_terms)
# ['Apple', 'CEO', 'Tim', 'Cook', 'features']
```

### Entity Extraction
```python
# Get entities by type
entities_by_type = nlp.extract_entities_by_type(text)
print(entities_by_type)
# {
#     'ORG': ['Apple'],
#     'PERSON': ['Tim Cook'],
#     'LOC': ['San Francisco'],
#     'DATE': []
# }
```

### Key Term Analysis
```python
# Extract key terms with frequency
key_terms = nlp.extract_key_terms(text, min_freq=1)
print(key_terms)
# [('features', 2), ('announced', 1), ('apple', 1)]
```

### Lemmatization
```python
# Lemmatize text
lemmatized = nlp.lemmatize_text("The companies are announcing features")
print(lemmatized)
# "the company be announce feature"
```

### Complexity Analysis
```python
# Get linguistic metrics
metrics = nlp.get_linguistic_complexity(text)
print(metrics)
# {
#     'stopword_ratio': 0.25,
#     'vocabulary_richness': 0.85,
#     'avg_sentence_length': 12.5,
#     'entity_density': 0.5,
#     'total_tokens': 50,
#     'unique_terms': 42,
#     'entity_count': 5,
#     'phrase_count': 8
# }
```

## Integration Points

### With SemanticGraph
NLPPipeline enriches token analysis with semantic information:

```python
# Each token gets semantic type from WordNet
token.semantic_type  # "known_concept" if in WordNet
```

### With DataManager
Uses DataManager for NLTK resource management:

```python
# Automatic corpus loading and stopword access
nlp.data_manager.ensure_required_data()
nlp.data_manager.get_stopwords()
```

### With Scribe Engine
Provides deep linguistic features for authorship analysis:

```python
from src import ScribeEngine, NLPPipeline

scribe = ScribeEngine()
nlp = NLPPipeline()

# Scribe can use NLP analysis for fingerprinting
analysis = nlp.analyze(text)
fingerprint = scribe.analyze_authorship(text)
```

### With Scout
Enhances gap detection with entity and key term analysis:

```python
from src import Scout, NLPPipeline

scout = Scout()
nlp = NLPPipeline()

# Extract entities and terms for gap detection
entities = nlp.extract_entities_by_type(query)
scout.find_gaps(query, entities)
```

## POS Tag Reference

Common NLTK tags:

| Tag | Meaning | Examples |
|-----|---------|----------|
| NN | Noun, singular | dog, house |
| NNS | Noun, plural | dogs, houses |
| NNP | Proper noun, singular | Apple, John |
| NNPS | Proper noun, plural | Americans, Lincolns |
| VB | Verb, base form | run, eat |
| VBD | Verb, past tense | ran, ate |
| VBG | Verb, gerund | running, eating |
| JJ | Adjective | good, large |
| RB | Adverb | quickly, well |
| IN | Preposition | in, on, at |
| DT | Determiner | the, a, an |

## NER Tag Reference

Common entity types:

| Tag | Type | Examples |
|-----|------|----------|
| PERSON | People | John Smith, Bill Gates |
| ORG | Organizations | Apple, Microsoft |
| GPE | Locations | San Francisco, USA |
| MONEY | Money amounts | $100, £50 |
| DATE | Dates | January 15, 2024 |
| TIME | Times | 3:00 PM |
| FACILITY | Buildings | Empire State Building |

## Configuration

Configure NLP pipeline via `config/config.yaml`:

```yaml
nlp:
  # POS tagger model
  tagger: "perceptron"
  
  # NER model (binary or more-granular)
  ner_model: "default"
  
  # Include semantic analysis
  use_semantic: true
  
  # Chunk parsing
  enable_chunking: true
```

## Performance Considerations

- **Lazy Loading**: NLTK data is loaded on first use
- **Caching**: Frequent operations are cached in DataManager
- **Parallel Processing**: Large texts can be split by sentence
- **Memory**: Each Token object holds multiple representations

### For Large Documents

```python
# Process by sentence instead of full text
sentences = nlp.data_manager.sentence_tokenize(large_text)
for sentence in sentences:
    analysis = nlp.analyze(sentence)
    # Process incrementally
```

## Error Handling

NLPPipeline handles missing NLTK data gracefully:

```python
# Pipeline checks availability on init
if not nlp.is_available():
    print("NLTK not properly configured")
    # Fall back to basic tokenization
```

## Dependencies

- **NLTK** (3.8+): Core NLP functionality
- **wordnet**: For semantic enrichment
- **DataManager**: Corpus and stopword management
- **SemanticGraph**: WordNet semantic analysis

## Related Modules

- [WordNet Integration](WORDNET_INTEGRATION.md) - Semantic relationship analysis
- [Data Manager](DATA_MANAGER.md) - Corpus and resource management
- [Scout Integration](SCOUT_INTEGRATION.md) - Gap detection with NLP
- [Scribe Engine](SCRIBE_ARCHITECTURE.md) - Authorship analysis with linguistic features

## API Reference

### Main Methods

#### `analyze(text: str) -> Optional[NLPAnalysis]`
Perform complete NLP analysis on text.

#### `extract_key_terms(text: str, min_freq: int = 1) -> List[Tuple[str, int]]`
Extract terms by frequency.

#### `extract_entities_by_type(text: str) -> Dict[str, List[str]]`
Get entities organized by type.

#### `lemmatize_text(text: str) -> str`
Return fully lemmatized text.

#### `get_linguistic_complexity(text: str) -> Dict[str, float]`
Calculate complexity metrics.

#### `is_available() -> bool`
Check if pipeline is ready to use.

## Future Enhancements

- **Dependency Parsing**: Full dependency tree extraction
- **Coreference Resolution**: Linking pronouns to entities
- **SRL**: Semantic Role Labeling for event extraction
- **Multilingual**: Support for languages beyond English
- **Custom Models**: Integration of spaCy for production NER

## See Also

- [Complete SimpleMem Reference](COMPLETE_SUMMARY.md)
- [Quick Start Guide](QUICK_START.md)
- [Architecture Overview](ARCHITECTURE_LAYER0_HARVESTER.md)
