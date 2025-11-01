"""Human-in-the-loop review interface with approval workflows."""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json


logger = logging.getLogger(__name__)


class ReviewDecision(Enum):
    """Review decision types."""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ESCALATED = "escalated"
    DEFERRED = "deferred"


class ReviewItem:
    """
    An item requiring human review.
    """

    def __init__(
        self,
        item_id: str,
        item_type: str,
        content: Dict[str, Any],
        risk_level: str,
        reason_for_review: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize review item.

        Args:
            item_id: Unique item identifier
            item_type: Type of item (task_result, finding, etc.)
            content: Item content
            risk_level: Risk level (low/medium/high/critical)
            reason_for_review: Why this item needs review
            metadata: Additional metadata
        """
        self.item_id = item_id
        self.item_type = item_type
        self.content = content
        self.risk_level = risk_level
        self.reason_for_review = reason_for_review
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()

        # Review state
        self.decision: Optional[ReviewDecision] = None
        self.reviewer: Optional[str] = None
        self.review_notes: Optional[str] = None
        self.reviewed_at: Optional[datetime] = None


class ReviewWorkflow:
    """
    Workflow for high-risk decision approval.
    """

    def __init__(
        self,
        workflow_id: str,
        required_approvals: int = 1,
        auto_approve_low_risk: bool = True
    ):
        """
        Initialize review workflow.

        Args:
            workflow_id: Workflow identifier
            required_approvals: Number of required approvals
            auto_approve_low_risk: Auto-approve low-risk items
        """
        self.workflow_id = workflow_id
        self.required_approvals = required_approvals
        self.auto_approve_low_risk = auto_approve_low_risk

        self.pending_items: List[ReviewItem] = []
        self.completed_items: List[ReviewItem] = []

    def add_item(self, item: ReviewItem) -> None:
        """
        Add item to workflow.

        Args:
            item: Review item
        """
        # Auto-approve low-risk items if enabled
        if self.auto_approve_low_risk and item.risk_level == "low":
            item.decision = ReviewDecision.APPROVED
            item.reviewer = "auto_system"
            item.review_notes = "Auto-approved (low risk)"
            item.reviewed_at = datetime.utcnow()
            self.completed_items.append(item)
            logger.info(f"Auto-approved low-risk item: {item.item_id}")
        else:
            self.pending_items.append(item)
            logger.info(f"Added item to review queue: {item.item_id} (risk: {item.risk_level})")

    def get_pending_items(
        self,
        risk_level: Optional[str] = None
    ) -> List[ReviewItem]:
        """
        Get pending review items.

        Args:
            risk_level: Filter by risk level

        Returns:
            List of pending items
        """
        if risk_level:
            return [
                item for item in self.pending_items
                if item.risk_level == risk_level
            ]
        return self.pending_items

    def submit_review(
        self,
        item_id: str,
        decision: ReviewDecision,
        reviewer: str,
        notes: str = ""
    ) -> bool:
        """
        Submit review decision for an item.

        Args:
            item_id: Item identifier
            decision: Review decision
            reviewer: Reviewer identifier
            notes: Review notes

        Returns:
            True if review submitted successfully
        """
        # Find item in pending
        item = None
        for i, pending_item in enumerate(self.pending_items):
            if pending_item.item_id == item_id:
                item = pending_item
                del self.pending_items[i]
                break

        if not item:
            logger.error(f"Item not found in pending queue: {item_id}")
            return False

        # Record review
        item.decision = decision
        item.reviewer = reviewer
        item.review_notes = notes
        item.reviewed_at = datetime.utcnow()

        self.completed_items.append(item)

        logger.info(
            f"Review submitted for {item_id}: {decision.value} by {reviewer}"
        )

        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get workflow status.

        Returns:
            Workflow status dictionary
        """
        return {
            "workflow_id": self.workflow_id,
            "pending_count": len(self.pending_items),
            "completed_count": len(self.completed_items),
            "by_risk_level": self._count_by_risk_level(),
            "by_decision": self._count_by_decision(),
        }

    def _count_by_risk_level(self) -> Dict[str, int]:
        """Count pending items by risk level."""
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for item in self.pending_items:
            counts[item.risk_level] = counts.get(item.risk_level, 0) + 1
        return counts

    def _count_by_decision(self) -> Dict[str, int]:
        """Count completed items by decision."""
        counts = {}
        for item in self.completed_items:
            if item.decision:
                decision = item.decision.value
                counts[decision] = counts.get(decision, 0) + 1
        return counts


class CLIReviewInterface:
    """
    Command-line interface for human review.

    Provides interactive prompts for reviewing pending items.
    """

    def __init__(self, workflow: ReviewWorkflow):
        """
        Initialize CLI review interface.

        Args:
            workflow: Review workflow
        """
        self.workflow = workflow

    def start_review_session(self, reviewer_name: str) -> Dict[str, Any]:
        """
        Start interactive review session.

        Args:
            reviewer_name: Name of reviewer

        Returns:
            Session results
        """
        print("\n" + "="*80)
        print("SAFETY RESEARCH SYSTEM - HUMAN REVIEW INTERFACE")
        print("="*80)
        print(f"\nReviewer: {reviewer_name}")
        print(f"Pending items: {len(self.workflow.pending_items)}\n")

        if not self.workflow.pending_items:
            print("No items pending review.")
            return {"items_reviewed": 0}

        reviewed_count = 0
        approved_count = 0
        rejected_count = 0

        # Review each pending item
        for item in list(self.workflow.pending_items):
            decision, notes = self._review_item_interactive(item)

            if decision:
                self.workflow.submit_review(
                    item.item_id,
                    decision,
                    reviewer_name,
                    notes
                )
                reviewed_count += 1

                if decision == ReviewDecision.APPROVED:
                    approved_count += 1
                elif decision == ReviewDecision.REJECTED:
                    rejected_count += 1

                # Ask if continue
                if self.workflow.pending_items:
                    continue_input = input("\nContinue to next item? (y/n): ").strip().lower()
                    if continue_input != 'y':
                        break

        print("\n" + "="*80)
        print("REVIEW SESSION COMPLETE")
        print("="*80)
        print(f"Items reviewed: {reviewed_count}")
        print(f"Approved: {approved_count}")
        print(f"Rejected: {rejected_count}")
        print(f"Remaining: {len(self.workflow.pending_items)}")

        return {
            "items_reviewed": reviewed_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "remaining": len(self.workflow.pending_items),
        }

    def _review_item_interactive(
        self,
        item: ReviewItem
    ) -> tuple[Optional[ReviewDecision], str]:
        """
        Interactive review of a single item.

        Args:
            item: Review item

        Returns:
            Tuple of (decision, notes)
        """
        print("\n" + "-"*80)
        print(f"REVIEW ITEM: {item.item_id}")
        print("-"*80)
        print(f"Type: {item.item_type}")
        print(f"Risk Level: {item.risk_level.upper()}")
        print(f"Reason for Review: {item.reason_for_review}")
        print(f"Created: {item.created_at.isoformat()}")
        print("\n" + "-"*80)
        print("CONTENT:")
        print("-"*80)
        self._display_content(item.content)
        print("-"*80)

        # Get decision
        print("\nDECISION OPTIONS:")
        print("  1. APPROVE")
        print("  2. REJECT")
        print("  3. NEEDS REVISION")
        print("  4. ESCALATE")
        print("  5. DEFER (skip for now)")
        print("  0. EXIT review session")

        while True:
            choice = input("\nEnter your decision (0-5): ").strip()

            if choice == "0":
                return None, ""
            elif choice == "1":
                decision = ReviewDecision.APPROVED
                break
            elif choice == "2":
                decision = ReviewDecision.REJECTED
                break
            elif choice == "3":
                decision = ReviewDecision.NEEDS_REVISION
                break
            elif choice == "4":
                decision = ReviewDecision.ESCALATED
                break
            elif choice == "5":
                decision = ReviewDecision.DEFERRED
                break
            else:
                print("Invalid choice. Please enter 0-5.")

        # Get notes
        notes = input("\nReview notes (optional): ").strip()

        return decision, notes

    def _display_content(self, content: Dict[str, Any], indent: int = 0) -> None:
        """
        Display content in readable format.

        Args:
            content: Content dictionary
            indent: Indentation level
        """
        indent_str = "  " * indent

        for key, value in content.items():
            if isinstance(value, dict):
                print(f"{indent_str}{key}:")
                self._display_content(value, indent + 1)
            elif isinstance(value, list):
                print(f"{indent_str}{key}: [{len(value)} items]")
                for i, item in enumerate(value[:3]):  # Show first 3
                    if isinstance(item, dict):
                        print(f"{indent_str}  [{i}]:")
                        self._display_content(item, indent + 2)
                    else:
                        print(f"{indent_str}  [{i}] {item}")
                if len(value) > 3:
                    print(f"{indent_str}  ... ({len(value) - 3} more items)")
            else:
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                print(f"{indent_str}{key}: {value_str}")

    def generate_review_summary(self) -> str:
        """
        Generate summary of review status.

        Returns:
            Formatted summary string
        """
        status = self.workflow.get_status()

        summary = []
        summary.append("\n" + "="*80)
        summary.append("REVIEW WORKFLOW SUMMARY")
        summary.append("="*80)
        summary.append(f"Workflow ID: {status['workflow_id']}")
        summary.append(f"\nPending Items: {status['pending_count']}")
        summary.append(f"Completed Items: {status['completed_count']}")

        summary.append("\n--- Pending by Risk Level ---")
        for level, count in status['by_risk_level'].items():
            if count > 0:
                summary.append(f"  {level.upper()}: {count}")

        summary.append("\n--- Completed by Decision ---")
        for decision, count in status['by_decision'].items():
            summary.append(f"  {decision.upper()}: {count}")

        summary.append("="*80)

        return "\n".join(summary)


class FeedbackCollector:
    """
    Collects feedback on system outputs for continuous improvement.
    """

    def __init__(self):
        """Initialize feedback collector."""
        self.feedback_items: List[Dict[str, Any]] = []

    def collect_feedback(
        self,
        item_id: str,
        item_type: str,
        rating: int,
        feedback_text: str = "",
        category: str = "general",
        user_id: str = "anonymous"
    ) -> None:
        """
        Collect feedback on an item.

        Args:
            item_id: Item identifier
            item_type: Type of item
            rating: Rating (1-5)
            feedback_text: Free-text feedback
            category: Feedback category
            user_id: User identifier
        """
        self.feedback_items.append({
            "item_id": item_id,
            "item_type": item_type,
            "rating": rating,
            "feedback_text": feedback_text,
            "category": category,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.info(f"Feedback collected for {item_id}: {rating}/5")

    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get feedback summary.

        Returns:
            Feedback summary statistics
        """
        if not self.feedback_items:
            return {"status": "no_feedback"}

        ratings = [item["rating"] for item in self.feedback_items]
        avg_rating = sum(ratings) / len(ratings)

        # Group by category
        by_category = {}
        for item in self.feedback_items:
            category = item["category"]
            if category not in by_category:
                by_category[category] = {
                    "count": 0,
                    "ratings": [],
                }
            by_category[category]["count"] += 1
            by_category[category]["ratings"].append(item["rating"])

        # Calculate category averages
        for category in by_category:
            ratings = by_category[category]["ratings"]
            by_category[category]["avg_rating"] = sum(ratings) / len(ratings)

        return {
            "total_feedback": len(self.feedback_items),
            "avg_rating": avg_rating,
            "by_category": by_category,
            "recent_feedback": self.feedback_items[-10:],  # Last 10
        }

    def collect_feedback_interactive(
        self,
        item_id: str,
        item_type: str
    ) -> None:
        """
        Collect feedback interactively via CLI.

        Args:
            item_id: Item identifier
            item_type: Item type
        """
        print("\n" + "="*80)
        print("FEEDBACK COLLECTION")
        print("="*80)
        print(f"Item: {item_id} ({item_type})")

        # Get rating
        while True:
            rating_input = input("\nRating (1-5, 5=excellent): ").strip()
            try:
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    break
                else:
                    print("Rating must be between 1 and 5")
            except ValueError:
                print("Please enter a number between 1 and 5")

        # Get feedback text
        feedback_text = input("Additional feedback (optional): ").strip()

        # Get category
        print("\nCategory:")
        print("  1. Accuracy")
        print("  2. Completeness")
        print("  3. Clarity")
        print("  4. Timeliness")
        print("  5. General")

        category_map = {
            "1": "accuracy",
            "2": "completeness",
            "3": "clarity",
            "4": "timeliness",
            "5": "general",
        }

        category_input = input("Select category (1-5, default=5): ").strip()
        category = category_map.get(category_input, "general")

        # Collect feedback
        self.collect_feedback(
            item_id,
            item_type,
            rating,
            feedback_text,
            category
        )

        print("\nThank you for your feedback!")


# Example usage
if __name__ == "__main__":
    # Create workflow
    workflow = ReviewWorkflow("test_workflow")

    # Add some review items
    workflow.add_item(ReviewItem(
        item_id="item_001",
        item_type="task_result",
        content={
            "summary": "Risk assessment completed",
            "risk_estimate": 0.15,
            "confidence": "Moderate",
        },
        risk_level="high",
        reason_for_review="Risk estimate >10% requires human approval",
    ))

    # Create CLI interface
    cli = CLIReviewInterface(workflow)

    # Display summary
    print(cli.generate_review_summary())

    # For testing, simulate review without actual interaction
    workflow.submit_review(
        "item_001",
        ReviewDecision.APPROVED,
        "test_reviewer",
        "Risk assessment looks reasonable"
    )

    print(cli.generate_review_summary())
