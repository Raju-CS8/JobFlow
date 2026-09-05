"""Order reconciliation processor."""

from typing import Any, Optional
from decimal import Decimal, InvalidOperation
import logging

from jobflow.domain.exceptions import PermanentError, RetryableError

logger = logging.getLogger(__name__)


class OrderReconciliationProcessor:
    """
    Processor for order_reconciliation jobs.
    
    Validates order records, detects duplicates, and produces a reconciliation result.
    Pure computation: deterministic and idempotent, safe for retries and crash recovery.
    """
    
    # Supported currencies
    SUPPORTED_CURRENCIES = {"INR", "USD", "EUR", "GBP"}
    
    # Supported statuses
    SUPPORTED_STATUSES = {"PENDING", "PAID", "FAILED", "REFUNDED"}
    
    @staticmethod
    def process(payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process an order reconciliation job.
        
        Args:
            payload: The job payload containing an "orders" list.
        
        Returns:
            Result dict with validation counts and any issues found.
        
        Raises:
            PermanentError: For malformed input (invalid structure, missing fields).
            RetryableError: For transient operational failures.
        """
        # Validate payload structure
        if not isinstance(payload, dict):
            raise PermanentError("Payload must be a dictionary")
        
        if "orders" not in payload:
            raise PermanentError("Payload must contain 'orders' field")
        
        orders = payload.get("orders")
        if not isinstance(orders, list):
            raise PermanentError("'orders' must be a list")
        
        # Process orders
        valid_orders = []
        invalid_orders = []
        issues = []
        seen_order_ids = set()
        duplicate_order_ids = set()
        
        for idx, order in enumerate(orders):
            error = OrderReconciliationProcessor._validate_order(order, idx)
            
            if error:
                invalid_orders.append(order)
                issues.append(error)
                continue
            
            # Check for duplicates
            order_id = order.get("order_id")
            if order_id in seen_order_ids:
                duplicate_order_ids.add(order_id)
                invalid_orders.append(order)
                issues.append(f"Record {idx}: duplicate order_id '{order_id}'")
                continue
            
            seen_order_ids.add(order_id)
            valid_orders.append(order)
        
        # Calculate valid total
        valid_total_amount = Decimal("0.00")
        for order in valid_orders:
            try:
                amount = Decimal(str(order["amount"]))
                valid_total_amount += amount
            except (InvalidOperation, ValueError):
                # Should not happen as we validated above, but be safe
                pass
        
        # Convert Decimal to float for JSON serialization
        valid_total_amount_float = float(valid_total_amount)
        
        result = {
            "total_records": len(orders),
            "valid_count": len(valid_orders),
            "invalid_count": len(invalid_orders),
            "valid_total_amount": valid_total_amount_float,
            "issues": issues,
        }
        
        logger.info(
            f"Order reconciliation completed: "
            f"{len(valid_orders)} valid, {len(invalid_orders)} invalid"
        )
        
        return result
    
    @staticmethod
    def _validate_order(order: Any, idx: int) -> Optional[str]:
        """
        Validate a single order record.
        
        Returns:
            Error message if invalid, None if valid.
        """
        # Check if order is a dict
        if not isinstance(order, dict):
            return f"Record {idx}: order must be a dictionary, got {type(order).__name__}"
        
        # Check required fields
        required_fields = {"order_id", "amount", "currency", "status"}
        missing_fields = required_fields - set(order.keys())
        if missing_fields:
            return f"Record {idx}: missing required fields {missing_fields}"
        
        # Validate order_id
        order_id = order.get("order_id")
        if not isinstance(order_id, str) or not order_id.strip():
            return f"Record {idx}: order_id must be a non-empty string"
        
        # Validate amount
        amount = order.get("amount")
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return f"Record {idx}: amount must be positive"
        except (InvalidOperation, ValueError, TypeError):
            return f"Record {idx}: amount must be a valid number"
        
        # Validate currency
        currency = order.get("currency")
        if not isinstance(currency, str):
            return f"Record {idx}: currency must be a string"
        if currency.upper() not in OrderReconciliationProcessor.SUPPORTED_CURRENCIES:
            return (
                f"Record {idx}: unsupported currency '{currency}'. "
                f"Supported: {OrderReconciliationProcessor.SUPPORTED_CURRENCIES}"
            )
        
        # Validate status
        status = order.get("status")
        if not isinstance(status, str):
            return f"Record {idx}: status must be a string"
        if status.upper() not in OrderReconciliationProcessor.SUPPORTED_STATUSES:
            return (
                f"Record {idx}: unsupported status '{status}'. "
                f"Supported: {OrderReconciliationProcessor.SUPPORTED_STATUSES}"
            )
        
        return None