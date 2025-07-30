import os
import reframe as rfm
# Import the base class from our common directory
from ..common.osu_performance_base import OsuPerformanceBase

@rfm.simple_test
class EessiOsuTest(OsuPerformanceBase):
    '''Runs OSU tests using the EESSI provided binaries.'''
    descr = 'OSU Performance Test (Source: EESSI)'
    tags = {'eessi'}
    
    
    # We stay inside the standard 'foss-2023b' environment.
    valid_prog_environs = ['foss-2023b']

    @run_before('run')
    def set_modules_from_eessi(self):
        # This prerun_cmds list is the correct way to initialize the
        # EESSI environment inside the job script.
        self.prerun_cmds = [
            'module load EESSI/2023.06',
            'module load OSU-Micro-Benchmarks/7.2-gompi-2023b'
        ]
        
