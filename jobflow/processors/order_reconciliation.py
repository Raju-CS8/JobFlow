"""Order reconciliation processor with comprehensive validation."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationRule:
    """A validation rule with name and check function."""
    name: str
    check: callable
    error_message: str


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class OrderValidator:
    """Validates orders with explicit, testable rules."""
    
    # Define valid values as class constants (not hardcoded in functions)
    VALID_CURRENCIES = {'INR', 'USD', 'EUR', 'GBP'}
    VALID_STATUSES = {'PENDING', 'PAID', 'FAILED', 'REFUNDED'}
    MIN_AMOUNT = Decimal('0.01')
    MAX_AMOUNT = Decimal('999999999.99')
    
    @classmethod
    def validate_order(cls, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single order.
        
        Args:
            order: Order dict with order_id, amount, currency, status
            
        Returns:
            Validated order data
            
        Raises:
            ValidationError: If order fails validation
        """
        issues = []
        
        # Rule 1: order_id must exist and be non-empty string
        if not isinstance(order.get('order_id'), str):
            issues.append("order_id must be a non-empty string")
        elif not order['order_id'].strip():
            issues.append("order_id cannot be empty")
        
        # Rule 2: amount must be numeric and positive
        try:
            amount = Decimal(str(order.get('amount', 0)))
        except (TypeError, ValueError):
            issues.append(f"amount must be numeric, got {type(order.get('amount')).__name__}")
            amount = None
        
        if amount is not None:
            if amount < cls.MIN_AMOUNT:
                issues.append(f"amount must be >= {cls.MIN_AMOUNT}, got {amount}")
            elif amount > cls.MAX_AMOUNT:
                issues.append(f"amount must be <= {cls.MAX_AMOUNT}, got {amount}")
        
        # Rule 3: currency must be in whitelist
        currency = order.get('currency', '').upper()
        if not currency:
            issues.append("currency is required")
        elif currency not in cls.VALID_CURRENCIES:
            issues.append(
                f"currency '{currency}' is invalid. "
                f"Allowed values: {', '.join(sorted(cls.VALID_CURRENCIES))}"
            )
        
        # Rule 4: status must be in whitelist
        status = order.get('status', '').upper()
        if not status:
            issues.append("status is required")
        elif status not in cls.VALID_STATUSES:
            issues.append(
                f"status '{status}' is invalid. "
                f"Allowed values: {', '.join(sorted(cls.VALID_STATUSES))}"
            )
        
        # If any validation failed, raise error with all issues
        if issues:
            raise ValidationError("; ".join(issues))
        
        return order
    
    @classmethod
    def validate_orders_batch(cls, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a batch of orders.
        
        Args:
            orders: List of order dicts
            
        Returns:
            List of validated orders
            
        Raises:
            ValidationError: If any order fails validation
        """
        validated = []
        for i, order in enumerate(orders):
            try:
                validated.append(cls.validate_order(order))
            except ValidationError as e:
                raise ValidationError(f"Order {i}: {str(e)}")
        return validated


class OrderReconciliationProcessor:
    """
    Processes order reconciliation jobs.
    
    Responsibility: Validate orders and return reconciliation summary.
    Deterministic: Same input always produces same output.
    Idempotent: Can be safely re-executed without side effects.
    """
    
    @staticmethod
    def process(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process order reconciliation.
        
        Args:
            payload: Dict with 'orders' key containing list of orders
            
        Returns:
            Summary with counts and issues list
            
        Raises:
            ValidationError: If validation fails (caught by worker as PermanentError)
        """
        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a dictionary")
        
        if 'orders' not in payload:
            raise ValidationError("Payload must contain 'orders' key")
        
        orders = payload['orders']
        if not isinstance(orders, list):
            raise ValidationError(f"orders must be a list, got {type(orders).__name__}")
        
        if not orders:
            raise ValidationError("orders list cannot be empty")
        
        # Validate all orders
        try:
            validated_orders = OrderValidator.validate_orders_batch(orders)
        except ValidationError as e:
            raise ValidationError(f"Order validation failed: {str(e)}")
        
        # Count valid orders
        valid_count = len(validated_orders)
        invalid_count = 0  # All are valid if we reached here
        
        # Calculate totals
        total_amount = sum(
            Decimal(str(order['amount']))
            for order in validated_orders
        )
        
        # Check for duplicates
        order_ids = [order['order_id'] for order in validated_orders]
        unique_ids = set(order_ids)
        duplicate_ids = [id for id in order_ids if order_ids.count(id) > 1]
        
        issues = []
        if duplicate_ids:
            issues.append(f"Duplicate order IDs found: {list(set(duplicate_ids))}")
        
        return {
            'total_records': len(orders),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'valid_total_amount': float(total_amount),
            'issues': issues,
        }