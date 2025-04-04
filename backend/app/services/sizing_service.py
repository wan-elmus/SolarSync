from app.services.weather_service import get_peak_sun_hours
import logging
from typing import Dict, Any, List
import math

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default power ratings for common appliances (in watts)
DEFAULT_APPLIANCE_POWER_RATINGS = {
    "lights": 7,
    "tv": 100,
    "deep_freezer": 350,
    "laptop": 60,
    "desktop": 150,
    "phone_charging": 30,
    "dispenser": 500,
    "fridge": 300
}

# System configuration constants (can be made configurable via a settings file or database)
SYSTEM_VOLTAGE_LE = 24  # Volts
SYSTEM_VOLTAGE_LI = 48  # Volts
INVERTER_EFFICIENCY = 0.90  # 90%
COULOMBIC_EFFICIENCY = 0.95  # 95% (for panels)
SYSTEM_LOSSES_FACTOR = 1.73  # Accounts for various system losses
AUTONOMY_DAYS = 1  # Number of days of autonomy
LEAD_ACID_DOD = 0.70  # 70% Depth of Discharge for Lead Acid batteries
LITHIUM_ION_DOD = 1.00  # 100% Depth of Discharge for Lithium-Ion batteries
AVAILABLE_LEAD_ACID_BATTERY = {"ah": 200, "voltage": 12}  # 200 Ah, 12 V
AVAILABLE_LITHIUM_ION_BATTERY = {"ah": 150, "voltage": 51.2}  # 150 Ah, 51.2 V
AVAILABLE_PANEL_POWER = 545  # 545 W per panel
AVAILABLE_INVERTER_POWER = 5000  # 5000 W per inverter

def calculate_sizing(
    system_type: str,
    appliances: List[Dict[str, Any]],
    position: Dict[str, float],
    battery_type: str
) -> Dict[str, Any]:
    """
    Calculate solar system sizing based on appliances, system type, and location.

    Args:
        system_type (str): The type of solar system ("pure" or "hybrid").
        appliances (List[Dict[str, Any]]): List of appliances with their details.
            Each appliance dict should have:
            - name (str): Name of the appliance (e.g., "lights").
            - power_w (float, optional): Power rating in watts (if not provided, use default).
            - quantity (int): Number of units.
            - runtime_hrs (float): Daily runtime in hours.
        position (Dict[str, float]): The location coordinates (e.g., {"lat": -1.2699, "lon": 36.8408}).

    Returns:
        Dict[str, Any]: A dictionary containing sizing results:
            - load_demand_kwh (float): Total daily energy demand in kWh.
            - power_demand_w (float): Total power demand in watts.
            - adjusted_energy_demand_kwh (float): Adjusted energy demand after efficiencies.
            - lead_acid_ah_demand (float): Ah demand for Lead Acid batteries.
            - lithium_ion_ah_demand (float): Ah demand for Lithium-Ion batteries.
            - panel_capacity_kw (float): Required panel capacity in kW.
            - battery_capacity_kwh (float): Required battery capacity in kWh.
            - inverter_capacity_kw (float): Required inverter capacity in kW.
            - daily_output_kwh (float): Daily energy output in kWh.
            - excess_kwh (float): Excess energy in kWh.
            - panel_cost_ksh (float): Cost of panels in KSh.
            - battery_cost_ksh (float): Cost of batteries in KSh.
            - inverter_cost_ksh (float): Cost of inverters in KSh.
            - installation_cost_ksh (float): Installation cost in KSh.
            - total_cost_ksh (float): Total cost in KSh.
            - roi_years (float): Return on investment in years.
            - system_efficiency (float): System efficiency percentage.
            - peak_sun_hours (float): Peak sun hours for the location.
            - panels_required (int): Number of panels required.
            - lead_acid_batteries_required (int): Number of Lead Acid batteries required.
            - lithium_ion_batteries_required (int): Number of Lithium-Ion batteries required.
            - inverters_required (int): Number of inverters required.
            - lead_acid_batteries_series (int): Number of Lead Acid batteries in series.
            - lead_acid_batteries_parallel (int): Number of Lead Acid batteries in parallel.
            - lithium_ion_batteries_series (int): Number of Lithium-Ion batteries in series.
            - lithium_ion_batteries_parallel (int): Number of Lithium-Ion batteries in parallel.

    Raises:
        ValueError: If system_type is invalid, position is missing required keys, or appliances are invalid.
    """
    try:
        # Validate system_type
        valid_system_types = ["pure", "hybrid"]
        if system_type not in valid_system_types:
            raise ValueError(f"Invalid system_type: {system_type}. Must be one of {valid_system_types}")
        
        # Validate battery_type
        valid_battery_types = ["lead_acid", "lithium_ion"]
        if battery_type not in valid_battery_types:
            raise ValueError(f"Invalid battery_type: {battery_type}. Must be one of {valid_battery_types}")

        # Validate position
        if not all(key in position for key in ["lat", "lon"]):
            raise ValueError("Position must contain 'lat' and 'lon' keys")

        # Validate appliances
        if not appliances or not isinstance(appliances, list):
            raise ValueError("Appliances must be a non-empty list")

        # Calculate total power and energy demand from appliances
        total_power_w = 0
        total_energy_wh = 0
        for appliance in appliances:
            if not all(key in appliance for key in ["name", "quantity", "runtime_hrs"]):
                raise ValueError(f"Appliance {appliance} must contain 'name', 'quantity', and 'runtime_hrs'")
            
            # Use default power rating if not provided
            name = appliance["name"].lower()
            power_w = appliance.get("power_w")
            if power_w is None:
                if name not in DEFAULT_APPLIANCE_POWER_RATINGS:
                    raise ValueError(f"No default power rating for appliance '{name}' and power_w not provided")
                power_w = DEFAULT_APPLIANCE_POWER_RATINGS[name]
                appliance["power_w"] = power_w  # Update the appliance dict with the default value
            
            quantity = appliance["quantity"]
            runtime_hrs = appliance["runtime_hrs"]
            
            # Calculate power and energy for this appliance
            appliance_power_w = power_w * quantity
            appliance_energy_wh = appliance_power_w * runtime_hrs
            
            total_power_w += appliance_power_w
            total_energy_wh += appliance_energy_wh

        # Convert to kWh for consistency
        load_demand_kwh = total_energy_wh / 1000  # Convert Wh to kWh
        power_demand_w = total_power_w

        # Fetch peak sun hours using weather service
        peak_sun_hours = get_peak_sun_hours(position["lat"], position["lon"])

        # Step 1: Calculate adjusted energy demand (considering inverter efficiency)
        adjusted_energy_demand_kwh = (load_demand_kwh * 1000) / INVERTER_EFFICIENCY / 1000  # Convert to Wh, adjust, then back to kWh

        # Step 2: Battery Sizing (Lead Acid)
        lead_acid_ah_demand = (adjusted_energy_demand_kwh * 1000) / SYSTEM_VOLTAGE_LE  # Ah = Wh / V
        lead_acid_ah_demand_adjusted = lead_acid_ah_demand / LEAD_ACID_DOD  # Adjust for DoD
        lead_acid_ah_demand_adjusted *= AUTONOMY_DAYS  # Adjust for autonomy days
        lead_acid_batteries_series = math.ceil(SYSTEM_VOLTAGE_LE / AVAILABLE_LEAD_ACID_BATTERY["voltage"])  # Number of batteries in series to reach system voltage
        lead_acid_battery_bank_voltage = lead_acid_batteries_series * AVAILABLE_LEAD_ACID_BATTERY["voltage"]
        lead_acid_battery_bank_ah = lead_acid_ah_demand_adjusted / lead_acid_batteries_series  # Ah per series string
        lead_acid_batteries_parallel = math.ceil(lead_acid_battery_bank_ah / AVAILABLE_LEAD_ACID_BATTERY["ah"])  # Number of parallel strings
        lead_acid_batteries_required = lead_acid_batteries_series * lead_acid_batteries_parallel
        lead_acid_battery_capacity_kwh = (lead_acid_batteries_required * AVAILABLE_LEAD_ACID_BATTERY["ah"] * AVAILABLE_LEAD_ACID_BATTERY["voltage"]) / 1000  # Convert to kWh

        # Step 3: Battery Sizing (Lithium-Ion)
        lithium_ion_ah_demand = (adjusted_energy_demand_kwh * 1000) / SYSTEM_VOLTAGE_LI
        lithium_ion_ah_demand_adjusted = lithium_ion_ah_demand / LITHIUM_ION_DOD
        lithium_ion_ah_demand_adjusted *= AUTONOMY_DAYS
        lithium_ion_batteries_series = math.ceil(SYSTEM_VOLTAGE_LI / AVAILABLE_LITHIUM_ION_BATTERY["voltage"])
        lithium_ion_battery_bank_voltage = lithium_ion_batteries_series * AVAILABLE_LITHIUM_ION_BATTERY["voltage"]
        lithium_ion_battery_bank_ah = lithium_ion_ah_demand_adjusted / lithium_ion_batteries_series
        lithium_ion_batteries_parallel = math.ceil(lithium_ion_battery_bank_ah / AVAILABLE_LITHIUM_ION_BATTERY["ah"])
        lithium_ion_batteries_required = lithium_ion_batteries_series * lithium_ion_batteries_parallel
        lithium_ion_battery_capacity_kwh = (lithium_ion_batteries_required * AVAILABLE_LITHIUM_ION_BATTERY["ah"] * AVAILABLE_LITHIUM_ION_BATTERY["voltage"]) / 1000
        
        # Select battery type for capacity and cost calculations
        if battery_type == "lead_acid":
            battery_capacity_kwh = lead_acid_battery_capacity_kwh if system_type == "hybrid" else 0
            batteries_required = lead_acid_batteries_required if system_type == "hybrid" else 0
            batteries_series = lead_acid_batteries_series if system_type == "hybrid" else 0
            batteries_parallel = lead_acid_batteries_parallel if system_type == "hybrid" else 0
            lithium_ion_batteries_required = 0
            lithium_ion_batteries_series = 0
            lithium_ion_batteries_parallel = 0
        else:  # lithium_ion
            battery_capacity_kwh = lithium_ion_battery_capacity_kwh if system_type == "hybrid" else 0
            batteries_required = lithium_ion_batteries_required if system_type == "hybrid" else 0
            batteries_series = lithium_ion_batteries_series if system_type == "hybrid" else 0
            batteries_parallel = lithium_ion_batteries_parallel if system_type == "hybrid" else 0
            lead_acid_batteries_required = 0
            lead_acid_batteries_series = 0
            lead_acid_batteries_parallel = 0

        # Step 4: Inverter Sizing
        adjusted_power_demand_w = power_demand_w / INVERTER_EFFICIENCY
        inverters_required = math.ceil(adjusted_power_demand_w / AVAILABLE_INVERTER_POWER)
        inverter_capacity_kw = (inverters_required * AVAILABLE_INVERTER_POWER) / 1000  # Convert to kW

        # Step 5: Panel Sizing
        adjusted_energy_for_panels_wh = (load_demand_kwh * 1000) / COULOMBIC_EFFICIENCY  # Adjust for coulombic efficiency
        required_power_w = (adjusted_energy_for_panels_wh / peak_sun_hours) * SYSTEM_LOSSES_FACTOR  # Account for system losses
        panels_required = math.ceil(required_power_w / AVAILABLE_PANEL_POWER)
        panel_capacity_kw = (panels_required * AVAILABLE_PANEL_POWER) / 1000  # Convert to kW

        # Step 6: Energy Output and Excess
        daily_output_kwh = panel_capacity_kw * peak_sun_hours
        excess_kwh = daily_output_kwh - load_demand_kwh if daily_output_kwh > load_demand_kwh else 0

        # Step 7: Cost Calculations (example rates, can be AI-predicted later)
        panel_cost_ksh = panel_capacity_kw * 25000  # 25,000 KSh/kW
        battery_cost_ksh = battery_capacity_kwh * 5000 # Using the selected battery type's capacity
        inverter_cost_ksh = inverter_capacity_kw * 12000  # 12,000 KSh/kW
        installation_cost_ksh = 35000  # Flat rate
        total_cost_ksh = panel_cost_ksh + battery_cost_ksh + inverter_cost_ksh + installation_cost_ksh

        # Step 8: ROI Calculation (assuming 20 KSh/kWh grid rate)
        annual_savings_ksh = excess_kwh * 365 * 20
        roi_years = total_cost_ksh / annual_savings_ksh if annual_savings_ksh > 0 else float("inf")

        # Step 9: System Efficiency (can be refined based on actual losses)
        system_efficiency = 0.85  # Default value

        result = {
            "load_demand_kwh": load_demand_kwh,
            "power_demand_w": power_demand_w,
            "adjusted_energy_demand_kwh": adjusted_energy_demand_kwh,
            "lead_acid_ah_demand": lead_acid_ah_demand_adjusted,
            "lithium_ion_ah_demand": lithium_ion_ah_demand_adjusted,
            "panel_capacity_kw": panel_capacity_kw,
            "battery_capacity_kwh": battery_capacity_kwh,
            "inverter_capacity_kw": inverter_capacity_kw,
            "daily_output_kwh": daily_output_kwh,
            "excess_kwh": excess_kwh,
            "panel_cost_ksh": panel_cost_ksh,
            "battery_cost_ksh": battery_cost_ksh,
            "inverter_cost_ksh": inverter_cost_ksh,
            "installation_cost_ksh": installation_cost_ksh,
            "total_cost_ksh": total_cost_ksh,
            "roi_years": roi_years,
            "system_efficiency": system_efficiency,
            "peak_sun_hours": peak_sun_hours,
            "panels_required": panels_required,
            "lead_acid_batteries_required": lead_acid_batteries_required if system_type == "hybrid" else 0,
            "lithium_ion_batteries_required": lithium_ion_batteries_required if system_type == "hybrid" else 0,
            "inverters_required": inverters_required,
            "lead_acid_batteries_series": lead_acid_batteries_series if system_type == "hybrid" else 0,
            "lead_acid_batteries_parallel": lead_acid_batteries_parallel if system_type == "hybrid" else 0,
            "lithium_ion_batteries_series": lithium_ion_batteries_series if system_type == "hybrid" else 0,
            "lithium_ion_batteries_parallel": lithium_ion_batteries_parallel if system_type == "hybrid" else 0,
            "battery_type": battery_type
        }
        logger.info(f"Sizing calculation result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error calculating sizing: {str(e)}")
        raise