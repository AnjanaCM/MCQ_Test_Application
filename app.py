from flask import Flask, render_template, request, redirect, url_for, session
from questions import QUESTIONS
import time
import json
import os
from datetime import datetime

app = Flask(__name__)

# Secret key for session
app.secret_key = "mcq-test-secret-key"

# Exam duration = 40 minutes
EXAM_DURATION = 40 * 60

# File where candidate answers will be stored
DATA_FILE = os.path.join("data", "responses.json")


# First page - Instructions
@app.route("/")
def home():
    return render_template("instructions.html")


# Candidate Details page
@app.route("/candidate", methods=["GET", "POST"])
def candidate():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        # Check whether both fields are entered
        if not name or not email:
            return render_template(
                "candidate.html",
                error="Please enter both name and email."
            )

        # Store candidate information
        session["candidate_name"] = name
        session["candidate_email"] = email

        # Start a fresh exam timer
        session.pop("exam_start_time", None)

        # Go to examination page
        return redirect(url_for("exam"))

    return render_template("candidate.html")


# Examination page
@app.route("/exam")
def exam():

    # Candidate must enter details before starting exam
    if "candidate_name" not in session:
        return redirect(url_for("candidate"))

    # Start timer only the first time exam page is opened
    if "exam_start_time" not in session:
        session["exam_start_time"] = time.time()

    # Calculate elapsed time
    elapsed_time = int(
        time.time() - session["exam_start_time"]
    )

    # Calculate remaining time
    remaining_seconds = max(
        0,
        EXAM_DURATION - elapsed_time
    )

    return render_template(
        "exam.html",
        questions=QUESTIONS,
        remaining_seconds=remaining_seconds
    )


# Submit Examination
@app.route("/submit", methods=["POST"])
def submit():

    # Make sure candidate has started the exam
    if "candidate_name" not in session:
        return redirect(url_for("candidate"))

    # Receive submitted answers
    answers = request.form

    # Calculate how much time has passed
    if "exam_start_time" in session:
        elapsed_time = time.time() - session["exam_start_time"]
    else:
        elapsed_time = 0

    # Check whether the exam time is over
    time_expired = elapsed_time >= EXAM_DURATION

    # Manual submission requires all questions
    if not time_expired:

        for i in range(len(QUESTIONS)):

            if f"q{i}" not in answers:
                return redirect(url_for("exam"))

    # Calculate score
    score = 0

    for i, question in enumerate(QUESTIONS):

        selected_answer = answers.get(f"q{i}")

        if selected_answer is not None:

            try:

                selected_answer = int(selected_answer)

                if selected_answer == question["answer"]:
                    score += 1

            except ValueError:
                pass

    # Total questions
    total_questions = len(QUESTIONS)

    # Calculate percentage
    percentage = round(
        (score / total_questions) * 100,
        2
    )

    # Create response data
    response_data = {
        "name": session["candidate_name"],
        "email": session["candidate_email"],
        "answers": {},
        "score": score,
        "total_questions": total_questions,
        "percentage": percentage,
        "submitted_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    # --------------------------------------------------
    # Store detailed answer information
    # --------------------------------------------------

    for i, question in enumerate(QUESTIONS):

        selected_answer = answers.get(f"q{i}")
        correct_answer = question["answer"]

        # Default values
        is_correct = False
        answer_status = "unanswered"

        # Check selected answer
        if selected_answer is not None:

            try:

                selected_answer_number = int(selected_answer)

                if selected_answer_number == correct_answer:
                    is_correct = True
                    answer_status = "correct"
                else:
                    answer_status = "incorrect"

            except ValueError:

                answer_status = "invalid"

        # Store detailed information
        response_data["answers"][f"q{i + 1}"] = {
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "status": answer_status
        }

    # --------------------------------------------------
    # Create data folder if it does not exist
    # --------------------------------------------------

    os.makedirs("data", exist_ok=True)

    # --------------------------------------------------
    # Read existing responses
    # --------------------------------------------------

    if os.path.exists(DATA_FILE):

        try:

            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                all_responses = json.load(file)

        except (json.JSONDecodeError, FileNotFoundError):

            all_responses = []

    else:

        all_responses = []

    # Make sure the loaded data is a list
    if not isinstance(all_responses, list):
        all_responses = []

    # --------------------------------------------------
    # Add new candidate response
    # --------------------------------------------------

    all_responses.append(response_data)

    # --------------------------------------------------
    # Save responses
    # --------------------------------------------------

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_responses,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------
    # Show result
    # --------------------------------------------------

    return render_template(
        "submitted.html",
        candidate_name=session["candidate_name"],
        score=score,
        total_questions=total_questions,
        percentage=percentage
    )


# Run Flask application
if __name__ == "__main__":

    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )