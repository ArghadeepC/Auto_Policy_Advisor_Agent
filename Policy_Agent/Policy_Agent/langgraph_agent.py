# # # """LangGraph orchestration for the Auto Policy Advisor capstone.

# # # The business tools remain ordinary Python functions. LangGraph supplies the
# # # explicit state, nodes, conditional routing and tool execution required by the
# # # capstone instead of Google ADK sub-agents.
# # # """

# # # from __future__ import annotations

# # # import os
# # # import json
# # # import ast
# # # from typing import Annotated, Any, TypedDict

# # # from dotenv import load_dotenv

# # # from pathlib import Path

# # # # Load variables from .env
# # # load_dotenv()

# # # from langchain_core.messages import (
# # #     BaseMessage,
# # #     HumanMessage,
# # #     SystemMessage,
# # #     ToolMessage,
# # # )

# # # from langchain_core.tools import tool

# # # # OpenAI model
# # # # pyrefly: ignore [missing-import]
# # # from langchain_openai import ChatOpenAI

# # # from langgraph.graph import END, START, StateGraph
# # # from langgraph.graph.message import add_messages
# # # from langgraph.prebuilt import ToolNode, tools_condition


# # # # ============================================================
# # # # BUSINESS TOOL IMPORTS
# # # # ============================================================

# # # from tools.root_tools.customer_details_tool import customer_details

# # # from tools.Fetch_tools.vehicle_and_license_accident_lookup import (
# # #     fetch_vehicle_driver_accident_details
# # # )

# # # from tools.Fetch_tools.violation_insurance_history_license_status import (
# # #     fetch_driver_related_details
# # # )

# # # from tools.Coverage_tools.IDV_details import (
# # #     IDV_calculation
# # # )

# # # from tools.Coverage_tools.coverage_calculation_details import (
# # #     coverage_calculation
# # # )

# # # from tools.Coverage_tools.plan_breakdown_tool import (
# # #     plan_breakdown
# # # )

# # # from tools.Payment_tools.payment_details_insert import (
# # #     insert_payment
# # # )

# # # from tools.Payment_tools.payment_pdf_creation import (
# # #     create_pdf_and_upload
# # # )

# # # from tools.Policy_Issuance_tools.policy_issuance_details import (
# # #     policy_pdf_details
# # # )

# # # from tools.email_tools.email_tools import (
# # #     send_email_tool as _send_email
# # # )


# # # INSTRUCTIONS_FILE = (
# # #     Path(__file__).resolve().parent
# # #     / "auto_policy_advisor_langgraph_instructions.md"
# # # )

# # # def load_instructions() -> str:
# # #     if not INSTRUCTIONS_FILE.exists():
# # #         raise FileNotFoundError(
# # #             f"Instruction file not found: {INSTRUCTIONS_FILE}"
# # #         )

# # #     return INSTRUCTIONS_FILE.read_text(encoding="utf-8")


# # # INSTRUCTIONS = load_instructions()

# # # # ============================================================
# # # # LANGGRAPH STATE
# # # # ============================================================

# # # class PolicyState(TypedDict, total=False):

# # #     messages: Annotated[
# # #         list[BaseMessage],
# # #         add_messages
# # #     ]

# # #     customer_id: str

# # #     customer: dict

# # #     vehicle: dict

# # #     driver: dict

# # #     accident: dict

# # #     driver_history: dict

# # #     coverage: dict

# # #     selected_plan: str

# # #     premium: float

# # #     payment: dict

# # #     payment_receipt: dict

# # #     policy: dict

# # #     policy_document: dict

# # #     email_result: dict

# # #     current_stage: str

# # #     error: str


# # # # ============================================================
# # # # LANGCHAIN TOOL WRAPPERS
# # # # ============================================================

# # # @tool
# # # def customer_details_tool(custid: str) -> dict:
# # #     """
# # #     Find an existing customer by customer ID in the local capstone dataset.
# # #     """
# # #     return customer_details(custid)


# # # @tool
# # # def lookup_tool(vin: str, license_number: str) -> dict:
# # #     """
# # #     Fetch local vehicle, driver and accident information
# # #     using VIN and license number.
# # #     """
# # #     return fetch_vehicle_driver_accident_details(
# # #         vin,
# # #         license_number
# # #     )


# # # @tool
# # # def driver_lookup_tool(driver_id: str) -> dict:
# # #     """
# # #     Fetch local insurance history, license status and
# # #     violation details for a driver.
# # #     """
# # #     return fetch_driver_related_details(driver_id)


# # # @tool
# # # def IDV_calculation_tool(
# # #     vehicle_price: float,
# # #     depreciation_rate: float
# # # ) -> float:
# # #     """
# # #     Calculate IDV.

# # #     Always use this tool rather than calculating IDV
# # #     directly in the model.
# # #     """
# # #     return IDV_calculation(
# # #         vehicle_price,
# # #         depreciation_rate
# # #     )


# # # @tool
# # # def coverage_calculation_tool(
# # #     base_premium: float,
# # #     age_factor: float,
# # #     driving_history_factor: float,
# # #     years_licensed_factor: float,
# # #     mileage_factor: float,
# # #     usage_factor: float,
# # #     location_factor: float,
# # #     safety_discount: float,
# # #     idv_value: float,
# # #     collision_percentage: float,
# # #     comprehensive_percentage: float,
# # #     liability_limit: float,
# # #     liability_limit_multiplier: float,
# # # ) -> dict:
# # #     """
# # #     Calculate liability, collision and comprehensive
# # #     premium values.
# # #     """

# # #     return coverage_calculation(
# # #         base_premium,
# # #         age_factor,
# # #         driving_history_factor,
# # #         years_licensed_factor,
# # #         mileage_factor,
# # #         usage_factor,
# # #         location_factor,
# # #         safety_discount,
# # #         idv_value,
# # #         collision_percentage,
# # #         comprehensive_percentage,
# # #         liability_limit,
# # #         liability_limit_multiplier,
# # #     )


# # # @tool
# # # def plan_breakdown_tool(
# # #     selected_plan: str,
# # #     base_price: float,
# # #     addon_names: list[str],
# # #     discount_percentage: float = 10,
# # # ) -> dict:
# # #     """
# # #     Calculate the final plan/add-on/discount breakdown.
# # #     """

# # #     return plan_breakdown(
# # #         selected_plan,
# # #         base_price,
# # #         addon_names,
# # #         discount_percentage,
# # #     )


# # # @tool
# # # def insert_payment_tool(
# # #     CustomerName: str,
# # #     Vehicle: str,
# # #     VIN: str,
# # #     PlateNumber: str,
# # #     License: str,
# # #     Address: str,
# # #     Policytype: str,
# # #     ZipCode: str,
# # #     PaymentMethod: str,
# # #     PaymentAmount: float,
# # #     PaymentStatus: str,
# # # ) -> dict:
# # #     """
# # #     Record a capstone payment locally.

# # #     Never stores a full card number.
# # #     """

# # #     return insert_payment(
# # #         CustomerName,
# # #         Vehicle,
# # #         VIN,
# # #         PlateNumber,
# # #         License,
# # #         Address,
# # #         Policytype,
# # #         ZipCode,
# # #         PaymentMethod,
# # #         PaymentAmount,
# # #         PaymentStatus,
# # #     )


# # # @tool
# # # def payment_pdf_tool(
# # #     Transaction_ID: str,
# # #     Customer_ID: str,
# # #     Policy_ID: str,
# # #     CustomerName: str,
# # #     Vehicle: str,
# # #     VIN: str,
# # #     PlateNumber: str,
# # #     License: str,
# # #     Address: str,
# # #     PolicyType: str,
# # #     PaymentMethod: str,
# # #     PaymentAmount: float,
# # #     PaymentStatus: str,
# # #     PaymentDateTime: str,
# # # ) -> dict:
# # #     """
# # #     Generate a local payment receipt PDF.
# # #     """

# # #     return create_pdf_and_upload(
# # #         Transaction_ID,
# # #         Customer_ID,
# # #         Policy_ID,
# # #         CustomerName,
# # #         Vehicle,
# # #         VIN,
# # #         PlateNumber,
# # #         License,
# # #         Address,
# # #         PolicyType,
# # #         PaymentMethod,
# # #         PaymentAmount,
# # #         PaymentStatus,
# # #         PaymentDateTime,
# # #     )


# # # @tool
# # # def policy_pdf_tool(
# # #     policy_details: dict,
# # #     vehicle_details: dict,
# # #     driver_details: dict,
# # # ) -> dict:
# # #     """
# # #     Generate the three-page local policy PDF.
# # #     """

# # #     return policy_pdf_details(
# # #         policy_details,
# # #         vehicle_details,
# # #         driver_details,
# # #     )


# # # @tool
# # # def send_email_tool(
# # #     to_email: str,
# # #     subject: str,
# # #     body_text: str,
# # #     from_email: str = "",
# # # ) -> dict:
# # #     """
# # #     Send a policy email through Gmail when credentials
# # #     are configured in .env.
# # #     """

# # #     return _send_email(
# # #         {
# # #             "to_email": to_email,
# # #             "subject": subject,
# # #             "body_text": body_text,
# # #             "from_email": (
# # #                 from_email
# # #                 or os.getenv("GMAIL_SENDER_EMAIL", "")
# # #             ),
# # #         }
# # #     )


# # # # ============================================================
# # # # TOOL COLLECTION
# # # # ============================================================

# # # TOOLS = [
# # #     customer_details_tool,
# # #     lookup_tool,
# # #     driver_lookup_tool,
# # #     IDV_calculation_tool,
# # #     coverage_calculation_tool,
# # #     plan_breakdown_tool,
# # #     insert_payment_tool,
# # #     payment_pdf_tool,
# # #     policy_pdf_tool,
# # #     send_email_tool,
# # # ]


# # # # ============================================================
# # # # BUILD LANGGRAPH
# # # # ============================================================

# # # def build_graph():

# # #     model_name = os.getenv(
# # #         "OPENAI_MODEL",
# # #         "gpt-5.6-luna"
# # #     )

# # #     api_key = os.getenv("OPENAI_API_KEY")

# # #     if not api_key:
# # #         raise RuntimeError(
# # #             "OPENAI_API_KEY was not found. "
# # #             "Please check your .env file."
# # #         )

# # #     llm = ChatOpenAI(
# # #         model=model_name,
# # #         api_key=api_key,
# # #         reasoning_effort="none",
# # #     )

# # #     llm_with_tools = llm.bind_tools(TOOLS)

# # #     # ========================================================
# # #     # ASSISTANT NODE
# # #     # ========================================================

# # #     def assistant_node(state: PolicyState):

# # #         messages = state.get(
# # #             "messages",
# # #             []
# # #         )

# # #         # Current workflow state is included in the prompt
# # #         # so the model can maintain context.
# # #         state_snapshot = {

# # #             "customer_id": state.get(
# # #                 "customer_id"
# # #             ),

# # #             "customer": state.get(
# # #                 "customer"
# # #             ),

# # #             "vehicle": state.get(
# # #                 "vehicle"
# # #             ),

# # #             "driver": state.get(
# # #                 "driver"
# # #             ),

# # #             "accident": state.get(
# # #                 "accident"
# # #             ),

# # #             "driver_history": state.get(
# # #                 "driver_history"
# # #             ),

# # #             "coverage": state.get(
# # #                 "coverage"
# # #             ),

# # #             "selected_plan": state.get(
# # #                 "selected_plan"
# # #             ),

# # #             "premium": state.get(
# # #                 "premium"
# # #             ),

# # #             "payment": state.get(
# # #                 "payment"
# # #             ),

# # #             "policy_document": state.get(
# # #                 "policy_document"
# # #             ),
# # #         }

# # #         system = SystemMessage(
# # #             content=(
# # #                 INSTRUCTIONS
# # #                 + "\n\nCURRENT WORKFLOW STATE:\n"
# # #                 + json.dumps(state_snapshot, default=str)
# # #             )
# # #         )

# # #         response = llm_with_tools.invoke(
# # #             [
# # #                 system,
# # #                 *messages
# # #             ]
# # #         )

# # #         return {
# # #             "messages": [
# # #                 response
# # #             ],
# # #             "current_stage": "assistant",
# # #         }


# # #     # ========================================================
# # #     # STATE SYNCHRONIZATION NODE
# # #     # ========================================================

# # #     def sync_state_node(
# # #         state: PolicyState
# # #     ):

# # #         updates: dict[str, Any] = {}

# # #         # Look backwards through the conversation
# # #         # to find the latest tool response.
# # #         for message in reversed(
# # #             state.get("messages", [])
# # #         ):

# # #             if not isinstance(
# # #                 message,
# # #                 ToolMessage
# # #             ):
# # #                 continue

# # #             try:

# # #                 if isinstance(
# # #                     message.content,
# # #                     str
# # #                 ):

# # #                     try:

# # #                         payload = json.loads(
# # #                             message.content
# # #                         )

# # #                     except json.JSONDecodeError:

# # #                         payload = ast.literal_eval(
# # #                             message.content
# # #                         )

# # #                 else:

# # #                     payload = message.content

# # #             except Exception:

# # #                 continue


# # #             name = message.name or ""


# # #             # ------------------------------------------------
# # #             # Customer lookup
# # #             # ------------------------------------------------

# # #             if (
# # #                 name == "customer_details_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["customer"] = payload

# # #                 updates["customer_id"] = (
# # #                     payload.get("custid")
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "customer_lookup"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Vehicle / Driver / Accident lookup
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name == "lookup_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["vehicle"] = (
# # #                     payload.get(
# # #                         "vehicle_details",
# # #                         {}
# # #                     )
# # #                 )

# # #                 updates["driver"] = (
# # #                     payload.get(
# # #                         "driver_details",
# # #                         {}
# # #                     )
# # #                 )

# # #                 updates["accident"] = (
# # #                     payload.get(
# # #                         "accident_details",
# # #                         {}
# # #                     )
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "details_fetched"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Driver history
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name == "driver_lookup_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["driver_history"] = (
# # #                     payload
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "driver_history_fetched"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Coverage / Plan
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name in {
# # #                     "coverage_calculation_tool",
# # #                     "plan_breakdown_tool",
# # #                 }
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["coverage"] = (
# # #                     payload
# # #                 )

# # #                 if "total_premium" in payload:

# # #                     updates["premium"] = (
# # #                         payload.get(
# # #                             "total_premium"
# # #                         )
# # #                     )

# # #                     updates["selected_plan"] = (
# # #                         payload.get(
# # #                             "coverage"
# # #                         )
# # #                     )

# # #                 updates["current_stage"] = (
# # #                     "coverage_calculated"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Payment
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name == "insert_payment_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["payment"] = (
# # #                     payload
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "payment_recorded"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Payment PDF
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name == "payment_pdf_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["payment_receipt"] = (
# # #                     payload
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "receipt_created"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Policy PDF
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name == "policy_pdf_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["policy_document"] = (
# # #                     payload
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "policy_created"
# # #                 )


# # #             # ------------------------------------------------
# # #             # Email
# # #             # ------------------------------------------------

# # #             elif (
# # #                 name == "send_email_tool"
# # #                 and isinstance(payload, dict)
# # #             ):

# # #                 updates["email_result"] = (
# # #                     payload
# # #                 )

# # #                 updates["current_stage"] = (
# # #                     "email_completed"
# # #                 )


# # #             # Stop once the most recent relevant
# # #             # tool result has been processed.
# # #             if updates:

# # #                 break


# # #         return updates


# # #     # ========================================================
# # #     # STATE GRAPH
# # #     # ========================================================

# # #     builder = StateGraph(
# # #         PolicyState
# # #     )


# # #     # --------------------------------------------------------
# # #     # Nodes
# # #     # --------------------------------------------------------

# # #     builder.add_node(
# # #         "assistant",
# # #         assistant_node
# # #     )

# # #     builder.add_node(
# # #         "tools",
# # #         ToolNode(TOOLS)
# # #     )

# # #     builder.add_node(
# # #         "sync_state",
# # #         sync_state_node
# # #     )


# # #     # --------------------------------------------------------
# # #     # START
# # #     # --------------------------------------------------------

# # #     builder.add_edge(
# # #         START,
# # #         "assistant"
# # #     )


# # #     # --------------------------------------------------------
# # #     # Conditional routing
# # #     #
# # #     # If OpenAI requests a tool:
# # #     #     assistant -> tools
# # #     #
# # #     # If OpenAI gives a final response:
# # #     #     assistant -> END
# # #     # --------------------------------------------------------

# # #     builder.add_conditional_edges(
# # #         "assistant",
# # #         tools_condition,
# # #         {
# # #             "tools": "tools",
# # #             END: END,
# # #         }
# # #     )


# # #     # --------------------------------------------------------
# # #     # After tools execute, synchronize state
# # #     # --------------------------------------------------------

# # #     builder.add_edge(
# # #         "tools",
# # #         "sync_state"
# # #     )


# # #     # --------------------------------------------------------
# # #     # Then return to assistant
# # #     # --------------------------------------------------------

# # #     builder.add_edge(
# # #         "sync_state",
# # #         "assistant"
# # #     )


# # #     # --------------------------------------------------------
# # #     # Compile graph
# # #     # --------------------------------------------------------

# # #     return builder.compile()


# # # # ============================================================
# # # # GRAPH INSTANCE
# # # # ============================================================

# # # graph = build_graph()

# # # # Keep root_agent alias for compatibility with
# # # # the existing application.
# # # root_agent = graph


# # # # ============================================================
# # # # DIRECT INVOCATION HELPER
# # # # ============================================================

# # # def invoke(
# # #     user_message: str,
# # #     history: list[BaseMessage] | None = None
# # # ) -> dict[str, Any]:

# # #     messages = (
# # #         list(history or [])
# # #         + [
# # #             HumanMessage(
# # #                 content=user_message
# # #             )
# # #         ]
# # #     )

# # #     return graph.invoke(
# # #         {
# # #             "messages": messages
# # #         }
# # #     )


# # """LangGraph orchestration for the Auto Policy Advisor capstone.

# # Structured as root-agent / sub-agent, ADK-style:

# # - Each stage of the flow (Quote, Fetch Details, Coverage, Payment,
# #   Policy Issuance, Email) is its own LangGraph node — a "sub-agent" with
# #   its own system instructions (from instructions.py) and its own scoped
# #   subset of tools.
# # - A `transfer_to_node` tool stands in for ADK's `transfer_to_agent`: a
# #   sub-agent calls it explicitly when its instructions say to hand off to
# #   another node. sync_state_node watches for that call and updates
# #   state["active_node"].
# # - A router — used both as the graph's entry point and after every tool
# #   call — reads state["active_node"] and dispatches to the matching
# #   sub-agent node. This router is effectively the "root agent": it doesn't
# #   reason about the conversation itself, it just delegates.

# # The business tools remain ordinary Python functions; only the wiring
# # around them changed.
# # """

# # from __future__ import annotations

# # import os
# # import json
# # import ast
# # from typing import Annotated, Any, Literal, TypedDict

# # from dotenv import load_dotenv

# # load_dotenv()

# # from langchain_core.messages import (
# #     BaseMessage,
# #     HumanMessage,
# #     SystemMessage,
# #     ToolMessage,
# # )

# # from langchain_core.tools import tool

# # # pyrefly: ignore [missing-import]
# # from langchain_openai import ChatOpenAI

# # from langgraph.graph import END, START, StateGraph
# # from langgraph.graph.message import add_messages
# # from langgraph.prebuilt import ToolNode, tools_condition


# # # ============================================================
# # # INSTRUCTIONS (one block per sub-agent)
# # # ============================================================

# # from instructions import (
# #     QUOTE_NODE_INSTRUCTIONS,
# #     FETCH_DETAILS_NODE_INSTRUCTIONS,
# #     COVERAGE_NODE_INSTRUCTIONS,
# #     PAYMENT_NODE_INSTRUCTIONS,
# #     POLICY_ISSUANCE_NODE_INSTRUCTIONS,
# #     EMAIL_NODE_INSTRUCTIONS,
# # )


# # # ============================================================
# # # BUSINESS TOOL IMPORTS
# # # ============================================================

# # from tools.root_tools.customer_details_tool import customer_details

# # from tools.Fetch_tools.vehicle_and_license_accident_lookup import (
# #     fetch_vehicle_driver_accident_details,
# # )

# # from tools.Fetch_tools.violation_insurance_history_license_status import (
# #     fetch_driver_related_details,
# # )

# # from tools.Coverage_tools.IDV_details import IDV_calculation

# # from tools.Coverage_tools.coverage_calculation_details import (
# #     coverage_calculation,
# # )

# # from tools.Coverage_tools.plan_breakdown_tool import plan_breakdown

# # from tools.Payment_tools.payment_details_insert import insert_payment

# # from tools.Payment_tools.payment_pdf_creation import create_pdf_and_upload

# # from tools.Policy_Issuance_tools.policy_issuance_details import (
# #     policy_pdf_details,
# # )

# # from tools.email_tools.email_tools import send_email_tool as _send_email


# # # ============================================================
# # # LANGGRAPH STATE
# # # ============================================================

# # NodeName = Literal[
# #     "quote",
# #     "fetch_details",
# #     "coverage",
# #     "payment",
# #     "policy_issuance",
# #     "email",
# # ]


# # class PolicyState(TypedDict, total=False):

# #     messages: Annotated[list[BaseMessage], add_messages]

# #     # Root-agent bookkeeping: which sub-agent handles the next step.
# #     active_node: NodeName

# #     customer_id: str
# #     customer: dict
# #     vehicle: dict
# #     driver: dict
# #     accident: dict
# #     driver_history: dict
# #     coverage: dict
# #     selected_plan: str
# #     premium: float
# #     payment: dict
# #     payment_receipt: dict
# #     policy: dict
# #     policy_document: dict
# #     email_result: dict

# #     current_stage: str
# #     error: str


# # # ============================================================
# # # LANGCHAIN TOOL WRAPPERS (business tools)
# # # ============================================================

# # @tool
# # def customer_details_tool(custid: str) -> dict:
# #     """Find an existing customer by customer ID in the local capstone dataset."""
# #     return customer_details(custid)


# # @tool
# # def vehicle_lookup_tool(vin: str, license_number: str) -> dict:
# #     """Fetch local vehicle, driver and accident information using VIN and license number."""
# #     return fetch_vehicle_driver_accident_details(vin, license_number)


# # # @tool
# # # def driver_lookup_tool(driver_id: str) -> dict:
# # #     """Fetch local insurance history, license status and violation details for a driver."""
# # #     return fetch_driver_related_details(driver_id)


# # @tool
# # def IDV_calculation_tool(vehicle_price: float, depreciation_rate: float) -> float:
# #     """Calculate IDV. Always use this tool rather than calculating IDV directly in the model."""
# #     return IDV_calculation(vehicle_price, depreciation_rate)


# # @tool
# # def coverage_calculation_tool(
# #     base_premium: float,
# #     age_factor: float,
# #     driving_history_factor: float,
# #     years_licensed_factor: float,
# #     mileage_factor: float,
# #     usage_factor: float,
# #     location_factor: float,
# #     safety_discount: float,
# #     idv_value: float,
# #     collision_percentage: float,
# #     comprehensive_percentage: float,
# #     liability_limit: float,
# #     liability_limit_multiplier: float,
# # ) -> dict:
# #     """Calculate liability, collision and comprehensive premium values."""
# #     return coverage_calculation(
# #         base_premium,
# #         age_factor,
# #         driving_history_factor,
# #         years_licensed_factor,
# #         mileage_factor,
# #         usage_factor,
# #         location_factor,
# #         safety_discount,
# #         idv_value,
# #         collision_percentage,
# #         comprehensive_percentage,
# #         liability_limit,
# #         liability_limit_multiplier,
# #     )


# # @tool
# # def plan_breakdown_tool(
# #     selected_plan: str,
# #     base_price: float,
# #     addon_names: list[str],
# #     discount_percentage: float = 10,
# # ) -> dict:
# #     """Calculate the final plan/add-on/discount breakdown."""
# #     return plan_breakdown(selected_plan, base_price, addon_names, discount_percentage)


# # @tool
# # def insert_payment_tool(
# #     CustomerName: str,
# #     Vehicle: str,
# #     VIN: str,
# #     PlateNumber: str,
# #     License: str,
# #     Address: str,
# #     Policytype: str,
# #     ZipCode: str,
# #     PaymentMethod: str,
# #     PaymentAmount: float,
# #     PaymentStatus: str,
# # ) -> dict:
# #     """Record a capstone payment locally. Never stores a full card number."""
# #     return insert_payment(
# #         CustomerName,
# #         Vehicle,
# #         VIN,
# #         PlateNumber,
# #         License,
# #         Address,
# #         Policytype,
# #         ZipCode,
# #         PaymentMethod,
# #         PaymentAmount,
# #         PaymentStatus,
# #     )


# # @tool
# # def payment_pdf_tool(
# #     Transaction_ID: str,
# #     Customer_ID: str,
# #     Policy_ID: str,
# #     CustomerName: str,
# #     Vehicle: str,
# #     VIN: str,
# #     PlateNumber: str,
# #     License: str,
# #     Address: str,
# #     PolicyType: str,
# #     PaymentMethod: str,
# #     PaymentAmount: float,
# #     PaymentStatus: str,
# #     PaymentDateTime: str,
# # ) -> dict:
# #     """Generate a local payment receipt PDF."""
# #     return create_pdf_and_upload(
# #         Transaction_ID,
# #         Customer_ID,
# #         Policy_ID,
# #         CustomerName,
# #         Vehicle,
# #         VIN,
# #         PlateNumber,
# #         License,
# #         Address,
# #         PolicyType,
# #         PaymentMethod,
# #         PaymentAmount,
# #         PaymentStatus,
# #         PaymentDateTime,
# #     )


# # @tool
# # def policy_pdf_tool(policy_details: dict, vehicle_details: dict, driver_details: dict) -> dict:
# #     """Generate the three-page local policy PDF."""
# #     return policy_pdf_details(policy_details, vehicle_details, driver_details)


# # @tool
# # def send_email_tool(to_email: str, subject: str, body_text: str, from_email: str = "") -> dict:
# #     """Send a policy email through Gmail when credentials are configured in .env."""
# #     return _send_email(
# #         {
# #             "to_email": to_email,
# #             "subject": subject,
# #             "body_text": body_text,
# #             "from_email": from_email or os.getenv("GMAIL_SENDER_EMAIL", ""),
# #         }
# #     )


# # # ============================================================
# # # HAND-OFF TOOL (stands in for ADK's transfer_to_agent)
# # # ============================================================

# # _VALID_TARGETS = {
# #     "quote",
# #     "fetch_details",
# #     "coverage",
# #     "payment",
# #     "policy_issuance",
# #     "email",
# # }


# # @tool
# # def transfer_to_node(target_node: str) -> dict:
# #     """Hand the conversation off to another sub-agent node.

# #     Call this when your own node's instructions say to route the workflow
# #     to another node (e.g. after the user confirms fetched details, call
# #     transfer_to_node(target_node="coverage")).

# #     target_node must be one of: quote, fetch_details, coverage, payment,
# #     policy_issuance, email.
# #     """
# #     if target_node not in _VALID_TARGETS:
# #         return {"status": "error", "message": f"Unknown target_node '{target_node}'"}
# #     return {"status": "success", "target_node": target_node}


# # # ============================================================
# # # PER-NODE TOOL SCOPES AND INSTRUCTIONS
# # # ============================================================
# # # This is the "sub-agent" definition table: each node only gets the tools
# # # and the instructions relevant to its own stage of the flow, instead of
# # # one assistant seeing all ten tools and one giant prompt.

# # NODE_INSTRUCTIONS: dict[NodeName, str] = {
# #     "quote": QUOTE_NODE_INSTRUCTIONS,
# #     "fetch_details": FETCH_DETAILS_NODE_INSTRUCTIONS,
# #     "coverage": COVERAGE_NODE_INSTRUCTIONS,
# #     "payment": PAYMENT_NODE_INSTRUCTIONS,
# #     "policy_issuance": POLICY_ISSUANCE_NODE_INSTRUCTIONS,
# #     "email": EMAIL_NODE_INSTRUCTIONS,
# # }

# # NODE_TOOLS: dict[NodeName, list] = {
# #     "quote": [customer_details_tool, transfer_to_node],
# #     "fetch_details": [vehicle_lookup_tool, transfer_to_node],
# #     "coverage": [
# #         IDV_calculation_tool,
# #         coverage_calculation_tool,
# #         plan_breakdown_tool,
# #         transfer_to_node,
# #     ],
# #     "payment": [insert_payment_tool, payment_pdf_tool, transfer_to_node],
# #     "policy_issuance": [policy_pdf_tool, transfer_to_node],
# #     "email": [send_email_tool],
# # }

# # NODE_NAMES: list[NodeName] = list(NODE_INSTRUCTIONS.keys())


# # # ============================================================
# # # BUILD LANGGRAPH
# # # ============================================================

# # def build_graph():

# #     model_name = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
# #     api_key = os.getenv("OPENAI_API_KEY")

# #     if not api_key:
# #         raise RuntimeError("OPENAI_API_KEY was not found. Please check your .env file.")

# #     base_llm = ChatOpenAI(model=model_name, api_key=api_key, reasoning_effort="none")

# #     # One tool-bound LLM per sub-agent, each seeing only its own tools.
# #     llm_by_node = {name: base_llm.bind_tools(tools) for name, tools in NODE_TOOLS.items()}

# #     # ========================================================
# #     # SUB-AGENT NODE FACTORY
# #     # ========================================================

# #     def make_agent_node(name: NodeName):

# #         instructions = NODE_INSTRUCTIONS[name]
# #         llm_with_tools = llm_by_node[name]

# #         def agent_node(state: PolicyState):

# #             messages = state.get("messages", [])

# #             state_snapshot = {
# #                 "active_node": name,
# #                 "customer_id": state.get("customer_id"),
# #                 "customer": state.get("customer"),
# #                 "vehicle": state.get("vehicle"),
# #                 "driver": state.get("driver"),
# #                 "accident": state.get("accident"),
# #                 "driver_history": state.get("driver_history"),
# #                 "coverage": state.get("coverage"),
# #                 "selected_plan": state.get("selected_plan"),
# #                 "premium": state.get("premium"),
# #                 "payment": state.get("payment"),
# #                 "payment_receipt": state.get("payment_receipt"),
# #                 "policy_document": state.get("policy_document"),
# #             }

# #             system = SystemMessage(
# #                 content=(
# #                     instructions
# #                     + "\n\nCURRENT WORKFLOW STATE:\n"
# #                     + json.dumps(state_snapshot, default=str)
# #                 )
# #             )

# #             response = llm_with_tools.invoke([system, *messages])

# #             return {
# #                 "messages": [response],
# #                 "current_stage": name,
# #             }

# #         return agent_node

# #     # ========================================================
# #     # STATE SYNCHRONIZATION NODE (per sub-agent, shares one impl)
# #     # ========================================================

# #     def make_sync_state_node(name: NodeName):

# #         def sync_state_node(state: PolicyState):

# #             updates: dict[str, Any] = {}

# #             for message in reversed(state.get("messages", [])):

# #                 if not isinstance(message, ToolMessage):
# #                     continue

# #                 try:
# #                     if isinstance(message.content, str):
# #                         try:
# #                             payload = json.loads(message.content)
# #                         except json.JSONDecodeError:
# #                             payload = ast.literal_eval(message.content)
# #                     else:
# #                         payload = message.content
# #                 except Exception:
# #                     continue

# #                 tool_name = message.name or ""

# #                 # Hand-off: update which sub-agent is active.
# #                 if tool_name == "transfer_to_node" and isinstance(payload, dict):
# #                     target = payload.get("target_node")
# #                     if target in _VALID_TARGETS:
# #                         updates["active_node"] = target

# #                 elif tool_name == "customer_details_tool" and isinstance(payload, dict):
# #                     updates["customer"] = payload
# #                     updates["customer_id"] = payload.get("custid")

# #                 elif tool_name == "vehicle_lookup_tool" and isinstance(payload, dict):
# #                     updates["vehicle"] = payload.get("vehicle_details", {})
# #                     updates["driver"] = payload.get("driver_details", {})
# #                     updates["accident"] = payload.get("accident_details", {})

# #                 # elif tool_name == "driver_lookup_tool" and isinstance(payload, dict):
# #                 #     updates["driver_history"] = payload

# #                 elif tool_name in {
# #                     "coverage_calculation_tool",
# #                     "plan_breakdown_tool",
# #                 } and isinstance(payload, dict):
# #                     updates["coverage"] = payload
# #                     if "total_premium" in payload:
# #                         updates["premium"] = payload.get("total_premium")
# #                         updates["selected_plan"] = payload.get("coverage")

# #                 elif tool_name == "insert_payment_tool" and isinstance(payload, dict):
# #                     updates["payment"] = payload

# #                 elif tool_name == "payment_pdf_tool" and isinstance(payload, dict):
# #                     updates["payment_receipt"] = payload

# #                 elif tool_name == "policy_pdf_tool" and isinstance(payload, dict):
# #                     updates["policy_document"] = payload

# #                 elif tool_name == "send_email_tool" and isinstance(payload, dict):
# #                     updates["email_result"] = payload

# #                 if updates:
# #                     break

# #             # Default: stay on the current sub-agent unless a hand-off fired.
# #             updates.setdefault("active_node", name)
# #             return updates

# #         return sync_state_node

# #     # ========================================================
# #     # ROUTER ("root agent") — dispatches by active_node
# #     # ========================================================

# #     def route_to_active_node(state: PolicyState) -> NodeName:
# #         return state.get("active_node", "quote")

# #     # ========================================================
# #     # STATE GRAPH
# #     # ========================================================

# #     builder = StateGraph(PolicyState)

# #     for name in NODE_NAMES:
# #         builder.add_node(name, make_agent_node(name))
# #         builder.add_node(f"{name}_tools", ToolNode(NODE_TOOLS[name]))
# #         builder.add_node(f"{name}_sync", make_sync_state_node(name))

# #     # Entry: root router picks the first sub-agent to run, based on
# #     # whatever active_node was left in state (defaults to "quote" for a
# #     # brand new conversation/thread).
# #     builder.add_conditional_edges(
# #         START,
# #         route_to_active_node,
# #         {name: name for name in NODE_NAMES},
# #     )

# #     for name in NODE_NAMES:

# #         # Sub-agent decides: call a tool, or hand control back (END, i.e.
# #         # wait for the next user message).
# #         builder.add_conditional_edges(
# #             name,
# #             tools_condition,
# #             {"tools": f"{name}_tools", END: END},
# #         )

# #         builder.add_edge(f"{name}_tools", f"{name}_sync")

# #         # After syncing state, route again: if a hand-off tool fired,
# #         # active_node now points at a different sub-agent, so this jumps
# #         # straight there in the same turn (mirrors ADK's transfer). If no
# #         # hand-off happened, this loops back into the same sub-agent so it
# #         # can react to the tool result.
# #         builder.add_conditional_edges(
# #             f"{name}_sync",
# #             route_to_active_node,
# #             {n: n for n in NODE_NAMES},
# #         )

# #     return builder.compile()


# # # ============================================================
# # # GRAPH INSTANCE
# # # ============================================================

# # graph = build_graph()

# # # Keep root_agent alias for compatibility with the existing application.
# # root_agent = graph


# # # ============================================================
# # # DIRECT INVOCATION HELPER
# # # ============================================================

# # def invoke(user_message: str, history: list[BaseMessage] | None = None) -> dict[str, Any]:

# #     messages = list(history or []) + [HumanMessage(content=user_message)]

# #     return graph.invoke({"messages": messages})


# from __future__ import annotations

# import os
# import json
# import ast
# from typing import Annotated, Any, Literal, TypedDict

# from dotenv import load_dotenv

# load_dotenv()

# from langchain_core.messages import (
#     BaseMessage,
#     HumanMessage,
#     SystemMessage,
#     ToolMessage,
# )

# from langchain_core.tools import tool

# # pyrefly: ignore [missing-import]
# from langchain_openai import ChatOpenAI

# from langgraph.graph import END, START, StateGraph
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition


# # ============================================================
# # INSTRUCTIONS (one block per sub-agent)
# # ============================================================

# from instructions import (
#     QUOTE_NODE_INSTRUCTIONS,
#     FETCH_DETAILS_NODE_INSTRUCTIONS,
#     COVERAGE_NODE_INSTRUCTIONS,
#     PAYMENT_NODE_INSTRUCTIONS,
#     POLICY_ISSUANCE_NODE_INSTRUCTIONS,
#     EMAIL_NODE_INSTRUCTIONS,
# )


# # ============================================================
# # BUSINESS TOOL IMPORTS
# # ============================================================

# from tools.root_tools.customer_details_tool import customer_details

# from tools.Fetch_tools.vehicle_and_license_accident_lookup import (
#     fetch_vehicle_driver_accident_details,
# )

# from tools.Fetch_tools.violation_insurance_history_license_status import (
#     fetch_driver_related_details,
# )

# from tools.Coverage_tools.IDV_details import IDV_calculation

# from tools.Coverage_tools.coverage_calculation_details import (
#     coverage_calculation,
# )

# from tools.Coverage_tools.plan_breakdown_tool import plan_breakdown

# from tools.Payment_tools.payment_details_insert import insert_payment

# from tools.Payment_tools.payment_pdf_creation import create_pdf_and_upload

# from tools.Policy_Issuance_tools.policy_issuance_details import (
#     policy_pdf_details,
# )

# from tools.email_tools.email_tools import send_email_tool as _send_email


# # ============================================================
# # LANGGRAPH STATE
# # ============================================================

# NodeName = Literal[
#     "quote",
#     "fetch_details",
#     "coverage",
#     "payment",
#     "policy_issuance",
#     "email",
# ]


# class PolicyState(TypedDict, total=False):

#     messages: Annotated[list[BaseMessage], add_messages]

#     # Root-agent bookkeeping: which sub-agent handles the next step.
#     active_node: NodeName

#     customer_id: str
#     customer: dict
#     vehicle: dict
#     driver: dict
#     accident: dict
#     driver_history: dict
#     coverage: dict
#     selected_plan: str
#     premium: float
#     payment: dict
#     payment_receipt: dict
#     policy: dict
#     policy_document: dict
#     email_result: dict

#     current_stage: str
#     error: str


# # ============================================================
# # LANGCHAIN TOOL WRAPPERS (business tools)
# # ============================================================

# @tool
# def customer_details_tool(custid: str) -> dict:
#     """Find an existing customer by customer ID in the local capstone dataset."""
#     return customer_details(custid)


# @tool
# def vehicle_lookup_tool(vin: str, license_number: str) -> dict:
#     """Fetch local vehicle, driver and accident information using VIN and license number."""
#     return fetch_vehicle_driver_accident_details(vin, license_number)


# # @tool
# # def driver_lookup_tool(driver_id: str) -> dict:
# #     """Fetch local insurance history, license status and violation details for a driver."""
# #     return fetch_driver_related_details(driver_id)


# @tool
# def IDV_calculation_tool(vehicle_age: int, vehicle_price: float) -> dict:
#     """Calculate IDV from vehicle age and vehicle price.

#     Depreciation is selected inside the tool. The model does not calculate
#     IDV itself. This matches the Coverage Node instruction:
#     IDV_calculation_tool(vehicle_age, vehicle_price).
#     """
#     depreciation_by_age = {
#         0: 0.10,
#         1: 0.15,
#         2: 0.20,
#         3: 0.30,
#         4: 0.40,
#         5: 0.50,
#     }

#     age = int(vehicle_age)
#     depreciation_rate = (
#         depreciation_by_age[age]
#         if age in depreciation_by_age
#         else 0.60
#     )

#     idv_value = IDV_calculation(vehicle_price, depreciation_rate)

#     return {
#         "vehicle_age": age,
#         "vehicle_price": float(vehicle_price),
#         "depreciation_rate": depreciation_rate,
#         "idv": idv_value,
#     }
# @tool
# def coverage_calculation_tool(
#     base_premium: float,
#     age_factor: float,
#     driving_history_factor: float,
#     years_licensed_factor: float,
#     mileage_factor: float,
#     usage_factor: float,
#     location_factor: float,
#     safety_discount: float,
#     idv_value: float,
#     collision_percentage: float,
#     comprehensive_percentage: float,
#     liability_limit: float,
#     liability_limit_multiplier: float,
# ) -> dict:
#     """Calculate liability, collision and comprehensive premium values."""
#     return coverage_calculation(
#         base_premium,
#         age_factor,
#         driving_history_factor,
#         years_licensed_factor,
#         mileage_factor,
#         usage_factor,
#         location_factor,
#         safety_discount,
#         idv_value,
#         collision_percentage,
#         comprehensive_percentage,
#         liability_limit,
#         liability_limit_multiplier,
#     )


# @tool
# def plan_breakdown_tool(
#     selected_plan: str,
#     base_price: float,
#     addon_names: list[str],
#     discount_percentage: float = 10,
# ) -> dict:
#     """Calculate the final plan/add-on/discount breakdown."""
#     return plan_breakdown(selected_plan, base_price, addon_names, discount_percentage)


# @tool
# def insert_payment_tool(
#     CustomerName: str,
#     Vehicle: str,
#     VIN: str,
#     PlateNumber: str,
#     License: str,
#     Address: str,
#     Policytype: str,
#     ZipCode: str,
#     PaymentMethod: str,
#     PaymentAmount: float,
#     PaymentStatus: str,
# ) -> dict:
#     """Record a capstone payment locally. Never stores a full card number."""
#     return insert_payment(
#         CustomerName,
#         Vehicle,
#         VIN,
#         PlateNumber,
#         License,
#         Address,
#         Policytype,
#         ZipCode,
#         PaymentMethod,
#         PaymentAmount,
#         PaymentStatus,
#     )


# @tool
# def payment_pdf_tool(
#     Transaction_ID: str,
#     Customer_ID: str,
#     Policy_ID: str,
#     CustomerName: str,
#     Vehicle: str,
#     VIN: str,
#     PlateNumber: str,
#     License: str,
#     Address: str,
#     PolicyType: str,
#     PaymentMethod: str,
#     PaymentAmount: float,
#     PaymentStatus: str,
#     PaymentDateTime: str,
# ) -> dict:
#     """Generate a local payment receipt PDF."""
#     return create_pdf_and_upload(
#         Transaction_ID,
#         Customer_ID,
#         Policy_ID,
#         CustomerName,
#         Vehicle,
#         VIN,
#         PlateNumber,
#         License,
#         Address,
#         PolicyType,
#         PaymentMethod,
#         PaymentAmount,
#         PaymentStatus,
#         PaymentDateTime,
#     )


# @tool
# def policy_pdf_tool(policy_details: dict, vehicle_details: dict, driver_details: dict) -> dict:
#     """Generate the three-page local policy PDF."""
#     return policy_pdf_details(policy_details, vehicle_details, driver_details)


# @tool
# def send_email_tool(to_email: str, subject: str, body_text: str, from_email: str = "") -> dict:
#     """Send a policy email through Gmail when credentials are configured in .env."""
#     return _send_email(
#         {
#             "to_email": to_email,
#             "subject": subject,
#             "body_text": body_text,
#             "from_email": from_email or os.getenv("GMAIL_SENDER_EMAIL", ""),
#         }
#     )


# # ============================================================
# # HAND-OFF TOOL (stands in for ADK's transfer_to_agent)
# # ============================================================

# _VALID_TARGETS = {
#     "quote",
#     "fetch_details",
#     "coverage",
#     "payment",
#     "policy_issuance",
#     "email",
# }


# @tool
# def transfer_to_node(target_node: str) -> dict:
#     """Hand the conversation off to another sub-agent node.

#     Call this when your own node's instructions say to route the workflow
#     to another node (e.g. after the user confirms fetched details, call
#     transfer_to_node(target_node="coverage")).

#     target_node must be one of: quote, fetch_details, coverage, payment,
#     policy_issuance, email.
#     """
#     if target_node not in _VALID_TARGETS:
#         return {"status": "error", "message": f"Unknown target_node '{target_node}'"}
#     return {"status": "success", "target_node": target_node}


# # ============================================================
# # PER-NODE TOOL SCOPES AND INSTRUCTIONS
# # ============================================================
# # This is the "sub-agent" definition table: each node only gets the tools
# # and the instructions relevant to its own stage of the flow, instead of
# # one assistant seeing all ten tools and one giant prompt.

# NODE_INSTRUCTIONS: dict[NodeName, str] = {
#     "quote": QUOTE_NODE_INSTRUCTIONS,
#     "fetch_details": FETCH_DETAILS_NODE_INSTRUCTIONS,
#     "coverage": COVERAGE_NODE_INSTRUCTIONS,
#     "payment": PAYMENT_NODE_INSTRUCTIONS,
#     "policy_issuance": POLICY_ISSUANCE_NODE_INSTRUCTIONS,
#     "email": EMAIL_NODE_INSTRUCTIONS,
# }

# NODE_TOOLS: dict[NodeName, list] = {
#     "quote": [customer_details_tool, transfer_to_node],
#     "fetch_details": [vehicle_lookup_tool, transfer_to_node],
#     "coverage": [
#         IDV_calculation_tool,
#         coverage_calculation_tool,
#         plan_breakdown_tool,
#         transfer_to_node,
#     ],
#     "payment": [insert_payment_tool, payment_pdf_tool, transfer_to_node],
#     "policy_issuance": [policy_pdf_tool, transfer_to_node],
#     "email": [send_email_tool],
# }

# NODE_NAMES: list[NodeName] = list(NODE_INSTRUCTIONS.keys())


# # ============================================================
# # BUILD LANGGRAPH
# # ============================================================

# def build_graph():

#     model_name = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
#     api_key = os.getenv("OPENAI_API_KEY")

#     if not api_key:
#         raise RuntimeError("OPENAI_API_KEY was not found. Please check your .env file.")

#     base_llm = ChatOpenAI(model=model_name, api_key=api_key, reasoning_effort="none")

#     # One tool-bound LLM per sub-agent, each seeing only its own tools.
#     llm_by_node = {name: base_llm.bind_tools(tools) for name, tools in NODE_TOOLS.items()}

#     # ========================================================
#     # SUB-AGENT NODE FACTORY
#     # ========================================================

#     def make_agent_node(name: NodeName):

#         instructions = NODE_INSTRUCTIONS[name]
#         llm_with_tools = llm_by_node[name]

#         def agent_node(state: PolicyState):

#             messages = state.get("messages", [])

#             state_snapshot = {
#                 "active_node": name,
#                 "customer_id": state.get("customer_id"),
#                 "customer": state.get("customer"),
#                 "vehicle": state.get("vehicle"),
#                 "driver": state.get("driver"),
#                 "accident": state.get("accident"),
#                 "driver_history": state.get("driver_history"),
#                 "coverage": state.get("coverage"),
#                 "selected_plan": state.get("selected_plan"),
#                 "premium": state.get("premium"),
#                 "payment": state.get("payment"),
#                 "payment_receipt": state.get("payment_receipt"),
#                 "policy_document": state.get("policy_document"),
#             }

#             system = SystemMessage(
#                 content=(
#                     instructions
#                     + "\n\nCURRENT WORKFLOW STATE:\n"
#                     + json.dumps(state_snapshot, default=str)
#                 )
#             )

#             response = llm_with_tools.invoke([system, *messages])

#             return {
#                 "messages": [response],
#                 "current_stage": name,
#             }

#         return agent_node

#     # ========================================================
#     # STATE SYNCHRONIZATION NODE (per sub-agent, shares one impl)
#     # ========================================================

#     def make_sync_state_node(name: NodeName):

#         def sync_state_node(state: PolicyState):

#             updates: dict[str, Any] = {}

#             for message in reversed(state.get("messages", [])):

#                 if not isinstance(message, ToolMessage):
#                     continue

#                 try:
#                     if isinstance(message.content, str):
#                         try:
#                             payload = json.loads(message.content)
#                         except json.JSONDecodeError:
#                             payload = ast.literal_eval(message.content)
#                     else:
#                         payload = message.content
#                 except Exception:
#                     continue

#                 tool_name = message.name or ""

#                 # Hand-off: update which sub-agent is active.
#                 if tool_name == "transfer_to_node" and isinstance(payload, dict):
#                     target = payload.get("target_node")
#                     if target in _VALID_TARGETS:
#                         updates["active_node"] = target

#                 elif tool_name == "customer_details_tool" and isinstance(payload, dict):
#                     updates["customer"] = payload
#                     updates["customer_id"] = payload.get("custid")

#                 elif tool_name == "vehicle_lookup_tool" and isinstance(payload, dict):
#                     updates["vehicle"] = payload.get("vehicle_details", {})
#                     updates["driver"] = payload.get("driver_details", {})
#                     updates["accident"] = payload.get("accident_details", {})

                
#                 elif tool_name == "IDV_calculation_tool" and isinstance(payload, dict):
#                     updates["coverage"] = {
#                         **updates.get("coverage", {}),
#                         "idv": payload.get("idv"),
#                         "depreciation_rate": payload.get("depreciation_rate"),
#                         "vehicle_age": payload.get("vehicle_age"),
#                         "vehicle_price": payload.get("vehicle_price"),
#                     }

#                 elif tool_name == "driver_lookup_tool" and isinstance(payload, dict):
#                     updates["driver_history"] = payload

#                 elif tool_name in {
#                     "coverage_calculation_tool",
#                     "plan_breakdown_tool",
#                 } and isinstance(payload, dict):
#                     updates["coverage"] = payload
#                     if "total_premium" in payload:
#                         updates["premium"] = payload.get("total_premium")
#                         updates["selected_plan"] = payload.get("coverage")

#                 elif tool_name == "insert_payment_tool" and isinstance(payload, dict):
#                     updates["payment"] = payload

#                 elif tool_name == "payment_pdf_tool" and isinstance(payload, dict):
#                     updates["payment_receipt"] = payload

#                 elif tool_name == "policy_pdf_tool" and isinstance(payload, dict):
#                     updates["policy_document"] = payload

#                 elif tool_name == "send_email_tool" and isinstance(payload, dict):
#                     updates["email_result"] = payload

#                 if updates:
#                     break

#             # Default: stay on the current sub-agent unless a hand-off fired.
#             updates.setdefault("active_node", name)
#             return updates

#         return sync_state_node

#     # ========================================================
#     # ROUTER ("root agent") — dispatches by active_node
#     # ========================================================

#     def route_to_active_node(state: PolicyState) -> NodeName:
#         return state.get("active_node", "quote")

#     # ========================================================
#     # STATE GRAPH
#     # ========================================================

#     builder = StateGraph(PolicyState)

#     for name in NODE_NAMES:
#         builder.add_node(name, make_agent_node(name))
#         builder.add_node(f"{name}_tools", ToolNode(NODE_TOOLS[name]))
#         builder.add_node(f"{name}_sync", make_sync_state_node(name))

#     # Entry: root router picks the first sub-agent to run, based on
#     # whatever active_node was left in state (defaults to "quote" for a
#     # brand new conversation/thread).
#     builder.add_conditional_edges(
#         START,
#         route_to_active_node,
#         {name: name for name in NODE_NAMES},
#     )

#     for name in NODE_NAMES:

#         # Sub-agent decides: call a tool, or hand control back (END, i.e.
#         # wait for the next user message).
#         builder.add_conditional_edges(
#             name,
#             tools_condition,
#             {"tools": f"{name}_tools", END: END},
#         )

#         builder.add_edge(f"{name}_tools", f"{name}_sync")

#         # After syncing state, route again: if a hand-off tool fired,
#         # active_node now points at a different sub-agent, so this jumps
#         # straight there in the same turn (mirrors ADK's transfer). If no
#         # hand-off happened, this loops back into the same sub-agent so it
#         # can react to the tool result.
#         builder.add_conditional_edges(
#             f"{name}_sync",
#             route_to_active_node,
#             {n: n for n in NODE_NAMES},
#         )

#     return builder.compile()


# # ============================================================
# # GRAPH INSTANCE
# # ============================================================

# graph = build_graph()

# # Keep root_agent alias for compatibility with the existing application.
# root_agent = graph


# # ============================================================
# # DIRECT INVOCATION HELPER
# # ============================================================

# def invoke(user_message: str, history: list[BaseMessage] | None = None) -> dict[str, Any]:

#     messages = list(history or []) + [HumanMessage(content=user_message)]

#     return graph.invoke({"messages": messages})


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


# ============================================================
# INSTRUCTIONS (one block per sub-agent)
# ============================================================

from instructions import (
    QUOTE_NODE_INSTRUCTIONS,
    FETCH_DETAILS_NODE_INSTRUCTIONS,
    COVERAGE_NODE_INSTRUCTIONS,
    PAYMENT_NODE_INSTRUCTIONS,
    POLICY_ISSUANCE_NODE_INSTRUCTIONS,
    EMAIL_NODE_INSTRUCTIONS,
)


# ============================================================
# BUSINESS TOOL IMPORTS
# ============================================================

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

    # Root-agent bookkeeping: which sub-agent handles the next step.
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


# ============================================================
# LANGCHAIN TOOL WRAPPERS (business tools)
# ============================================================

@tool
def customer_details_tool(custid: str) -> dict:
    """Find an existing customer by customer ID in the local capstone dataset."""
    return customer_details(custid)


@tool
def vehicle_lookup_tool(vin: str, license_number: str) -> dict:
    """Fetch local vehicle, driver and accident information using VIN and license number."""
    return fetch_vehicle_driver_accident_details(vin, license_number)


# @tool
# def driver_lookup_tool(driver_id: str) -> dict:
#     """Fetch local insurance history, license status and violation details for a driver."""
#     return fetch_driver_related_details(driver_id)


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


# ============================================================
# HAND-OFF TOOL (stands in for ADK's transfer_to_agent)
# ============================================================

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


# ============================================================
# PER-NODE TOOL SCOPES AND INSTRUCTIONS
# ============================================================
# This is the "sub-agent" definition table: each node only gets the tools
# and the instructions relevant to its own stage of the flow, instead of
# one assistant seeing all ten tools and one giant prompt.

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


# ============================================================
# BUILD LANGGRAPH
# ============================================================

def build_graph():

    model_name = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found. Please check your .env file.")

    base_llm = ChatOpenAI(model=model_name, api_key=api_key, reasoning_effort="none")

    # One tool-bound LLM per sub-agent, each seeing only its own tools.
    llm_by_node = {name: base_llm.bind_tools(tools) for name, tools in NODE_TOOLS.items()}

    # ========================================================
    # SUB-AGENT NODE FACTORY
    # ========================================================

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

    # ========================================================
    # STATE SYNCHRONIZATION NODE (per sub-agent, shares one impl)
    # ========================================================

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

                # Hand-off: update which sub-agent is active.
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

            # Default: stay on the current sub-agent unless a hand-off fired.
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

    # ========================================================
    # STATE GRAPH
    # ========================================================

    builder = StateGraph(PolicyState)

    for name in NODE_NAMES:
        builder.add_node(name, make_agent_node(name))
        builder.add_node(f"{name}_tools", ToolNode(NODE_TOOLS[name]))
        builder.add_node(f"{name}_sync", make_sync_state_node(name))

    # Entry: root router picks the first sub-agent to run, based on
    # whatever active_node was left in state (defaults to "quote" for a
    # brand new conversation/thread).
    builder.add_conditional_edges(
        START,
        route_to_active_node,
        {name: name for name in NODE_NAMES},
    )

    for name in NODE_NAMES:

        # The sub-agent can call a tool, hand off to another node, or finish
        # the current turn and wait for the next user message.
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

        # After syncing state, route again: if a hand-off tool fired,
        # active_node now points at a different sub-agent, so this jumps
        # straight there in the same turn (mirrors ADK's transfer). If no
        # hand-off happened, this loops back into the same sub-agent so it
        # can react to the tool result.
        builder.add_conditional_edges(
            f"{name}_sync",
            route_to_active_node,
            {n: n for n in NODE_NAMES},
        )

    return builder.compile()


# ============================================================
# GRAPH INSTANCE
# ============================================================

graph = build_graph()

# Keep root_agent alias for compatibility with the existing application.
root_agent = graph


# ============================================================
# DIRECT INVOCATION HELPER
# ============================================================

def invoke(user_message: str, history: list[BaseMessage] | None = None) -> dict[str, Any]:

    messages = list(history or []) + [HumanMessage(content=user_message)]

    return graph.invoke({"messages": messages})