import numpy as np

def fit_line(ratings: list[int]) -> dict:
    if len(ratings) < 2:
        raise ValueError("Need at least 2 points to fit a line")
    
    y = np.array(ratings, dtype=float)
    x = np.arange(len(y))

    x_dev = x - x.mean()
    y_dev = y - y.mean()

    slope = (x_dev * y_dev).sum() / (x_dev**2).sum()
    intercept = y.mean() - slope * x.mean()

    fitted = slope * x + intercept
    ss_res = ((y - fitted) ** 2).sum()
    ss_tot = (y_dev ** 2).sum()
    r_squared = 1 - ss_res / ss_tot if ss_tot else 1.0

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "n": len(y),
    }

def predict(model: dict, games_ahead: int) -> float:
    next_index = model["n"] - 1 + games_ahead
    return model["slope"] * next_index + model["intercept"]
