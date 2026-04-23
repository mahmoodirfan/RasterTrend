import numpy as np


def mann_kendall_vectorized(data):
    """
    Vectorized Mann-Kendall test on a 2D array where:
      - axis 0 = time steps
      - axis 1 = pixels (flattened spatial)

    Returns:
        tau   : Kendall's tau per pixel
        p     : two-tailed p-value per pixel
        trend : +1 increasing, -1 decreasing, 0 no trend
    """
    from scipy.stats import norm

    n = data.shape[0]
    s = np.zeros(data.shape[1], dtype=np.float64)

    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = data[j] - data[i]
            s += np.sign(diff)

    # Variance of S (no ties correction — adequate for continuous raster data)
    var_s = n * (n - 1) * (2 * n + 5) / 18.0

    # Z statistic
    z = np.where(s > 0, (s - 1) / np.sqrt(var_s),
        np.where(s < 0, (s + 1) / np.sqrt(var_s), 0.0))

    # Two-tailed p-value
    p = 2 * (1 - norm.cdf(np.abs(z)))

    # Kendall tau
    tau = s / (0.5 * n * (n - 1))

    trend = np.sign(s).astype(np.int8)

    return tau, p, trend


def seasonal_mann_kendall_vectorized(data, period):
    """
    Seasonal Mann-Kendall: computes MK separately per season,
    combines S and Var(S) across seasons.

    Parameters:
        data   : 2D array (time x pixels)
        period : number of seasons per cycle (e.g. 12 for monthly)

    Returns:
        tau, p, trend per pixel
    """
    from scipy.stats import norm

    n_total = data.shape[0]
    n_pixels = data.shape[1]

    s_total = np.zeros(n_pixels, dtype=np.float64)
    var_total = np.zeros(n_pixels, dtype=np.float64)

    for season in range(period):
        season_data = data[season::period]  # subset for this season
        n = season_data.shape[0]
        if n < 3:
            continue

        s = np.zeros(n_pixels, dtype=np.float64)
        for i in range(n - 1):
            for j in range(i + 1, n):
                diff = season_data[j] - season_data[i]
                s += np.sign(diff)

        var_s = n * (n - 1) * (2 * n + 5) / 18.0
        s_total += s
        var_total += var_s

    # Guard against zero variance
    var_total = np.where(var_total == 0, 1e-10, var_total)

    z = np.where(s_total > 0, (s_total - 1) / np.sqrt(var_total),
        np.where(s_total < 0, (s_total + 1) / np.sqrt(var_total), 0.0))

    p = 2 * (1 - norm.cdf(np.abs(z)))
    tau = s_total / (np.sqrt(var_total) * np.sqrt(var_total))  # normalised
    trend = np.sign(s_total).astype(np.int8)

    return tau, p, trend


def sens_slope_vectorized(data):
    """
    Sen's slope estimator: median of all pairwise slopes.
    data: 2D array (time x pixels)

    Returns:
        slope per pixel (float64)
    """
    n = data.shape[0]
    slopes = []

    for i in range(n - 1):
        for j in range(i + 1, n):
            rise = data[j] - data[i]
            run = j - i
            slopes.append(rise / run)

    slopes = np.array(slopes)  # shape: (n_pairs, n_pixels)
    return np.median(slopes, axis=0)
