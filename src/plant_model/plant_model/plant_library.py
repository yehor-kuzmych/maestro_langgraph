import numpy as np 
import scipy.optimize as opt
import matplotlib.pyplot as plt


def sigmoid(x, K, a, b):
    """!
    Sigmoid function for curve fitting.

    @param x<float>: Input value or array.
    @param K<float>: Maximum value of the sigmoid.
    @param a<float>: Growth rate of the sigmoid.
    @param b<float>: Midpoint of the sigmoid.
    @return<float>: Output of the sigmoid function.
    """
    return K/(1 + np.exp(-a * (x - b)))


def sigmoid_fit(x_data, y_data):
    """!
    Fits a sigmoid function to the given data.

    @param x_data<list>: Independent variable data.
    @param y_data<list>: Dependent variable data.
    @return<tuple>: Fitted parameters (K, a, b) of the sigmoid function.
    """
    params, covariance = opt.curve_fit(sigmoid, x_data, y_data, p0=[max(y_data), 1, np.median(x_data)])
    K_fit, a_fit, b_fit = params
    return K_fit, a_fit, b_fit


def pH_photosynthesis_CO2(k_pH, delta_pH):
    """!
    Calculates the CO2 absorption rate based on pH deviation.

    @param k_pH<float>: Sensitivity coefficient for pH.
    @param delta_pH<float>: Difference between current and optimal soil pH.
    @return<float>: CO2 absorption rate change.
    """
    delta_CO2 = -k_pH * delta_pH
    return delta_CO2


def Evaporation(R, moisture_history=[], sunlight_history=[], time_window=[0, 10], dt=300):
    """!
    Estimates soil evaporation rate based on historical and environmental data.

    @param R<float>: Incident radiation energy (W/m²).
    @param moisture_history<list>: Historical soil moisture values.
    @param sunlight_history<list>: Historical sunlight intensity values.
    @param time_window<list>: Time range for estimation (start, end indices).
    @param dt<int>: Time step in seconds.
    @return<float>: Estimated evaporation rate (kg/(s*m²)).
    """
    K_soil = 0
    L = (40.65 * 1000) / (18 / 1000)  # Latent heat of vaporization (J/kg).
    soil_mass = estimate_soil_mass(moisture_history, sunlight_history, time_window)
    water_mass_history = [soil_mass * wp / (1 - wp) for wp in moisture_history]
    K_fit, A_fit, B_fit = sigmoid_fit(list(range(0, dt * len(water_mass_history), dt)), water_mass_history)
    current_P_estimate = sigmoid(dt * len(water_mass_history), K_fit, A_fit, B_fit)
    ## very small float in order to prevent division by zero errors
    epsilon = 0.00000001 
    evap = current_P_estimate - K_soil / (L + epsilon) + R / (L + epsilon)
    return evap


def next_watering_estimate(percentage_threshold, R, moisture_history=[], sunlight_history=[], time_window=[0, 10], dt=300):
    """!
    Estimates the time until the next watering is needed.

    @param percentage_threshold<float>: Moisture percentage threshold for watering.
    @param R<float>: Incident radiation energy (W/m²).
    @param moisture_history<list>: Historical soil moisture values.
    @param sunlight_history<list>: Historical sunlight intensity values.
    @param time_window<list>: Time range for estimation (start, end indices).
    @param dt<int>: Time step in seconds.
    @return<float>: Estimated time (seconds) until watering is needed.
    """
    wm_init = estimate_water_mass(moisture_history, sunlight_history, time_window)
    sm = estimate_soil_mass(moisture_history, sunlight_history, time_window)
    evap = Evaporation(R, moisture_history, sunlight_history, time_window, dt)
    t = (wm_init * (1 - percentage_threshold) - percentage_threshold * sm) / (evap * (1 - percentage_threshold))
    return t


def total_energy(sunlight_history=[], dt=300):
    """!
    Calculates the total energy from sunlight over a given period.

    @param sunlight_history<list>: Historical sunlight intensity values.
    @param dt<int>: Time step in seconds.
    @return<float>: Total incident energy (J).
    """
    total_E = 0
    if len(sunlight_history) > 0:
        for e in sunlight_history:
            total_E += e * dt
    return total_E


def estimate_soil_mass(moisture_history=[], sunlight_history=[], time_window=[0, 10]):
    """!
    Estimates soil mass based on historical moisture and sunlight data.

    @param moisture_history<list>: Historical soil moisture values.
    @param sunlight_history<list>: Historical sunlight intensity values.
    @param time_window<list>: Time range for estimation (start, end indices).
    @return<float>: Estimated soil mass (kg).
    """
    if len(moisture_history) > (time_window[1] - time_window[0]) and len(sunlight_history) > (time_window[1] - time_window[0]):
        moisture_history = moisture_history[time_window[0]:time_window[1]]
        sunlight_history = sunlight_history[time_window[0]:time_window[1]]
    E = total_energy(sunlight_history, dt=300)
    L = 40.65 / 18
    Evaporated_water = L * E
    M1 = moisture_history[0]
    M2 = moisture_history[-1]
    soil_mass = Evaporated_water / (M1 / (1 - M1) + M2 / (1 - M2))
    return soil_mass


def estimate_water_mass(moisture_history=[], sunlight_history=[], time_window=[0, 10]):
    """!
    Estimates the water mass in the soil.

    @param moisture_history<list>: Historical soil moisture values.
    @param sunlight_history<list>: Historical sunlight intensity values.
    @param time_window<list>: Time range for estimation (start, end indices).
    @return<float>: Estimated water mass (kg).
    """
    soil_mass = estimate_soil_mass(moisture_history, sunlight_history, time_window)
    water_percentage = moisture_history[-1]
    water_mass = soil_mass * water_percentage / (1 - water_percentage)
    return water_mass


def estimate_nutrient(nutrient_measurement, moisture_history=[], sunlight_history=[], nutrient_history=[], time_window=[0, 10], dt=86400):
    """!
    Estimates nutrient uptake based on historical data.

    @param nutrient_measurement<float>: Current nutrient concentration.
    @param moisture_history<list>: Historical soil moisture values.
    @param sunlight_history<list>: Historical sunlight intensity values.
    @param nutrient_history<list>: Historical nutrient concentration values.
    @param time_window<list>: Time range for estimation (start, end indices).
    @param dt<int>: Time step in seconds.
    @return<float>: Estimated nutrient uptake.
    """
    soil_mass = estimate_soil_mass(moisture_history, sunlight_history, time_window)
    K_fit, a_fit, b_fit = sigmoid_fit(list(range(0, len(nutrient_history) * dt, dt))[time_window[0]:time_window[1]], 
                                      nutrient_measurement[time_window[0]:time_window[1]])
    nutrient_uptake_estimate = sigmoid(len(nutrient_history), K_fit, a_fit, b_fit)
    return nutrient_uptake_estimate


def estimate_next_fertilization(nutrient_measurement, nutrient_threshold=0, moisture_history=[], sunlight_history=[], nutrient_history=[], time_window=[0, 10], dt=86400):
    """!
    Estimates the time until the next fertilization is needed.

    @param nutrient_measurement<float>: Current nutrient concentration.
    @param nutrient_threshold<float>: Minimum required nutrient level.
    @param moisture_history<list>: Historical soil moisture values.
    @param sunlight_history<list>: Historical sunlight intensity values.
    @param nutrient_history<list>: Historical nutrient concentration values.
    @param time_window<list>: Time range for estimation (start, end indices).
    @param dt<int>: Time step in seconds.
    @return<float>: Estimated time (seconds) until fertilization is needed.
    """
    soil_mass = estimate_soil_mass(moisture_history, sunlight_history, time_window)
    total_nutrient_mass = soil_mass * nutrient_measurement
    K_fit, a_fit, b_fit = sigmoid_fit(list(range(0, len(nutrient_history) * dt, dt))[time_window[0]:time_window[1]], 
                                      nutrient_measurement[time_window[0]:time_window[1]])
    nutrient_uptake_estimate = sigmoid(len(nutrient_history), K_fit, a_fit, b_fit)
    return (total_nutrient_mass - nutrient_threshold) / (nutrient_uptake_estimate + 0.000000001)


def plot_history(measurements, dt, time_window=[0, 10], save=False, fig_name=""):
    """!
    Plots historical measurement data over a given time period.

    @param measurements<list>: Historical measurements to plot.
    @param dt<int>: Time step in seconds.
    @param time_window<list>: Time range for plotting (start, end indices).
    @param save<bool>: Whether to save the plot as a file.
    @param fig_name<str>: File name for saving the plot.
    """
    time = [i * dt / 3600 for i in range(len(measurements))]
    measurements = measurements[time_window[0]:time_window[1]]
    plt.figure(figsize=(10, 6))
    plt.plot(time, measurements, marker='o', linestyle='-', color='b')
    plt.title('Soil Moisture Measurements Over 24 Hours', fontsize=18)
    plt.xlabel('Hour of the Day', fontsize=16)
    plt.ylabel('Soil Moisture (%)', fontsize=16)
    plt.xticks(np.arange(0, 24, step=3), fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)
    plt.tight_layout(pad=0)
    if save:
        plt.savefig(fig_name if fig_name else "soil_moisture_plot.pdf", bbox_inches='tight', format='pdf')
    plt.show()