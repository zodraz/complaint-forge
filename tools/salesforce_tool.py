from __future__ import annotations

from typing import Any

import requests

from config import (
    SALESFORCE_API_VERSION,
    SALESFORCE_CLIENT_ID,
    SALESFORCE_CLIENT_SECRET,
    SALESFORCE_LOGIN_URL,
    SALESFORCE_RETURN_ORDER_ACCOUNT_FIELD,
    SALESFORCE_RETURN_ORDER_OBJECT,
    SALESFORCE_RETURN_ORDER_ORDER_FIELD,
)


def _salesforce_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        body = response.text.strip()
        return body[:500] if body else "No response body"

    if isinstance(payload, dict):
        error = payload.get("error")
        description = payload.get("error_description")
        if error and description:
            return f"{error}: {description}"
        if error:
            return str(error)
        return str(payload)

    return str(payload)


def _raise_for_status(response: requests.Response, *, context: str) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = _salesforce_error_message(response)
        raise RuntimeError(
            f"Salesforce {context} failed with HTTP {response.status_code}: {detail}"
        ) from exc


def _missing_config() -> list[str]:
    return [
        name
        for name, value in {
            "SALESFORCE_CLIENT_ID": SALESFORCE_CLIENT_ID,
            "SALESFORCE_CLIENT_SECRET": SALESFORCE_CLIENT_SECRET,
            "SALESFORCE_LOGIN_URL": SALESFORCE_LOGIN_URL,
        }.items()
        if not value
    ]


def _get_access_token() -> tuple[str, str]:
    missing = _missing_config()
    if missing:
        raise RuntimeError("Missing Salesforce configuration: " + ", ".join(missing))

    response = requests.post(
        SALESFORCE_LOGIN_URL.rstrip("/") + "/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": SALESFORCE_CLIENT_ID,
            "client_secret": SALESFORCE_CLIENT_SECRET,
        },
        timeout=30,
    )
    _raise_for_status(response, context="OAuth token request")
    payload = response.json()
    return payload["access_token"], payload["instance_url"].rstrip("/")


def _headers() -> tuple[dict[str, str], str]:
    access_token, instance_url = _get_access_token()
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }, instance_url


def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    headers, instance_url = _headers()
    response = requests.request(
        method,
        f"{instance_url}/services/data/{SALESFORCE_API_VERSION}{path}",
        headers=headers,
        timeout=30,
        **kwargs,
    )
    _raise_for_status(response, context=f"{method} {path}")
    if response.status_code == 204 or not response.content:
        return {}
    return response.json()


def _soql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _query(soql: str) -> list[dict[str, Any]]:
    return _request("GET", "/query", params={"q": soql}).get("records", [])


def _first(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    return records[0] if records else None


def _find_contact(email: str) -> dict[str, Any] | None:
    return _first(
        _query(
            "SELECT Id, Email, Phone, Name, AccountId, Account.Name "
            f"FROM Contact WHERE Email = {_soql_string(email)} LIMIT 1"
        )
    )


def _recent_cases(contact_id: str) -> list[dict[str, Any]]:
    return _query(
        "SELECT Id, CaseNumber, Subject, Status, Priority, Origin, CreatedDate "
        f"FROM Case WHERE ContactId = {_soql_string(contact_id)} "
        "ORDER BY CreatedDate DESC LIMIT 5"
    )


def _recent_opportunities(account_id: str | None) -> list[dict[str, Any]]:
    if not account_id:
        return []
    return _query(
        "SELECT Id, Name, StageName, Amount, CloseDate, CreatedDate "
        f"FROM Opportunity WHERE AccountId = {_soql_string(account_id)} "
        "ORDER BY CreatedDate DESC LIMIT 5"
    )


def _find_order(order_id: str | None, account_id: str | None) -> dict[str, Any] | None:
    if order_id:
        order = _first(
            _query(
                "SELECT Id, OrderNumber, Status, TotalAmount, EffectiveDate, AccountId "
                f"FROM Order WHERE OrderNumber = {_soql_string(order_id)} LIMIT 1"
            )
        )
        if order:
            return order

    if account_id:
        return _first(
            _query(
                "SELECT Id, OrderNumber, Status, TotalAmount, EffectiveDate, AccountId "
                f"FROM Order WHERE AccountId = {_soql_string(account_id)} "
                "ORDER BY EffectiveDate DESC LIMIT 1"
            )
        )

    return None


def _salesforce_identifier(value: str) -> str:
    if not value.replace("_", "").replace(".", "").isalnum():
        raise ValueError(f"Invalid Salesforce identifier: {value}")
    return value


def _recent_return_orders(
    account_id: str | None,
    matched_order: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    filters = []
    if account_id:
        filters.append(
            f"{_salesforce_identifier(SALESFORCE_RETURN_ORDER_ACCOUNT_FIELD)} = "
            f"{_soql_string(account_id)}"
        )
    if matched_order and matched_order.get("Id"):
        filters.append(
            f"{_salesforce_identifier(SALESFORCE_RETURN_ORDER_ORDER_FIELD)} = "
            f"{_soql_string(matched_order['Id'])}"
        )
    if not filters:
        return []

    return _query(
        "SELECT Id, OrderId,CreatedDate, LastModifiedDate "
        f"FROM {_salesforce_identifier(SALESFORCE_RETURN_ORDER_OBJECT)} "
        f"WHERE {' OR '.join(filters)} "
        "ORDER BY CreatedDate DESC LIMIT 5"
    )


def _case_description(
    customer_history: dict[str, Any],
    amount: float | None,
    reason: str | None,
) -> str:
    lines = [
        reason or "Customer complaint resolution requested.",
        f"Customer email: {customer_history.get('email')}",
        f"Order ID: {customer_history.get('order_id')}",
    ]
    if amount is not None:
        lines.append(f"Requested amount: {amount}")
    return "\n".join(line for line in lines if line and not line.endswith(": None"))


def _create_case(
    customer_history: dict[str, Any],
    *,
    subject: str,
    description: str,
    priority: str = "Medium",
) -> dict[str, Any]:
    contact_id = customer_history.get("contact_id")
    account_id = customer_history.get("account_id")
    payload = {
        "Subject": subject,
        "Description": description,
        "Status": "New",
        "Origin": "Web",
        "Priority": priority,
    }
    if contact_id:
        payload["ContactId"] = contact_id
    if account_id:
        payload["AccountId"] = account_id

    created = _request("POST", "/sobjects/Case", json=payload)
    return {
        "status": "success",
        "salesforce_action": "case_created",
        "case_id": created.get("id"),
    }


def _create_task(
    customer_history: dict[str, Any],
    *,
    subject: str,
    description: str,
) -> dict[str, Any]:
    payload = {
        "Subject": subject,
        "Description": description,
        "Status": "Not Started",
        "Priority": "Normal",
    }
    if customer_history.get("contact_id"):
        payload["WhoId"] = customer_history["contact_id"]
    if customer_history.get("account_id"):
        payload["WhatId"] = customer_history["account_id"]

    created = _request("POST", "/sobjects/Task", json=payload)
    return {
        "status": "success",
        "salesforce_action": "task_created",
        "task_id": created.get("id"),
    }


def get_customer_history(email: str, order_id: str | None = None) -> dict[str, Any]:
    """Pull customer, case, opportunity, and order context from Salesforce."""
    try:
        contact = _find_contact(email)
        if not contact:
            return {"error": "Contact not found", "email": email, "order_id": order_id}

        account = contact.get("Account") or {}
        account_id = contact.get("AccountId")
        cases = _recent_cases(contact["Id"])
        opportunities = _recent_opportunities(account_id)
        order = _find_order(order_id, account_id)
        return_orders = _recent_return_orders(account_id, order)

        return {
            "source": "salesforce",
            "contact_id": contact["Id"],
            "account_id": account_id,
            "account_name": account.get("Name"),
            "name": contact.get("Name"),
            "email": email,
            "phone": contact.get("Phone"),
            "order_id": order_id,
            "matched_order": order,
            "recent_return_orders": return_orders,
            "recent_cases": cases,
            "recent_opportunities": opportunities,
            "total_recent_return_orders": len(return_orders),
            "total_recent_cases": len(cases),
            "total_recent_opportunities": len(opportunities),
            "repeat_customer": bool(account_id and (cases or opportunities)),
            "has_prior_cases": bool(cases),
            "has_prior_return_orders": bool(return_orders),
        }
    except Exception as e:
        return {"error": str(e), "source": "salesforce"}


def process_refund(
    customer_history: dict[str, Any],
    amount: float,
    reason: str | None = None,
) -> dict[str, Any]:
    """Create a Salesforce Case for a refund workflow."""
    try:
        return _create_case(
            customer_history,
            subject=f"Refund request - {customer_history.get('email', 'unknown customer')}",
            description=_case_description(customer_history, amount, reason),
            priority="High",
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


def issue_credit(
    customer_history: dict[str, Any],
    amount: float,
    reason: str | None = None,
) -> dict[str, Any]:
    """Create a Salesforce Case for a customer credit workflow."""
    try:
        return _create_case(
            customer_history,
            subject=f"Customer credit request - {customer_history.get('email', 'unknown customer')}",
            description=_case_description(customer_history, amount, reason),
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_replacement_order(customer_history: dict[str, Any]) -> dict[str, Any]:
    """Create a Salesforce Task to coordinate a replacement order."""
    try:
        return _create_task(
            customer_history,
            subject=f"Replacement order follow-up - {customer_history.get('email', 'unknown customer')}",
            description=_case_description(
                customer_history,
                amount=None,
                reason="Coordinate replacement order for complaint resolution.",
            ),
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

