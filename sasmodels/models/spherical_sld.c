static double form_volume(
    int n_shells,
    double thickness[],
    double interface[])
{
    double r = 0.0;
    for (int i=0; i < n_shells; i++) {
        r += thickness[i] + interface[i];
    }
    return M_4PI_3*cube(r);
}

static double blend(int shape, double nu, double z)
{
    if (shape==0) {
        const double num = sas_erf(nu * M_SQRT1_2 * (2.0*z - 1.0));
        const double denom = 2.0 * sas_erf(nu * M_SQRT1_2);
        return num/denom + 0.5;
    } else if (shape==1) {
        return pow(z, nu);
    } else if (shape==2) {
        return 1.0 - pow(1. - z, nu);
    } else if (shape==3) {
        return expm1(-nu*z)/expm1(-nu);
    } else if (shape==4) {
        return expm1(nu*z)/expm1(nu);
    } else {
        return NAN;
    }
}

static double f_linear(double q, double r, double contrast, double slope)
{
    const double qr = q * r;
    const double qrsq = qr * qr;
    const double bes = sph_j1c(qr);
    double sinqr, cosqr;
    SINCOS(qr, sinqr, cosqr);
    const double fun = 3.0*r*(2.0*qr*sinqr - (qrsq-2.0)*cosqr)/(qrsq*qrsq);
    const double vol = M_4PI_3 * cube(r);
    return vol*(bes*contrast + fun*slope);
}

static double Iq(
    double q,
    int n_shells,
    double sld_solvent,
    double sld[],
    double thickness[],
    double interface[],
    double shape[],
    double nu[],
    int n_steps)
{
    // iteration for # of shells + core + solvent
    double f=0.0;
    double r=0.0;
    for (int shell=0; shell<n_shells; shell++){
        const double sld_l = sld[shell];

        // uniform shell; r=0 => r^3=0 => f=0, so works for core as well.
        f -= M_4PI_3 * cube(r) * sld_l * sph_j1c(q*r);
        r += thickness[shell];
        f += M_4PI_3 * cube(r) * sld_l * sph_j1c(q*r);

        // iterate over sub_shells in the interface
        const double dr = interface[shell]/n_steps;
        const double delta = (shell==n_shells-1 ? sld_solvent : sld[shell+1]) - sld_l;
        const double nu_shell = fmax(fabs(nu[shell]), 1.e-14);
        const int shape_shell = (int)(shape[shell]);

        // if there is no interface the equations don't work
        if (dr == 0.) continue;

        double sld_in = sld_l;
        for (int step=1; step <= n_steps; step++) {
            // find sld_i at the outer boundary of sub-shell step
            //const double z = (double)step/(double)n_steps;
            const double z = (double)step/(double)n_steps;
            const double fraction = blend(shape_shell, nu_shell, z);
            const double sld_out = fraction*delta + sld_l;
            // calculate slope
            const double slope = (sld_out - sld_in)/dr;
            const double contrast = sld_in - slope*r;

            // iteration for the left and right boundary of the shells
            f -= f_linear(q, r, contrast, slope);
            r += dr;
            f += f_linear(q, r, contrast, slope);
            sld_in = sld_out;
        }
    }
    // add in solvent effect
    f -= M_4PI_3 * cube(r) * sld_solvent * sph_j1c(q*r);

    const double f2 = f * f * 1.0e-4;
    return f2;
}

