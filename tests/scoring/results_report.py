"""
Results Report Generator Module

Provides report generation utilities for scoring results.
"""

import json
from typing import Dict, List, Union, Optional, Any
from datetime import datetime


class ResultsReportGenerator:
    """
    Report generator for scoring results.

    Generates text, JSON, and HTML reports from scoring results.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize report generator.

        Args:
            config: Optional configuration dictionary
        """
        self._config = config or {}

    def generate_text_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate text report.

        Args:
            results: Single result or list of results

        Returns:
            Formatted text report
        """
        if isinstance(results, list):
            return self._generate_batch_text_report(results)
        else:
            return self._generate_single_text_report(results)

    def _generate_single_text_report(self, result: Dict[str, Any]) -> str:
        """Generate text report for single result."""
        lines = [
            "=" * 60,
            f"Scoring Report: {result.get('test_name', 'Unknown')}",
            "=" * 60,
            "",
            f"Total Score: {result.get('total_score', 0):.2f} / 1.00",
            f"Grade: {result.get('grade', 'N/A')}",
            "",
            "Component Scores:",
            "-" * 40
        ]

        for component in result.get("components", []):
            lines.append(
                f"  {component['name']:15} {component['score']:6.2f} "
                f"(weight: {component['weight']:.2f})"
            )

        lines.extend([
            "",
            f"Execution Time: {result.get('execution_time', 0):.4f} seconds",
            f"Memory Used: {result.get('memory_used', 0):,} bytes",
            "",
            "=" * 60
        ])

        return "\n".join(lines)

    def _generate_batch_text_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate text report for batch of results."""
        lines = [
            "=" * 60,
            "Batch Scoring Report",
            "=" * 60,
            f"Total Tests: {len(results)}",
            "",
            "-" * 60,
            "Individual Results:",
            "-" * 60
        ]

        total_score = 0.0
        for result in results:
            score = result.get("total_score", 0)
            total_score += score

            lines.append(
                f"  {result.get('test_name', 'Unknown'):30} "
                f"Score: {score:6.2f}  Grade: {result.get('grade', 'N/A')}"
            )

        lines.extend([
            "-" * 60,
            "Summary:",
            f"  Average Score: {total_score / len(results):.2f}",
            f"  Total Score: {total_score:.2f}",
            "=" * 60
        ])

        return "\n".join(lines)

    def generate_json_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate JSON report.

        Args:
            results: Single result or list of results

        Returns:
            JSON string
        """
        if isinstance(results, list):
            return json.dumps(results, indent=2)
        else:
            return json.dumps(results, indent=2)

    def generate_html_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate HTML report.

        Args:
            results: Single result or list of results

        Returns:
            HTML string
        """
        if isinstance(results, list):
            return self._generate_batch_html_report(results)
        else:
            return self._generate_single_html_report(results)

    def _generate_single_html_report(self, result: Dict[str, Any]) -> str:
        """Generate HTML report for single result."""
        score = result.get("total_score", 0)
        grade = result.get("grade", "N/A")

        # Color based on grade
        colors = {
            "A": "#4CAF50",
            "B": "#8BC34A",
            "C": "#FFC107",
            "D": "#FF9800",
            "F": "#F44336"
        }
        color = colors.get(grade, "#9E9E9E")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Scoring Report: {result.get('test_name', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .score {{ font-size: 24px; color: {color}; }}
        .grade {{ font-size: 32px; font-weight: bold; color: {color}; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Scoring Report: {result.get('test_name', 'Unknown')}</h1>
    </div>
    <div class="score">
        Total Score: {score:.2f} / 1.00
    </div>
    <div class="grade">
        Grade: {grade}
    </div>
    <table>
        <tr><th>Component</th><th>Score</th><th>Weight</th></tr>
"""

        for component in result.get("components", []):
            html += f"""        <tr>
            <td>{component['name']}</td>
            <td>{component['score']:.2f}</td>
            <td>{component['weight']:.2f}</td>
        </tr>"""

        html += f"""    </table>
    <p>
        Execution Time: {result.get('execution_time', 0):.4f} seconds<br>
        Memory Used: {result.get('memory_used', 0):,} bytes
    </p>
</body>
</html>"""

        return html

    def _generate_batch_html_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML report for batch of results."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Batch Scoring Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .report {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .score {{ font-size: 24px; color: #4CAF50; }}
        .grade {{ font-size: 32px; font-weight: bold; color: #4CAF50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Batch Scoring Report</h1>
    <p>Total Tests: {total_tests}</p>
""".format(total_tests=len(results))

        for result in results:
            score = result.get("total_score", 0)
            grade = result.get("grade", "N/A")

            # Color based on grade
            colors = {
                "A": "#4CAF50",
                "B": "#8BC34A",
                "C": "#FFC107",
                "D": "#FF9800",
                "F": "#F44336"
            }
            color = colors.get(grade, "#9E9E9E")

            html += f"""
    <div class="report">
        <div class="header">
            <h2>{result.get('test_name', 'Unknown')}</h2>
        </div>
        <div class="score">
            Total Score: {score:.2f} / 1.00
        </div>
        <div class="grade">
            Grade: {grade}
        </div>
        <table>
            <tr><th>Component</th><th>Score</th><th>Weight</th></tr>
"""

            for component in result.get("components", []):
                html += f"""            <tr>
                <td>{component['name']}</td>
                <td>{component['score']:.2f}</td>
                <td>{component['weight']:.2f}</td>
            </tr>"""

            html += f"""        </table>
        <p>
            Execution Time: {result.get('execution_time', 0):.4f} seconds<br>
            Memory Used: {result.get('memory_used', 0):,} bytes
        </p>
    </div>
"""

        html += """
</body>
</html>"""

        return html

    def generate_summary_report(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate summary report.

        Args:
            results: List of result dictionaries

        Returns:
            Summary string
        """
        if not results:
            return "No results to summarize."

        if isinstance(results, dict):
            results = [results]

        total_score = sum(r.get("total_score", 0) for r in results)
        avg_score = total_score / len(results)

        grade_distribution = {}
        for result in results:
            grade = result.get("grade", "Unknown")
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        summary = f"""
Summary Report
==============

Total Tests: {len(results)}
Average Score: {avg_score:.2f}

Grade Distribution:
"""

        for grade in ["A", "B", "C", "D", "F"]:
            count = grade_distribution.get(grade, 0)
            summary += f"  {grade}: {count}\n"

        return summary.strip()

    def generate_markdown_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> str:
        """
        Generate Markdown report.

        Args:
            results: Single result or list of results

        Returns:
            Markdown string
        """
        if isinstance(results, list):
            return self._generate_batch_markdown_report(results)
        else:
            return self._generate_single_markdown_report(results)

    def _generate_single_markdown_report(self, result: Dict[str, Any]) -> str:
        """Generate Markdown report for single result."""
        lines = [
            f"# Scoring Report: {result.get('test_name', 'Unknown')}",
            "",
            f"**Total Score:** {result.get('total_score', 0):.2f} / 1.00",
            f"**Grade:** {result.get('grade', 'N/A')}",
            "",
            "## Component Scores",
            ""
        ]

        for component in result.get("components", []):
            lines.append(
                f"- {component['name']}: {component['score']:.2f} "
                f"(weight: {component['weight']:.2f})"
            )

        lines.extend([
            "",
            f"**Execution Time:** {result.get('execution_time', 0):.4f} seconds",
            f"**Memory Used:** {result.get('memory_used', 0):,} bytes",
            ""
        ])

        return "\n".join(lines)

    def _generate_batch_markdown_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate Markdown report for batch of results."""
        lines = [
            "# Batch Scoring Report",
            "",
            f"Total Tests: {len(results)}",
            "",
            "## Individual Results",
            ""
        ]

        total_score = 0.0
        for result in results:
            score = result.get("total_score", 0)
            total_score += score

            lines.append(
                f"- {result.get('test_name', 'Unknown')}: "
                f"Score: {score:.2f}, Grade: {result.get('grade', 'N/A')}"
            )

        lines.extend([
            "",
            "## Summary",
            "",
            f"- Average Score: {total_score / len(results):.2f}",
            f"- Total Score: {total_score:.2f}",
            ""
        ])

        return "\n".join(lines)

    def export_report(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]],
        format: str = "text",
        filename: Optional[str] = None
    ) -> str:
        """
        Export report in specified format.

        Args:
            results: Results to export
            format: Export format ("text", "json", "html", "markdown")
            filename: Optional filename for HTML export

        Returns:
            Exported report string
        """
        formats = {
            "text": self.generate_text_report,
            "json": self.generate_json_report,
            "html": self.generate_html_report,
            "markdown": self.generate_markdown_report
        }

        if format not in formats:
            raise ValueError(f"Unsupported format: {format}")

        return formats[format](results)


def generate_report(
    results: Union[Dict[str, Any], List[Dict[str, Any]]],
    format: str = "text"
) -> str:
    """
    Convenience function to generate report.

    Args:
        results: Results to report
        format: Report format

    Returns:
        Report string
    """
    generator = ResultsReportGenerator()
    return generator.export_report(results, format)


if __name__ == "__main__":
    # Example usage
    results = [
        {
            "test_name": "test_function_1",
            "total_score": 0.9,
            "grade": "A",
            "components": [
                {"name": "correctness", "score": 1.0, "weight": 0.4},
                {"name": "performance", "score": 0.8, "weight": 0.3},
                {"name": "complexity", "score": 0.7, "weight": 0.2},
                {"name": "memory", "score": 0.9, "weight": 0.1}
            ],
            "execution_time": 0.5,
            "memory_used": 1024 * 1024
        },
        {
            "test_name": "test_function_2",
            "total_score": 0.7,
            "grade": "C",
            "components": [
                {"name": "correctness", "score": 0.8, "weight": 0.4},
                {"name": "performance", "score": 0.6, "weight": 0.3},
                {"name": "complexity", "score": 0.7, "weight": 0.2},
                {"name": "memory", "score": 0.7, "weight": 0.1}
            ],
            "execution_time": 1.0,
            "memory_used": 2 * 1024 * 1024
        }
    ]

    # Generate reports
    generator = ResultsReportGenerator()

    print("=== TEXT REPORT ===")
    print(generator.generate_text_report(results))

    print("\n=== JSON REPORT ===")
    print(generator.generate_json_report(results))

    print("\n=== HTML REPORT ===")
    print(generator.generate_html_report(results))

    print("\n=== MARKDOWN REPORT ===")
    print(generator.generate_markdown_report(results))

    print("\n=== SUMMARY REPORT ===")
    print(generator.generate_summary_report(results))
