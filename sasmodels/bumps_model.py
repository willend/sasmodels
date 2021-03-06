"""
Wrap sasmodels for direct use by bumps.

:class:`Model` is a wrapper for the sasmodels kernel which defines a
bumps *Parameter* box for each kernel parameter.  *Model* accepts keyword
arguments to set the initial value for each parameter.

:class:`Experiment` combines the *Model* function with a data file loaded by
the sasview data loader.  *Experiment* takes a *cutoff* parameter controlling
how far the polydispersity integral extends.

"""
from __future__ import print_function

__all__ = ["Model", "Experiment"]

import numpy as np  # type: ignore

from .data import plot_theory
from .direct_model import DataMixin

try:
    from typing import Dict, Union, Tuple, Any
    from .data import Data1D, Data2D
    from .kernel import KernelModel
    from .modelinfo import ModelInfo
    Data = Union[Data1D, Data2D]
except ImportError:
    pass

try:
    # Optional import. This allows the doc builder and nosetests to run even
    # when bumps is not on the path.
    from bumps.names import Parameter # type: ignore
except ImportError:
    pass


def create_parameters(model_info, **kwargs):
    # type: (ModelInfo, **Union[float, str, Parameter]) -> Tuple[Dict[str, Parameter], Dict[str, str]]
    """
    Generate Bumps parameters from the model info.

    *model_info* is returned from :func:`generate.model_info` on the
    model definition module.

    Any additional *key=value* pairs are initial values for the parameters
    to the models.  Uninitialized parameters will use the model default
    value.  The value can be a float, a bumps parameter, or in the case
    of the distribution type parameter, a string.

    Returns a dictionary of *{name: Parameter}* containing the bumps
    parameters for each model parameter, and a dictionary of
    *{name: str}* containing the polydispersity distribution types.
    """
    pars = {}     # type: Dict[str, Parameter]
    pd_types = {} # type: Dict[str, str]
    for p in model_info.parameters.call_parameters:
        value = kwargs.pop(p.name, p.default)
        pars[p.name] = Parameter.default(value, name=p.name, limits=p.limits)
        if p.polydisperse:
            for part, default, limits in [
                    ('_pd', 0., pars[p.name].limits),
                    ('_pd_n', 35., (0, 1000)),
                    ('_pd_nsigma', 3., (0, 10)),
                ]:
                name = p.name + part
                value = kwargs.pop(name, default)
                pars[name] = Parameter.default(value, name=name, limits=limits)
            name = p.name + '_pd_type'
            pd_types[name] = str(kwargs.pop(name, 'gaussian'))

    if kwargs:  # args not corresponding to parameters
        raise TypeError("unexpected parameters: %s"
                        % (", ".join(sorted(kwargs.keys()))))

    return pars, pd_types

class Model(object):
    """
    Bumps wrapper for a SAS model.

    *model* is a runnable module as returned from :func:`core.load_model`.

    *cutoff* is the polydispersity weight cutoff.

    Any additional *key=value* pairs are model dependent parameters.
    """
    def __init__(self, model, **kwargs):
        # type: (KernelModel, **Dict[str, Union[float, Parameter]]) -> None
        self.sasmodel = model
        pars, pd_types = create_parameters(model.info, **kwargs)
        for k, v in pars.items():
            setattr(self, k, v)
        for k, v in pd_types.items():
            setattr(self, k, v)
        self._parameter_names = list(pars.keys())
        self._pd_type_names = list(pd_types.keys())

    def parameters(self):
        # type: () -> Dict[str, Parameter]
        """
        Return a dictionary of parameters objects for the parameters,
        excluding polydispersity distribution type.
        """
        return dict((k, getattr(self, k)) for k in self._parameter_names)

    def state(self):
        # type: () -> Dict[str, Union[Parameter, str]]
        """
        Return a dictionary of current values for all the parameters,
        including polydispersity distribution type.
        """
        pars = dict((k, getattr(self, k).value) for k in self._parameter_names)
        pars.update((k, getattr(self, k)) for k in self._pd_type_names)
        return pars

class Experiment(DataMixin):
    r"""
    Bumps wrapper for a SAS experiment.

    *data* is a :class:`data.Data1D`, :class:`data.Data2D` or
    :class:`data.Sesans` object.  Use :func:`data.empty_data1D` or
    :func:`data.empty_data2D` to define $q, \Delta q$ calculation
    points for displaying the SANS curve when there is no measured data.

    *model* is a :class:`Model` object.

    *cutoff* is the integration cutoff, which avoids computing the
    the SAS model where the polydispersity weight is low.

    The resulting model can be used directly in a Bumps FitProblem call.
    """
    _cache = None # type: Dict[str, np.ndarray]
    def __init__(self, data, model, cutoff=1e-5):
        # type: (Data, Model, float) -> None
        # remember inputs so we can inspect from outside
        self.model = model
        self.cutoff = cutoff
        self._interpret_data(data, model.sasmodel)
        self._cache = {}

    def update(self):
        # type: () -> None
        """
        Call when model parameters have changed and theory needs to be
        recalculated.
        """
        self._cache.clear()

    def numpoints(self):
        # type: () -> float
        """
        Return the number of data points
        """
        return len(self.Iq)

    def parameters(self):
        # type: () -> Dict[str, Parameter]
        """
        Return a dictionary of parameters
        """
        return self.model.parameters()

    def theory(self):
        # type: () -> np.ndarray
        """
        Return the theory corresponding to the model parameters.

        This method uses lazy evaluation, and requires model.update() to be
        called when the parameters have changed.
        """
        if 'theory' not in self._cache:
            pars = self.model.state()
            self._cache['theory'] = self._calc_theory(pars, cutoff=self.cutoff)
        return self._cache['theory']

    def residuals(self):
        # type: () -> np.ndarray
        """
        Return theory minus data normalized by uncertainty.
        """
        #if np.any(self.err ==0): print("zeros in err")
        return (self.theory() - self.Iq) / self.dIq

    def nllf(self):
        # type: () -> float
        """
        Return the negative log likelihood of seeing data given the model
        parameters, up to a normalizing constant which depends on the data
        uncertainty.
        """
        delta = self.residuals()
        #if np.any(np.isnan(R)): print("NaN in residuals")
        return 0.5 * np.sum(delta**2)

    #def __call__(self):
    #    return 2 * self.nllf() / self.dof

    def plot(self, view='log'):
        # type: (str) -> None
        """
        Plot the data and residuals.
        """
        data, theory, resid = self._data, self.theory(), self.residuals()
        plot_theory(data, theory, resid, view, Iq_calc=self.Iq_calc)

    def simulate_data(self, noise=None):
        # type: (float) -> None
        """
        Generate simulated data.
        """
        Iq = self.theory()
        self._set_data(Iq, noise)

    def save(self, basename):
        # type: (str) -> None
        """
        Save the model parameters and data into a file.

        Not Implemented.
        """
        if self.data_type == "sesans":
            np.savetxt(basename+".dat", np.array([self._data.x, self.theory()]).T)

    def __getstate__(self):
        # type: () -> Dict[str, Any]
        # Can't pickle gpu functions, so instead make them lazy
        state = self.__dict__.copy()
        state['_kernel'] = None
        return state

    def __setstate__(self, state):
        # type: (Dict[str, Any]) -> None
        # pylint: disable=attribute-defined-outside-init
        self.__dict__ = state

