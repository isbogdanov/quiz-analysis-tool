import os
import sys
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.data_loader import DataLoader
from scripts.analyze_results import PerformanceAnalyzer


class QuizVisualizer:
    def __init__(self, analysis_data: dict, output_dir: str = "visualizations"):
        self.data = analysis_data
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams["figure.figsize"] = [12, 8]

    def save_plot(self, name: str):
        """Save the current plot with proper formatting"""
        plt.tight_layout()
        plt.savefig(self.output_dir / f"{name}.png", dpi=300, bbox_inches="tight")
        plt.close()

    def plot_proficiency_distribution(self):
        """Plot distribution of proficiency scores"""
        scores = [
            {
                "user": user_id,
                "Overall Proficiency": data["proficiency"]["overall_proficiency"],
                "Quiz Performance": data["proficiency"]["performance_score"],
                "Assessment Accuracy": data["proficiency"]["accuracy_score"],
                "Assessment Consistency": data["proficiency"]["consistency_score"],
            }
            for user_id, data in self.data.items()
        ]
        df = pd.DataFrame(scores)

        # Distribution plot
        plt.figure(figsize=(15, 10))

        # Overall distribution
        plt.subplot(2, 1, 1)
        sns.histplot(data=df, x="Overall Proficiency", bins=20)
        plt.title("Distribution of Overall Proficiency Scores")
        plt.xlabel("Proficiency Score")

        # Component comparison
        plt.subplot(2, 1, 2)
        df_melted = pd.melt(
            df,
            id_vars=["user"],
            value_vars=[
                "Quiz Performance",
                "Assessment Accuracy",
                "Assessment Consistency",
            ],
        )
        sns.boxplot(data=df_melted, x="variable", y="value")
        plt.title("Distribution of Proficiency Components")
        plt.xticks(rotation=45)

        self.save_plot("proficiency_distribution")

    def plot_assessment_accuracy(self):
        """Plot self-assessment accuracy patterns"""
        comparisons = []
        for user_id, data in self.data.items():
            for comp in data["comparison"]["by_category"]:
                comparisons.append(
                    {
                        "user": user_id,
                        "category": comp["category"],
                        "quiz_score": comp["quiz_normalized"],
                        "self_assessment": comp["self_normalized"],
                        "difference": comp["difference"],
                    }
                )
        df = pd.DataFrame(comparisons)

        plt.figure(figsize=(15, 10))

        # Scatter plot with perfect assessment line
        plt.subplot(2, 1, 1)

        # Add diagonal bands for accuracy zones
        plt.fill_between(
            [0, 1],
            [0.1, 1.1],
            [0, 1],
            alpha=0.1,
            color="red",
            label="Overestimation Zone",
        )
        plt.fill_between(
            [0, 1],
            [0, 1],
            [-0.1, 0.9],
            alpha=0.1,
            color="blue",
            label="Underestimation Zone",
        )
        plt.fill_between(
            [0, 1],
            [0.1, 1.1],
            [-0.1, 0.9],
            alpha=0.1,
            color="green",
            label="Accurate Zone",
        )

        # Plot points with category-based colors
        scatter = sns.scatterplot(
            data=df,
            x="quiz_score",
            y="self_assessment",
            hue="category",
            style="category",
            s=100,  # Larger points
            alpha=0.6,
        )

        # Add perfect assessment line
        plt.plot([0, 1], [0, 1], "k--", label="Perfect Assessment")

        plt.title("Self-Assessment vs Actual Performance by Category")
        plt.xlabel("Normalized Quiz Score (Actual Performance)")
        plt.ylabel("Normalized Self-Assessment Score")

        # Adjust legend
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)

        # Add explanatory text
        text = (
            "Each point represents one user's self-assessment\n"
            "vs actual performance in a specific category.\n\n"
            "Points above the line: Overestimation\n"
            "Points below the line: Underestimation\n"
            "Points near the line: Accurate assessment"
        )
        plt.text(
            1.05,
            0.5,
            text,
            transform=plt.gca().transAxes,
            bbox=dict(facecolor="white", alpha=0.8),
        )

        # Distribution of differences
        plt.subplot(2, 1, 2)
        sns.histplot(data=df, x="difference", bins=20)
        plt.axvline(x=0, color="k", linestyle="--", label="Perfect Assessment")
        plt.axvline(x=0.1, color="g", linestyle=":", label="Accuracy Threshold (+0.1)")
        plt.axvline(x=-0.1, color="g", linestyle=":", label="Accuracy Threshold (-0.1)")

        plt.title("Distribution of Assessment Differences")
        plt.xlabel("Difference (Quiz Score - Self Assessment)")
        plt.legend()

        # Add summary statistics
        stats_text = (
            f"Total Assessments: {len(df)}\n"
            f"Average Difference: {df['difference'].mean():.3f}\n"
            f"Std Dev: {df['difference'].std():.3f}\n"
            f"Accurate (±0.1): {(abs(df['difference']) <= 0.1).mean():.1%}\n"
            f"Overestimates: {(df['difference'] < -0.1).mean():.1%}\n"
            f"Underestimates: {(df['difference'] > 0.1).mean():.1%}"
        )
        plt.text(
            0.95,
            0.95,
            stats_text,
            transform=plt.gca().transAxes,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(facecolor="white", alpha=0.8),
        )

        self.save_plot("assessment_accuracy")

    def plot_category_performance(self):
        """Plot performance across categories"""
        category_scores = []
        for user_id, data in self.data.items():
            for score in data["mc_quiz"]["scores"]:
                category_scores.append(
                    {
                        "user": user_id,
                        "category": score["category"],
                        "percentage": score["percentage"],
                    }
                )
        df = pd.DataFrame(category_scores)

        plt.figure(figsize=(15, 10))
        sns.boxplot(data=df, x="category", y="percentage")
        plt.title("Performance Distribution by Category")
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Score Percentage")

        self.save_plot("category_performance")

    def plot_proficiency_correlation(self):
        """Plot correlation between components"""
        scores = [
            {
                "user": user_id,
                "proficiency": data["proficiency"]["overall_proficiency"],
                "performance": data["proficiency"]["performance_score"],
                "accuracy": data["proficiency"]["accuracy_score"],
                "consistency": data["proficiency"]["consistency_score"],
            }
            for user_id, data in self.data.items()
        ]
        df = pd.DataFrame(scores)

        plt.figure(figsize=(12, 10))
        sns.heatmap(
            df[["proficiency", "performance", "accuracy", "consistency"]].corr(),
            annot=True,
            cmap="coolwarm",
            center=0,
        )
        plt.title("Correlation between Proficiency Components")

        self.save_plot("proficiency_correlation")

    def plot_overall_results_distribution(self):
        """Plot distribution of overall quiz results"""
        # Collect all scores
        scores = [
            {
                "user": user_id,
                "percentage": data["total_score"]["percentage"],
                "points": data["total_score"]["points"],
                "possible": data["total_score"]["possible"],
            }
            for user_id, data in self.data.items()
        ]
        df = pd.DataFrame(scores)

        plt.figure(figsize=(15, 10))

        # Main histogram with KDE
        plt.subplot(2, 1, 1)
        sns.histplot(data=df, x="percentage", bins=20, kde=True)
        plt.axvline(
            df["percentage"].mean(),
            color="r",
            linestyle="--",
            label=f'Mean: {df["percentage"].mean():.1f}%',
        )
        plt.axvline(
            df["percentage"].median(),
            color="g",
            linestyle="--",
            label=f'Median: {df["percentage"].median():.1f}%',
        )

        # Add statistical annotations
        stats_text = (
            f'Mean: {df["percentage"].mean():.1f}%\n'
            f'Median: {df["percentage"].median():.1f}%\n'
            f'Std Dev: {df["percentage"].std():.1f}%\n'
            f'Min: {df["percentage"].min():.1f}%\n'
            f'Max: {df["percentage"].max():.1f}%'
        )
        plt.text(
            0.95,
            0.95,
            stats_text,
            transform=plt.gca().transAxes,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        plt.title("Distribution of Overall Quiz Scores")
        plt.xlabel("Score Percentage")
        plt.ylabel("Count")
        plt.legend()

        # Score ranges histogram
        plt.subplot(2, 1, 2)
        score_ranges = pd.cut(
            df["percentage"],
            bins=[0, 50, 60, 70, 80, 90, 100],
            labels=["0-50%", "51-60%", "61-70%", "71-80%", "81-90%", "91-100%"],
        )
        range_counts = score_ranges.value_counts().sort_index()

        sns.barplot(x=range_counts.index, y=range_counts.values)
        plt.title("Distribution by Score Ranges")
        plt.xlabel("Score Range")
        plt.ylabel("Number of Users")

        # Add count labels on bars
        for i, v in enumerate(range_counts.values):
            plt.text(i, v, str(v), ha="center", va="bottom")

        # Add percentage labels on bars
        total = len(df)
        for i, v in enumerate(range_counts.values):
            percentage = (v / total) * 100
            plt.text(
                i, v / 2, f"{percentage:.1f}%", ha="center", va="center", color="white"
            )

        self.save_plot("overall_results_distribution")


def main(data_dir="data", output_dir="visualizations", column_mappings=None):
    """Generate visualization plots
    Args:
        data_dir (str): Path to data directory
        output_dir (str): Path to output directory
        column_mappings (dict): Mapping of standard column names to actual names in files
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load and analyze data with column mappings
    loader = DataLoader(data_dir, column_mappings)
    raw_data = loader.load_all_data()

    analyzer = PerformanceAnalyzer(raw_data)
    analysis_results = analyzer.analyze_user_performance()

    # Generate visualizations
    visualizer = QuizVisualizer(analysis_results, output_dir)
    visualizer.plot_proficiency_distribution()
    visualizer.plot_assessment_accuracy()
    visualizer.plot_category_performance()
    visualizer.plot_proficiency_correlation()
    visualizer.plot_overall_results_distribution()


if __name__ == "__main__":
    main()
