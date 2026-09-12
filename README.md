# MCQ Test Application

## Assignment

A web-based MCQ examination application developed using Python and Flask.

## Requirements Implemented

* Company logo and examination instructions
* Candidate name and email input
* 40 multiple-choice questions
* 4 options for each question
* 40-minute examination duration
* Visible countdown timer
* Automatic submission when the timer ends
* Laptop camera must remain active during the examination
* Submit button enabled only when the camera is active
* Validation to ensure all 40 questions are answered
* Candidate answers stored after submission
* Server-side time-limit validation
* No negative marking

## Technologies Used

* Python
* Flask
* HTML
* CSS
* JavaScript
* JSON

## Folder Structure

MCQ_Test_Application/
│
├── app.py
├── questions.py
├── README.md
│
├── data/
│   └── responses.json
│
├── static/
│   └── images/
│       └── tts_logo.png
│
└── templates/
    ├── instructions.html
    ├── candidate.html
    ├── exam.html
    └── submitted.html

## How to Run

### 1. Activate the environment

```bash
conda activate mcqapp
```

### 2. Open the assignment folder

```bash
cd D:\MCQ_Test_Application
```

### 3. Run the application

```bash
python app.py
```

### 4. Open in the browser

Open:

```text
http://127.0.0.1:5000
```

## Answer Storage

Submitted candidate details and answers are stored in:

```text
data/responses.json
```

The current version uses JSON storage. The application can be extended to use a database in the future if required.

## Note

Camera permission is required for the examination. Please allow camera access when prompted by the browser.
