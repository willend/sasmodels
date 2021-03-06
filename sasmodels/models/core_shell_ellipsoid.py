r"""
Definition
----------

Parameters for this model are the core axial ratio X and a shell thickness,
which are more often what we would like to determine and makes the model
better behaved, particularly when polydispersity is applied than the four
independent radii used in the original parameterization of this model.


.. figure:: img/core_shell_ellipsoid_geometry.png

The geometric parameters of this model are shown in the diagram above, which
shows (a) a cut through at the circular equator and (b) a cross section through
the poles, of a prolate ellipsoid.

When *X_core < 1* the core is oblate; when *X_core > 1* it is prolate.
*X_core = 1* is a spherical core.

For a fixed shell thickness *XpolarShell = 1*, to scale the shell thickness
pro-rata with the radius set or constrain *XpolarShell = X_core*.

When including an $S(q)$, the radius in $S(q)$ is calculated to be that of
a sphere with the same 2nd virial coefficient of the outer surface of the
ellipsoid. This may have some undesirable effects if the aspect ratio of the
ellipsoid is large (ie, if $X << 1$ or $X >> 1$ ), when the $S(q)$
- which assumes spheres - will not in any case be valid.  Generating a 
custom product model will enable separate effective volume fraction and effective 
radius in the $S(q)$.

If SAS data are in absolute units, and the SLDs are correct, then scale should
be the total volume fraction of the "outer particle". When $S(q)$ is introduced
this moves to the $S(q)$ volume fraction, and scale should then be 1.0,
or contain some other units conversion factor (for example, if you have SAXS data).

The calculation of intensity follows that for the solid ellipsoid, but with separate
terms for the core-shell and shell-solvent boundaries.

.. math::

    P(q,\alpha) = \frac{\text{scale}}{V} F^2(q,\alpha) + \text{background}

where

.. math::
    \begin{align}    
    F(q,\alpha) = &f(q,radius\_equat\_core,radius\_equat\_core.x\_core,\alpha) \\
    &+ f(q,radius\_equat\_core + thick\_shell,radius\_equat\_core.x\_core + thick\_shell.x\_polar\_shell,\alpha)
    \end{align} 

where
 
.. math::

    f(q,R_e,R_p,\alpha) = \frac{3 \Delta \rho V (\sin[qr(R_p,R_e,\alpha)]
                - \cos[qr(R_p,R_e,\alpha)])}
                {[qr(R_p,R_e,\alpha)]^3}

and

.. math::

    r(R_e,R_p,\alpha) = \left[ R_e^2 \sin^2 \alpha
        + R_p^2 \cos^2 \alpha \right]^{1/2}


$\alpha$ is the angle between the axis of the ellipsoid and $\vec q$,
$V = (4/3)\pi R_pR_e^2$ is the volume of the ellipsoid , $R_p$ is the polar radius along the
rotational axis of the ellipsoid, $R_e$ is the equatorial radius perpendicular
to the rotational axis of the ellipsoid and $\Delta \rho$ (contrast) is the
scattering length density difference, either $(sld\_core - sld\_shell)$ or $(sld\_shell - sld\_solvent)$.

For randomly oriented particles:

.. math::

   F^2(q)=\int_{0}^{\pi/2}{F^2(q,\alpha)\sin(\alpha)d\alpha}


References
----------
see for example:
Kotlarchyk, M.; Chen, S.-H. J. Chem. Phys., 1983, 79, 2461.
Berr, S.  J. Phys. Chem., 1987, 91, 4760.

Authorship and Verification
----------------------------

* **Author:** NIST IGOR/DANSE **Date:** pre 2010
* **Last Modified by:** Richard Heenan (reparametrised model) **Date:** 2015
* **Last Reviewed by:** Richard Heenan **Date:** October 6, 2016

"""

from numpy import inf, sin, cos, pi

name = "core_shell_ellipsoid"
title = "Form factor for an spheroid ellipsoid particle with a core shell structure."
description = """
        [core_shell_ellipsoid] Calculates the form factor for an spheroid
        ellipsoid particle with a core_shell structure.
        The form factor is averaged over all possible
        orientations of the ellipsoid such that P(q)
        = scale*<f^2>/Vol + bkg, where f is the
        single particle scattering amplitude.
        [Parameters]:
        radius_equat_core = equatorial radius of core,
        x_core = ratio of core polar/equatorial radii,
        thick_shell = equatorial radius of outer surface,
        x_polar_shell = ratio of polar shell thickness to equatorial shell thickness,
        sld_core = SLD_core
        sld_shell = SLD_shell
        sld_solvent = SLD_solvent
        background = Incoherent bkg
        scale =scale
        Note:It is the users' responsibility to ensure
        that shell radii are larger than core radii.
        oblate: polar radius < equatorial radius
        prolate :  polar radius > equatorial radius - this new model will make this easier
        and polydispersity integrals more logical (as previously the shell could disappear).
    """
category = "shape:ellipsoid"

# pylint: disable=bad-whitespace, line-too-long
#             ["name", "units", default, [lower, upper], "type", "description"],
parameters = [
    ["radius_equat_core","Ang",     20,   [0, inf],    "volume",      "Equatorial radius of core"],
    ["x_core",        "None",       3,   [0, inf],    "volume",      "axial ratio of core, X = r_polar/r_equatorial"],
    ["thick_shell",   "Ang",       30,   [0, inf],    "volume",      "thickness of shell at equator"],
    ["x_polar_shell", "",           1,   [0, inf],    "volume",      "ratio of thickness of shell at pole to that at equator"],
    ["sld_core",      "1e-6/Ang^2", 2,   [-inf, inf], "sld",         "Core scattering length density"],
    ["sld_shell",     "1e-6/Ang^2", 1,   [-inf, inf], "sld",         "Shell scattering length density"],
    ["sld_solvent",   "1e-6/Ang^2", 6.3, [-inf, inf], "sld",         "Solvent scattering length density"],
    ["theta",         "degrees",    0,   [-inf, inf], "orientation", "Oblate orientation wrt incoming beam"],
    ["phi",           "degrees",    0,   [-inf, inf], "orientation", "Oblate orientation in the plane of the detector"],
    ]
# pylint: enable=bad-whitespace, line-too-long

source = ["lib/sph_j1c.c", "lib/gfn.c", "lib/gauss76.c",
          "core_shell_ellipsoid.c"]

def ER(radius_equat_core, x_core, thick_shell, x_polar_shell):
    """
        Returns the effective radius used in the S*P calculation
    """
    from .ellipsoid import ER as ellipsoid_ER
    polar_outer = radius_equat_core*x_core + thick_shell*x_polar_shell
    equat_outer = radius_equat_core + thick_shell
    return ellipsoid_ER(polar_outer, equat_outer)


demo = dict(scale=0.05, background=0.001,
            radius_equat_core=20.0,
            x_core=3.0,
            thick_shell=30.0,
            x_polar_shell=1.0,
            sld_core=2.0,
            sld_shell=1.0,
            sld_solvent=6.3,
            theta=0,
            phi=0)

q = 0.1
phi = pi/6
qx = q*cos(phi)
qy = q*sin(phi)
# After redefinition of angles find new reasonable values for unit test
#tests = [
#    # Accuracy tests based on content in test/utest_coreshellellipsoidXTmodel.py
#    [{'radius_equat_core': 200.0,
#      'x_core': 0.1,
#      'thick_shell': 50.0,
#      'x_polar_shell': 0.2,
#      'sld_core': 2.0,
#      'sld_shell': 1.0,
#      'sld_solvent': 6.3,
#      'background': 0.001,
#      'scale': 1.0,
#     }, 1.0, 0.00189402],

    # Additional tests with larger range of parameters
#    [{'background': 0.01}, 0.1, 11.6915],

#    [{'radius_equat_core': 20.0,
#      'x_core': 200.0,
#      'thick_shell': 54.0,
#      'x_polar_shell': 3.0,
#      'sld_core': 20.0,
#      'sld_shell': 10.0,
#      'sld_solvent': 6.0,
#      'background': 0.0,
#      'scale': 1.0,
#     }, 0.01, 8688.53],

#   [{'background': 0.001}, (0.4, 0.5), 0.00690673],

#   [{'radius_equat_core': 20.0,
#      'x_core': 200.0,
#      'thick_shell': 54.0,
#      'x_polar_shell': 3.0,
#      'sld_core': 20.0,
#      'sld_shell': 10.0,
#      'sld_solvent': 6.0,
#      'background': 0.01,
#      'scale': 0.01,
#     }, (qx, qy), 0.0100002],
#    ]
