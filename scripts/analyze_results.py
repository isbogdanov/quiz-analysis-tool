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

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.data_loader import DataLoader
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from pathlib import Path


class PerformanceAnalyzer:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.self_assessed_categories = self.data["metadata"]["self_assessment"][
            "categories"
        ]

    def calculate_proficiency_score(
        self, user_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate proficiency score with detailed consistency calculation"""
        # Quiz performance score (0-100)
        performance_score = user_data["total_score"]["percentage"]

        if user_data["comparison"]["by_category"]:
            # Get differences for each category
            differences = [
                c["difference"] for c in user_data["comparison"]["by_category"]
            ]

            # Assessment accuracy (0-100)
            avg_abs_diff = sum(abs(d) for d in differences) / len(differences)
            accuracy_score = (1 - avg_abs_diff) * 100

            # Consistency score (0-100)
            # Lower std_dev means more consistent assessment
            std_dev = np.std(differences) if len(differences) > 1 else 0
            consistency_score = (1 - min(std_dev, 1)) * 100

            proficiency_score = (
                0.60 * performance_score
                + 0.20 * accuracy_score
                + 0.20 * consistency_score
            )

            return {
                "overall_proficiency": round(proficiency_score, 1),
                "performance_score": round(performance_score, 1),
                "accuracy_score": round(accuracy_score, 1),
                "consistency_score": round(consistency_score, 1),
                "differences": differences,
                "std_dev": std_dev,
            }

    def analyze_user_performance(self) -> Dict[str, Dict[str, Any]]:
        """Analyze each user's performance in three separate aspects"""
        analysis = {}

        for user_id, user_data in self.data["users"].items():
            mc_scores = []
            self_scores = []
            comparisons = []

            # Get total quiz score
            total_score = user_data["total_score"]

            # Analyze each category
            for category, scores in user_data["score"]["by_category"].items():
                # Skip categories with no questions
                if scores["points_possible"] > 0:
                    mc_scores.append(
                        {
                            "category": category,
                            "points": scores["points_earned"],
                            "possible": scores["points_possible"],
                            "percentage": round(
                                scores["points_earned"]
                                / scores["points_possible"]
                                * 100,
                                1,
                            ),
                        }
                    )

                # Only include self-assessment for relevant categories
                if category in self.self_assessed_categories:
                    if (
                        scores["points_possible"] > 0
                    ):  # Skip categories without questions
                        # Self Assessment
                        self_score = user_data["self_assessment"]["scores"].get(
                            category, 0
                        )
                        self_scores.append(
                            {
                                "category": category,
                                "score": self_score,
                                "out_of": self.data["metadata"]["self_assessment"][
                                    "max_score"
                                ],
                            }
                        )

                        # Comparison (using normalized scores)
                        comparisons.append(
                            {
                                "category": category,
                                "quiz_normalized": scores["normalized_score"],
                                "self_normalized": scores["normalized_self_assessment"],
                                "difference": scores["normalized_score"]
                                - scores["normalized_self_assessment"],
                            }
                        )

            # Calculate total percentage only if there are possible points
            total_percentage = (
                round(
                    total_score["points_earned"] / total_score["points_possible"] * 100,
                    1,
                )
                if total_score["points_possible"] > 0
                else 0
            )

            user_analysis = {
                "total_score": {
                    "points": total_score["points_earned"],
                    "possible": total_score["points_possible"],
                    "percentage": total_percentage,
                },
                "mc_quiz": {
                    "scores": mc_scores,
                    "total_points": sum(s["points"] for s in mc_scores),
                    "total_possible": sum(s["possible"] for s in mc_scores),
                },
                "self_assessment": {
                    "scores": self_scores,
                    "average": (
                        round(
                            sum(s["score"] for s in self_scores) / len(self_scores), 1
                        )
                        if self_scores
                        else 0
                    ),
                },
                "comparison": {
                    "by_category": comparisons,
                    "average_difference": (
                        round(
                            sum(c["difference"] for c in comparisons)
                            / len(comparisons),
                            3,
                        )
                        if comparisons
                        else 0
                    ),
                    "accurate_count": sum(
                        1 for c in comparisons if abs(c["difference"]) < 0.1
                    ),
                    "overestimate_count": sum(
                        1 for c in comparisons if c["difference"] < -0.1
                    ),
                    "underestimate_count": sum(
                        1 for c in comparisons if c["difference"] > 0.1
                    ),
                },
            }

            # Add proficiency scores
            user_analysis["proficiency"] = self.calculate_proficiency_score(
                user_analysis
            )
            analysis[user_id] = user_analysis

        return analysis

    def get_overall_statistics(
        self, analysis: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall statistics across all users and categories"""
        all_scores = []
        user_self_assessment_averages = []
        user_comparison_stats = []  # Store per-user comparison statistics

        for user_data in analysis.values():
            # Collect all MC scores
            all_scores.extend(
                [
                    {
                        "points": s["points"],
                        "possible": s["possible"],
                        "percentage": s["percentage"],
                    }
                    for s in user_data["mc_quiz"]["scores"]
                ]
            )

            # Store user's average self-assessment
            if user_data["self_assessment"]["scores"]:
                user_self_assessment_averages.append(
                    user_data["self_assessment"]["average"]
                )

            # Calculate user's comparison statistics
            if user_data["comparison"]["by_category"]:
                user_comparison_stats.append(
                    {
                        "average_difference": user_data["comparison"][
                            "average_difference"
                        ],
                        "accurate_ratio": user_data["comparison"]["accurate_count"]
                        / len(user_data["comparison"]["by_category"]),
                        "overestimate_ratio": user_data["comparison"][
                            "overestimate_count"
                        ]
                        / len(user_data["comparison"]["by_category"]),
                        "underestimate_ratio": user_data["comparison"][
                            "underestimate_count"
                        ]
                        / len(user_data["comparison"]["by_category"]),
                    }
                )

        # Calculate average ratios across users
        num_users = len(user_comparison_stats)
        comparison_stats = {
            "average_difference": round(
                sum(stats["average_difference"] for stats in user_comparison_stats)
                / num_users,
                3,
            ),
            "accurate_ratio": round(
                sum(stats["accurate_ratio"] for stats in user_comparison_stats)
                / num_users,
                3,
            ),
            "overestimate_ratio": round(
                sum(stats["overestimate_ratio"] for stats in user_comparison_stats)
                / num_users,
                3,
            ),
            "underestimate_ratio": round(
                sum(stats["underestimate_ratio"] for stats in user_comparison_stats)
                / num_users,
                3,
            ),
        }

        return {
            "quiz_performance": {
                "total_points": sum(s["points"] for s in all_scores),
                "total_possible": sum(s["possible"] for s in all_scores),
                "average_percentage": (
                    round(sum(s["percentage"] for s in all_scores) / len(all_scores), 1)
                    if all_scores
                    else 0
                ),
            },
            "self_assessment": {
                "average_score": (
                    round(
                        sum(user_self_assessment_averages)
                        / len(user_self_assessment_averages),
                        1,
                    )
                    if user_self_assessment_averages
                    else 0
                ),
                "total_users": len(user_self_assessment_averages),
                "min_average": (
                    round(min(user_self_assessment_averages), 1)
                    if user_self_assessment_averages
                    else 0
                ),
                "max_average": (
                    round(max(user_self_assessment_averages), 1)
                    if user_self_assessment_averages
                    else 0
                ),
            },
            "comparison": {
                "total_users": num_users,
                "average_difference": comparison_stats["average_difference"],
                "accurate_ratio": comparison_stats["accurate_ratio"],
                "overestimate_ratio": comparison_stats["overestimate_ratio"],
                "underestimate_ratio": comparison_stats["underestimate_ratio"],
            },
        }


def main():
    # Load data
    loader = DataLoader("data")
    data = loader.load_all_data()

    # Initialize analyzer and get analysis
    analyzer = PerformanceAnalyzer(data)
    analysis = analyzer.analyze_user_performance()
    overall_stats = analyzer.get_overall_statistics(analysis)

    # Print results
    print("\nFigma Quiz Analysis")
    print("==================")

    print("\nOVERALL STATISTICS")
    print("-----------------")
    print(f"Total Quiz Performance:")
    print(
        f"  Points: {overall_stats['quiz_performance']['total_points']}/"
        f"{overall_stats['quiz_performance']['total_possible']}"
    )
    print(
        f"  Average Category Score: {overall_stats['quiz_performance']['average_percentage']}%"
    )

    print(f"\nSelf-Assessment Overview:")
    print(
        f"  Average User Score: {overall_stats['self_assessment']['average_score']}/10"
    )
    print(
        f"  Range: {overall_stats['self_assessment']['min_average']} - "
        f"{overall_stats['self_assessment']['max_average']}"
    )
    print(f"  Total Users: {overall_stats['self_assessment']['total_users']}")

    print(f"\nOverall Assessment Accuracy (averaged across users):")
    print(f"  Total Users: {overall_stats['comparison']['total_users']}")
    print(f"  Average Difference: {overall_stats['comparison']['average_difference']}")
    print(
        f"  Accurate Assessments: {overall_stats['comparison']['accurate_ratio']:.1%}"
    )
    print(f"  Overestimates: {overall_stats['comparison']['overestimate_ratio']:.1%}")
    print(f"  Underestimates: {overall_stats['comparison']['underestimate_ratio']:.1%}")

    print("\nPER-USER ANALYSIS")
    print("----------------")

    for user_id, results in analysis.items():
        print(f"\nUSER: {user_id}")
        print("=" * (len(user_id) + 6))

        print("\nPROFICIENCY SCORES")
        print("-----------------")
        print(
            f"Overall Proficiency: {results['proficiency']['overall_proficiency']}/100"
        )
        print("Components:")
        print(
            f"  Quiz Performance (60%): {results['proficiency']['performance_score']}/100"
        )
        print(
            f"  Assessment Accuracy (20%): {results['proficiency']['accuracy_score']}/100"
        )
        print(
            f"  Assessment Consistency (20%): {results['proficiency']['consistency_score']}/100"
        )

        print("\n1. Overall Quiz Performance")
        print("-------------------------")
        print(
            f"Total Score: {results['total_score']['points']}/{results['total_score']['possible']} "
            f"({results['total_score']['percentage']}%)"
        )

        print("\n2. Category Breakdown")
        print("-------------------")
        for score in results["mc_quiz"]["scores"]:
            print(
                f"  {score['category']}: {score['points']}/{score['possible']} ({score['percentage']}%)"
            )

        print("\n3. Self-Assessment Analysis")
        print("-------------------------")
        if results["self_assessment"]["scores"]:
            print(
                f"Average self-assessment: {results['self_assessment']['average']}/10"
            )
            print("\nBy Category:")
            for score in results["self_assessment"]["scores"]:
                print(f"  {score['category']}: {score['score']}/10")
        else:
            print("No self-assessed categories")

        print("\n4. Self-Assessment vs Performance")
        print("-------------------------------")
        if results["comparison"]["by_category"]:
            for comp in results["comparison"]["by_category"]:
                print(f"\n  {comp['category']}:")
                print(f"    Quiz Score (normalized): {comp['quiz_normalized']:.3f}")
                print(
                    f"    Self-Assessment (normalized): {comp['self_normalized']:.3f}"
                )
                print(f"    Difference: {comp['difference']:.3f}")

                # Add interpretation
                if abs(comp["difference"]) < 0.1:
                    print("    Interpretation: Accurate self-assessment")
                elif comp["difference"] > 0:
                    print("    Interpretation: Underestimated skills")
                else:
                    print("    Interpretation: Overestimated skills")

            print(f"\nOverall Assessment Accuracy:")
            print(
                f"  Average difference: {results['comparison']['average_difference']}"
            )
            print(f"  Accurate assessments: {results['comparison']['accurate_count']}")
            print(f"  Overestimates: {results['comparison']['overestimate_count']}")
            print(f"  Underestimates: {results['comparison']['underestimate_count']}")
        else:
            print("No comparison data available")

        print("\n" + "-" * 50)


if __name__ == "__main__":
    main()
