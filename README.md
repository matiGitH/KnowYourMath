# Knowyourmath

#### Video presentation: [URL](https://youtu.be/hDoQNz_iU2w)

#### Description

Knowyourmath is a web application designed to help independent and curious students improve their math skills across various topics. It evaluates the user's knowledge through adaptive exercises that adjust to their current level and then identifies what concepts they have mastered and which ones need reinforcement. 
Based on the results, the platform recommends a curated list of study materials tailored to the user's weak points. It is specially suited for self-taught students like myself, offering a complete and guided experience: helping users locate where they stand and clearly showing what steps come next.

### How it works

The core of the system is an **adaptive test algorithm**. It estimates the user's level on a scale from 1 to 100. To achieve this, for each level, it predicts -based on the user's previous responses- whether they are likely to succeed, and selects the newt question accordingly. The goal is to gather as much information as possible by choosing the questions with the greatest uncertainty. After every submission, the algorithm looks for a point where the user's performance clearly drops. Once this point is found, it asks a few additional questions around the estimated level to collect extra valuable data before presenting a comprehensive review. The algorithm also includes some randomness and probablity to better reflect the human performance variability.

Once the test is completed, users receive a **detailed analysis** showing:
- An estimate of their overall level
- A graph of performance vs. difficulty, estimated by the system
- A breakdown of their strengths and weaknesses
- Tailored learning resources for each subtopic


## Project Structure

Here’s a breakdown of the key files and what they do:

- `app.py`: The main Flask application file. It handles routing, session management, data manipulation and connection between frontend and backend (supabase).
- `helpers.py`: Contains core logic functions, including the adaptive algorithm, level estimation updates, and other indespensable functions for the project.
- `requirements.txt`: Lists all the Python dependencies required to run the app.
- `.env`: A file storing API keys and sensitive credentials (not included in the repo for security).
- `templates/`: Contains all HTML files for different routes (`index.html`, `login.html`, `quiz.html`, etc.). These templates are rendered by Flask.
- `static/css`: Contains all css files.
- `static/js`: Contains js files that manage interactivity on the frontend.

---

## Built with

- **Python** with **Flask** for the backend and routing
- **HTML, CSS, JavaScript** for the frontend
- **PostgreSQL** for storing user data, questions and study material in well-organized tables on Supabase.

### Supabase

This algorithm essentially needs data to feed from in order to test the user's level (via stored questions), recommend precisely curated study material (via stored material alongside its details) and remember user's data and progress. To accomplish these goals, I decided to use Supabase, considering it allows global interaction server-side.

#### Database Structure

- `questions`: Stores all questions along with their corresponding details, such as difficulty, category, type and subject.
- `question_types`: Contains one row per type of question (e.g., numeric input, multiple choice, multiple answers, fill-in-the-blank)
- `categories`: lists all available categories used to classify questions, study materials, and tests.
- `subjects`:  Lists all math subjects used to classify questions and study materials.
- `materials`: Stores study materials along with their relevant details, including category and the level range they are intended for.
- `subjects_materials`: Defines a many-to-many relationship between subjects and materials.
- `answers`: Contains the question's answers for each question, linked via the question ID.
- `user_answers`: Contains user's results for each question attempted during a given test. Records are cleared once the test is completed.
- `review_data`: Saves all data necessary to render the review.html page after a test is completed.
- `tests`: Stores all test sessions. Incomplete tests are automatically cleaned by logic in index.html.
- `users`: Stores user sign-up credentials and basic information.

## Limitations and Future Improvements

### Inconsistent input management

One of the main limitations of the current algorithm is its difficulty in handling inconsistent user responses. For instance, if a user correctly answers a high-level question but then consistently fails easier ones, the system may struggle to adapt its assumptions. Once it forms an estimation, it can be relatively rigid in updating or correcting it, as the question choosing logic relies on those estimations. This can sometimes prevent the level estimation from working properly.

### Level-estimation logic

In addition, the level detection logic is not as sophisticated as necessary. It relies on identifying a steep performance drop between two groups of levels -expecting an 80% to 20% accuracy shift across a 6-level window. While this works in many cases, it doesn’t always reflect how people actually perform, especially if their knowledge on different topics varies considerably.

### question's level accuracy

Another important issue is that the question's levels have not been validated. Since the app hasn't yet been tested by a large group of people, the level labels may not accurately reflect the real difficulty each question presents.

### Limited content

It is important to note that the accessible content is very limited. At the moment, the database only includes questions and study materials for **trigonometry**. Other topics have not yet been added, although the app's structure is fully prepared to support new categories. Populating the database with all the necessary content remains an important goal for the near future. I plan to expand it gradually over the coming months as I continue my own studies, aiming for both breadth and balance in content coverage.

## Installation

To run the app locally, follow these steps:

```bash
git clone https://github.com/matiGitH/mathtest_repo.git
cd mathtest_repo
pip install -r requirements.txt
flask run

