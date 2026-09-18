from __future__ import annotations

import os
import json
import ast
from typing import Annotated, Any, Literal, TypedDict

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from langchain_core.tools import tool

# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


from instructions import (
    QUOTE_NODE_INSTRUCTIONS,
    FETCH_DETAILS_NODE_INSTRUCTIONS,
    COVERAGE_NODE_INSTRUCTIONS,
    PAYMENT_NODE_INSTRUCTIONS,
    POLICY_ISSUANCE_NODE_INSTRUCTIONS,
    EMAIL_NODE_INSTRUCTIONS,
)


# Tool Imports

from tools.root_tools.customer_details_tool import customer_details

from tools.Fetch_tools.vehicle_and_license_accident_lookup import (
    fetch_vehicle_driver_accident_details,
)

from tools.Fetch_tools.violation_insurance_history_license_status import (
    fetch_driver_related_details,
)

from tools.Coverage_tools.IDV_details import IDV_calculation

from tools.Coverage_tools.coverage_calculation_details import (
    coverage_calculation,
)

from tools.Coverage_tools.plan_breakdown_tool import plan_breakdown

from tools.Payment_tools.payment_pdf_creation import create_payment_receipt_pdf

from tools.Policy_Issuance_tools.policy_issuance_details import (
    policy_pdf_details,
)

from tools.email_tools.email_tools import send_email_tool as _send_email


# ============================================================
# LANGGRAPH STATE
# ============================================================

NodeName = Literal[
    "quote",
    "fetch_details",
    "coverage",
    "payment",
    "policy_issuance",
    "email",
]


class PolicyState(TypedDict, total=False):

    messages: Annotated[list[BaseMessage], add_messages]
    active_node: NodeName

    customer_id: str
    customer: dict
    vehicle: dict
    driver: dict
    accident: dict
    driver_history: dict
    coverage: dict
    selected_plan: str
    premium: float
    payment: dict
    payment_receipt: dict
    policy: dict
    policy_document: dict
    email_result: dict

    current_stage: str
    error: str

# TOOL Wrappers

@tool
def customer_details_tool(custid: str) -> dict:
    """Find an existing customer by customer ID in the local capstone dataset."""
    return customer_details(custid)


@tool
def vehicle_lookup_tool(vin: str, license_number: str) -> dict:
    """Fetch local vehicle, driver and accident information using VIN and license number."""
    return fetch_vehicle_driver_accident_details(vin, license_number)


@tool
def IDV_calculation_tool(vehicle_age: int, vehicle_price: float) -> dict:
    """Calculate IDV from vehicle age and vehicle price.

    Depreciation is selected inside the tool. The model does not calculate
    IDV itself. This matches the Coverage Node instruction:
    IDV_calculation_tool(vehicle_age, vehicle_price).
    """
    depreciation_by_age = {
        0: 0.10,
        1: 0.15,
        2: 0.20,
        3: 0.30,
        4: 0.40,
        5: 0.50,
    }

    age = int(vehicle_age)
    depreciation_rate = (
        depreciation_by_age[age]
        if age in depreciation_by_age
        else 0.60
    )

    idv_value = IDV_calculation(vehicle_price, depreciation_rate)

    return {
        "vehicle_age": age,
        "vehicle_price": float(vehicle_price),
        "depreciation_rate": depreciation_rate,
        "idv": idv_value,
    }
@tool
def coverage_calculation_tool(
    base_premium: float,
    age_factor: float,
    driving_history_factor: float,
    years_licensed_factor: float,
    mileage_factor: float,
    usage_factor: float,
    location_factor: float,
    safety_discount: float,
    idv_value: float,
    collision_percentage: float,
    comprehensive_percentage: float,
    liability_limit: float,
    liability_limit_multiplier: float,
) -> dict:
    """Calculate liability, collision and comprehensive premium values."""
    return coverage_calculation(
        base_premium,
        age_factor,
        driving_history_factor,
        years_licensed_factor,
        mileage_factor,
        usage_factor,
        location_factor,
        safety_discount,
        idv_value,
        collision_percentage,
        comprehensive_percentage,
        liability_limit,
        liability_limit_multiplier,
    )


@tool
def plan_breakdown_tool(
    selected_plan: str,
    base_price: float,
    addon_names: list[str],
    discount_percentage: float = 10,
) -> dict:
    """Calculate the final plan/add-on/discount breakdown."""
    return plan_breakdown(selected_plan, base_price, addon_names, discount_percentage)

@tool
def payment_pdf_tool(
    Transaction_ID: str,
    Customer_ID: str,
    Policy_ID: str,
    CustomerName: str,
    Vehicle: str,
    VIN: str,
    PlateNumber: str,
    License: str,
    Address: str,
    PolicyType: str,
    PaymentMethod: str,
    PaymentAmount: float,
    PaymentStatus: str,
    PaymentDateTime: str,
) -> dict:
    """Generate the local insurance payment receipt PDF."""

    return create_payment_receipt_pdf(
        Transaction_ID,
        Customer_ID,
        Policy_ID,
        CustomerName,
        Vehicle,
        VIN,
        PlateNumber,
        License,
        Address,
        PolicyType,
        PaymentMethod,
        PaymentAmount,
        PaymentStatus,
        PaymentDateTime,
    )


@tool
def policy_pdf_tool(policy_details: dict, vehicle_details: dict, driver_details: dict) -> dict:
    """Generate the three-page local policy PDF."""
    return policy_pdf_details(policy_details, vehicle_details, driver_details)


@tool
def send_email_tool(to_email: str, subject: str, body_text: str, from_email: str = "") -> dict:
    """Send a policy email through Gmail when credentials are configured in .env."""
    return _send_email(
        {
            "to_email": to_email,
            "subject": subject,
            "body_text": body_text,
            "from_email": from_email or os.getenv("GMAIL_SENDER_EMAIL", ""),
        }
    )


_VALID_TARGETS = {
    "quote",
    "fetch_details",
    "coverage",
    "payment",
    "policy_issuance",
    "email",
}


@tool
def transfer_to_node(target_node: str) -> dict:
    """Hand the conversation off to another sub-agent node.

    Call this when your own node's instructions say to route the workflow
    to another node (e.g. after the user confirms fetched details, call
    transfer_to_node(target_node="coverage")).

    target_node must be one of: quote, fetch_details, coverage, payment,
    policy_issuance, email.
    """
    if target_node not in _VALID_TARGETS:
        return {"status": "error", "message": f"Unknown target_node '{target_node}'"}
    return {"status": "success", "target_node": target_node}


NODE_INSTRUCTIONS: dict[NodeName, str] = {
    "quote": QUOTE_NODE_INSTRUCTIONS,
    "fetch_details": FETCH_DETAILS_NODE_INSTRUCTIONS,
    "coverage": COVERAGE_NODE_INSTRUCTIONS,
    "payment": PAYMENT_NODE_INSTRUCTIONS,
    "policy_issuance": POLICY_ISSUANCE_NODE_INSTRUCTIONS,
    "email": EMAIL_NODE_INSTRUCTIONS,
}

NODE_TOOLS: dict[NodeName, list] = {
    "quote": [customer_details_tool, transfer_to_node],
    "fetch_details": [vehicle_lookup_tool, transfer_to_node],
    "coverage": [
        IDV_calculation_tool,
        coverage_calculation_tool,
        plan_breakdown_tool,
        transfer_to_node,
    ],
    "payment": [payment_pdf_tool, transfer_to_node],
    "policy_issuance": [policy_pdf_tool, transfer_to_node],
    "email": [send_email_tool],
}

NODE_NAMES: list[NodeName] = list(NODE_INSTRUCTIONS.keys())


# LANGGRAPH

def build_graph():

    model_name = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found. Please check your .env file.")

    base_llm = ChatOpenAI(model=model_name, api_key=api_key, reasoning_effort="none")

    llm_by_node = {name: base_llm.bind_tools(tools) for name, tools in NODE_TOOLS.items()}

    def make_agent_node(name: NodeName):

        instructions = NODE_INSTRUCTIONS[name]
        llm_with_tools = llm_by_node[name]

        def agent_node(state: PolicyState):

            messages = state.get("messages", [])

            state_snapshot = {
                "active_node": name,
                "customer_id": state.get("customer_id"),
                "customer": state.get("customer"),
                "vehicle": state.get("vehicle"),
                "driver": state.get("driver"),
                "accident": state.get("accident"),
                "driver_history": state.get("driver_history"),
                "coverage": state.get("coverage"),
                "selected_plan": state.get("selected_plan"),
                "premium": state.get("premium"),
                "payment": state.get("payment"),
                "payment_receipt": state.get("payment_receipt"),
                "policy_document": state.get("policy_document"),
            }

            system = SystemMessage(
                content=(
                    instructions
                    + "\n\nCURRENT WORKFLOW STATE:\n"
                    + json.dumps(state_snapshot, default=str)
                )
            )

            response = llm_with_tools.invoke([system, *messages])

            result = {
                "messages": [response],
                "current_stage": name,
            }

            # Deterministic confirmation hand-offs. The LLM can acknowledge
            # a confirmation in plain text without emitting transfer_to_node.
            latest_human = None
            for message in reversed(messages):
                if isinstance(message, HumanMessage):
                    latest_human = str(message.content).strip().lower()
                    break

            affirmative = {
                "yes", "y", "yeah", "yep", "sure", "correct",
                "confirm", "confirmed", "that's correct", "that is correct",
                "proceed", "okay", "ok",
            }

            if latest_human in affirmative and name == "quote":
                result["active_node"] = "fetch_details"
            elif latest_human in affirmative and name == "fetch_details":
                result["active_node"] = "coverage"
            else:
                result["active_node"] = state.get("active_node", name)

            return result

        return agent_node


    def make_sync_state_node(name: NodeName):

        def sync_state_node(state: PolicyState):

            updates: dict[str, Any] = {}

            for message in reversed(state.get("messages", [])):

                if not isinstance(message, ToolMessage):
                    continue

                try:
                    if isinstance(message.content, str):
                        try:
                            payload = json.loads(message.content)
                        except json.JSONDecodeError:
                            payload = ast.literal_eval(message.content)
                    else:
                        payload = message.content
                except Exception:
                    continue

                tool_name = message.name or ""

                if tool_name == "transfer_to_node" and isinstance(payload, dict):
                    target = payload.get("target_node")
                    if target in _VALID_TARGETS:
                        updates["active_node"] = target

                elif tool_name == "customer_details_tool" and isinstance(payload, dict):
                    updates["customer"] = payload
                    updates["customer_id"] = payload.get("custid")

                elif tool_name == "vehicle_lookup_tool" and isinstance(payload, dict):
                    updates["vehicle"] = payload.get("vehicle_details", {})
                    updates["driver"] = payload.get("driver_details", {})
                    updates["accident"] = payload.get("accident_details", {})

                
                elif tool_name == "IDV_calculation_tool" and isinstance(payload, dict):
                    updates["coverage"] = {
                        **updates.get("coverage", {}),
                        "idv": payload.get("idv"),
                        "depreciation_rate": payload.get("depreciation_rate"),
                        "vehicle_age": payload.get("vehicle_age"),
                        "vehicle_price": payload.get("vehicle_price"),
                    }

                elif tool_name == "driver_lookup_tool" and isinstance(payload, dict):
                    updates["driver_history"] = payload

                elif tool_name in {
                    "coverage_calculation_tool",
                    "plan_breakdown_tool",
                } and isinstance(payload, dict):
                    updates["coverage"] = payload
                    if "total_premium" in payload:
                        updates["premium"] = payload.get("total_premium")
                        updates["selected_plan"] = payload.get("coverage")

                elif tool_name == "insert_payment_tool" and isinstance(payload, dict):
                    updates["payment"] = payload

                elif tool_name == "payment_pdf_tool" and isinstance(payload, dict):
                    updates["payment_receipt"] = payload

                elif tool_name == "policy_pdf_tool" and isinstance(payload, dict):
                    updates["policy_document"] = payload

                elif tool_name == "send_email_tool" and isinstance(payload, dict):
                    updates["email_result"] = payload

                if updates:
                    break

            updates.setdefault("active_node", name)
            return updates

        return sync_state_node

    # ========================================================
    # ROUTER ("root agent") — dispatches by active_node
    # ========================================================

    def route_to_active_node(state: PolicyState) -> NodeName:
        return state.get("active_node", "quote")

    # ========================================================
    # ROUTE AFTER SUB-AGENT RESPONSE
    # ========================================================

    def route_after_agent(state: PolicyState):
        messages = state.get("messages", [])
        latest = messages[-1] if messages else None

        if latest is not None and getattr(latest, "tool_calls", None):
            return "tools"

        active = state.get("active_node")
        current = state.get("current_stage")

        if active and active != current:
            return active

        return END

    builder = StateGraph(PolicyState)

    for name in NODE_NAMES:
        builder.add_node(name, make_agent_node(name))
        builder.add_node(f"{name}_tools", ToolNode(NODE_TOOLS[name]))
        builder.add_node(f"{name}_sync", make_sync_state_node(name))


    builder.add_conditional_edges(
        START,
        route_to_active_node,
        {name: name for name in NODE_NAMES},
    )

    for name in NODE_NAMES:

        builder.add_conditional_edges(
            name,
            route_after_agent,
            {
                "tools": f"{name}_tools",
                "quote": "quote",
                "fetch_details": "fetch_details",
                "coverage": "coverage",
                "payment": "payment",
                "policy_issuance": "policy_issuance",
                "email": "email",
                END: END,
            },
        )

        builder.add_edge(f"{name}_tools", f"{name}_sync")

        builder.add_conditional_edges(
            f"{name}_sync",
            route_to_active_node,
            {n: n for n in NODE_NAMES},
        )

    return builder.compile()


graph = build_graph()
root_agent = graph



def invoke(user_message: str, history: list[BaseMessage] | None = None) -> dict[str, Any]:

    messages = list(history or []) + [HumanMessage(content=user_message)]

    return graph.invoke({"messages": messages})