"""
Evaluation Harness for Multi-Agent Research Paper Reviewer
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from orchestrator import ResearchReviewOrchestrator
from metrics import MetricsCalculator


class EvaluationHarness:
    """
    Runs test cases and computes evaluation metrics.
    """
    
    def __init__(self, test_cases_file: str = "test_cases.json"):
        self.test_cases_file = test_cases_file
        self.test_cases = self._load_test_cases()
        self.orchestrator = ResearchReviewOrchestrator()
        self.metrics_calculator = MetricsCalculator()
        self.results = []
        
    def _load_test_cases(self) -> Dict[str, Any]:
        """Load test cases from JSON file."""
        with open(self.test_cases_file, 'r') as f:
            return json.load(f)
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test case.
        
        Args:
            test_case: Test case configuration
            
        Returns:
            Test result with metrics and pass/fail status
        """
        test_id = test_case.get("test_id")
        print(f"\n{'='*60}")
        print(f"Running Test: {test_id} - {test_case.get('name')}")
        print(f"{'='*60}")
        
        input_data = test_case.get("input", {})
        expected = test_case.get("expected_outcomes", {})
        constraints = test_case.get("constraints", {})
        
        start_time = datetime.now()
        
        try:
            # Run review
            result = self.orchestrator.review_paper(
                paper_source=input_data.get("paper_source"),
                source_type=input_data.get("source_type")
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Validate results
            violations = self._check_constraints(result, constraints)
            expectations_met = self._check_expectations(result, expected)
            
            test_result = {
                "test_id": test_id,
                "name": test_case.get("name"),
                "timestamp": start_time.isoformat(),
                "passed": len(violations) == 0 and expectations_met,
                "processing_time": processing_time,
                "review_result": result,
                "constraint_violations": violations,
                "expectations_met": expectations_met,
                "metrics": {
                    "tool_calls": result.get("metadata", {}).get("tool_calls", 0),
                    "errors": len(result.get("metadata", {}).get("errors", [])),
                    "overall_score": result.get("critic_analysis", {}).get("overall_score", 0)
                }
            }
            
            # Print summary
            status = "✅ PASSED" if test_result["passed"] else "❌ FAILED"
            print(f"\nStatus: {status}")
            print(f"Processing Time: {processing_time:.2f}s")
            print(f"Constraint Violations: {len(violations)}")
            print(f"Expectations Met: {expectations_met}")
            
            if violations:
                print("\nViolations:")
                for violation in violations:
                    print(f"  - {violation}")
            
            return test_result
            
        except Exception as e:
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"\n❌ Test FAILED with exception: {str(e)}")
            
            return {
                "test_id": test_id,
                "name": test_case.get("name"),
                "timestamp": start_time.isoformat(),
                "passed": False,
                "processing_time": processing_time,
                "error": str(e),
                "constraint_violations": [f"Exception: {str(e)}"],
                "expectations_met": False
            }
    
    def _check_constraints(self, result: Dict[str, Any], 
                          constraints: Dict[str, Any]) -> List[str]:
        """Check if result violates any constraints."""
        violations = []
        
        paper_content = result.get("paper_content", {})
        critique = result.get("critic_analysis", {})
        review = result.get("final_review", {})
        
        # Check must_extract_title
        if constraints.get("must_extract_title"):
            if not paper_content.get("title") or paper_content["title"] == "Unknown Title":
                violations.append("Failed to extract paper title")
        
        # Check must_extract_abstract
        if constraints.get("must_extract_abstract"):
            if not paper_content.get("abstract") or len(paper_content["abstract"]) < 50:
                violations.append("Failed to extract meaningful abstract")
        
        # Check must_have_critique
        if constraints.get("must_have_critique"):
            if not critique or not critique.get("overall_score"):
                violations.append("Missing critical analysis")
        
        # Check must_have_eli5
        if constraints.get("must_have_eli5"):
            if not review.get("eli5_summary"):
                violations.append("Missing ELI5 summary")
        
        # Check agent success
        metadata = result.get("metadata", {})
        if constraints.get("reader_agent_success") and "reader" in str(metadata.get("errors", [])).lower():
            violations.append("Reader agent failed")
        
        if constraints.get("critic_agent_success") and not critique:
            violations.append("Critic agent failed")
        
        if constraints.get("meta_reviewer_success") and not review:
            violations.append("MetaReviewer agent failed")
        
        if constraints.get("cite_agent_success"):
            citations = result.get("citation_data", {})
            if not citations or len(citations.get("related_papers", [])) == 0:
                violations.append("CiteAgent failed to find related papers")
        
        return violations
    
    def _check_expectations(self, result: Dict[str, Any],
                           expected: Dict[str, Any]) -> bool:
        """Check if result meets expected outcomes."""
        paper_content = result.get("paper_content", {})
        critique = result.get("critic_analysis", {})
        citations = result.get("citation_data", {})
        metadata = result.get("metadata", {})
        
        # Check min_overall_score
        if "min_overall_score" in expected:
            overall = critique.get("overall_score", 0)
            if overall < expected["min_overall_score"]:
                return False
        
        # Check max_overall_score
        if "max_overall_score" in expected:
            overall = critique.get("overall_score", 10)
            if overall > expected["max_overall_score"]:
                return False
        
        # Check min_references
        if "min_references" in expected:
            refs = len(paper_content.get("references", []))
            if refs < expected["min_references"]:
                return False
        
        # Check min_related_papers
        if "min_related_papers" in expected:
            related = len(citations.get("related_papers", []))
            if related < expected["min_related_papers"]:
                return False
        
        # Check max_processing_time
        if "max_processing_time" in expected:
            time = metadata.get("processing_time_seconds", 0)
            if time > expected["max_processing_time"]:
                return False
        
        # Check min_weaknesses
        if "min_weaknesses" in expected:
            weaknesses = len(critique.get("weaknesses", []))
            if weaknesses < expected["min_weaknesses"]:
                return False
        
        # Check max_errors
        if "max_errors" in expected:
            errors = len(metadata.get("errors", []))
            if errors > expected["max_errors"]:
                return False
        
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and compile results."""
        print(f"\n{'#'*60}")
        print(f"# EVALUATION HARNESS - MULTI-AGENT PAPER REVIEWER")
        print(f"# Total Test Cases: {len(self.test_cases['test_cases'])}")
        print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")
        
        all_results = []
        
        for test_case in self.test_cases["test_cases"]:
            result = self.run_single_test(test_case)
            all_results.append(result)
        
        # Calculate aggregate metrics
        metrics = self.metrics_calculator.calculate_aggregate_metrics(all_results)
        
        # Save results
        output = {
            "evaluation_date": datetime.now().isoformat(),
            "test_results": all_results,
            "aggregate_metrics": metrics,
            "summary": {
                "total_tests": len(all_results),
                "passed": sum(1 for r in all_results if r.get("passed")),
                "failed": sum(1 for r in all_results if not r.get("passed")),
                "success_rate": metrics.get("success_rate", 0)
            }
        }
        
        # Save to file
        output_dir = Path("eval/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"EVALUATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total Tests: {output['summary']['total_tests']}")
        print(f"Passed: {output['summary']['passed']}")
        print(f"Failed: {output['summary']['failed']}")
        print(f"Success Rate: {metrics['success_rate']:.1f}%")
        print(f"Avg Latency: {metrics['avg_latency']:.2f}s")
        print(f"Total Tool Calls: {metrics['total_tool_calls']}")
        print(f"\nResults saved to: {output_file}")
        print(f"{'='*60}\n")
        
        return output
    
    def generate_report(self, results: Dict[str, Any]):
        """Generate HTML report from results."""
        # TODO: Implement HTML report generation
        pass


def main():
    parser = argparse.ArgumentParser(description="Run evaluation harness")
    parser.add_argument("--test-id", help="Run specific test case")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--test-file", default="test_cases.json", 
                       help="Path to test cases file")
    
    args = parser.parse_args()
    
    harness = EvaluationHarness(test_cases_file=args.test_file)
    
    if args.test_id:
        # Run specific test
        test_case = next(
            (tc for tc in harness.test_cases["test_cases"] 
             if tc["test_id"] == args.test_id),
            None
        )
        
        if test_case:
            result = harness.run_single_test(test_case)
            print(json.dumps(result, indent=2))
        else:
            print(f"Test case '{args.test_id}' not found")
    else:
        # Run all tests
        results = harness.run_all_tests()
        
        if args.report:
            harness.generate_report(results)


if __name__ == "__main__":
    main()