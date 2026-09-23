import streamlit as st
import os
import io
import re
import time
import json
import html
import logging
from datetime import datetime

from dotenv import load_dotenv
import fitz  # PyMuPDF
from langchain_core.messages import HumanMessage

# LangGraph backend
from agent import graph


# =========================================================
# Environment
# =========================================================
load_dotenv()


# =========================================================
# CSS LOADING
# =========================================================
LOCAL_CSS_FILE = "custom.css"


def load_local_css(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.warning(f"Custom CSS file not found: {filename}")
        return ""
    except Exception as e:
        st.warning(f"Error reading local CSS: {e}")
        return ""


def load_css():
    custom_css = load_local_css(LOCAL_CSS_FILE)
    if custom_css:
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Auto Policy Issuance",
    page_icon="🛡️",
    layout="wide",
)

load_css()


# =========================================================
# SESSION STATE
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "🌟 Welcome to the Insurance Agent! Ask me anything 🚀",
        }
    ]

# Persistent LangGraph workflow state.
if "policy_state" not in st.session_state:
    st.session_state.policy_state = {
        "messages": [],
        "active_node": "quote",
    }

# Dashboard information is deliberately kept in Streamlit state so that
# it remains populated between reruns.
if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = {
        "customer_details": {},
        "vin_number": None,
        "license_number": None,
        "vehicle_details": {},
        "driver_details": {},
        "accident_details": {},
        "driver_history": {},
        "insurance_history": {},
        "coverage_details": {},
        "coverage_selected": None,
        "coverage_option": None,
        "selected_plan": {},
        "premium": None,
        "payment": {},
        "payment_receipt": {},
        "policy_details": {},
        "policy_document": {},
        "active_node": "quote",
        "last_updated": None,
    }

if "activity_traces" not in st.session_state:
    st.session_state.activity_traces = []

if "show_activity_panel" not in st.session_state:
    st.session_state.show_activity_panel = False


# =========================================================
# CONSTANTS
# =========================================================
AGENT_AVATARS = {
    "user": "🧑",
    "assistant": "🛡️",
}


# =========================================================
# ACTIVITY LOG
# =========================================================
def add_activity_trace(agent_name, message, trace_type="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")

    st.session_state.activity_traces.append(
        {
            "timestamp": timestamp,
            "agent": agent_name,
            "message": str(message),
            "type": trace_type,
        }
    )

    # Keep the log bounded while still giving the evaluator useful traces.
    st.session_state.activity_traces = st.session_state.activity_traces[-100:]


# =========================================================
# USER INPUT EXTRACTION
# =========================================================
def extract_info_from_message(message):
    info = {}
    normalized_message = message.upper().replace("=", " ").replace(",", " ")
    normalized = message.lower()

    vin_match = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", normalized_message)
    if vin_match:
        info["vin_number"] = vin_match.group()
        add_activity_trace(
            "INFO_EXTRACTOR",
            f"VIN number extracted: {vin_match.group()}",
        )

    license_patterns = [
        r"LICENSE\s+([A-Z0-9\-]{4,20})",
        r"LICENSE[:\s]+([A-Z0-9\-]{4,20})",
        r"DL[:\s]+([A-Z0-9\-]{4,20})",
        r"DRIVER\s+LICENSE[:\s]+([A-Z0-9\-]{4,20})",
        r"LIC[:\s]+([A-Z0-9\-]{4,20})",
    ]

    for pattern in license_patterns:
        match = re.search(pattern, normalized_message)
        if match:
            info["license_number"] = match.group(1).strip()
            add_activity_trace(
                "INFO_EXTRACTOR",
                f"License number extracted: {match.group(1).strip()}",
            )
            break

    if "license_number" not in info:
        fallback = re.search(r"\b[A-Z]{2}\d{4,10}\b", normalized_message)
        if fallback:
            info["license_number"] = fallback.group().strip()
            add_activity_trace(
                "INFO_EXTRACTOR",
                f"License number (fallback): {fallback.group().strip()}",
            )

    coverage_option = None
    liability_limits = None

    liability_match = re.search(r"(\d{2,3}/\d{2,3})", normalized)
    if liability_match:
        liability_limits = liability_match.group(1)

    has_full = re.search(
        r"\b(full\s*coverage|full|max|all-inclusive)\b",
        normalized,
    )
    has_comprehensive = re.search(r"\bcomprehensive\b", normalized)
    has_collision = re.search(r"\bcollision\b", normalized)
    has_liability = re.search(r"\bliability\b", normalized)

    if has_full:
        coverage_option = "Full Coverage"
    elif has_comprehensive:
        coverage_option = "Liability + Comprehensive"
    elif has_collision:
        coverage_option = "Liability + Collision"
    elif has_liability:
        coverage_option = "Liability Only"

    if coverage_option:
        info["coverage_selected"] = True

        if liability_limits:
            info["coverage_option"] = f"{coverage_option} ({liability_limits})"
        else:
            info["coverage_option"] = coverage_option

        add_activity_trace(
            "COVERAGE_NODE",
            f"Coverage option identified: {info['coverage_option']}",
        )

    add_on_map = {
        "roadside": "Roadside Assistance",
        "glass": "Glass Coverage",
        "rental": "Rental Car Coverage",
    }

    add_ons_found = [
        pretty
        for key, pretty in add_on_map.items()
        if key in normalized
    ]

    if add_ons_found:
        info["add_ons_selected"] = True
        info["add_ons"] = add_ons_found

        add_activity_trace(
            "ADDONS_NODE",
            f"Add-ons selected: {', '.join(add_ons_found)}",
        )

    elif "no add" in normalized or normalized.strip() == "no":
        info["add_ons_selected"] = True
        info["add_ons"] = []

        add_activity_trace(
            "ADDONS_NODE",
            "No add-ons selected by user",
        )

    return info


def update_dashboard_data(message):
    extracted_info = extract_info_from_message(message)

    if extracted_info:
        st.session_state.dashboard_data.update(extracted_info)

        st.session_state.dashboard_data["last_updated"] = (
            time.strftime("%Y-%m-%d %H:%M:%S")
        )

        add_activity_trace(
            "DASHBOARD",
            f"Dashboard updated with {len(extracted_info)} new fields",
        )


# =========================================================
# RESPONSE PARSING
# =========================================================
def parse_vehicle_info_from_text(text):
    vehicle_info = {}

    patterns = {
        "VIN": r"VIN:\s*([A-Za-z0-9]+)",
        "Plate Number": r"Plate Number:\s*([A-Za-z0-9]+)",
        "Owner ID": r"Owner ID:\s*([A-Za-z0-9]+)",
        "Make": r"Make:\s*([A-Za-z0-9 ]+)",
        "Model": r"Model:\s*([A-Za-z0-9]+)",
        "Year": r"Year:\s*([0-9]{4})",
        "Body Type": r"Body Type:\s*([A-Za-z0-9 ]+)",
        "Fuel Type": r"Fuel Type:\s*([A-Za-z0-9 ]+)",
        "Registration Date": r"Registration Date:\s*([0-9\-]+)",
        "Expiry Date": r"Expiry Date:\s*([0-9\-]+)",
        "Status": r"Status:\s*([A-Za-z0-9 ]+)",
        "Usage Type": r"Usage Type:\s*([A-Za-z0-9 ]+)",
        "Ex-Showroom Price": r"Ex-Showroom Price:\s*([A-Za-z0-9\.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            vehicle_info[key] = match.group(1)

    if vehicle_info:
        add_activity_trace(
            "FETCH_NODE",
            f"Vehicle details parsed: {len(vehicle_info)} fields found",
        )

    return vehicle_info


def parse_accident_details_from_text(text):
    match = re.search(
        r"Accident Details:([\s\S]*?)(\n\w|$|Insurance History:)",
        text,
        re.IGNORECASE,
    )

    return match.group(1).strip() if match else ""


def parse_insurance_history_from_text(text):
    insurance_info = {}

    patterns = {
        "Insurer Name": r"Insurer Name:\s*([\w\s]+)",
        "Policy Number": r"Policy Number:\s*([\w\d]+)",
        "Coverage Type": r"Coverage Type:\s*([\w\s]+)",
        "Start Date": r"Start Date:\s*([\d\-]+)",
        "End Date": r"End Date:\s*([\d\-]+)",
        "Lapse": r"Lapse:\s*(\w+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            insurance_info[key] = match.group(1)

    return insurance_info


def extract_vehicle_details_from_response(response_text):
    try:
        data = json.loads(response_text)

        return {
            "vehicle": data.get("Vehicle Details", {}),
            "driver": data.get("Driver Details", {}),
            "accident": data.get("Accident Details", {}),
            "insurance": data.get("Insurance History", {}),
        }

    except Exception:
        pass

    return {
        "vehicle": parse_vehicle_info_from_text(response_text),
        "driver": {},
        "accident": parse_accident_details_from_text(response_text),
        "insurance": parse_insurance_history_from_text(response_text),
    }


# =========================================================
# LANGGRAPH STATE -> DASHBOARD
# =========================================================
def _is_nonempty(value):
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, dict):
        return bool(value)

    if isinstance(value, list):
        return bool(value)

    return True


def _copy_if_present(source, target, key):
    value = source.get(key)

    if _is_nonempty(value):
        target[key] = value


def sync_dashboard_from_policy_state():
    """
    Populate the left dashboard from the actual LangGraph PolicyState.

    This is the important change from the older dashboard implementation:
    the dashboard no longer depends only on parsing the assistant's text.
    It reads the structured workflow state returned by LangGraph.
    """
    state = st.session_state.get("policy_state", {})
    dash = st.session_state.dashboard_data

    if not isinstance(state, dict):
        return

    # Basic workflow information.
    if state.get("active_node"):
        dash["active_node"] = state.get("active_node")

    # Customer.
    if _is_nonempty(state.get("customer")):
        dash["customer_details"] = state.get("customer")

    if _is_nonempty(state.get("customer_id")):
        dash["customer_id"] = state.get("customer_id")

    # Vehicle / driver / accident.
    if _is_nonempty(state.get("vehicle")):
        dash["vehicle_details"] = state.get("vehicle")

        vehicle = state.get("vehicle") or {}

        if isinstance(vehicle, dict):
            vin = (
                vehicle.get("VIN")
                or vehicle.get("vin")
                or vehicle.get("vin_number")
            )

            plate = (
                vehicle.get("Plate Number")
                or vehicle.get("plate_number")
                or vehicle.get("registration_number")
            )

            if vin:
                dash["vin_number"] = vin

            if plate and not dash.get("license_number"):
                # This is vehicle registration/plate information, not
                # necessarily the driver's license number.
                dash["plate_number"] = plate

    if _is_nonempty(state.get("driver")):
        dash["driver_details"] = state.get("driver")

        driver = state.get("driver") or {}

        if isinstance(driver, dict):
            license_number = (
                driver.get("License Number")
                or driver.get("license_number")
                or driver.get("License")
                or driver.get("license")
            )

            if license_number:
                dash["license_number"] = license_number

    if _is_nonempty(state.get("accident")):
        dash["accident_details"] = state.get("accident")

    if _is_nonempty(state.get("driver_history")):
        dash["driver_history"] = state.get("driver_history")

    # Coverage / quote.
    if _is_nonempty(state.get("coverage")):
        dash["coverage_details"] = state.get("coverage")

    if _is_nonempty(state.get("selected_plan")):
        dash["selected_plan"] = state.get("selected_plan")

        selected_plan = state.get("selected_plan") or {}

        if isinstance(selected_plan, dict):
            coverage_name = (
                selected_plan.get("coverage")
                or selected_plan.get("coverage_option")
                or selected_plan.get("plan")
                or selected_plan.get("name")
            )

            if coverage_name:
                dash["coverage_option"] = coverage_name

    if _is_nonempty(state.get("premium")):
        dash["premium"] = state.get("premium")

    # Payment / policy.
    if _is_nonempty(state.get("payment")):
        dash["payment"] = state.get("payment")

    if _is_nonempty(state.get("payment_receipt")):
        dash["payment_receipt"] = state.get("payment_receipt")

    if _is_nonempty(state.get("policy")):
        dash["policy_details"] = state.get("policy")

    if _is_nonempty(state.get("policy_document")):
        dash["policy_document"] = state.get("policy_document")

    # Preserve information extracted directly from the user's message.
    if not dash.get("vin_number") and state.get("vehicle"):
        vehicle = state.get("vehicle") or {}

        if isinstance(vehicle, dict):
            dash["vin_number"] = (
                vehicle.get("VIN")
                or vehicle.get("vin")
                or vehicle.get("vin_number")
            )

    dash["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# DISPLAY HELPERS
# =========================================================
def display_value(value):
    if value is None:
        return "—"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)

    return str(value)


def pretty_key(key):
    return str(key).replace("_", " ").replace("-", " ").title()


def render_html_table(data):
    if not isinstance(data, dict) or not data:
        return

    rows = ""

    for key, value in data.items():
        safe_key = html.escape(pretty_key(key))
        safe_value = html.escape(display_value(value))

        rows += (
            "<tr>"
            f"<th>{safe_key}</th>"
            f"<td>{safe_value}</td>"
            "</tr>"
        )

    st.markdown(
        f"""
        <table style="
            width:100%;
            border-collapse:collapse;
            margin-bottom:12px;">
            <tbody>
                {rows}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# DASHBOARD
# =========================================================
def render_dashboard():
    dash = st.session_state.dashboard_data

    st.markdown(
        """
        <div class="dashboard-data-outline">
            <div class="dashboard-title">
                📋 Policy Operations Dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Keep the dashboard compact enough to fit beside the chat while
    # still showing the structured workflow state.
    with st.container(height=620, border=True):

        # Workflow status.
        active_node = dash.get("active_node") or "quote"

        st.markdown(
            f"""
            <div style="
                padding:10px;
                margin-bottom:12px;
                border-radius:8px;
                background:rgba(73,121,247,0.10);
                border:1px solid rgba(73,121,247,0.25);">
                <b>🔄 Active Workflow Node</b><br>
                <span style="font-size:1.05rem;">
                    {html.escape(str(active_node).replace("_", " ").title())}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Customer.
        customer = dash.get("customer_details") or {}

        with st.expander("👤 Customer", expanded=True):
            if customer:
                render_html_table(customer)
            else:
                st.caption("Customer details will appear here after lookup.")

        # Vehicle.
        vehicle = dash.get("vehicle_details") or {}

        with st.expander("🚗 Vehicle", expanded=True):
            quick_vehicle = {}

            if dash.get("vin_number"):
                quick_vehicle["VIN"] = dash.get("vin_number")

            if dash.get("plate_number"):
                quick_vehicle["Plate Number"] = dash.get("plate_number")

            if quick_vehicle:
                render_html_table(quick_vehicle)

            if vehicle:
                render_html_table(vehicle)
            elif not quick_vehicle:
                st.caption("Vehicle details will appear here after lookup.")

        # Driver.
        driver = dash.get("driver_details") or {}

        with st.expander("🧑 Driver", expanded=True):
            if driver:
                render_html_table(driver)
            else:
                if dash.get("license_number"):
                    render_html_table(
                        {"License Number": dash.get("license_number")}
                    )
                else:
                    st.caption("Driver details will appear here after lookup.")

        # Accident / history.
        accident = dash.get("accident_details")
        driver_history = dash.get("driver_history") or {}
        insurance = dash.get("insurance_history") or {}

        with st.expander("⚠️ Accident & History", expanded=False):
            if accident:
                if isinstance(accident, dict):
                    render_html_table(accident)
                else:
                    st.write(str(accident))
            else:
                st.caption("No accident details available yet.")

            if driver_history:
                st.markdown("**Driver History**")
                if isinstance(driver_history, dict):
                    render_html_table(driver_history)
                else:
                    st.write(str(driver_history))

            if insurance:
                st.markdown("**Insurance History**")
                render_html_table(insurance)

        # Coverage / plan / premium.
        coverage = dash.get("coverage_details") or {}
        selected_plan = dash.get("selected_plan") or {}
        premium = dash.get("premium")

        with st.expander("🛡️ Coverage & Quote", expanded=True):
            if dash.get("coverage_option"):
                render_html_table(
                    {"Coverage Option": dash.get("coverage_option")}
                )

            if coverage:
                st.markdown("**Coverage Details**")
                render_html_table(coverage)

            if selected_plan:
                st.markdown("**Selected Plan**")
                render_html_table(selected_plan)

            if premium is not None:
                st.markdown("**Premium**")
                st.metric("Premium", display_value(premium))

            if not coverage and not selected_plan and premium is None:
                st.caption("Coverage and quote details will appear here.")

        # Payment.
        payment = dash.get("payment") or {}
        receipt = dash.get("payment_receipt") or {}

        with st.expander("💳 Payment", expanded=False):
            if payment:
                render_html_table(payment)
            else:
                st.caption("Payment details will appear here after payment.")

            if receipt:
                status = receipt.get("success")

                if status:
                    st.success("Payment receipt generated.")
                elif status is False:
                    st.error("Payment receipt generation failed.")

        # Policy.
        policy = dash.get("policy_details") or {}
        policy_document = dash.get("policy_document") or {}

        with st.expander("📃 Policy", expanded=False):
            if policy:
                render_html_table(policy)
            else:
                st.caption("Policy details will appear here after issuance.")

            if policy_document:
                if policy_document.get("success"):
                    st.success("Policy document generated.")
                elif policy_document.get("success") is False:
                    st.error("Policy document generation failed.")


# =========================================================
# CHAT PDF
# =========================================================
def generate_chat_pdf(messages):
    pdf_buffer = io.BytesIO()
    doc = fitz.open()
    page = doc.new_page()

    text = "Insurance Chat History\n\n"

    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        text += f"{role}:\n{msg['content']}\n\n"

    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(rect, text, fontsize=11)

    doc.save(pdf_buffer)
    doc.close()
    pdf_buffer.seek(0)

    return pdf_buffer


# =========================================================
# LOCAL PDF DOWNLOAD HELPERS
# =========================================================
def render_payment_receipt_download():
    """
    Render a browser download button for the locally generated payment receipt.
    """
    policy_state = st.session_state.get("policy_state", {})
    receipt = policy_state.get("payment_receipt")

    if not isinstance(receipt, dict):
        return

    if not receipt.get("success"):
        return

    receipt_path = receipt.get("local_path")
    filename = receipt.get("filename") or "payment_receipt.pdf"

    if not receipt_path:
        return

    receipt_path = os.path.normpath(str(receipt_path))

    if not os.path.isfile(receipt_path):
        return

    try:
        with open(receipt_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        st.download_button(
            label="📄 Download Payment Receipt",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key="payment_receipt_download_button",
            on_click="ignore",
            type="primary",
            width="stretch",
        )

    except Exception as e:
        logging.exception("Unable to prepare payment receipt for download")
        st.error(f"Unable to prepare the payment receipt: {e}")


def render_policy_document_download():
    """
    Render a browser download button for the locally generated policy PDF.
    """
    policy_state = st.session_state.get("policy_state", {})
    policy_document = policy_state.get("policy_document")

    if not isinstance(policy_document, dict):
        return

    if not policy_document.get("success"):
        return

    policy_path = policy_document.get("local_path")
    filename = policy_document.get("filename") or "insurance_policy.pdf"

    if not policy_path:
        return

    policy_path = os.path.normpath(str(policy_path))

    if not os.path.isfile(policy_path):
        return

    try:
        with open(policy_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        st.download_button(
            label="📄 Download Policy Document",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key="policy_document_download_button",
            on_click="ignore",
            type="primary",
            width="stretch",
        )

    except Exception as e:
        logging.exception("Unable to prepare policy document for download")
        st.error(f"Unable to prepare the policy document: {e}")


# =========================================================
# LANGGRAPH INVOCATION
# =========================================================
def _extract_text_from_message(message):
    content = getattr(message, "content", message)

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)

        return "\n".join(parts)

    return str(content)


def invoke_langgraph(user_message):
    """
    Invoke LangGraph and preserve its PolicyState between user turns.
    """
    try:
        add_activity_trace(
            "LANGGRAPH",
            "Starting LangGraph execution",
        )

        policy_state = st.session_state.policy_state

        policy_state["messages"] = list(
            policy_state.get("messages", [])
        )

        policy_state["messages"].append(
            HumanMessage(content=user_message)
        )

        policy_state.setdefault("active_node", "quote")

        result = graph.invoke(policy_state)

        # Persist the complete returned state.
        st.session_state.policy_state = result

        # Populate the structured dashboard directly from LangGraph state.
        sync_dashboard_from_policy_state()

        response_messages = result.get("messages", [])

        if not response_messages:
            return "⚠️ No response was returned by LangGraph."

        response_text = _extract_text_from_message(
            response_messages[-1]
        )

        add_activity_trace(
            "LANGGRAPH",
            (
                f"LangGraph execution completed: "
                f"{len(response_text)} characters | "
                f"next node: {result.get('active_node', 'quote')}"
            ),
        )

        return response_text.strip() or "⚠️ No response received."

    except Exception as e:
        logging.exception("LangGraph execution failed")

        add_activity_trace(
            "SYSTEM",
            f"LangGraph error: {e}",
            "ERROR",
        )

        return f"⚠️ Error while processing the request: {e}"


# =========================================================
# MESSAGE PROCESSING
# =========================================================
def send_message_to_agent(user_message):
    add_activity_trace(
        "USER",
        f"Message received: {user_message[:50]}"
        f"{'...' if len(user_message) > 50 else ''}",
    )

    update_dashboard_data(user_message)

    response_text = invoke_langgraph(user_message)

    # Keep response parsing as a fallback for older/partial backend
    # responses, but the dashboard primarily uses structured PolicyState.
    parsed = extract_vehicle_details_from_response(response_text)

    if parsed.get("vehicle"):
        st.session_state.dashboard_data.setdefault(
            "vehicle_details",
            {},
        ).update(parsed["vehicle"])

    if parsed.get("driver"):
        st.session_state.dashboard_data.setdefault(
            "driver_details",
            {},
        ).update(parsed["driver"])

    if parsed.get("accident"):
        st.session_state.dashboard_data["accident_details"] = (
            parsed["accident"]
        )

    if parsed.get("insurance"):
        st.session_state.dashboard_data.setdefault(
            "insurance_history",
            {},
        ).update(parsed["insurance"])

    # Re-sync after fallback parsing.
    sync_dashboard_from_policy_state()

    st.session_state.dashboard_data["last_updated"] = (
        time.strftime("%Y-%m-%d %H:%M:%S")
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )

    add_activity_trace(
        "SYSTEM",
        "Message processing completed",
    )


# =========================================================
# MAIN UI
# =========================================================
def main():

    # -----------------------------------------------------
    # Top title
    # -----------------------------------------------------
    with st.container():
        _, col_center, _ = st.columns([2, 12, 2])

        with col_center:
            st.markdown(
                """
                <div style="
                    width:100%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    box-sizing:border-box;
                    padding:18px 0 16px 0;
                    margin:0;
                    min-height:72px;
                    font-size:2.8rem;
                    line-height:1.2;
                    font-weight:900;
                    letter-spacing:0.5px;
                    color:var(--primary-color);
                    overflow:visible;">
                    <span style="
                        display:inline-flex;
                        align-items:center;
                        line-height:1;
                        font-size:2.1rem;
                        margin-right:0.55rem;">
                        🛡️
                    </span>
                    <span style="line-height:1.2;">Auto Policy Issuance</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------
    # NO PROGRESS BAR
    # -----------------------------------------------------
    # The previous multi-stage progress tracker has intentionally
    # been removed for the capstone presentation.

    st.markdown("<div style=\"height:1px;background:rgba(255,255,255,0.14);margin:0 0 18px 0;\"></div>", unsafe_allow_html=True)

    activity_panel_open = st.session_state.show_activity_panel

    if activity_panel_open:
        col_dash, col_chat, col_activity = st.columns(
            [3.5, 6.0, 2.5]
        )
    else:
        col_dash, col_chat, col_activity = st.columns(
            [3.5, 8.5, 0.001]
        )

    # -----------------------------------------------------
    # LEFT: DASHBOARD
    # -----------------------------------------------------
    with col_dash:
        render_dashboard()

    # -----------------------------------------------------
    # CENTER: CHAT
    # -----------------------------------------------------
    with col_chat:

        header_col_title, header_col_reset, header_col_download, header_col_log = (
            st.columns([6.6, 1.2, 1.2, 0.8])
        )

        with header_col_title:
            st.subheader("💬 Chat Interface")

        with header_col_reset:
            if st.button(
                "➕ New Chat",
                key="reset_button_chat",
                help="Start a new session",
            ):
                st.session_state.clear()
                st.rerun()

        with header_col_download:
            pdf_file = generate_chat_pdf(
                st.session_state.messages
            )

            st.download_button(
                label="📄 Download",
                data=pdf_file,
                file_name="insurance_chat.pdf",
                mime="application/pdf",
                key="download_pdf_chat",
                on_click="ignore",
            )

        with header_col_log:
            if st.button(
                "☰ Log",
                key="toggle_activity",
                help="Show Activity Log",
            ):
                st.session_state.show_activity_panel = (
                    not st.session_state.show_activity_panel
                )
                st.rerun()

        chat_container = st.container(
        height=420,
        border=True,
        autoscroll=True,
        )

        with chat_container:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    with st.chat_message(
                        "user",
                        avatar=AGENT_AVATARS["user"],
                    ):
                        st.write(msg["content"])

                else:
                    with st.chat_message(
                        "assistant",
                        avatar=AGENT_AVATARS["assistant"],
                    ):
                        st.markdown(msg["content"])

        # Locally generated PDFs.
        render_payment_receipt_download()
        render_policy_document_download()

        if prompt := st.chat_input(
            "💬 Ask me anything about insurance..."
        ):
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            with st.spinner("Processing..."):
                send_message_to_agent(prompt)

            st.rerun()

    # -----------------------------------------------------
    # RIGHT: SCROLLABLE ACTIVITY LOG
    # -----------------------------------------------------
    with col_activity:

        if activity_panel_open:

            if st.button(
                "× Close",
                key="close_panel",
                help="Close Activity Log",
            ):
                st.session_state.show_activity_panel = False
                st.rerun()

            st.markdown(
                """
                <div style="
                    color:var(--primary-color);
                    font-weight:700;
                    font-size:1.1rem;
                    text-align:center;
                    border-bottom:2px solid var(--primary-color);
                    padding-bottom:8px;">
                    🔍 ACTIVITY LOG (TRACES)
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Fixed-height Streamlit container = native scrolling.
            # This avoids a large HTML block expanding the whole page.
            log_container = st.container(
                height=520,
                border=True,
                autoscroll=True,
            )

            with log_container:

                traces = st.session_state.activity_traces[-100:]

                if not traces:
                    st.caption(
                        "No activity traces yet..."
                    )

                else:
                    icon_map = {
                        "SYSTEM": "🟢",
                        "USER": "🧑‍💻",
                        "PROGRESS_TRACKER": "🔄",
                        "DASHBOARD": "📊",
                        "LANGGRAPH": "🧠",
                        "QUOTE_NODE": "📝",
                        "FETCH_NODE": "🔎",
                        "COVERAGE_NODE": "🔐",
                        "ADDONS_NODE": "➕",
                        "FINAL_QUOTE_NODE": "💸",
                        "PAYMENT_NODE": "💳",
                        "POLICY_INSURED_NODE": "📃",
                        "INFO_EXTRACTOR": "🔍",
                    }

                    for trace in reversed(traces):

                        agent = trace["agent"]
                        icon = icon_map.get(
                            agent,
                            "⚙️",
                        )

                        display_name = (
                            agent
                            .replace("_", " ")
                            .title()
                        )

                        st.markdown(
                            f"""
                            <div style="
                                margin-bottom:10px;
                                padding-bottom:8px;
                                border-bottom:1px solid
                                    rgba(128,128,128,0.20);">

                                <div style="
                                    font-weight:700;
                                    color:#4979f7;">
                                    {icon} {html.escape(display_name)}
                                    <span style="
                                        font-size:0.75rem;
                                        color:#888;
                                        font-weight:400;">
                                        {html.escape(trace["timestamp"])}
                                    </span>
                                </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        for line in str(
                            trace["message"]
                        ).splitlines():

                            line = line.strip()

                            if not line:
                                continue

                            safe_line = html.escape(line)

                            st.markdown(
                                f"""
                                <div style="
                                    margin-left:16px;
                                    margin-top:3px;
                                    color:inherit;
                                    font-size:0.88rem;
                                    overflow-wrap:anywhere;">
                                    – {safe_line}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            "</div>",
                            unsafe_allow_html=True,
                        )


if __name__ == "__main__":
    main()
