import os
import pickle
import re
import traceback

import pandas as pd
import pyterrier as pt
from django.shortcuts import render
from django.http import JsonResponse, Http404
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize PyTerrier and load the model (do this once when the app starts)
if not pt.started():
    pt.init()

# Load the index
index_dir = os.path.join(os.getcwd(), "index")
index_ref = pt.IndexFactory.of(index_dir)

tfidf = pt.terrier.Retriever(index_ref, wmodel="TF_IDF")
pl2 = pt.terrier.Retriever(index_ref, wmodel="PL2")
bb2 = pt.terrier.Retriever(index_ref, wmodel="BB2")

def remove_nonalphanum(text):
  pattern = re.compile('[\W_]+')
  return pattern.sub(' ', text)

def lowercast(text):
  return text.lower()

collections = pd.read_csv("corpus.csv")
collections = collections.rename(columns={'id':'docno'})
collections['text'] = collections['text'].apply(remove_nonalphanum)
collections['text'] = collections['text'].apply(lowercast)
collections["docno"] = collections["docno"].astype(str)

tfidf_vectorizer = TfidfVectorizer()
tfidf_vectorizer.fit(collections["text"])

def cosine_similarity_feature(doc, query):
    doc_vector = tfidf_vectorizer.transform([doc])
    query_vector = tfidf_vectorizer.transform([query])
    return cosine_similarity(doc_vector, query_vector)[0][0]

def length_ratio_feature(doc, query):
    doc_length = len(doc.split())
    query_length = len(query.split())
    return doc_length / query_length if query_length > 0 else 0

def generate_features(doc, query):
    features = [
        cosine_similarity_feature(doc, query),
        length_ratio_feature(doc, query)
    ]
    return np.array(features)

features = pt.apply.doc_features(lambda row: generate_features(row["text"], row["query"]))

# Load the model and create pipeline (do this once when the app starts)
with open('xgb_model.pkl', 'rb') as f:
    xgb_model = pickle.load(f)

bm25 = pt.BatchRetrieve(index_ref, wmodel="BM25")
features = pt.apply.doc_features(lambda row: generate_features(row["text"], row["query"]))
K = 30

pipeline = bm25 >> pt.text.get_text(index_ref, "text") >> (features ** bm25 ** tfidf ** pl2 ** bb2)
lmart_pipe = pipeline >> pt.ltr.apply_learned_model(xgb_model, form="ltr")

def search_view(request):
    # Handle POST request (search query)
    if request.method == 'POST':
        query = request.POST.get('query', '')
        query = lowercast(remove_nonalphanum(query))

        if not query:
            return JsonResponse({
                'status': 'error',
                'message': 'No query provided',
                'results': []
            })

        try:
            # Get search results using lmart_pipe
            results = lmart_pipe.search(query)
            # Convert DataFrame to list of dictionaries with selected fields
            results_list = results.apply(lambda x: {
                'docid': str(x['docid']),
                'docno': str(x['docno']),
                'text': str(x['text']),
                'score': float(x['score']),
                'rank': int(x['rank'])
            }, axis=1).tolist()

            # Return JSON response with results
            return JsonResponse({
                'status': 'success',
                'query': query,
                'results': results_list
            })

        except Exception as e:
            # Log the full error for debugging
            print(f"Search error: {str(e)}")
            print(traceback.format_exc())

            # Return error response
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while processing your search',
                'query': query,
                'results': []
            }, status=500)

    # Handle GET request (initial page load)
    return render(request, 'search.html')

def document_view(request, doc_id):
    try:
        # Using the same index_ref from the search view
        # Get the document metadata and content
        doc_content = index_ref.getMetaIndex().getItem("text", int(doc_id))

        if not doc_content:
            raise Http404("Document not found")

        # Create a document context with all the information we want to display
        document = {
            'docno': doc_id,
            'text': doc_content,
            # You can add more fields here if needed
        }

        return render(request, 'document.html', {
            'document': document,
            'title': f'Document #{doc_id}'
        })

    except Exception as e:
        print(f"Error retrieving document: {str(e)}")
        raise Http404(f"Error retrieving document: {str(e)}")