# Copyright 2024 Igor Bogdanov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
from datetime import datetime, timedelta
import random


def generate_sample_data(num_users=100):
    # Questions with corrected headers
    questions = [
        ["question", "category", "answer", "value"],
        [
            "What is the purpose of list comprehension in Python?",
            "Basic Python",
            "To create lists using compact syntax",
            "1",
        ],
        [
            "How do you handle exceptions in Python?",
            "Error Handling",
            "Using try-except blocks",
            "1",
        ],
        [
            "What is the difference between a list and tuple?",
            "Data Structures",
            "Lists are mutable while tuples are immutable",
            "1",
        ],
        [
            "How do you create a virtual environment in Python?",
            "Development Tools",
            "Using python -m venv command",
            "1",
        ],
        [
            "What is the purpose of __init__ method in Python classes?",
            "OOP Concepts",
            "To initialize object attributes",
            "2",
        ],
        [
            "How do you import modules in Python?",
            "Basic Python",
            "Using the import statement",
            "2",
        ],
        [
            "What is the purpose of decorators in Python?",
            "Advanced Python",
            "To modify function behavior without changing code",
            "2",
        ],
        [
            "How do you read files in Python?",
            "File Operations",
            "Using the open() function with appropriate mode",
            "2",
        ],
        [
            "What is the difference between append and extend in lists?",
            "Data Structures",
            "Append adds one element while extend adds multiple elements",
            "3",
        ],
        [
            "What is the purpose of context managers in Python?",
            "Advanced Python",
            "To ensure proper resource management",
            "3",
        ],
    ]

    # Generate results for specified number of users with more realistic patterns
    base_time = datetime(2024, 3, 15, 9, 0)
    results = []
    self_assessments = []

    # Headers with corrected column names
    results.append(["date_time", "user_id"] + [q[0] for q in questions[1:]])
    self_assessments.append(
        [
            "date_time",
            "user_id",
            "Basic Python",
            "Error Handling",
            "Data Structures",
            "OOP Concepts",
            "Advanced Python",
            "File Operations",
            "Development Tools",
        ]
    )

    # Generate user data with correlated performance
    for i in range(1, num_users + 1):
        timestamp = base_time + timedelta(minutes=15 * i)
        user_id = f"user{i}"

        # Generate user skill level (1-10)
        skill_level = random.randint(1, 10)

        # Generate quiz responses based on skill level
        responses = [timestamp.strftime("%Y-%m-%d %H:%M"), user_id]
        for q in questions[1:]:
            # Higher skill level = higher chance of correct answer
            if random.random() < (0.4 + (skill_level * 0.06)):
                responses.append(q[2])
            else:
                responses.append("Wrong Answer")
        results.append(responses)

        # Generate correlated self-assessment scores
        self_assessment = [timestamp.strftime("%Y-%m-%d %H:%M"), user_id]
        base_score = min(10, max(1, skill_level + random.randint(-2, 2)))
        for _ in range(7):
            # Vary around base score with some randomness
            score = min(10, max(1, base_score + random.randint(-1, 1)))
            self_assessment.append(str(score))
        self_assessments.append(self_assessment)

    return questions, results, self_assessments
