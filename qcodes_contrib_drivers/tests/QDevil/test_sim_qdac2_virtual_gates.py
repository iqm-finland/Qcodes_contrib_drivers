import pytest
from .sim_qdac2_fixtures import qdac  # noqa
from qcodes_contrib_drivers.drivers.QDevil.QDAC2 import forward_and_back
import numpy as np


def test_arrangement_default_correction(qdac):  # noqa
    # -----------------------------------------------------------------------
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2, 'plunger3': 3})
    # -----------------------------------------------------------------------
    assert np.array_equal(arrangement.correction_matrix,
                          np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))


def test_arrangement_contact_names(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2, 'plunger3': 3})
    # -----------------------------------------------------------------------
    contacts = arrangement.contact_names
    # -----------------------------------------------------------------------
    assert contacts == ['plunger1', 'plunger2', 'plunger3']


def test_arrangement_set_virtual_voltage_non_exiting_contact(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'plunger': 1})
    # -----------------------------------------------------------------------
    with pytest.raises(ValueError) as error:
        arrangement.set_virtual_voltage('sensor', 1.0)
    # -----------------------------------------------------------------------
    assert 'No contact named "sensor"' in repr(error)


def test_arrangement_set_virtual_voltage_effectuated_immediately(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2, 'plunger3': 3})
    qdac.start_recording_scpi()
    # -----------------------------------------------------------------------
    arrangement.set_virtual_voltage('plunger2', 0.5)
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        'sour1:volt:mode fix',
        'sour1:volt 0.0',
        'sour2:volt:mode fix',
        'sour2:volt 0.5',
        'sour3:volt:mode fix',
        'sour3:volt 0.0',
    ]


def test_arrangement_default_actuals_1d(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2})
    arrangement.set_virtual_voltage('plunger2', 1.0)
    # -----------------------------------------------------------------------
    sweep = arrangement.virtual_sweep(
        contact='plunger1',
        voltages=np.linspace(-0.1, 0.1, 5),
        step_time_s=2e-5)
    # -----------------------------------------------------------------------
    assert np.allclose(sweep.actual_values_V('plunger1'),
                       [-0.1, -0.05, 0.0, 0.05, 0.1])
    assert np.allclose(sweep.actual_values_V('plunger2'),
                       [1.0, 1.0, 1.0, 1.0, 1.0])


def test_arrangement_default_actuals_2d(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2, 'plunger3': 3})
    # -----------------------------------------------------------------------
    sweep = arrangement.virtual_sweep2d(
        inner_contact='plunger2',
        inner_voltages=np.linspace(-0.2, 0.6, 5),
        outer_contact='plunger3',
        outer_voltages=np.linspace(-0.7, 0.15, 5),
        inner_step_time_s=2e-6)
    # -----------------------------------------------------------------------
    assert np.allclose(sweep.actual_values_V('plunger2'),
                       np.tile([-0.2, 0.0, 0.2, 0.4, 0.6], 5))
    assert np.allclose(sweep.actual_values_V('plunger3'),
                       np.repeat([-0.7, -0.4875, -0.275, -0.0625, 0.15], 5))


def test_arrangement_sweep(qdac):  # noqa
    qdac.free_all_triggers()
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2, 'plunger3': 3})
    sweep = arrangement.virtual_sweep2d(
        inner_contact='plunger2',
        inner_voltages=np.linspace(-0.2, 0.6, 5),
        outer_contact='plunger3',
        outer_voltages=np.linspace(-0.7, 0.15, 5),
        inner_step_time_s=2e-6)
    qdac.start_recording_scpi()
    # -----------------------------------------------------------------------
    sweep.start()
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        # Sensor 1
        'sour1:dc:trig:sour hold',
        'sour1:volt:mode list',
        'sour1:list:volt 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0',
        'sour1:list:tmod auto',
        'sour1:list:dwel 2e-06',
        'sour1:list:dir up',
        'sour1:list:coun 1',
        'sour1:dc:trig:sour bus',
        'sour1:dc:init:cont on',
        'sour1:dc:init',
        'sour1:dc:trig:sour int1',
        'sour1:dc:init:cont on',
        'sour1:dc:init',
        # Plunger 2
        'sour2:dc:trig:sour hold',
        'sour2:volt:mode list',
        'sour2:list:volt -0.2,0,0.2,0.4,0.6,-0.2,0,0.2,0.4,0.6,-0.2,0,0.2,0.4,0.6,-0.2,0,0.2,0.4,0.6,-0.2,0,0.2,0.4,0.6',
        'sour2:list:tmod auto',
        'sour2:list:dwel 2e-06',
        'sour2:list:dir up',
        'sour2:list:coun 1',
        'sour2:dc:trig:sour bus',
        'sour2:dc:init:cont on',
        'sour2:dc:init',
        'sour2:dc:trig:sour int1',
        'sour2:dc:init:cont on',
        'sour2:dc:init',
        # Plunger 3
        'sour3:dc:trig:sour hold',
        'sour3:volt:mode list',
        'sour3:list:volt -0.7,-0.7,-0.7,-0.7,-0.7,-0.4875,-0.4875,-0.4875,-0.4875,-0.4875,-0.275,-0.275,-0.275,-0.275,-0.275,-0.0625,-0.0625,-0.0625,-0.0625,-0.0625,0.15,0.15,0.15,0.15,0.15',
        'sour3:list:tmod auto',
        'sour3:list:dwel 2e-06',
        'sour3:list:dir up',
        'sour3:list:coun 1',
        'sour3:dc:trig:sour bus',
        'sour3:dc:init:cont on',
        'sour3:dc:init',
        'sour3:dc:trig:sour int1',
        'sour3:dc:init:cont on',
        'sour3:dc:init',
        # Start sweep
        'tint 1'
    ]


def test_arrangement_context_releases_trigger(qdac):  # noqa
    before = len(qdac._internal_triggers)
    # -----------------------------------------------------------------------
    with qdac.arrange(contacts={}, output_triggers={'dmm': 4}):
        pass
    # -----------------------------------------------------------------------
    after = len(qdac._internal_triggers)
    assert before == after


def test_sweep_context_releases_trigger(qdac):  # noqa
    before = len(qdac._internal_triggers)
    # -----------------------------------------------------------------------
    with qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2}) as arrangement:
        arrangement.virtual_sweep2d(
            inner_contact='plunger1',
            inner_voltages=np.linspace(-0.2, 0.6, 5),
            outer_contact='plunger2',
            outer_voltages=np.linspace(-0.7, 0.15, 5),
            inner_step_time_s=1e-6)
    # -----------------------------------------------------------------------
    after = len(qdac._internal_triggers)
    assert before == after


def test_arrangement_set_virtual_voltage_affects_whole_arrangement(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'gate1': 1, 'gate2': 2, 'gate3': 3})
    arrangement.initiate_correction('gate1', [1.0, 0.5, -0.5])
    arrangement.initiate_correction('gate2', [-0.5, 1.0, 0.5])
    arrangement.initiate_correction('gate3', [0.0, 0.0, 1.0])
    arrangement.set_virtual_voltage('gate1', 1)
    arrangement.set_virtual_voltage('gate2', 2)
    arrangement.set_virtual_voltage('gate3', 3)
    qdac.start_recording_scpi()
    # -----------------------------------------------------------------------
    arrangement.set_virtual_voltage('gate2', 4)
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        'sour1:volt:mode fix',
        'sour1:volt 1.5',
        'sour2:volt:mode fix',
        'sour2:volt 5.0',
        'sour3:volt:mode fix',
        'sour3:volt 3.0'
    ]


def test_arrangement_set_virtual_voltages_affects_at_once(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'gate1': 1, 'gate2': 2})
    arrangement.initiate_correction('gate1', [1.0, 0.12])
    arrangement.initiate_correction('gate2', [-0.12, 0.98])
    # -----------------------------------------------------------------------
    arrangement.set_virtual_voltages({'gate1': 0.1, 'gate2': 0.2})
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        'sour1:volt:mode fix',
        'sour1:volt 0.124',
        'sour2:volt:mode fix',
        'sour2:volt 0.184',
    ]


def test_stability_diagram_external(qdac):  # noqa
    qdac.free_all_triggers()
    arrangement = qdac.arrange(
        # QDAC channels 3, 6, 7, 8 connected to sample
        contacts={'sensor1': 3, 'plunger2': 6, 'plunger3': 7, 'plunger4': 8},
        # DMM external trigger connected to QDAC Output Trigger 4
        output_triggers={'dmm': 4})
    # After tuning first DQD
    arrangement.initiate_correction('sensor1', [1.0, 0.1, 0.05, -0.02])
    arrangement.initiate_correction('plunger2', [-0.2, 0.98, 0.3, 0.06])
    arrangement.initiate_correction('plunger3', [0.01, 0.41, 1.0, 0.15])
    arrangement.set_virtual_voltages({'sensor1': 0.1, 'plunger2': 0.2, 'plunger3': 0.3})
    # After tuning third QD
    arrangement.add_correction('plunger4', [0.75, -0.16, 0.56, 1.0])
    arrangement.set_virtual_voltage('plunger4', 0.4)
    # -----------------------------------------------------------------------
    assert np.allclose(arrangement.correction_matrix, np.array([
        [1, 0.1, 0.05, -0.02],
        [-0.2, 0.98, 0.3, 0.06],
        [0.01, 0.41, 1.0, 0.15],
        [0.79, 0.15, 0.55, 1.06]
    ]), atol=1e-2)
    # -----------------------------------------------------------------------
    sweep = arrangement.virtual_sweep2d(
        inner_contact='plunger4',
        inner_voltages=np.linspace(-0.2, 0.6, 5),
        outer_contact='plunger3',
        outer_voltages=np.linspace(-0.7, 0.15, 5),
        inner_step_time_s=1e-6,
        inner_step_trigger='dmm')
    # -----------------------------------------------------------------------
    A = np.array([
        # S1,   P2,     P3,    P4
        [0.089, -0.046, -0.65, -0.49],
        [0.085, -0.034, -0.62, -0.28],
        [0.081, -0.022, -0.59, -0.06],
        [0.077, -0.010, -0.56, 0.15],
        [0.073, 0.002, -0.53, 0.36],
        [0.100, 0.018, -0.43, -0.37],
        [0.096, 0.030, -0.40, -0.16],
        [0.092, 0.042, -0.37, 0.05],
        [0.088, 0.054, -0.34, 0.26],
        [0.084, 0.066, -0.31, 0.48],
        [0.110, 0.082, -0.22, -0.25],
        [0.106, 0.094, -0.19, -0.04],
        [0.102, 0.106, -0.16, 0.17],
        [0.098, 0.118, -0.13, 0.38],
        [0.094, 0.130, -0.10, 0.59],
        [0.120, 0.145, -0.01, -0.14],
        [0.117, 0.157, 0.02, 0.07],
        [0.113, 0.169, 0.05, 0.29],
        [0.109, 0.181, 0.08, 0.50],
        [0.105, 0.193, 0.11, 0.71],
        [0.132, 0.209, 0.20, -0.02],
        [0.128, 0.221, 0.23, 0.19],
        [0.124, 0.233, 0.26, 0.40],
        [0.120, 0.245, 0.29, 0.61],
        [0.116, 0.257, 0.32, 0.83]
    ])
    assert np.allclose(sweep.actual_values_V('sensor1'), A[:, 0], atol=1e-02)
    assert np.allclose(sweep.actual_values_V('plunger2'), A[:, 1], atol=1e-02)
    assert np.allclose(sweep.actual_values_V('plunger3'), A[:, 2], atol=1e-02)
    assert np.allclose(sweep.actual_values_V('plunger4'), A[:, 3], atol=1e-02)
    # -----------------------------------------------------------------------
    sweep.start()
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        # Initial voltages
        'outp:trig4:sour int1',
        'outp:trig4:widt 1e-06',
        'sour3:volt:mode fix',
        'sour3:volt 0.135',
        'sour6:volt:mode fix',
        'sour6:volt 0.266',
        'sour7:volt:mode fix',
        'sour7:volt 0.383',
        'sour8:volt:mode fix',
        'sour8:volt 0.0',
        # plunger4
        'sour3:volt:mode fix',
        'sour3:volt 0.127',
        'sour6:volt:mode fix',
        'sour6:volt 0.29',
        'sour7:volt:mode fix',
        'sour7:volt 0.443',
        'sour8:volt:mode fix',
        'sour8:volt 0.69693',
        # sweep
        'sour3:dc:mark:sst 1',
        # Sensor 1
        'sour3:dc:trig:sour hold',
        'sour3:volt:mode list',
        'sour3:list:volt 0.089,0.085,0.081,0.077,0.073,0.099625,0.095625,0.091625,0.087625,0.083625,0.11025,0.10625,0.10225,0.09825,0.09425,0.120875,0.116875,0.112875,0.108875,0.104875,0.1315,0.1275,0.1235,0.1195,0.1155',
        'sour3:list:tmod auto',
        'sour3:list:dwel 1e-06',
        'sour3:list:dir up',
        'sour3:list:coun 1',
        'sour3:dc:trig:sour bus',
        'sour3:dc:init:cont on',
        'sour3:dc:init',
        'sour3:dc:trig:sour int2',
        'sour3:dc:init:cont on',
        'sour3:dc:init',
        # Plunger 2
        'sour6:dc:trig:sour hold',
        'sour6:volt:mode list',
        'sour6:list:volt -0.046,-0.034,-0.022,-0.01,0.002,0.01775,0.02975,0.04175,0.05375,0.06575,0.0815,0.0935,0.1055,0.1175,0.1295,0.14525,0.15725,0.16925,0.18125,0.19325,0.209,0.221,0.233,0.245,0.257',
        'sour6:list:tmod auto',
        'sour6:list:dwel 1e-06',
        'sour6:list:dir up',
        'sour6:list:coun 1',
        'sour6:dc:trig:sour bus',
        'sour6:dc:init:cont on',
        'sour6:dc:init',
        'sour6:dc:trig:sour int2',
        'sour6:dc:init:cont on',
        'sour6:dc:init',
        # Plunger 3
        'sour7:dc:trig:sour hold',
        'sour7:volt:mode list',
        'sour7:list:volt -0.647,-0.617,-0.587,-0.557,-0.527,-0.4345,-0.4045,-0.3745,-0.3445,-0.3145,-0.222,-0.192,-0.162,-0.132,-0.102,-0.0095,0.0205,0.0505,0.0805,0.1105,0.203,0.233,0.263,0.293,0.323',
        'sour7:list:tmod auto',
        'sour7:list:dwel 1e-06',
        'sour7:list:dir up',
        'sour7:list:coun 1',
        'sour7:dc:trig:sour bus',
        'sour7:dc:init:cont on',
        'sour7:dc:init',
        'sour7:dc:trig:sour int2',
        'sour7:dc:init:cont on',
        'sour7:dc:init',
        # Plunger 4
        'sour8:dc:trig:sour hold',
        'sour8:volt:mode list',
        'sour8:list:volt -0.48821,-0.27633,-0.06445,0.14743,0.35931,-0.371441,-0.159561,0.0523187,0.264199,0.476079,-0.254672,-0.0427925,0.169088,0.380968,0.592847,-0.137904,0.0739763,0.285856,0.497736,0.709616,-0.021135,0.190745,0.402625,0.614505,0.826385',
        'sour8:list:tmod auto',
        'sour8:list:dwel 1e-06',
        'sour8:list:dir up',
        'sour8:list:coun 1',
        'sour8:dc:trig:sour bus',
        'sour8:dc:init:cont on',
        'sour8:dc:init',
        'sour8:dc:trig:sour int2',
        'sour8:dc:init:cont on',
        'sour8:dc:init',
        # Start sweep
        'tint 2'
    ]


def test_arrangement_detune_wrong_number_of_voltages(qdac):  # noqa
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2})
    # -----------------------------------------------------------------------
    with pytest.raises(ValueError) as error:
        arrangement.virtual_detune(
            contacts=('plunger1', 'plunger2'),
            start_V=(-0.3, 0.6),
            end_V=(0.3,),
            steps=2)
    # -----------------------------------------------------------------------
    assert 'There must be exactly one voltage per contact' in repr(error)


def test_forward_and_back():
    assert list(forward_and_back(-1, 1, 3)) == [-1, 0, 1, 0]
    assert list(forward_and_back(-2, 2, 5)) == [-2, -1, 0, 1, 2, 1, 0, -1]


def test_arrangement_detune(qdac):  # noqa
    qdac.free_all_triggers()
    arrangement = qdac.arrange(contacts={'plunger1': 1, 'plunger2': 2})
    detune = arrangement.virtual_detune(
        contacts=('plunger1', 'plunger2'),
        start_V=(-0.3, 0.6),
        end_V=(0.3, -0.1),
        steps=5,
        step_time_s=5e-6,
        repetitions=2)
    qdac.start_recording_scpi()
    # -----------------------------------------------------------------------
    detune.start()
    # -----------------------------------------------------------------------
    commands = qdac.get_recorded_scpi_commands()
    assert commands == [
        # Plunger 1
        'sour1:dc:trig:sour hold',
        'sour1:volt:mode list',
        'sour1:list:volt -0.3,-0.15,0,0.15,0.3,0.15,0,-0.15',
        'sour1:list:tmod auto',
        'sour1:list:dwel 5e-06',
        'sour1:list:dir up',
        'sour1:list:coun 2',
        'sour1:dc:trig:sour bus',
        'sour1:dc:init:cont on',
        'sour1:dc:init',
        'sour1:dc:trig:sour int1',
        'sour1:dc:init:cont on',
        'sour1:dc:init',
        # Plunger 2
        'sour2:dc:trig:sour hold',
        'sour2:volt:mode list',
        'sour2:list:volt 0.6,0.425,0.25,0.075,-0.1,0.075,0.25,0.425',
        'sour2:list:tmod auto',
        'sour2:list:dwel 5e-06',
        'sour2:list:dir up',
        'sour2:list:coun 2',
        'sour2:dc:trig:sour bus',
        'sour2:dc:init:cont on',
        'sour2:dc:init',
        'sour2:dc:trig:sour int1',
        'sour2:dc:init:cont on',
        'sour2:dc:init',
        # Start sweep
        'tint 1'
    ]
