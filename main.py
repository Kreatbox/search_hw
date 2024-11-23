from flask import Flask, render_template, request
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
            # Boolean Model
            search_question = search_question.lower()
            search_question = search_question.replace(
                'and', 'AND').replace('or', 'OR').replace('not', 'NOT')
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
            # Extended Boolean Model
            search_question = search_question.lower()
            terms = search_question.split()
            query_parts = [f"question LIKE '%{term}%'" for term in terms]
            final_query = ' AND '.join(query_parts)
            cursor.execute(f"SELECT * FROM faqs WHERE {final_query}")
            results = cursor.fetchall()

        elif retrieval_model == "3":
            # Simplified Vector Model
            search_question = search_question.lower()
            cursor.execute("SELECT question, answer, language FROM faqs")
            questions = cursor.fetchall()

            def calculate_similarity(question_text, search_query):
                # Simple similarity based on common word overlap
                q_words = set(question_text.lower().split())
                s_words = set(search_query.lower().split())
                return len(q_words & s_words) / max(len(q_words | s_words), 1)

            scored_questions = [
                {
                    "question": q["question"],
                    "answer": q["answer"],
                    "language": q["language"],
                    "similarity": calculate_similarity(q["question"], search_question)
                }
                for q in questions
            ]
            results = sorted(scored_questions,
                             key=lambda x: x["similarity"], reverse=True)[:5]
        else:
            results = []

        conn.close()
        return render_template("search.html", results=results, query=search_question)
    return render_template("search.html", results=[])


if __name__ == "__main__":
    app.run(debug=True)
