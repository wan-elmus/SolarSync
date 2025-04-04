from typing import TypedDict, List, Optional, Dict, Any
from typing_extensions import Annotated
from langgraph.graph import add_messages

class JobState(TypedDict):
    """
    A TypedDict representing the state of a job in the LangGraph workflow.

    This state is used to pass data between nodes in the workflow, including job details,
    sizing calculations, AI predictions, technician assignment, notifications, weather updates,
    and messages for the LangGraph agent.

    Attributes:
        job_id (Optional[str]): The unique identifier of the job.
        user_id (Optional[str]): The ID of the customer who created the job.
        description (Optional[str]): Description of the job (e.g., 'GRID TIE OFFLINE').
        priority (Optional[str]): Priority of the job (e.g., 'high', 'medium', 'low').
        customer (Optional[Dict[str, Any]]): Customer details.
        system_type (Optional[str]): Type of solar system ('pure' or 'hybrid').
        appliances (Optional[List[Dict[str, Any]]]): List of appliances with power ratings, quantities, and runtimes.
        load_demand_kwh (Optional[float]): Daily energy demand in kWh.
        peak_sun_hours (Optional[float]): Peak sun hours for the location.
        panel_capacity_kw (Optional[float]): Calculated panel capacity in kW.
        battery_capacity_kwh (Optional[float]): Calculated battery capacity in kWh.
        inverter_capacity_kw (Optional[float]): Calculated inverter capacity in kW.
        daily_output_kwh (Optional[float]): Daily energy output in kWh.
        excess_kwh (Optional[float]): Excess energy in kWh.
        panel_cost_ksh (Optional[float]): Cost of panels in KSH.
        battery_cost_ksh (Optional[float]): Cost of batteries in KSH.
        inverter_cost_ksh (Optional[float]): Cost of inverters in KSH.
        installation_cost_ksh (Optional[float]): Installation cost in KSH.
        total_cost_ksh (Optional[float]): Total cost in KSH.
        roi_years (Optional[float]): Return on investment in years.
        system_efficiency (Optional[float]): System efficiency percentage.
        site (Optional[str]): Site name or identifier.
        equipment (Optional[Dict[str, Any]]): Equipment details.
        project (Optional[Dict[str, Any]]): Project details.
        type (Optional[str]): Job type.
        report_template (Optional[str]): Report template identifier.
        created_by (Optional[Dict[str, Any]]): Details of the user who created the job.
        address_street (Optional[str]): Street address.
        address_province (Optional[str]): Province or state.
        address_city (Optional[str]): City.
        address_zip (Optional[str]): ZIP or postal code.
        address_country (Optional[str]): Country.
        address (Optional[str]): Full address string.
        address_complement (Optional[str]): Additional address details.
        contact_first_name (Optional[str]): Contact's first name.
        contact_last_name (Optional[str]): Contact's last name.
        contact_mobile (Optional[str]): Contact's mobile number.
        contact_phone (Optional[str]): Contact's phone number.
        contact_email (Optional[str]): Contact's email address.
        status (Optional[str]): Job status ('pending', 'in_progress', 'completed').
        public_link (Optional[str]): Public link to the job.
        technician_id (Optional[str]): ID of the assigned technician.
        scheduled_start (Optional[str]): Scheduled start date (ISO format).
        scheduled_end (Optional[str]): Scheduled end date (ISO format).
        actual_start (Optional[str]): Actual start date (ISO format).
        actual_end (Optional[str]): Actual end date (ISO format).
        created_by_customer (Optional[bool]): Whether the job was created by a customer.
        position (Optional[Dict[str, float]]): Location coordinates (e.g., {'lat': -1.2699, 'lon': 36.8408}).
        custom_field_values (Optional[Dict[str, Any]]): Custom field values.
        date_created (Optional[str]): Creation date (ISO format).
        date_modified (Optional[str]): Last modified date (ISO format).
        preferences (Optional[Dict[str, Any]]): User preferences.
        technician_name (Optional[str]): Name of the assigned technician.
        technician_login (Optional[str]): Login (email) of the assigned technician.
        job_type (Optional[str]): Type of job.
        diagnosis (Optional[str]): Diagnosis from the AI Prediction Agent.
        feedback (Optional[str]): Feedback from the technician during job completion.
        adjusted_energy_demand_kwh (Optional[float]): Adjusted energy demand after efficiencies.
        lead_acid_ah_demand (Optional[float]): Ah demand for Lead Acid batteries.
        lithium_ion_ah_demand (Optional[float]): Ah demand for Lithium-Ion batteries.
        panels_required (Optional[int]): Number of panels required.
        lead_acid_batteries_required (Optional[int]): Number of Lead Acid batteries required.
        lithium_ion_batteries_required (Optional[int]): Number of Lithium-Ion batteries required.
        inverters_required (Optional[int]): Number of inverters required.
        lead_acid_batteries_series (Optional[int]): Number of Lead Acid batteries in series.
        lead_acid_batteries_parallel (Optional[int]): Number of Lead Acid batteries in parallel.
        lithium_ion_batteries_series (Optional[int]): Number of Lithium-Ion batteries in series.
        lithium_ion_batteries_parallel (Optional[int]): Number of Lithium-Ion batteries in parallel.
        messages (Annotated[List[Dict[str, Any]], add_messages]): Messages for the LangGraph agent.
        db (Optional[Any]): Database session (for workflow use).
    """
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    customer: Optional[Dict[str, Any]] = None
    system_type: Optional[str] = None
    appliances: Optional[List[Dict[str, Any]]] = None  # Added
    load_demand_kwh: Optional[float] = None
    peak_sun_hours: Optional[float] = None
    panel_capacity_kw: Optional[float] = None
    battery_capacity_kwh: Optional[float] = None
    inverter_capacity_kw: Optional[float] = None
    daily_output_kwh: Optional[float] = None
    excess_kwh: Optional[float] = None
    battery_type: Optional[str] = None
    panel_cost_ksh: Optional[float] = None
    battery_cost_ksh: Optional[float] = None
    inverter_cost_ksh: Optional[float] = None
    installation_cost_ksh: Optional[float] = None
    total_cost_ksh: Optional[float] = None
    roi_years: Optional[float] = None
    system_efficiency: Optional[float] = None
    site: Optional[str] = None
    equipment: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    report_template: Optional[str] = None
    created_by: Optional[Dict[str, Any]] = None
    address_street: Optional[str] = None
    address_province: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_country: Optional[str] = None
    address: Optional[str] = None
    address_complement: Optional[str] = None
    contact_first_name: Optional[str] = None
    contact_last_name: Optional[str] = None
    contact_mobile: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = None
    public_link: Optional[str] = None
    technician_id: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    created_by_customer: Optional[bool] = None
    position: Optional[Dict[str, float]] = None
    custom_field_values: Optional[Dict[str, Any]] = None
    date_created: Optional[str] = None
    date_modified: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    technician_name: Optional[str] = None
    technician_login: Optional[str] = None
    job_type: Optional[str] = None
    diagnosis: Optional[str] = None
    feedback: Optional[str] = None
    adjusted_energy_demand_kwh: Optional[float] = None  # Added
    lead_acid_ah_demand: Optional[float] = None  # Added
    lithium_ion_ah_demand: Optional[float] = None  # Added
    panels_required: Optional[int] = None  # Added
    lead_acid_batteries_required: Optional[int] = None  # Added
    lithium_ion_batteries_required: Optional[int] = None  # Added
    inverters_required: Optional[int] = None  # Added
    lead_acid_batteries_series: Optional[int] = None  # Added
    lead_acid_batteries_parallel: Optional[int] = None  # Added
    lithium_ion_batteries_series: Optional[int] = None  # Added
    lithium_ion_batteries_parallel: Optional[int] = None  # Added
    messages: Annotated[List[Dict[str, Any]], add_messages] = []
    db: Optional[Any] = None