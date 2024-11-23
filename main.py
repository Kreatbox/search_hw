from flask import Flask, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3

app = Flask(__name__)
DATABASE = "faqs.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/insert", methods=["POST"])
def insert():
    question = request.form.get("question")
    answer = request.form.get("answer")
    language = request.form.get("language")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO faqs (question, answer, language) VALUES (?, ?, ?)",
                   (question, answer, language))
    conn.commit()
    conn.close()

    return render_template("search.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_question = request.form.get("searchQuestion")
        retrieval_model = request.form.get("retrievalModel")

        conn = get_db_connection()
        cursor = conn.cursor()

        if retrieval_model == "1":
            search_question = search_question.lower()
            search_question = search_question.replace(
                'and', 'AND').replace('or', 'OR').replace('not', 'NOT').replace(' و ', ' AND ').replace('أو ', 'OR ')
            terms = search_question.split()
            query_parts = []

            for term in terms:
                if term.lower() == 'and':
                    query_parts.append('AND')
                elif term.lower() == 'or':
                    query_parts.append('OR')
                elif term.lower() == 'not':
                    query_parts.append('NOT')
                else:
                    query_parts.append(f"question LIKE '%{term}%'")
            final_query = ' '.join(query_parts)
            cursor.execute(f"SELECT * FROM faqs WHERE {final_query}")
            results = cursor.fetchall()

        elif retrieval_model == "2":
            search_question = search_question.lower()
            terms = search_question.split()
            query_parts = []
            weights = {}
            important_terms = ['what', 'why', 'Dubai']
            for term in terms:
                if term in important_terms:
                    weights[term] = 2
                else:
                    weights[term] = 1
            for term in terms:
                if weights[term] == 2:
                    query_parts.append(f"question LIKE '%{term}%'")
                else:
                    query_parts.append(f"question LIKE '%{term}%'")
            final_query = ' AND '.join(query_parts)
            cursor.execute(f"SELECT * FROM faqs WHERE {final_query}")
            results = cursor.fetchall()

        elif retrieval_model == "3":
            search_question = search_question.lower()
            cursor.execute("SELECT question, answer, language FROM faqs")
            questions = cursor.fetchall()
            documents = [q['question'] for q in questions]
            documents.append(search_question)
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(documents)
            cosine_similarities = cosine_similarity(
                tfidf_matrix[-1], tfidf_matrix[:-1])
            ranked_questions = sorted(
                zip(cosine_similarities[0], questions), reverse=True, key=lambda x: x[0]
            )
            top_results = ranked_questions[:5]
            results = [{
                "question": q[1]['question'],
                "answer": q[1]['answer'],
                "language": q[1]['language'],
                "similarity": q[0]
            } for q in top_results]
        conn.close()
        return render_template("search.html", results=results, query=search_question)
    return render_template("search.html", results=[])


if __name__ == "__main__":
    app.run(debug=True)
