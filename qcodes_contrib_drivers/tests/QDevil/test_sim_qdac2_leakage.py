import pytest
from unittest.mock import MagicMock, call
import numpy as np
import itertools
import math
from .sim_qdac2_fixtures import qdac  # noqa
from qcodes_contrib_drivers.drivers.QDevil.QDAC2 import diff_matrix


def test_diff_matrix():
    # -----------------------------------------------------------------------
    diff = diff_matrix([0.1,0.2], [[0.1,0.3],[0.3,0.2]])
    # -----------------------------------------------------------------------
    expected = np.array([[0.0,0.1], [0.2,0.0]])
    assert np.allclose(diff, expected)


def test_arrangement_channel_numbers(qdac):
    gates = {'sensor1': 1, 'plunger2': 2, 'plunger3': 3}
    arrangement = qdac.arrange(gates)
    # -----------------------------------------------------------------------
    numbers = arrangement.channel_numbers
    # -----------------------------------------------------------------------
    assert numbers == [1,2,3]


def test_arrangement_steady_state(qdac, mocker):
    sleep_fn = mocker.patch('qcodes_contrib_drivers.drivers.QDevil.QDAC2.sleep_s')
    gates = {'sensor1': 1, 'plunger2': 2, 'plunger3': 3}
    arrangement = qdac.arrange(gates)
    qdac.start_recording_scpi()
    # -----------------------------------------------------------------------
    nplc=2
    currents_A = arrangement.currents_A(nplc=nplc)
    # -----------------------------------------------------------------------
    assert currents_A == [0.1,0.2,0.3]  # Hard-coded in simulation
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        'sens:rang low,(@1,2,3)',
        'sens:nplc 2,(@1,2,3)',
        # (Sleep 1 PLC)
        'read? (@1,2,3)',
        # (Sleep NPLC / line_freq)
        'read? (@1,2,3)',
    ]
    discard_s = 1/50
    measure_s = (nplc+1)/50
    sleep_fn.assert_has_calls([call(discard_s),call(measure_s)])


def test_arrangement_leakage(qdac, mocker):  # noqa
    sleep_fn = mocker.patch('qcodes_contrib_drivers.drivers.QDevil.QDAC2.sleep_s')
    gates = {'sensor1': 1, 'plunger2': 2, 'plunger3': 3}
    # Mock current readings
    currents = {'sensor1': 0.1, 'plunger2': 0.2, 'plunger3': 0.3}
    for gate, current_A in currents.items():
        qdac.channel(gates[gate]).read_current_A = MagicMock(return_value=current_A)
    arrangement = qdac.arrange(gates)
    arrangement.set_virtual_voltages({'sensor1': 0.3, 'plunger3': 0.4})
    # Mock clear_measurements to do nothing
    arrangement.clear_measurements = MagicMock()
    qdac.start_recording_scpi()
    # -----------------------------------------------------------------------
    nplc=2
    leakage_matrix = arrangement.leakage(modulation_V=0.005, nplc=nplc)
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        'sens:rang low,(@1,2,3)',
        'sens:nplc 2,(@1,2,3)',
        # Discard first reading
        'read? (@1,2,3)',
        # Steady-state reading
        'read? (@1,2,3)',
        # First modulation
        'sour1:volt:mode fix',
        'sour1:volt 0.305',
        'sour2:volt:mode fix',
        'sour2:volt 0.0',
        'sour3:volt:mode fix',
        'sour3:volt 0.4',
        'sens:rang low,(@1,2,3)',
        'sens:nplc 2,(@1,2,3)',
        'read? (@1,2,3)',
        'read? (@1,2,3)',
        'sour1:volt:mode fix',
        'sour1:volt 0.3',
        'sour2:volt:mode fix',
        'sour2:volt 0.0',
        'sour3:volt:mode fix',
        'sour3:volt 0.4',
        # Second modulation
        'sour1:volt:mode fix',
        'sour1:volt 0.3',
        'sour2:volt:mode fix',
        'sour2:volt 0.005',
        'sour3:volt:mode fix',
        'sour3:volt 0.4',
        'sens:rang low,(@1,2,3)',
        'sens:nplc 2,(@1,2,3)',
        'read? (@1,2,3)',
        'read? (@1,2,3)',
        'sour1:volt:mode fix',
        'sour1:volt 0.3',
        'sour2:volt:mode fix',
        'sour2:volt 0.0',
        'sour3:volt:mode fix',
        'sour3:volt 0.4',
        # Third modulation
        'sour1:volt:mode fix',
        'sour1:volt 0.3',
        'sour2:volt:mode fix',
        'sour2:volt 0.0',
        'sour3:volt:mode fix',
        'sour3:volt 0.405',
        'sens:rang low,(@1,2,3)',
        'sens:nplc 2,(@1,2,3)',
        'read? (@1,2,3)',
        'read? (@1,2,3)',
        'sour1:volt:mode fix',
        'sour1:volt 0.3',
        'sour2:volt:mode fix',
        'sour2:volt 0.0',
        'sour3:volt:mode fix',
        'sour3:volt 0.4',
    ]
    inf = math.inf
    expected = [[inf, inf, inf], [inf, inf, inf], [inf, inf, inf]]
    assert np.allclose(leakage_matrix, np.array(expected))
