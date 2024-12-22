import pickle
import pyterrier as pt
from django.shortcuts import render
from django.http import JsonResponse, Http404
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize PyTerrier and load the model (do this once when the app starts)
if not pt.started():
    pt.init(version='snapshot')

# Load the index
index_ref = pt.IndexRef.of("./index/data.properties")

def jaccard(doc, query):
    doc_tokens = set(doc.split())
    query_tokens = set(query.split())
    intersection = len(doc_tokens.intersection(query_tokens))
    union = len(doc_tokens.union(query_tokens))
    return intersection / union if union != 0 else 0

def tfidf_sim(doc, query):
    vectorizer = TfidfVectorizer().fit_transform([doc, query])
    vectors = vectorizer.toarray()
    cos_sim = cosine_similarity(vectors)
    return cos_sim[0, 1]

def generate_features(doc, query):
    return np.array([
        jaccard(doc, query),
        tfidf_sim(doc, query)
    ])

# Load the model and create pipeline (do this once when the app starts)
with open('xgb_model.pkl', 'rb') as f:
    xgb_model = pickle.load(f)

bm25 = pt.BatchRetrieve(index_ref, wmodel="BM25")
features = pt.apply.doc_features(lambda row: generate_features(row["text"], row["query"]))
K = 30

pipeline = (bm25 % K) >> pt.text.get_text(index_ref, "text") >> (features ** bm25)
lmart_pipe = pipeline >> pt.ltr.apply_learned_model(xgb_model, form="ltr")

def search_view(request):
    # Handle POST request (search query)
    if request.method == 'POST':
        query = request.POST.get('query', '')
        
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
        doc_content = index_ref.getMetaIndex().getItem("text", doc_id)
        
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