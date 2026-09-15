from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from questions import QUESTIONS
import json
import os
import time


app = Flask(__name__)

app.secret_key = "mcq-test-secret-key"

# 40 minutes
EXAM_DURATION = 40 * 60

RESPONSES_FILE = os.path.join("data", "responses.json")


# =========================================================
# LOAD SAVED RESPONSES
# =========================================================

def load_responses():

    if not os.path.exists(RESPONSES_FILE):
        return []

    try:

        with open(
            RESPONSES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, FileNotFoundError):

        return []


# =========================================================
# CHECK WHETHER EMAIL HAS ALREADY ATTENDED
# =========================================================

def email_already_used(email):

    email = email.strip().lower()

    responses = load_responses()

    for response in responses:

        saved_email = str(
            response.get("email", "")
        ).strip().lower()

        if saved_email == email:

            return True

    return False


# =========================================================
# SAVE RESPONSE
# =========================================================

def save_response(response_data):

    os.makedirs(
        "data",
        exist_ok=True
    )

    responses = load_responses()

    responses.append(
        response_data
    )

    with open(
        RESPONSES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            responses,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# HOME / INSTRUCTIONS PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "instructions.html"
    )


# =========================================================
# EMAIL CHECK ROUTE
# =========================================================

@app.route(
    "/check_email",
    methods=["POST"]
)
def check_email():

    data = request.get_json()

    if not data:

        return jsonify({
            "allowed": False,
            "message": "Invalid request."
        })

    email = data.get(
        "email",
        ""
    ).strip().lower()

    if not email:

        return jsonify({
            "allowed": False,
            "message": "Please enter your email address."
        })

    if email_already_used(email):

        return jsonify({
            "allowed": False,
            "message": "This email ID has already attended the examination."
        })

    return jsonify({
        "allowed": True
    })


# =========================================================
# CANDIDATE PAGE
# =========================================================

@app.route(
    "/candidate",
    methods=["GET", "POST"]
)
def candidate():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        # -------------------------------------------------
        # VALIDATE NAME
        # -------------------------------------------------

        if not name:

            return render_template(
                "candidate.html",
                error="Please enter your full name."
            )

        if not all(
            character.isalpha() or character.isspace()
            for character in name
        ):

            return render_template(
                "candidate.html",
                error="Name should contain letters and spaces only."
            )

        # -------------------------------------------------
        # VALIDATE EMAIL
        # -------------------------------------------------

        if not email:

            return render_template(
                "candidate.html",
                error="Please enter your email address."
            )

        # -------------------------------------------------
        # CHECK DUPLICATE EMAIL
        # -------------------------------------------------

        if email_already_used(email):

            return render_template(
                "candidate.html",
                error="This email ID has already attended the examination."
            )

        # -------------------------------------------------
        # STORE CANDIDATE DETAILS
        # -------------------------------------------------

        session["candidate_name"] = name
        session["candidate_email"] = email

        # Start a completely new examination
        session.pop(
            "exam_start_time",
            None
        )

        session.pop(
            "exam_submitted",
            None
        )

        session.pop(
            "score",
            None
        )

        session.pop(
            "percentage",
            None
        )

        session.pop(
            "total_questions",
            None
        )

        return redirect(
            url_for("exam")
        )

    return render_template(
        "candidate.html"
    )


# =========================================================
# EXAM PAGE
# =========================================================

@app.route(
    "/exam",
    methods=["GET"]
)
def exam():

    # -----------------------------------------------------
    # CANDIDATE MUST HAVE ENTERED DETAILS
    # -----------------------------------------------------

    if "candidate_email" not in session:

        return redirect(
            url_for("candidate")
        )

    # -----------------------------------------------------
    # PREVENT OPENING EXAM AGAIN AFTER SUBMISSION
    # -----------------------------------------------------

    if session.get("exam_submitted"):

        return render_template(
            "submitted.html",
            candidate_name=session.get(
                "candidate_name",
                ""
            ),
            candidate_email=session.get(
                "candidate_email",
                ""
            ),
            score=session.get(
                "score",
                0
            ),
            percentage=session.get(
                "percentage",
                0
            ),
            total_questions=session.get(
                "total_questions",
                len(QUESTIONS)
            )
        )

    email = session.get(
        "candidate_email",
        ""
    ).strip().lower()

    # -----------------------------------------------------
    # EXTRA DUPLICATE EMAIL PROTECTION
    # -----------------------------------------------------

    if email_already_used(email):

        session.clear()

        return render_template(
            "candidate.html",
            error="This email ID has already attended the examination."
        )

    # -----------------------------------------------------
    # START TIMER ONLY ON FIRST EXAM LOAD
    # -----------------------------------------------------

    if "exam_start_time" not in session:

        session["exam_start_time"] = time.time()

    start_time = session["exam_start_time"]

    elapsed_time = int(
        time.time() - start_time
    )

    remaining_seconds = max(
        0,
        EXAM_DURATION - elapsed_time
    )

    # -----------------------------------------------------
    # TIME ALREADY EXPIRED
    # -----------------------------------------------------

    if remaining_seconds <= 0:

        return render_template(
            "submitted.html",
            candidate_name=session.get(
                "candidate_name",
                ""
            ),
            candidate_email=session.get(
                "candidate_email",
                ""
            ),
            score=0,
            percentage=0,
            total_questions=len(QUESTIONS)
        )

    # -----------------------------------------------------
    # SHOW EXAM
    # -----------------------------------------------------

    return render_template(
        "exam.html",
        questions=QUESTIONS,
        remaining_seconds=remaining_seconds
    )


# =========================================================
# SUBMIT EXAM
# =========================================================

@app.route(
    "/submit",
    methods=["POST"]
)
def submit():

    # -----------------------------------------------------
    # CANDIDATE MUST HAVE STARTED EXAM
    # -----------------------------------------------------

    if "candidate_email" not in session:

        return redirect(
            url_for("candidate")
        )

    # -----------------------------------------------------
    # PREVENT DUPLICATE SUBMISSION
    # -----------------------------------------------------

    if session.get("exam_submitted"):

        return render_template(
            "submitted.html",
            candidate_name=session.get(
                "candidate_name",
                ""
            ),
            candidate_email=session.get(
                "candidate_email",
                ""
            ),
            score=session.get(
                "score",
                0
            ),
            percentage=session.get(
                "percentage",
                0
            ),
            total_questions=session.get(
                "total_questions",
                len(QUESTIONS)
            )
        )

    name = session.get(
        "candidate_name",
        ""
    )

    email = session.get(
        "candidate_email",
        ""
    ).strip().lower()

    # -----------------------------------------------------
    # CHECK EMAIL AGAIN
    # -----------------------------------------------------

    if email_already_used(email):

        session.clear()

        return render_template(
            "candidate.html",
            error="This email ID has already attended the examination."
        )

    # -----------------------------------------------------
    # CHECK EXAM TIMER
    # -----------------------------------------------------

    start_time = session.get(
        "exam_start_time"
    )

    if start_time is None:

        return redirect(
            url_for("candidate")
        )

    elapsed_time = int(
        time.time() - start_time
    )

    time_expired = (
        elapsed_time >= EXAM_DURATION
    )

    # -----------------------------------------------------
    # GET SUBMITTED ANSWERS
    # -----------------------------------------------------

    submitted_answers = {}

    for index in range(
        len(QUESTIONS)
    ):

        answer = request.form.get(
            f"question_{index}"
        )

        submitted_answers[
            str(index)
        ] = answer

    # -----------------------------------------------------
    # MANUAL SUBMISSION
    # -----------------------------------------------------

    if not time_expired:

        unanswered_questions = []

        for index in range(
            len(QUESTIONS)
        ):

            answer = submitted_answers.get(
                str(index)
            )

            if not answer:

                unanswered_questions.append(
                    index + 1
                )

        if unanswered_questions:

            remaining_seconds = max(
                0,
                EXAM_DURATION - elapsed_time
            )

            return render_template(
                "exam.html",
                questions=QUESTIONS,
                remaining_seconds=remaining_seconds,
                error=(
                    "Please attend all questions "
                    "before submitting the examination."
                )
            )

    # =====================================================
    # CALCULATE SCORE
    # =====================================================

    score = 0

    detailed_answers = []

    for index, question in enumerate(QUESTIONS):

        # -------------------------------------------------
        # HTML sends the OPTION INDEX
        #
        # Example:
        # option 0 = "27"
        # option 1 = "28"
        # option 2 = "29"
        # option 3 = "30"
        # -------------------------------------------------

        selected_answer_index = submitted_answers.get(
            str(index)
        )

        # -------------------------------------------------
        # Convert option index to actual option text
        # -------------------------------------------------

        selected_answer = None

        if selected_answer_index is not None:

            try:

                selected_answer = question["options"][
                    int(selected_answer_index)
                ]

            except (
                ValueError,
                IndexError
            ):

                selected_answer = None

        # -------------------------------------------------
        # CORRECT ANSWER FROM questions.py
        # -------------------------------------------------

        correct_answer = question.get(
            "answer"
        )

        # -------------------------------------------------
        # COMPARE ACTUAL ANSWER TEXT
        # -------------------------------------------------

        is_correct = (
            selected_answer == correct_answer
        )

        if is_correct:

            score += 1

        # -------------------------------------------------
        # ANSWER STATUS
        # -------------------------------------------------

        if selected_answer:

            status = "Answered"

        else:

            status = "Not Answered"

        # -------------------------------------------------
        # STORE DETAILED ANSWER
        # -------------------------------------------------

        detailed_answers.append({

            "question": question.get(
                "question"
            ),

            "selected_answer": selected_answer,

            "correct_answer": correct_answer,

            "is_correct": is_correct,

            "status": status

        })

    # =====================================================
    # CALCULATE PERCENTAGE
    # =====================================================

    total_questions = len(QUESTIONS)

    percentage = round(
        (
            score /
            total_questions
        ) * 100,
        2
    )

    # =====================================================
    # SAVE RESULT
    # =====================================================

    response_data = {

        "name": name,

        "email": email,

        "score": score,

        "total_questions": total_questions,

        "percentage": percentage,

        "submitted_at": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "answers": detailed_answers

    }

    save_response(
        response_data
    )

    # =====================================================
    # MARK EXAM AS SUBMITTED
    # =====================================================

    session["exam_submitted"] = True

    session["score"] = score

    session["percentage"] = percentage

    session["total_questions"] = total_questions

    # Timer no longer needed after submission
    session.pop(
        "exam_start_time",
        None
    )

    # =====================================================
    # SHOW RESULT PAGE
    # =====================================================

    return render_template(
        "submitted.html",

        candidate_name=name,

        candidate_email=email,

        score=score,

        percentage=percentage,

        total_questions=total_questions
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
