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

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import shutil
from typing import Dict, Any
import matplotlib.pyplot as plt

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.data_loader import DataLoader
from .analyze_results import PerformanceAnalyzer
from .visualize_results import QuizVisualizer


def extract_user_number(user_id: str) -> int:
    """Extract numeric part from userID string"""
    # Find all digits in the string and join them
    number = "".join(filter(str.isdigit, user_id))
    return int(number) if number else 0


def generate_latex_table(formatted_data: dict) -> str:
    """Generate main results table as a longtable"""

    table = """
\\footnotesize
\\begin{longtable}{|l|c|c|c|c|c|c|}
\\caption{Individual Assessment Results} \\\\
\\hline
\\textbf{User ID} & \\textbf{Quiz Score} & \\textbf{Quiz} & \\textbf{Self-Assess.} & \\textbf{Accuracy} & \\textbf{Consistency} & \\textbf{Calc. Prof.} \\\\
\\textbf{} & \\textbf{(points)} & \\textbf{(\\%)} & \\textbf{(0-10)} & \\textbf{(0-100)} & \\textbf{(0-100)} & \\textbf{(0-100)} \\\\
\\hline
\\endfirsthead

\\multicolumn{7}{c}{\\tablename\\ \\thetable\\ -- Continued} \\\\
\\hline
\\textbf{User ID} & \\textbf{Quiz Score} & \\textbf{Quiz} & \\textbf{Self-Assess.} & \\textbf{Accuracy} & \\textbf{Consistency} & \\textbf{Calc. Prof.} \\\\
\\textbf{} & \\textbf{(points)} & \\textbf{(\\%)} & \\textbf{(0-10)} & \\textbf{(0-100)} & \\textbf{(0-100)} & \\textbf{(0-100)} \\\\
\\hline
\\endhead

\\hline
\\multicolumn{7}{|r|}{Continued on next page} \\\\
\\hline
\\endfoot

\\hline
\\endlastfoot
"""

    # Sort users by ID number
    sorted_users = sorted(
        formatted_data["user_responses"].keys(),
        key=lambda x: int("".join(filter(str.isdigit, x))),
    )

    for user_id in sorted_users:
        user_data = formatted_data["user_responses"][user_id]

        points_earned = user_data["score"]["earned"]
        points_possible = user_data["score"]["possible"]
        quiz_percentage = user_data["score"]["percentage"]

        metrics = user_data.get("metrics", {})
        avg_self_assessment = metrics.get("avg_self_assessment", "N/A")
        accuracy = metrics.get("accuracy", "N/A")
        consistency = metrics.get("consistency", "N/A")

        if accuracy != "N/A":
            calc_prof = (quiz_percentage * 0.7) + (float(accuracy) * 0.3)
        else:
            calc_prof = quiz_percentage

        if quiz_percentage >= 80:
            color = "green!70!black"
        elif quiz_percentage >= 60:
            color = "orange!70!black"
        else:
            color = "red!70!black"

        table += (
            f"{user_id} & "
            f"{points_earned}/{points_possible} & "
            f"\\textcolor{{{color}}}{{{quiz_percentage:.1f}}} & "
            f"{avg_self_assessment if isinstance(avg_self_assessment, str) else f'{avg_self_assessment:.1f}'} & "
            f"{accuracy if isinstance(accuracy, str) else f'{accuracy:.1f}'} & "
            f"{consistency if isinstance(consistency, str) else f'{consistency:.1f}'} & "
            f"{calc_prof:.1f} \\\\\n"
        )

    # Add explanatory notes after the table
    table += """\\end{longtable}

\\vspace{0.5em}

\\tiny
\\begin{itemize}[leftmargin=2em,itemsep=0pt]
    \\item \\textbf{Quiz Score} --- Points earned vs. total possible points
    \\item \\textbf{Quiz \\%} --- Percentage of total possible points
    \\item \\textbf{Self-Assess.} --- Average self-rated skill level (0-10)
    \\item \\textbf{Accuracy} --- How well self-assessment matches quiz performance (100 = perfect match)
    \\item \\textbf{Consistency} --- Consistency of self-assessment across categories (100 = perfectly consistent)
    \\item \\textbf{Calc. Prof.} --- Calculated proficiency (70\\% quiz + 30\\% accuracy)
    \\item Color coding: \\textcolor{green!70!black}{$\\geq$80\\%} (Good),
          \\textcolor{orange!70!black}{60--79\\%} (Needs Improvement),
          \\textcolor{red!70!black}{$<$60\\%} (Critical)
\\end{itemize}"""

    return table


def generate_category_performance_table(formatted_data: dict, raw_data: dict) -> str:
    """Generate table showing per-user performance in each category"""

    # Get categories from metadata
    categories = raw_data["metadata"]["categories"].keys()

    # Create abbreviations
    category_abbrev = {}
    for category in categories:
        if category == "no-category":
            continue  # Skip no-category
        else:
            # Take first letter of each word
            abbrev = "".join(word[0].upper() for word in category.split())
            category_abbrev[category] = abbrev

    # Start longtable
    table = """
\\footnotesize
\\begin{longtable}{|l|"""

    # Add column for each category
    table += "c|" * len(category_abbrev)
    table += "}\n"

    # Caption
    table += "\\caption{Individual Category Performance} \\\\\n"

    # Header
    header = "\\hline\n\\textbf{User ID}"
    for category, abbrev in category_abbrev.items():
        header += f" & \\textbf{{{abbrev}}}"
    header += " \\\\\n\\hline\\hline\n"

    # Add headers for first and subsequent pages
    table += header + "\\endfirsthead\n"
    table += f"\\multicolumn{{{len(category_abbrev) + 1}}}{{c}}{{\\tablename\\ \\thetable\\ -- Continued}} \\\\\n"
    table += header + "\\endhead\n"

    # Add footer for all but last page
    table += f"\\hline \\multicolumn{{{len(category_abbrev) + 1}}}{{|r|}}{{Continued on next page}} \\\\ \\hline\n"
    table += "\\endfoot\n"

    # Add footer for last page
    table += "\\hline\n\\endlastfoot\n"

    # Sort users
    sorted_users = sorted(
        formatted_data["user_responses"].keys(),
        key=lambda x: int("".join(filter(str.isdigit, x))),
    )

    # Add data rows
    for user_id in sorted_users:
        user_data = formatted_data["user_responses"][user_id]
        table += user_id

        # Calculate category scores
        category_scores = {}
        for category in category_abbrev.keys():
            points_earned = 0
            points_possible = 0

            # Look through all answers to find ones matching this category
            for q_id, answer in user_data["answers"].items():
                q_category = raw_data["questions"][q_id]["category"]
                if q_category == category:
                    points_earned += answer["points"]["earned"]
                    points_possible += answer["points"]["possible"]

            # Calculate percentage if possible
            if points_possible > 0:
                score = (points_earned / points_possible) * 100
                category_scores[category] = f"{score:.1f}"
            else:
                category_scores[category] = "--"

        # Add scores to table
        for category in category_abbrev.keys():
            score = category_scores.get(category, "--")
            # Add color based on score
            if score != "--":
                score_val = float(score)
                if score_val >= 80:
                    color = "green!70!black"
                elif score_val >= 60:
                    color = "orange!70!black"
                else:
                    color = "red!70!black"
                table += f" & \\textcolor{{{color}}}{{{score}}}"
            else:
                table += f" & {score}"

        table += " \\\\\n"

    # End longtable and add legend
    table += """\\end{longtable}

\\vspace{0.5em}
\\tiny
\\begin{itemize}[leftmargin=2em,itemsep=0pt]
    \\item Category abbreviations:
    \\begin{itemize}[leftmargin=1em,itemsep=0pt]"""

    for category, abbrev in category_abbrev.items():
        table += f"\n        \\item \\textbf{{{abbrev}}} --- {category}"

    table += """
    \\end{itemize}
    \\item Scores shown as percentages
    \\item Color coding: \\textcolor{green!70!black}{$\\geq$80\\%} (Good),
          \\textcolor{orange!70!black}{60--79\\%} (Needs Improvement),
          \\textcolor{red!70!black}{$<$60\\%} (Critical)
    \\item '--' indicates no questions in category
\\end{itemize}"""

    return table


def generate_category_summary_table(formatted_data: dict) -> str:
    """Generate summary statistics table for all quiz categories"""

    # Get all categories from questions data
    all_categories = set()
    for question in formatted_data["questions"].values():
        category = question.get("category", "no-category")
        if category != "no-category":
            all_categories.add(category)

    # Initialize statistics for each category
    stats = {
        cat: {
            "points_earned": 0,
            "points_possible": 0,
            "users_attempted": 0,
            "total_questions": 0,
            "worth": 0,
        }
        for cat in all_categories
    }

    # First pass: get total points possible and question count per category
    for question in formatted_data["questions"].values():
        category = question.get("category", "no-category")
        if category in stats:
            stats[category]["total_questions"] += 1
            stats[category]["worth"] += question.get("worth", 1)

    # Second pass: collect user performance data
    for user_data in formatted_data["user_responses"].values():
        category_points = {}

        # Calculate points per category for this user
        for q_id, answer_data in user_data["answers"].items():
            category = formatted_data["questions"][q_id].get("category", "no-category")
            if category in stats:
                if category not in category_points:
                    category_points[category] = {"earned": 0, "possible": 0}
                category_points[category]["earned"] += answer_data["points"]["earned"]
                category_points[category]["possible"] += answer_data["points"][
                    "possible"
                ]

        # Add to overall statistics
        for category, points in category_points.items():
            stats[category]["points_earned"] += points["earned"]
            stats[category]["points_possible"] += points["possible"]
            if points["possible"] > 0:
                stats[category]["users_attempted"] += 1

    # Calculate percentages
    for cat_stats in stats.values():
        if cat_stats["points_possible"] > 0:
            cat_stats["avg"] = (
                cat_stats["points_earned"] / cat_stats["points_possible"]
            ) * 100

    # Sort categories by average score
    sorted_cats = sorted(all_categories, key=lambda x: stats[x]["avg"], reverse=True)

    # Generate table
    table = """
\\begin{table}[H]
\\centering
\\caption{Category Performance Summary (All Quiz Categories)}
\\small
\\begin{tabular}{|l|c|c|c|c|}
\\hline
\\textbf{Category} & \\textbf{Score} & \\textbf{Points} & \\textbf{Questions} & \\textbf{Users} \\\\
\\textbf{} & \\textbf{\\%} & \\textbf{Earned/Total} & \\textbf{Count} & \\textbf{N} \\\\
\\hline\\hline
"""

    # Add rows for each category
    for cat in sorted_cats:
        s = stats[cat]
        # Color code the average score
        if s["avg"] >= 80:
            avg_color = "green!70!black"
        elif s["avg"] >= 60:
            avg_color = "orange!70!black"
        else:
            avg_color = "red!70!black"

        table += (
            f"{cat[:30]}{'...' if len(cat) > 30 else ''} & "
            f"\\textcolor{{{avg_color}}}{{{s['avg']:.1f}}} & "
            f"{s['points_earned']}/{s['points_possible']} & "
            f"{s['total_questions']} & "
            f"{s['users_attempted']} \\\\\n"
            "\\hline\n"
        )

    # Add notes
    table += """\\end{tabular}

\\vspace{0.5em}
\\begin{itemize}[leftmargin=2em,itemsep=0pt]
    \\item \\textbf{Score} --- Percentage of total possible points earned in category
    \\item \\textbf{Points} --- Total points earned vs. possible points
    \\item \\textbf{Questions} --- Number of questions in category
    \\item \\textbf{Users} --- Number of users who attempted questions in category
    \\item Color coding: \\textcolor{green!70!black}{$\\geq$80\\%} (Good),
          \\textcolor{orange!70!black}{60--79\\%} (Needs Improvement),
          \\textcolor{red!70!black}{$<$60\\%} (Critical)
\\end{itemize}
\\end{table}
"""

    return table


def generate_latex_document(formatted_data: dict, raw_data: dict) -> str:
    """Generate complete LaTeX document"""

    latex_doc = """\\documentclass[12pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{xcolor}
\\usepackage{float}
\\usepackage{enumitem}
\\usepackage{graphicx}
\\usepackage[margin=1in]{geometry}
\\usepackage{longtable}

\\begin{document}

\\title{Quiz Results Analysis}
\\author{Generated Report}
\\date{\\today}

\\maketitle

\\begin{figure}[H]
\\centering
\\includegraphics[width=0.8\\textwidth]{./visualizations/overall_results_distribution.png}
\\caption{Overall Results Distribution}
\\label{fig:overall-dist}
\\end{figure}

"""

    latex_doc += generate_latex_table(formatted_data)
    latex_doc += "\\clearpage\n"
    latex_doc += generate_category_performance_table(formatted_data, raw_data)
    latex_doc += "\\clearpage\n"
    latex_doc += generate_category_summary_table(formatted_data)
    latex_doc += "\\end{document}"

    return latex_doc


def calculate_self_assessment_metrics(user_data: dict, quiz_percentage: float) -> tuple:
    """Calculate average, accuracy, and consistency from self-assessment data"""
    if not user_data.get("self_assessment") or not user_data["self_assessment"].get(
        "scores"
    ):
        return "N/A", "N/A", "N/A"

    # Get scores from the correct path
    scores = user_data["self_assessment"]["scores"]
    if not scores:
        return "N/A", "N/A", "N/A"

    # Calculate average self-assessment
    values = [
        float(score) for score in scores.values() if isinstance(score, (int, float))
    ]
    if not values:
        return "N/A", "N/A", "N/A"

    avg_self = sum(values) / len(values)

    # Calculate accuracy (how well self-assessment matches performance)
    self_assess_pct = avg_self * 10  # Convert to 0-100 scale
    accuracy = 100 - min(100, abs(quiz_percentage - self_assess_pct))

    # Calculate consistency (variation in self-assessment scores)
    if len(values) > 1:
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance**0.5
        # Convert to 0-100 scale where lower std_dev means higher consistency
        consistency = 100 * (1 - min(1, std_dev / 5))  # 5 is half the scale
    else:
        consistency = "N/A"

    return avg_self, accuracy, consistency


def main(data_dir="data", output_dir="report", column_mappings=None):
    print("Starting report generation...")

    # Convert to Path objects
    data_dir = Path(data_dir)
    report_dir = Path(output_dir)
    report_dir.mkdir(exist_ok=True)

    # Create visualizations directory in report folder
    vis_dir = report_dir / "visualizations"
    vis_dir.mkdir(exist_ok=True)

    # Initialize DataLoader with column mappings
    print("Loading data...")
    loader = DataLoader(data_dir, column_mappings)
    raw_data = loader.load_all_data()

    # First analyze the data
    analyzer = PerformanceAnalyzer(raw_data)
    analysis_results = analyzer.analyze_user_performance()

    # Generate visualizations
    print("Generating visualizations...")
    visualizer = QuizVisualizer(analysis_results, str(vis_dir))
    visualizer.plot_proficiency_distribution()
    visualizer.plot_assessment_accuracy()
    visualizer.plot_category_performance()
    visualizer.plot_proficiency_correlation()
    visualizer.plot_overall_results_distribution()

    print("Formatting data...")
    formatted_data = {
        "questions": {},
        "user_responses": {},
        "metadata": {
            "total_questions": len(raw_data["questions"]),
            "total_users": len(raw_data["users"]),
            "max_possible_score": sum(
                q["worth"] for q in raw_data["questions"].values()
            ),
        },
    }

    # Format questions
    for q_id, q_data in raw_data["questions"].items():
        formatted_data["questions"][q_id] = {
            "text": q_data["text"],
            "category": q_data.get("category", "no-category"),
            "correct_answer": q_data.get("correct_answer", "no-answer"),
            "worth": q_data.get("worth", 1),
        }

    # Format user responses
    for user_id, user_data in raw_data["users"].items():
        # Calculate total points
        total_earned = sum(
            resp["points_earned"] for resp in user_data["responses"].values()
        )
        total_possible = sum(resp["worth"] for resp in user_data["responses"].values())

        # Calculate quiz percentage
        quiz_percentage = (
            (total_earned / total_possible * 100) if total_possible > 0 else 0
        )

        # Calculate self-assessment metrics
        avg_self, accuracy, consistency = calculate_self_assessment_metrics(
            user_data, quiz_percentage
        )

        formatted_data["user_responses"][user_id] = {
            "score": {
                "earned": total_earned,
                "possible": total_possible,
                "percentage": quiz_percentage,
            },
            "self_assessment": user_data.get("self_assessment", {}).get("scores", {}),
            "answers": {},
            "metrics": {
                "avg_self_assessment": avg_self,
                "accuracy": accuracy,
                "consistency": consistency,
            },
        }

        # Format individual answers
        for q_id, response in user_data["responses"].items():
            formatted_data["user_responses"][user_id]["answers"][q_id] = {
                "user_answer": response["answer"],
                "correct_answer": raw_data["questions"][q_id]["correct_answer"],
                "is_correct": response["is_correct"],
                "points": {
                    "earned": response["points_earned"],
                    "possible": response["worth"],
                },
            }

    print(
        f"Formatted data: {len(formatted_data['questions'])} questions, {len(formatted_data['user_responses'])} users"
    )

    # Generate LaTeX document
    print("Generating LaTeX document...")
    latex_content = generate_latex_document(formatted_data, raw_data)

    # Save to file
    tex_file = report_dir / "quiz_report.tex"
    print(f"Saving LaTeX to: {tex_file}")
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(latex_content)

    # Compile to PDF
    print("Compiling PDF...")
    import subprocess
    import os

    # Change to report directory for compilation
    original_dir = os.getcwd()
    os.chdir(report_dir)

    try:
        # Run pdflatex twice to resolve references
        for i in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "quiz_report.tex"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"\nError during PDF compilation (run {i+1}):")
                print(result.stderr)
                break

        if os.path.exists("quiz_report.pdf"):
            print(f"\nPDF generated successfully: {report_dir}/quiz_report.pdf")
        else:
            print("\nWarning: PDF file was not created!")

    finally:
        # Return to original directory
        os.chdir(original_dir)

    print("Report generation complete!")


if __name__ == "__main__":
    main()
