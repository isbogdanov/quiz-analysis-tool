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


import pandas as pd
from pathlib import Path
from typing import Dict, Any, Set


class DataLoader:
    def __init__(self, data_dir: str, column_mappings=None):
        """Initialize DataLoader
        Args:
            data_dir: Path to data directory
            column_mappings: Dictionary mapping standard column names to actual names in files
        """
        self.data_dir = Path(data_dir)
        # Default column mappings
        self.column_mappings = {
            "question": "question",
            "category": "category",
            "answer": "answer",
            "value": "value",
            "date_time": "date_time",
            "user_id": "user_id",
        }
        # Update with provided mappings if any
        if column_mappings:
            self.column_mappings.update(column_mappings)

        self.questions = {}
        self.quiz_categories = set()
        self.users = {}

    def load_all_data(self) -> dict:
        """Load and combine all data sources"""
        self._load_questions()
        self._load_responses()
        self._load_self_assessment()
        return self._combine_data()

    def _load_questions(self):
        """Load questions from CSV file"""
        df = pd.read_csv(self.data_dir / "questions.csv")

        # Rename columns according to mappings
        inverse_mappings = {v: k for k, v in self.column_mappings.items()}
        df = df.rename(columns=inverse_mappings)

        # Now we can use standard column names
        self.quiz_categories = set(df["category"].unique())

        # Convert to dictionary format
        self.questions = {}
        for _, row in df.iterrows():
            question_id = f"Q{len(self.questions) + 1}"
            self.questions[question_id] = {
                "text": row["question"],
                "category": row["category"],
                "correct_answer": row["answer"],
                "worth": int(row["value"]),
            }

    def _load_responses(self):
        """Load responses from CSV file"""
        df = pd.read_csv(self.data_dir / "results.csv")

        # Rename columns according to mappings
        inverse_mappings = {v: k for k, v in self.column_mappings.items()}
        df = df.rename(columns=inverse_mappings)

        # Check required columns
        required_cols = ["date_time", "user_id"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in results.csv: {missing_cols}")

        # Process each response
        for _, row in df.iterrows():
            user_id = row["user_id"]
            timestamp = row["date_time"]

            # Initialize user data if not exists
            if user_id not in self.users:
                self.users[user_id] = {"responses": {}, "self_assessment": None}

            # Process each question's response
            for q_id, question in self.questions.items():
                q_text = question["text"]
                if q_text in df.columns:
                    answer = row[q_text]
                    is_correct = answer == question["correct_answer"]
                    points = question["worth"] if is_correct else 0

                    self.users[user_id]["responses"][q_id] = {
                        "timestamp": timestamp,
                        "answer": answer,
                        "is_correct": is_correct,
                        "points_earned": points,
                        "worth": question["worth"],
                    }

    def _load_self_assessment(self):
        """Load self-assessment from CSV file"""
        try:
            df = pd.read_csv(self.data_dir / "self_assessment.csv")

            # Rename columns according to mappings
            inverse_mappings = {v: k for k, v in self.column_mappings.items()}
            df = df.rename(columns=inverse_mappings)

            # Check required columns
            required_cols = ["date_time", "user_id"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(
                    f"Missing required columns in self_assessment.csv: {missing_cols}"
                )

            # Process each assessment
            for _, row in df.iterrows():
                user_id = row["user_id"]
                timestamp = row["date_time"]

                if user_id in self.users:
                    scores = {}
                    for category in self.quiz_categories:
                        if category in df.columns:
                            scores[category] = float(row[category])

                    self.users[user_id]["self_assessment"] = {
                        "timestamp": timestamp,
                        "scores": scores,
                    }
        except FileNotFoundError:
            print("Warning: self_assessment.csv not found")

    def _get_categories(self) -> Dict[str, Dict[str, Any]]:
        """Calculate category statistics dynamically"""
        categories = {}

        # First get all categories from questions
        for q_data in self.questions.values():
            category = q_data["category"]
            if pd.isna(category):  # Skip NaN categories
                continue

            category = str(category)
            if category not in categories:
                categories[category] = {
                    "question_count": 0,
                    "total_points": 0,
                    "has_self_assessment": category in self._self_assessed_categories,
                    "self_assessment_max": (
                        self._max_self_assessment_score
                        if category in self._self_assessed_categories
                        else 0
                    ),
                }
            categories[category]["question_count"] += 1
            categories[category]["total_points"] += q_data["worth"]

        return categories

    def _combine_data(self):
        """Combine all loaded data into a single dictionary"""

        # Process user data to include scores
        for user_id, user_data in self.users.items():
            # Calculate total score
            total_points = 0
            total_possible = 0

            # Initialize category scores
            category_scores = {}

            # Calculate scores by category and total
            for q_id, response in user_data["responses"].items():
                category = self.questions[q_id]["category"]

                # Initialize category if not exists
                if category not in category_scores:
                    category_scores[category] = {
                        "points_earned": 0,
                        "points_possible": 0,
                    }

                # Add to category scores
                category_scores[category]["points_earned"] += response["points_earned"]
                category_scores[category]["points_possible"] += response["worth"]

                # Add to total scores
                total_points += response["points_earned"]
                total_possible += response["worth"]

            # Calculate normalized scores for each category
            for category, scores in category_scores.items():
                scores["normalized_score"] = (
                    scores["points_earned"] / scores["points_possible"]
                    if scores["points_possible"] > 0
                    else 0
                )

                # Add normalized self-assessment if available
                if (
                    user_data.get("self_assessment")
                    and user_data["self_assessment"].get("scores")
                    and category in user_data["self_assessment"]["scores"]
                ):
                    scores["normalized_self_assessment"] = (
                        float(user_data["self_assessment"]["scores"][category]) / 10
                    )

            # Add total score to user data
            user_data["total_score"] = {
                "points_earned": total_points,
                "points_possible": total_possible,
                "normalized_score": (
                    total_points / total_possible if total_possible > 0 else 0
                ),
            }

            # Add score by category
            user_data["score"] = {"by_category": category_scores}

        # Calculate metadata
        categories_metadata = {}
        for q_id, question in self.questions.items():
            category = question["category"]
            if category not in categories_metadata:
                categories_metadata[category] = {
                    "question_count": 0,
                    "total_points": 0,
                    "has_self_assessment": False,
                    "self_assessment_max": 0,
                }
            categories_metadata[category]["question_count"] += 1
            categories_metadata[category]["total_points"] += question["worth"]

        # Update self-assessment info in metadata
        self_assessment_categories = set()
        for user_data in self.users.values():
            if user_data.get("self_assessment") and user_data["self_assessment"].get(
                "scores"
            ):
                for category in user_data["self_assessment"]["scores"].keys():
                    self_assessment_categories.add(category)
                    if category in categories_metadata:
                        categories_metadata[category]["has_self_assessment"] = True
                        categories_metadata[category]["self_assessment_max"] = 10

        return {
            "questions": self.questions,
            "users": self.users,
            "metadata": {
                "total_questions": len(self.questions),
                "total_users": len(self.users),
                "total_points_possible": sum(
                    q["worth"] for q in self.questions.values()
                ),
                "categories": categories_metadata,
                "self_assessment": {
                    "categories": list(self_assessment_categories),
                    "max_score": 10,
                },
            },
        }

    def load_and_process_data(self):
        """Load and process all quiz data, ensuring all categories are included"""

        # First, collect all unique categories from quiz questions
        all_categories = set()
        quiz_data = {}  # Raw quiz data by category

        # Load raw quiz data and collect all categories
        for (
            user_id,
            user_responses,
        ) in self.responses.items():  # Assuming this is how we get raw data
            for question in user_responses:
                category = question["category"]
                all_categories.add(category)

                # Initialize category data structure if needed
                if category not in quiz_data:
                    quiz_data[category] = {"responses": [], "users": set()}

                # Store response and track user
                quiz_data[category]["responses"].append(
                    {"user_id": user_id, "is_correct": question["is_correct"]}
                )
                quiz_data[category]["users"].add(user_id)

        # Now process into our analysis format
        analysis = {}
        for user_id in self.responses.keys():
            analysis[user_id] = {
                "total_score": calculate_total_score(user_id),
                "comparison": {"by_category": []},
            }

            # Add data for ALL categories
            for (
                category
            ) in all_categories:  # Use all_categories instead of just compared ones
                user_responses = [
                    r
                    for r in quiz_data[category]["responses"]
                    if r["user_id"] == user_id
                ]

                if user_responses:  # If user attempted questions in this category
                    correct = sum(1 for r in user_responses if r["is_correct"])
                    total = len(user_responses)
                    quiz_normalized = correct / total
                else:
                    quiz_normalized = (
                        0  # Or we might want to use None or some other indicator
                    )

                # Always add category data, even if no responses
                analysis[user_id]["comparison"]["by_category"].append(
                    {"category": category, "quiz_normalized": quiz_normalized}
                )

        return analysis
