"""
Metrics Calculator for Evaluation Harness
"""

from typing import Dict, Any, List
import numpy as np


class MetricsCalculator:
    """
    Calculates various metrics for evaluating the system.
    """
    
    def calculate_aggregate_metrics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across all test results.
        
        Args:
            test_results: List of test result dictionaries
            
        Returns:
            Dictionary of aggregate metrics
        """
        if not test_results:
            return self._empty_metrics()
        
        metrics = {
            "success_rate": self._calculate_success_rate(test_results),
            "avg_latency": self._calculate_avg_latency(test_results),
            "median_latency": self._calculate_median_latency(test_results),
            "total_tool_calls": self._calculate_total_tool_calls(test_results),
            "avg_tool_calls": self._calculate_avg_tool_calls(test_results),
            "total_constraint_violations": self._count_total_violations(test_results),
            "error_rate": self._calculate_error_rate(test_results),
            "avg_overall_score": self._calculate_avg_score(test_results),
            "latency_distribution": self._calculate_latency_distribution(test_results),
            "failure_breakdown": self._analyze_failures(test_results)
        }
        
        return metrics
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "success_rate": 0.0,
            "avg_latency": 0.0,
            "median_latency": 0.0,
            "total_tool_calls": 0,
            "avg_tool_calls": 0.0,
            "total_constraint_violations": 0,
            "error_rate": 0.0,
            "avg_overall_score": 0.0
        }
    
    def _calculate_success_rate(self, results: List[Dict[str, Any]]) -> float:
        """Calculate percentage of successful tests."""
        passed = sum(1 for r in results if r.get("passed", False))
        return (passed / len(results)) * 100 if results else 0.0
    
    def _calculate_avg_latency(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average processing time."""
        latencies = [r.get("processing_time", 0) for r in results]
        return sum(latencies) / len(latencies) if latencies else 0.0
    
    def _calculate_median_latency(self, results: List[Dict[str, Any]]) -> float:
        """Calculate median processing time."""
        latencies = [r.get("processing_time", 0) for r in results]
        return float(np.median(latencies)) if latencies else 0.0
    
    def _calculate_total_tool_calls(self, results: List[Dict[str, Any]]) -> int:
        """Calculate total tool invocations."""
        return sum(
            r.get("metrics", {}).get("tool_calls", 0) 
            for r in results
        )
    
    def _calculate_avg_tool_calls(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average tool calls per test."""
        tool_calls = [
            r.get("metrics", {}).get("tool_calls", 0) 
            for r in results
        ]
        return sum(tool_calls) / len(tool_calls) if tool_calls else 0.0
    
    def _count_total_violations(self, results: List[Dict[str, Any]]) -> int:
        """Count total constraint violations."""
        return sum(
            len(r.get("constraint_violations", [])) 
            for r in results
        )
    
    def _calculate_error_rate(self, results: List[Dict[str, Any]]) -> float:
        """Calculate percentage of tests with errors."""
        with_errors = sum(
            1 for r in results 
            if r.get("metrics", {}).get("errors", 0) > 0 or r.get("error")
        )
        return (with_errors / len(results)) * 100 if results else 0.0
    
    def _calculate_avg_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average overall score from critiques."""
        scores = [
            r.get("metrics", {}).get("overall_score", 0) 
            for r in results 
            if r.get("metrics", {}).get("overall_score", 0) > 0
        ]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_latency_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate latency percentiles."""
        latencies = [r.get("processing_time", 0) for r in results]
        
        if not latencies:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        
        return {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "p50": float(np.percentile(latencies, 50)),
            "p90": float(np.percentile(latencies, 90)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99))
        }
    
    def _analyze_failures(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze failure patterns."""
        failed_tests = [r for r in results if not r.get("passed", False)]
        
        if not failed_tests:
            return {"total_failures": 0, "failure_reasons": {}}
        
        # Count failure reasons
        reasons = {}
        for test in failed_tests:
            violations = test.get("constraint_violations", [])
            for violation in violations:
                # Extract general category
                if "extract" in violation.lower():
                    category = "extraction_failure"
                elif "agent" in violation.lower():
                    category = "agent_failure"
                elif "timeout" in violation.lower() or "time" in violation.lower():
                    category = "timeout"
                else:
                    category = "other"
                
                reasons[category] = reasons.get(category, 0) + 1
        
        return {
            "total_failures": len(failed_tests),
            "failure_reasons": reasons,
            "failure_rate_by_test": {
                r["test_id"]: r.get("constraint_violations", [])
                for r in failed_tests
            }
        }
    
    def calculate_citation_accuracy(self, results: List[Dict[str, Any]], 
                                    ground_truth: Dict[str, List[str]] = None) -> float:
        """
        Calculate accuracy of citation recommendations.
        
        Args:
            results: Test results
            ground_truth: Dict mapping paper IDs to relevant paper IDs
            
        Returns:
            Accuracy percentage
        """
        if not ground_truth:
            return 0.0
        
        correct_citations = 0
        total_citations = 0
        
        for result in results:
            paper_id = result.get("review_result", {}).get("paper_content", {}).get("paper_id")
            
            if not paper_id or paper_id not in ground_truth:
                continue
            
            found_papers = result.get("review_result", {}).get("citation_data", {}).get("related_papers", [])
            found_ids = [p.get("arxiv_id") for p in found_papers]
            
            relevant_ids = ground_truth[paper_id]
            
            # Calculate intersection
            correct = len(set(found_ids) & set(relevant_ids))
            correct_citations += correct
            total_citations += len(relevant_ids)
        
        return (correct_citations / total_citations) * 100 if total_citations > 0 else 0.0
    
    def generate_metrics_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate human-readable metrics summary."""
        summary = []
        summary.append("=== METRICS SUMMARY ===\n")
        
        summary.append(f"Success Rate: {metrics['success_rate']:.1f}%")
        summary.append(f"Average Latency: {metrics['avg_latency']:.2f}s")
        summary.append(f"Median Latency: {metrics['median_latency']:.2f}s")
        summary.append(f"Total Tool Calls: {metrics['total_tool_calls']}")
        summary.append(f"Avg Tool Calls per Test: {metrics['avg_tool_calls']:.1f}")
        summary.append(f"Total Constraint Violations: {metrics['total_constraint_violations']}")
        summary.append(f"Error Rate: {metrics['error_rate']:.1f}%")
        summary.append(f"Avg Overall Score: {metrics['avg_overall_score']:.2f}/10")
        
        summary.append("\n=== LATENCY DISTRIBUTION ===")
        dist = metrics.get("latency_distribution", {})
        summary.append(f"Min: {dist.get('min', 0):.2f}s")
        summary.append(f"p50: {dist.get('p50', 0):.2f}s")
        summary.append(f"p90: {dist.get('p90', 0):.2f}s")
        summary.append(f"p95: {dist.get('p95', 0):.2f}s")
        summary.append(f"Max: {dist.get('max', 0):.2f}s")
        
        failures = metrics.get("failure_breakdown", {})
        if failures.get("total_failures", 0) > 0:
            summary.append("\n=== FAILURE ANALYSIS ===")
            summary.append(f"Total Failures: {failures['total_failures']}")
            summary.append("Failure Reasons:")
            for reason, count in failures.get("failure_reasons", {}).items():
                summary.append(f"  - {reason}: {count}")
        
        return "\n".join(summary)


if __name__ == "__main__":
    # Test metrics calculator
    calculator = MetricsCalculator()
    
    sample_results = [
        {
            "test_id": "test_1",
            "passed": True,
            "processing_time": 45.2,
            "metrics": {"tool_calls": 4, "errors": 0, "overall_score": 7.5}
        },
        {
            "test_id": "test_2",
            "passed": False,
            "processing_time": 38.1,
            "metrics": {"tool_calls": 3, "errors": 1, "overall_score": 5.2},
            "constraint_violations": ["Failed to extract abstract"]
        }
    ]
    
    metrics = calculator.calculate_aggregate_metrics(sample_results)
    print(calculator.generate_metrics_summary(metrics))