# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Contain the main class to link input to working functions.

"""
from pyhyb.inout.inout import read_data_file, parse_settings_file
from pyhyb.tools.tools import local_mean, check_segment_consistency
from pyhyb.tools.cross_tools import person, segment_overlap
from pyhyb.core.hybrid_runner import HybridWorkflowRunner

def run_build_hybrid(material_path, substrate_path, **kwargs):
    """Executes the hybrid building process."""
    runner = HybridWorkflowRunner()
    success, msg = runner.run(material_path, substrate_path, **kwargs)
    if not success:
        raise ValueError(f"Hybrid builder failed: {msg}")
    return msg

DATA_MAP = {'local_mean': ['segments', 'functions'],
            'build_hybrid': ['materials', 'substrates']}
OPERATE_MAP = {'local_mean': local_mean,
               'build_hybrid': run_build_hybrid}

CROSS_DATA_MAP = {'person': 'functions',
                  'overlap': 'segments'}
CROSS_OPERATE_MAP = {'person': person,
                     'overlap': segment_overlap}


class Geni:
    """
    Main class.

    """
    def __init__(self, input_file=None, description='PyHyB simulation'):
        """
        Initialize.

        """
        self.description = description
        self.input_file = input_file
        self.settings = {}
        self.data = {'segments': [],
                     'functions': [],
                     'materials': [],
                     'substrates': []}

    def read_settings(self):
        """
        Read settings file.

        """
        self.settings = parse_settings_file(self.input_file)

    def read_data_files(self):
        """
        Read FUNCTION and SEGMENT files given in settings.

        """
        for file_s in self.settings.get('Input', {}).get('file_segments', []):
            segments = read_data_file(file_s)
            if check_segment_consistency(segments):
                self.data['segments'].append(segments)
            else:
                raise ValueError(
                    f'Invalid segment file {file_s}')  # pragma: no cover

        for file_f in self.settings.get('Input', {}).get('file_functions', []):
            self.data['functions'].append(read_data_file(file_f))

        for file_m in self.settings.get('Input', {}).get('file_materials', []):
            self.data['materials'].append(file_m)

        for file_sub in self.settings.get('Input', {}).get('file_substrates', []):
            self.data['substrates'].append(file_sub)

    def check_data(self):
        """
        Checks for segment consistency.

        """
        for segment in self.data['segments']:
            check_segment_consistency(segment)

    def check_settings(self):
        """
        Checks for settings consistency.

        """
        for main_task in self.settings['Main']['tasks']:
            if main_task not in OPERATE_MAP:
                raise ValueError(f'Task {main_task} not supported')

        for main_cross_task in self.settings['Main']['cross_tasks']:
            if main_cross_task not in CROSS_OPERATE_MAP:
                raise ValueError(f'Cross-Task {main_cross_task} not supported')

    def execute(self):
        """
        Runs the task assigned to the read data.

        """
        results = {}
        for task, idx_task in zip(self.settings['Main'].get('tasks', []),
                                  self.settings['Main'].get('idx_tasks', [])):
            results[task] = []
            for idx in idx_task:
                data = [self.data[DATA_MAP[task][0]][idx],
                        self.data[DATA_MAP[task][1]][idx]]
                if task == 'build_hybrid':
                    builder_settings = self.settings.get('Builder', {})
                    results[task].append(OPERATE_MAP[task](data[0], data[1], **builder_settings))
                else:
                    results[task].append(OPERATE_MAP[task](*data))

        for task, idx_task in zip(self.settings['Main'].get('cross_tasks', []),
                                  self.settings['Main'].get('idx_cross_tasks', [])):
            results[task] = []
            for idx in idx_task:
                data = [self.data[CROSS_DATA_MAP[task]][idx[0]],
                        self.data[CROSS_DATA_MAP[task]][idx[1]]]
                results[task].append(CROSS_OPERATE_MAP[task](*data))

        return results

    @staticmethod
    def cheers():
        """
        If triggered, it is a good sign.

        """
        print('Simulation D-O-N-E !')
