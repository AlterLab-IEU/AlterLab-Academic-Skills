---
name: alterlab-digital-humanities
description: "Text mining, corpus linguistics, digital archives, GIS for history, network analysis, stylometry, OCR, and data visualization for humanities research. Part of the AlterLab Academic Skills suite."
license: MIT
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-03-18"
---

# Digital Humanities Methods and Tools

## Overview

Digital humanities (DH) applies computational methods to the study of human culture, history, language, and society. It is not the replacement of humanistic inquiry with algorithms but the augmentation of interpretive scholarship with tools that can reveal patterns invisible to unaided reading, connect dispersed archives, visualize historical processes, and make cultural heritage accessible to broader audiences.

This skill covers the major computational methods used in humanities research: text mining and natural language processing (topic modeling with LDA and BERTopic, sentiment analysis, named entity recognition), corpus linguistics (concordance, collocation, frequency analysis, keyness), digital archiving and metadata standards (Dublin Core, TEI XML), geographic information systems (GIS) for historical research, network analysis of historical figures and literary characters, stylometry and computational authorship attribution, optical character recognition (OCR) workflows for digitizing historical texts, digital scholarly editions, data visualization for humanities data, distant reading as theorized by Franco Moretti, cultural analytics as developed by Lev Manovich, and the Python ecosystem for humanities computing (spaCy, NLTK, Voyant Tools, AntConc).

The skill is designed for humanities scholars who want to integrate computational methods into their research -- whether they are analyzing Victorian novels, mapping colonial trade networks, studying the evolution of political rhetoric, or building digital archives of endangered languages. No prior programming experience is assumed, though some methods require basic Python or R skills. For each method, the skill describes the intellectual rationale, practical implementation, available tools (from no-code to full programming), and critical perspectives on the method's limitations.

## When to Use This Skill

Use this skill when you need to:

- Apply topic modeling (LDA, BERTopic) to a large text corpus to discover thematic patterns
- Perform sentiment analysis on historical texts, literary works, or political discourse
- Extract named entities (people, places, organizations, dates) from unstructured text
- Conduct corpus linguistics analysis: concordance, collocation, frequency, keyness
- Create or work with digital archives using Dublin Core or TEI XML metadata standards
- Use GIS to map historical events, trade routes, migration patterns, or spatial narratives
- Build and analyze networks of historical figures, literary characters, or intellectual influence
- Attribute authorship of disputed texts using stylometry and computational methods
- Digitize historical documents using OCR (Tesseract, Kraken, Transkribus)
- Create digital scholarly editions with critical apparatus
- Visualize humanities data using Palladio, Gephi, or custom tools
- Apply distant reading methods to analyze literary trends across large corpora
- Conduct cultural analytics on visual media, social media, or digital culture
- Work with Python NLP tools (spaCy, NLTK) for humanities text analysis

## Core Capabilities

### Text Mining and NLP for Humanities

Natural language processing (NLP) provides computational tools for analyzing text at scales impossible for human readers. In humanities research, NLP is not a replacement for close reading but a complement that can identify patterns across thousands or millions of texts, guide the selection of passages for close analysis, and test hypotheses about language change, genre conventions, and cultural trends.

#### Topic Modeling

Topic modeling uses unsupervised machine learning to discover latent thematic structure in document collections. The two dominant approaches are Latent Dirichlet Allocation (LDA) and BERTopic.

**Latent Dirichlet Allocation (LDA):**

LDA (Blei, Pritchard, & Ng, 2003) models each document as a mixture of topics, and each topic as a distribution over words. It is a bag-of-words model -- word order does not matter.

**LDA workflow:**

1. **Corpus preparation** -- Collect and clean texts (remove headers, footers, metadata)
2. **Preprocessing** -- Tokenize, lowercase, remove stop words, lemmatize
3. **Feature extraction** -- Create document-term matrix or bag-of-words representation
4. **Model training** -- Run LDA with specified number of topics (k)
5. **Evaluation** -- Assess coherence scores, inspect topic-word distributions
6. **Interpretation** -- Label topics based on high-probability words and representative documents
7. **Analysis** -- Track topic proportions across time, genres, authors, or other categories

**Example: LDA topic from a corpus of 19th-century British novels**

```
Topic 7 (labeled "Domestic Life"):
  Top words: room, house, door, table, fire, chair, window, sat,
             morning, evening, bed, garden, dinner, tea, kitchen

  Top documents: Cranford (Gaskell), Middlemarch (Eliot),
                 North and South (Gaskell)

  Interpretation: This topic captures domestic settings and daily
  routines. Its prevalence increases in novels by women authors
  and in novels published after 1850, suggesting a shift toward
  domestic realism in mid-Victorian fiction.
```

**Choosing the number of topics (k):**
- Coherence scores (higher is better) -- compute for k = 5, 10, 15, 20, 25, 30, 40, 50
- Human interpretability -- can you label each topic meaningfully?
- Research question alignment -- does the granularity match your analytical needs?
- Common range: 15-50 topics for corpora of 1,000-10,000 documents

**BERTopic:**

BERTopic (Grootendorst, 2022) uses transformer-based sentence embeddings (BERT) to create document representations, then clusters them using HDBSCAN and extracts topic representations using c-TF-IDF. Unlike LDA, it captures semantic meaning beyond individual words.

**BERTopic advantages over LDA:**
- Captures semantic similarity (not just word co-occurrence)
- Handles short texts better (tweets, abstracts, metadata)
- Produces more coherent topics on modern text
- Does not require specifying the number of topics in advance

**BERTopic Python implementation:**

```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

# Use a sentence transformer model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize and fit BERTopic
topic_model = BERTopic(
    embedding_model=embedding_model,
    min_topic_size=10,
    nr_topics="auto"
)

topics, probs = topic_model.fit_transform(documents)

# Inspect topics
topic_model.get_topic_info()

# Visualize topic distribution
topic_model.visualize_topics()

# Track topics over time
topics_over_time = topic_model.topics_over_time(
    documents, timestamps
)
topic_model.visualize_topics_over_time(topics_over_time)
```

#### Sentiment Analysis

Sentiment analysis classifies text by emotional valence (positive, negative, neutral) or more specific emotional categories. In humanities research, it is used to study emotional arcs in novels, shifts in political rhetoric, audience reception in reviews, and emotional expression across historical periods.

**Approaches to sentiment analysis:**

| Approach | How It Works | Best For | Limitations |
|----------|-------------|----------|------------|
| Lexicon-based (VADER, AFINN, NRC) | Counts words from sentiment dictionaries | Quick analysis, transparent | Misses context, sarcasm, domain-specific usage |
| Machine learning (Naive Bayes, SVM) | Trained on labeled examples | Domain-specific tasks | Requires labeled training data |
| Transformer-based (BERT, RoBERTa) | Fine-tuned language models | High accuracy, context-aware | Computationally expensive, may need fine-tuning |

**Cautions for humanities research:**
- Historical texts use language differently than modern training data -- a sentiment model trained on product reviews will misclassify 18th-century prose
- Literary language uses irony, ambiguity, and indirection that confound automated classification
- Always validate automated sentiment against human annotation on a sample of your corpus
- Report the specific tool, model, and version used for reproducibility

**Example: Sentiment arc analysis of a novel**

```python
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize VADER
sid = SentimentIntensityAnalyzer()

# Split novel into chunks (e.g., 1000-word windows)
chunks = split_text(novel_text, window_size=1000)

# Calculate sentiment for each chunk
sentiments = []
for chunk in chunks:
    scores = sid.polarity_scores(chunk)
    sentiments.append(scores["compound"])

# Plot the sentiment arc
import matplotlib.pyplot as plt
plt.plot(range(len(sentiments)), sentiments)
plt.xlabel("Narrative Position")
plt.ylabel("Sentiment (VADER compound)")
plt.title("Emotional Arc: Pride and Prejudice")
plt.axhline(y=0, color="gray", linestyle="--")
plt.show()
```

#### Named Entity Recognition (NER)

NER identifies and classifies named entities in text -- people, places, organizations, dates, monetary values, and other proper nouns. In humanities research, NER enables automated extraction of historical actors, geographic references, and temporal markers from large corpora.

**NER tools for humanities:**

| Tool | Language | Strengths | Notes |
|------|----------|----------|-------|
| spaCy | Python | Fast, accurate, multiple languages | Best general-purpose NER |
| NLTK | Python | Educational, well-documented | Older, less accurate than spaCy |
| Stanza (Stanford NLP) | Python | Research-grade, many languages | Good for non-English texts |
| Flair | Python | State-of-the-art, flexible | Can fine-tune for historical text |
| BookNLP | Python/Java | Designed for literary texts | Character identification, coreference |

**Fine-tuning NER for historical texts:**

Pre-trained NER models are trained on modern text (news articles, Wikipedia) and perform poorly on historical text with archaic spelling, different naming conventions, and unfamiliar entities. Fine-tuning on manually annotated historical text dramatically improves accuracy.

```python
import spacy
from spacy.training import Example

# Load base model
nlp = spacy.load("en_core_web_sm")

# Prepare training data (manually annotated historical text)
TRAIN_DATA = [
    ("Mr. Darcy arrived at Pemberley in the autumn of 1811.",
     {"entities": [(0, 10, "PERSON"), (22, 31, "LOC"), (50, 54, "DATE")]}),
    ("The East India Company dispatched three vessels from Calcutta.",
     {"entities": [(4, 22, "ORG"), (53, 61, "LOC")]}),
]

# Fine-tune the NER component
# (simplified -- production code needs more examples and proper training loop)
```

### Corpus Linguistics

Corpus linguistics analyzes large, structured text collections to study language patterns. It provides empirical evidence for claims about language use, change, and variation that would be impossible to verify by intuition alone.

#### Concordance

A concordance displays every occurrence of a search term in its immediate context (typically 5-10 words on each side), creating a Key Word in Context (KWIC) view. This reveals patterns of usage, collocates, and semantic prosody.

**Example: KWIC concordance for "liberty" in 18th-century political texts**

```
...the natural  LIBERTY  of mankind is to be free from...
...that civil   LIBERTY  consists in the security of...
...enemies of   LIBERTY  who would enslave the nation...
...religious    LIBERTY  and freedom of conscience...
...took up arms for  LIBERTY  against tyrannical oppression...
```

Patterns visible: "liberty" collocates with "natural," "civil," "religious" -- different conceptual frames for the same word.

#### Collocation

Collocation analysis identifies words that co-occur with a target word more frequently than chance would predict. Statistical measures include Mutual Information (MI), t-score, log-likelihood, and Log Dice.

**Collocation measures compared:**

| Measure | Favors | Best For |
|---------|--------|----------|
| MI (Mutual Information) | Rare, exclusive collocates | Finding fixed phrases |
| t-score | Frequent collocates | Common usage patterns |
| Log-likelihood (G2) | Statistically significant collocates | Balanced analysis |
| Log Dice | Stable across corpus sizes | Comparing corpora |

#### Frequency and Keyness

**Word frequency** counts how often each word appears in a corpus. Raw frequency, normalized frequency (per million words), and relative frequency are all useful.

**Keyness** compares word frequencies between two corpora to identify words that are statistically over- or under-represented in one corpus relative to the other. This reveals what is distinctive about a text or collection.

**Example: Keyness analysis comparing male vs. female authored Victorian novels**

```
Words overrepresented in female-authored novels:
  she, her, room, mother, child, dress, felt, tears, home

Words overrepresented in male-authored novels:
  he, his, money, business, gentleman, sir, political, war

Interpretation: Keyness analysis reveals gendered thematic emphases
in Victorian fiction, with female authors more frequently writing about
domestic spaces and emotional states, and male authors more frequently
addressing public life and commerce. However, these are statistical
tendencies, not absolute divisions -- individual authors cross these
patterns in interesting ways.
```

**Corpus linguistics software:**

| Tool | Type | Cost | Best For |
|------|------|------|----------|
| AntConc | Desktop application | Free | Concordance, collocation, keyness |
| Voyant Tools | Web-based | Free | Quick visualization, no installation |
| Sketch Engine | Web-based | Paid (free for academics) | Large corpora, SketchDiff |
| CQPweb | Web-based | Free (institutional) | Corpus query language |
| NLTK | Python library | Free | Programmable analysis |
| quanteda | R package | Free | Statistical text analysis |

### Digital Archives and Metadata

#### Dublin Core

Dublin Core is a 15-element metadata standard used widely in digital archives and libraries. It provides a simple, universal vocabulary for describing digital resources.

**The 15 Dublin Core elements:**

| Element | Description | Example |
|---------|-------------|---------|
| Title | Name of the resource | "Letter from Thomas Jefferson to John Adams" |
| Creator | Entity primarily responsible | "Jefferson, Thomas" |
| Subject | Topic of the resource | "American politics; Enlightenment philosophy" |
| Description | Account of the resource | "Personal letter discussing agrarian policy..." |
| Publisher | Entity making resource available | "Library of Congress" |
| Contributor | Entity contributing to the resource | "Adams, John (recipient)" |
| Date | Date associated with the resource | "1812-06-11" |
| Type | Nature or genre | "Text; Correspondence" |
| Format | Physical or digital format | "image/tiff; 2 pages" |
| Identifier | Unambiguous reference | "loc.gov/item/mtjbib024567" |
| Source | Derived-from resource | "Thomas Jefferson Papers, Series 1" |
| Language | Language of the resource | "en" |
| Relation | Related resources | "Reply to Adams letter of 1812-05-28" |
| Coverage | Spatial or temporal coverage | "Monticello, Virginia; 1812" |
| Rights | Rights information | "Public domain" |

#### TEI XML

The Text Encoding Initiative (TEI) provides an XML-based standard for encoding literary, historical, and linguistic texts with rich structural and interpretive markup. TEI is the standard for digital scholarly editions.

**TEI document structure:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Letter from Mary Shelley to Leigh Hunt</title>
        <author>Shelley, Mary Wollstonecraft, 1797-1851</author>
        <editor>Digital editor name</editor>
      </titleStmt>
      <publicationStmt>
        <publisher>Digital Archive Name</publisher>
        <date>2026</date>
        <availability>
          <licence target="https://creativecommons.org/licenses/by/4.0/">
            CC-BY 4.0
          </licence>
        </availability>
      </publicationStmt>
      <sourceDesc>
        <msDesc>
          <msIdentifier>
            <repository>Bodleian Library</repository>
            <idno>MS. Shelley c.1, f.234</idno>
          </msIdentifier>
        </msDesc>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <opener>
        <dateline><placeName>Genoa</placeName>,
          <date when="1823-02-15">15 February 1823</date>
        </dateline>
        <salute>My dear <persName ref="#hunt">Hunt</persName>,</salute>
      </opener>
      <p>I write to you in great haste, having just received
        your letter from <placeName ref="#london">London</placeName>.
        The news of <persName ref="#byron">Lord Byron</persName>'s
        departure for <placeName ref="#greece">Greece</placeName>
        has left us all in a state of considerable anxiety.</p>
      <closer>
        <salute>Yours most affectionately,</salute>
        <signed><persName ref="#mshelley">Mary Shelley</persName></signed>
      </closer>
    </body>
  </text>
</TEI>
```

**Key TEI elements for humanities encoding:**

| Element | Purpose | Example Use |
|---------|---------|-------------|
| `<persName>` | Personal name | Tagging historical figures |
| `<placeName>` | Place name | Geographic references |
| `<date>` | Date (with @when for normalization) | Temporal references |
| `<note>` | Editorial annotation | Footnotes, commentary |
| `<app>` and `<rdg>` | Apparatus (textual variants) | Critical editions |
| `<del>` and `<add>` | Deletions and additions | Manuscript editing |
| `<unclear>` | Uncertain reading | Damaged or illegible text |
| `<gap>` | Omitted material | Lost or censored text |
| `<choice>` | Alternative encodings | Original/regularized spelling |

### GIS for Historical Research

Geographic Information Systems (GIS) enable spatial analysis of historical data -- mapping events, tracking movements, analyzing spatial patterns, and overlaying historical information on geographic space.

**Common GIS applications in humanities:**

1. **Historical mapping** -- Georeferencing old maps and overlaying them on modern geography
2. **Event mapping** -- Plotting historical events (battles, migrations, epidemics) in space and time
3. **Trade route analysis** -- Mapping commercial networks and flows
4. **Literary geography** -- Mapping settings, journeys, and spatial references in literature
5. **Urban history** -- Analyzing neighborhood change, segregation, and development
6. **Environmental history** -- Tracking landscape change over time
7. **Archaeological site mapping** -- Recording and analyzing excavation data spatially

**GIS tools for humanities:**

| Tool | Type | Cost | Best For |
|------|------|------|----------|
| QGIS | Desktop | Free | Full GIS functionality, open source |
| ArcGIS | Desktop + cloud | Paid (free for students) | Industry standard, extensive tools |
| Google Earth Pro | Desktop | Free | Visualization, KML import |
| Palladio | Web-based | Free | Network + map visualization for humanities |
| Mapbox | Web + API | Free tier | Custom interactive web maps |
| Leaflet | JavaScript library | Free | Lightweight web maps |
| kepler.gl | Web-based | Free | Large-scale geospatial data visualization |

**Example: Georeferencing a historical map**

```
Workflow in QGIS:
1. Load the scanned historical map as a raster layer
2. Add a modern basemap (OpenStreetMap) for reference
3. Identify Ground Control Points (GCPs) -- locations identifiable
   on both the historical map and modern basemap
4. Place at least 4 GCPs (more is better, spread across the map)
5. Choose a transformation type:
   - Linear: 3 GCPs minimum (shift, rotate, scale)
   - Polynomial 1: 3 GCPs minimum (affine transformation)
   - Polynomial 2: 6 GCPs minimum (handles distortion)
   - Thin Plate Spline: many GCPs (flexible, handles local distortion)
6. Run the transformation and inspect the result
7. Save the georeferenced map with spatial reference metadata
```

### Network Analysis for Historical Figures

Network analysis reveals patterns of connection, influence, and community structure among historical actors. Applied to correspondence networks, co-appearance in documents, intellectual citation, or organizational membership, it can reveal hidden structures in historical social worlds.

**Types of historical networks:**

| Network Type | Nodes | Edges | Example |
|-------------|-------|-------|---------|
| Correspondence | People | Letters exchanged | Republic of Letters network |
| Co-occurrence | People | Mentioned in same document | Colonial administration officials |
| Citation | Texts/authors | One cites another | Intellectual influence networks |
| Kinship | People | Family relations | Dynastic networks |
| Trade | Places/merchants | Commercial exchange | Mediterranean trade network |
| Organizational | People/orgs | Membership/affiliation | Reform movement networks |

**Building a historical network from archival sources:**

```
Step 1: Define nodes and edges
  - What counts as a node? (person, place, text, organization)
  - What counts as an edge? (letter, co-occurrence, citation, transaction)
  - Is the edge directed or undirected?
  - What edge attributes to record? (date, type, weight)

Step 2: Extract data from sources
  - Manual extraction from archival documents
  - Semi-automated extraction using NER on digitized texts
  - Structured databases (EMLO for early modern letters, SNAP for prosopography)

Step 3: Create edge list
  Format: Source, Target, Weight, Date, Type
  "Jefferson", "Adams", 1, "1812-06-11", "letter"
  "Jefferson", "Madison", 1, "1812-06-15", "letter"

Step 4: Analyze in Gephi, NetworkX, or igraph
  - Calculate centrality measures
  - Detect communities (Louvain, modularity)
  - Visualize with meaningful layout (ForceAtlas2, geographic)
  - Filter by time period for temporal analysis
```

### Stylometry and Authorship Attribution

Stylometry uses statistical analysis of writing style to attribute authorship of anonymous or disputed texts. It relies on the principle that authors have measurable stylistic habits -- especially in function words, sentence length, and vocabulary richness -- that are unconscious and therefore difficult to imitate.

**Key stylometric features:**

| Feature | Description | Why It Works |
|---------|-------------|-------------|
| Function word frequencies | the, of, and, to, a, in, is, it | Unconscious, content-independent |
| Word length distribution | Average and variance of word lengths | Reflects vocabulary preferences |
| Sentence length | Average and variance | Reflects syntactic habits |
| Vocabulary richness | Type-token ratio, hapax legomena | Lexical diversity |
| Character n-grams | Sequences of n characters | Captures sub-word patterns |
| POS tag n-grams | Sequences of part-of-speech tags | Syntactic patterns |

**Stylometry tools:**

| Tool | Language | Method | Best For |
|------|----------|--------|----------|
| Stylo (R package) | R | Delta, PCA, cluster analysis | Literary stylometry |
| JGAAP | Java | Multiple classifiers | General authorship attribution |
| PyDelta | Python | Burrows Delta variants | Python-based workflows |
| Signature | Web-based | Visualization | Quick exploration |

**Burrows Delta method:**

Delta (Burrows, 2002) is the most widely used stylometric method. It measures the "distance" between texts based on z-scores of the most frequent words:

```
Algorithm:
1. Select the n most frequent words across all texts (typically 100-500)
2. For each word, calculate z-scores across all texts
3. For each pair of texts, calculate the mean absolute difference
   of z-scores (this is Delta)
4. The text with the smallest Delta to the anonymous text is the
   most likely author

Variants:
- Classic Delta (Burrows, 2002): Mean absolute z-score difference
- Cosine Delta (Wurzburg group): Cosine distance on z-scores
- Eder Delta: Emphasis on very frequent words
- Argamon Linear Delta: Manhattan distance
```

**Example: Stylometric analysis in R (stylo package)**

```r
library(stylo)

# Place texts in corpus/ subdirectory
# Filename format: AuthorName_TextTitle.txt

# Run cluster analysis
results <- stylo(
  gui = FALSE,
  corpus.dir = "corpus",
  corpus.lang = "English",
  mfw.min = 100,        # Minimum most frequent words
  mfw.max = 500,        # Maximum most frequent words
  mfw.incr = 100,       # Increment
  analysis.type = "CA", # Cluster Analysis
  distance.measure = "wurzburg",  # Cosine Delta
  write.png.file = TRUE
)
```

### OCR Workflows

Optical Character Recognition (OCR) converts images of text (scanned documents, photographs of manuscripts, historical newspapers) into machine-readable text. OCR quality is critical for all downstream text analysis.

**OCR tools comparison:**

| Tool | Type | Best For | Languages | Historical Text |
|------|------|----------|-----------|----------------|
| Tesseract | Open source | General purpose | 100+ | Moderate (needs training) |
| Kraken | Open source | Historical/non-Latin scripts | Many | Excellent (designed for it) |
| Transkribus | Free platform | Handwritten text (HTR) | Many | Excellent |
| ABBYY FineReader | Commercial | High-volume production | Many | Good |
| Google Cloud Vision | API | Large-scale, cloud | Many | Good |
| Amazon Textract | API | Structured documents | English primarily | Moderate |

**OCR workflow for historical documents:**

```
1. IMAGE PREPARATION
   - Scan at 300-400 DPI minimum (600 DPI for small text)
   - Use grayscale or binary (not color unless needed)
   - Deskew rotated pages
   - Crop to text area
   - Binarize (convert to black and white) using adaptive thresholding

2. OCR PROCESSING
   - Select appropriate engine and language model
   - For historical text: use period-appropriate training data if available
   - Process page by page
   - Maintain page/document structure

3. POST-PROCESSING
   - Spell-check against period-appropriate dictionaries
   - Correct common OCR errors (rn -> m, cl -> d, etc.)
   - Validate against spot-checks of original images
   - Preserve original line/page breaks in metadata

4. QUALITY ASSESSMENT
   - Character Error Rate (CER): % of characters incorrectly recognized
   - Word Error Rate (WER): % of words with at least one error
   - Acceptable CER for research: < 5% (ideally < 2%)
   - Always report OCR quality in publications using the data
```

**Tesseract command-line example:**

```bash
# Basic OCR
tesseract input.tiff output -l eng

# With page segmentation mode for single column
tesseract input.tiff output -l eng --psm 6

# With custom trained model for historical English
tesseract input.tiff output -l eng_hist --psm 6 --oem 1
```

### Digital Scholarly Editions

Digital editions present primary texts with critical apparatus, annotations, and multimedia in a digital environment. They go beyond digitized facsimiles by adding scholarly interpretation, textual variants, and interactive features.

**Components of a digital scholarly edition:**

1. **Transcription** -- Accurate text of the source document(s)
2. **Encoding** -- TEI XML markup of structural and semantic features
3. **Apparatus** -- Textual variants from multiple witnesses
4. **Annotation** -- Editorial notes, commentary, contextual information
5. **Facsimile** -- High-resolution images of the source documents
6. **Search** -- Full-text and metadata search functionality
7. **Visualization** -- Interactive displays of textual relationships
8. **Stable identifiers** -- Persistent URLs for citation

**Digital edition platforms:**

| Platform | Type | Best For |
|----------|------|----------|
| Edition Visualization Technology (EVT) | Open source | TEI-based critical editions |
| Versioning Machine | Open source | Parallel text comparison |
| TextGrid | Platform | German-language editions |
| FromThePage | Web platform | Collaborative transcription |
| Scripto | Plugin (Omeka) | Crowdsourced transcription |
| IIIF (protocol) | Standard | Interoperable image delivery |

### Data Visualization for Humanities

Visualization in the humanities serves both analytical and communicative purposes -- revealing patterns in data and presenting arguments visually.

**Humanities-specific visualization tools:**

| Tool | Best For | Output |
|------|----------|--------|
| Palladio | Historical data (maps, networks, timelines) | Interactive web |
| Gephi | Network visualization | Static images, interactive (via plugins) |
| Voyant Tools | Text visualization (word clouds, trends, contexts) | Interactive web |
| StoryMapJS | Narrative maps | Interactive web |
| TimelineJS | Chronological narratives | Interactive web |
| Flourish | General data storytelling | Interactive web |
| RAWGraphs | Unconventional chart types | SVG export |
| D3.js | Custom interactive visualizations | Web (requires JavaScript) |
| matplotlib/seaborn | Statistical plots | Static images |

**Visualization principles for humanities data:**

1. **Uncertainty is data** -- Historical and humanities data are often incomplete, ambiguous, or contested. Visualizations should represent uncertainty explicitly (confidence intervals, fuzzy boundaries, missing data indicators).
2. **Context over decoration** -- Every visual element should serve an analytical purpose.
3. **Narrative integration** -- Visualizations should be embedded in interpretive arguments, not presented as self-explanatory evidence.
4. **Accessibility** -- Use colorblind-safe palettes, provide alt text, ensure screen reader compatibility.
5. **Reproducibility** -- Document data sources, processing steps, and visualization parameters.

### Distant Reading

Distant reading, as theorized by Franco Moretti (2005, 2013), proposes that we can understand literary history not only by close reading individual texts but by analyzing large numbers of texts through quantitative and computational methods. Instead of reading a few canonical works closely, distant reading examines hundreds or thousands of texts to reveal patterns of genre, form, theme, and cultural evolution.

**Key distant reading methods:**

1. **Quantitative genre analysis** -- Tracking the rise and fall of literary genres over time
2. **Title analysis** -- Studying how book titles change across periods and genres
3. **Plot structure analysis** -- Mapping narrative arcs computationally (sentiment trajectories)
4. **Geographic imagination** -- Mapping the settings of novels across national literatures
5. **Network analysis of characters** -- Examining the social world within novels
6. **Stylistic change** -- Tracking sentence length, vocabulary complexity, and other formal features over literary history

**Moretti's key arguments:**
- The literary canon represents a tiny fraction of published literature -- we need methods that address the "great unread"
- Quantitative patterns reveal structures invisible to close reading
- Literary forms evolve through mechanisms analogous to biological evolution (variation, selection, drift)
- Maps, graphs, and trees are analytical tools, not mere illustrations

### Cultural Analytics

Cultural analytics, developed by Lev Manovich (2020), applies computational analysis to large collections of cultural artifacts -- images, video, music, design, social media, and other digital media. It extends distant reading beyond text to the full spectrum of human cultural production.

**Cultural analytics methods:**

1. **Image analysis** -- Color histograms, composition analysis, object detection across thousands of images
2. **Time series of visual features** -- Tracking changes in visual style over decades
3. **Media visualization** -- Displaying large collections as composite images (e.g., every cover of Time magazine arranged chronologically)
4. **Social media analytics** -- Patterns in Instagram photos, TikTok videos, or Twitter discourse
5. **Interface analysis** -- Studying the design of software, websites, and apps as cultural artifacts

**Python tools for cultural analytics:**

| Library | Purpose |
|---------|---------|
| OpenCV | Image processing, feature extraction |
| Pillow (PIL) | Image manipulation |
| scikit-image | Scientific image analysis |
| face_recognition | Face detection and recognition |
| ImageAI | Object detection |
| matplotlib / seaborn | Visualization |
| plotly | Interactive visualization |

### Python Tools for Humanities Computing

**spaCy -- Industrial-strength NLP:**

```python
import spacy

# Load English model
nlp = spacy.load("en_core_web_sm")

# Process text
doc = nlp("Mary Shelley wrote Frankenstein in Geneva in 1816.")

# Named entities
for ent in doc.ents:
    print(f"{ent.text} -> {ent.label_}")
# Mary Shelley -> PERSON
# Frankenstein -> WORK_OF_ART
# Geneva -> GPE
# 1816 -> DATE

# Part-of-speech tags
for token in doc:
    print(f"{token.text}: {token.pos_} ({token.dep_})")

# Sentence segmentation, dependency parsing, lemmatization
```

**NLTK -- Natural Language Toolkit:**

```python
import nltk
from nltk.corpus import gutenberg
from nltk import FreqDist, ConditionalFreqDist

# Load a Gutenberg text
text = gutenberg.words("austen-emma.txt")

# Frequency distribution
fdist = FreqDist(text)
fdist.most_common(20)

# Concordance
from nltk.text import Text
emma = Text(text)
emma.concordance("marriage", width=80, lines=10)

# Collocations
emma.collocations()
```

**Voyant Tools (no-code option):**

Voyant Tools (voyant-tools.org) provides browser-based text analysis with no programming required:
- Upload texts or paste URLs
- Instant word clouds, frequency graphs, KWIC concordances
- Trends visualization across documents
- Collocate analysis
- Document similarity clustering
- Embeddable visualizations for websites

**AntConc (desktop corpus tool):**

AntConc (laurenceanthony.net/software/antconc) provides:
- KWIC concordance with sorting options
- Collocation analysis with multiple statistical measures
- Word/keyword frequency lists
- N-gram analysis
- Keyness comparison between corpora
- Concordance plot (dispersion visualization)

## Best Practices

### Starting a Digital Humanities Project

1. **Start with a humanistic question** -- Technology is a means, not an end. What do you want to know about culture, history, or language?
2. **Choose the simplest tool that works** -- Voyant Tools and AntConc can answer many questions without programming.
3. **Learn iteratively** -- You do not need to master Python before starting. Begin with existing tools and add technical skills as needed.
4. **Document everything** -- Record every decision about corpus construction, preprocessing, parameter selection, and interpretation.
5. **Validate computationally derived patterns with close reading** -- Distant and close reading are complementary, not competing.

### Data Quality and Preparation

1. **Corpus construction is an argument** -- What you include and exclude shapes your results. Document and justify your corpus boundaries.
2. **OCR quality matters** -- Always assess and report OCR error rates. Garbage in, garbage out.
3. **Metadata is essential** -- Author, date, genre, publication context -- without metadata, you cannot contextualize computational findings.
4. **Preprocessing choices are analytical choices** -- Lemmatization, stop word removal, and tokenization all affect results. Report what you did.
5. **Preserve originals** -- Never modify your source data. Keep raw and processed versions separate.

### Interpretation and Argumentation

1. **Computational results require interpretation** -- A topic model does not speak for itself. The scholar must interpret what the patterns mean.
2. **Visualizations are arguments** -- Every visualization makes choices about what to show and how to show it. Be explicit about these choices.
3. **Acknowledge limitations** -- Computational methods have blind spots. Discuss what your method cannot capture.
4. **Engage with disciplinary debates** -- Situate your computational findings within existing humanistic scholarship.
5. **Collaborate** -- DH benefits from collaboration between domain experts and technical specialists.

## Common Pitfalls

### Text Mining Pitfalls

- **Black box models** -- Using NLP tools without understanding what they do. Always know what your tool measures and how it works.
- **Anachronistic analysis** -- Applying sentiment models trained on modern text to historical corpora without validation.
- **Overclaiming from topics** -- Topic models show word co-occurrence patterns, not "meanings." Human interpretation bridges the gap.
- **Ignoring preprocessing effects** -- Different lemmatizers, stop word lists, and tokenizers produce different results. Test sensitivity.

### Corpus Linguistics Pitfalls

- **Small corpus, big claims** -- Statistical measures require sufficient data. Do not generalize from a corpus of 10 texts.
- **Frequency without context** -- A word being frequent does not make it important. Always examine concordance lines.
- **Ignoring genre and register** -- Comparing word frequencies across genres (poetry vs. prose, speech vs. writing) without accounting for genre effects.

### GIS and Mapping Pitfalls

- **False precision** -- Mapping historical locations to exact modern coordinates implies accuracy that may not exist.
- **Projection distortion** -- All map projections distort reality. Choose projections appropriate for your region and purpose.
- **Empty maps** -- Absence of data is not absence of activity. Communicate what is not shown.

### Stylometry Pitfalls

- **Insufficient text length** -- Stylometric methods need substantial text (minimum 2,000-5,000 words per sample) to produce reliable results.
- **Genre contamination** -- Stylometric features vary by genre. Comparing a novel to a letter introduces genre effects that may overwhelm authorial signal.
- **Circular reasoning** -- Training a model on the disputed text and then using the model to attribute it.

## References

- Moretti, F. (2005). *Graphs, Maps, Trees: Abstract Models for Literary History*. Verso.
- Moretti, F. (2013). *Distant Reading*. Verso.
- Manovich, L. (2020). *Cultural Analytics*. MIT Press.
- Jockers, M. L. (2013). *Macroanalysis: Digital Methods and Literary History*. University of Illinois Press.
- Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet Allocation. *Journal of Machine Learning Research*, 3, 993-1022.
- Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure. *arXiv preprint*, arXiv:2203.05794.
- Burrows, J. (2002). Delta: A measure of stylistic difference and a guide to likely authorship. *Literary and Linguistic Computing*, 17(3), 267-287.
- Burnard, L., & Bauman, S. (Eds.). (2023). *TEI P5: Guidelines for Electronic Text Encoding and Interchange*. Text Encoding Initiative Consortium.
- Bodenhamer, D. J., Corrigan, J., & Harris, T. M. (Eds.). (2010). *The Spatial Humanities: GIS and the Future of Humanities Scholarship*. Indiana University Press.
- Graham, S., Milligan, I., & Weingart, S. (2015). *Exploring Big Historical Data: The Historian's Macroscope*. Imperial College Press.
