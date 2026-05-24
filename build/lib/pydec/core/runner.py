# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Contain the main class to link input to working functions.

"""
from pydec.inout.inout import read_data_file, parse_settings_file
from pydec.tools.tools import local_mean, check_segment_consistency
from pydec.tools.cross_tools import person, segment_overlap

DATA_MAP = {'local_mean': ['segments', 'functions']}
OPERATE_MAP = {'local_mean': local_mean}

CROSS_DATA_MAP = {'person': 'functions',
                  'overlap': 'segments'}
CROSS_OPERATE_MAP = {'person': person,
                     'overlap': segment_overlap}


class Geni:
    """
    Main class.

    """
    def __init__(self, input_file=None, description='DNA reads'):
        """
        Initialize.

        """
        self.description = description
        self.input_file = input_file
        self.settings = {}
        self.data = {'segments': [],
                     'functions': []}

    def read_settings(self):
        """
        Read settings file.

        """
        self.settings = parse_settings_file(self.input_file)

    def read_data_files(self):
        """
        Read FUNCTION and SEGMENT files given in settings.

        """
        for file_s in self.settings['Input']['file_segments']:
            segments = read_data_file(file_s)
            if check_segment_consistency(segments):
                self.data['segments'].append(segments)
            else:
                raise ValueError(
                    f'Invalid segment file {file_s}')  # pragma: no cover

        for file_f in self.settings['Input']['file_functions']:
            self.data['functions'].append(read_data_file(file_f))

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
        for task, idx_task in zip(self.settings['Main']['tasks'],
                                  self.settings['Main']['idx_tasks']):
            results[task] = []
            for idx in idx_task:
                data = [self.data[DATA_MAP[task][0]][idx],
                        self.data[DATA_MAP[task][1]][idx]]
                results[task].append(OPERATE_MAP[task](*data))

        for task, idx_task in zip(self.settings['Main']['cross_tasks'],
                                  self.settings['Main']['idx_cross_tasks']):
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
