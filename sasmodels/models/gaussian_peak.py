r"""

Definition
----------

This model describes a Gaussian shaped peak on a flat background

.. math::

    I(q) = (\text{scale}) \exp\left[ -\tfrac12 (q-q_0)^2 / \sigma^2 \right]
        + \text{background}

with the peak having height of *scale* centered at $q_0$ and having a standard
deviation of $\sigma$. The FWHM (full-width half-maximum) is $2.354 \sigma$.

For 2D data, scattering intensity is calculated in the same way as 1D,
where the $q$ vector is defined as

.. math::

    q = \sqrt{q_x^2 + q_y^2}


References
----------

None.
"""

from numpy import inf

name = "gaussian_peak"
title = "Gaussian shaped peak"
description = """
    Model describes a Gaussian shaped peak including a flat background
    Provide F(q) = scale*exp( -1/2 *[(q-peak_pos)/sigma]^2 )+ background
"""
category = "shape-independent"

#             ["name", "units", default, [lower, upper], "type","description"],
parameters = [["peak_pos", "1/Ang", 0.05, [-inf, inf], "", "Peak position"],
              ["sigma", "1/Ang", 0.005, [0, inf], "",
               "Peak width (standard deviation)"],
             ]

Iq = """
    double scaled_dq = (q - peak_pos)/sigma;
    return exp(-0.5*scaled_dq*scaled_dq); //sqrt(2*M_PI*sigma*sigma);
    """

# VR defaults to 1.0

demo = dict(scale=1, background=0, peak_pos=0.05, sigma=0.005)
