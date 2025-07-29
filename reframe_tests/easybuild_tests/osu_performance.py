import os
import reframe as rfm
import reframe.utility.sanity as sn

_THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))

# =================================================================================
#  Part 1: The Build Fixture (This part is correct and unchanged)
# =================================================================================

@rfm.simple_test
class OsuBuildEasyBuild(rfm.CompileOnlyRegressionTest):
    name = 'OsuBuildEasyBuild_v7_2'
    descr = 'Builds OSU Micro-Benchmarks v7.2 with EasyBuild'
    valid_systems = ['*']
    valid_prog_environs = ['*']
    build_system = 'EasyBuild'
    time_limit = '15m'
    exclusive_access = True

    @run_before('compile')
    def set_easybuild_options(self):
        eb_file = 'osu-micro-benchmarks-7.2-foss-2023b.eb'
        source_eb_path = os.path.join(_THIS_FILE_DIR, '..', 'easyconfigs', eb_file)
        self.prebuild_cmds = [f'cp "{source_eb_path}" "{self.stagedir}"']
        self.build_system.easyconfigs = [eb_file]
        self.build_system.options = ['--detect-loaded-modules=warn']

    @sanity_function
    def validate_build(self):
        return sn.assert_found(r'== COMPLETED: Installation ended successfully', self.stdout)

    @property
    def generated_modules(self):
        return self.build_system.generated_modules

# =================================================================================
#  Part 2: The Unified Performance Test (With the final fix)
# =================================================================================

@rfm.simple_test
class OsuPerformanceTest(rfm.RunOnlyRegressionTest):
    '''Runs OSU Latency and Bandwidth tests for various placements.'''
    valid_systems = ['aion:batch', 'iris:batch']
    valid_prog_environs = ['foss-2023b']
    
    num_tasks = 2
    exclusive_access = True
    
    benchmark_info = parameter([
        ('latency', 'osu_latency', 8192, 'us'),
        ('bandwidth', 'osu_bw', 1048576, 'MB/s')
    ], fmt=lambda x: x[0])
    
    placement = parameter(['same_core', 'same_numa', 'diff_numa', 'diff_node'])
    osu_build = fixture(OsuBuildEasyBuild, scope='environment')

    @run_after('init')
    def setup_from_parameters(self):
        self.perf_name, self.executable, self.msg_size, self.perf_unit = self.benchmark_info
        self.executable_opts = ['-m', f'{self.msg_size}:{self.msg_size}', '-x', '100', '-i', '1000']
        
        # === THIS IS THE FIX ===
        # The perf_variables dictionary must be populated with objects created
        # by sn.make_performance_function. This fixes the TypeError.
        self.perf_variables = {
            self.perf_name: sn.make_performance_function(
                sn.extractsingle(rf'^{self.msg_size}\s+(\S+)', self.stdout, 1, float),
                unit=self.perf_unit
            )
        }
        
    @run_before('run')
    def set_environment_and_placement(self):
        self.modules = self.osu_build.generated_modules
        placement_desc = {
            'same_core': 'two processes on the same physical core',
            'same_numa': 'two processes on the same NUMA node',
            'diff_numa': 'two processes on different NUMA nodes (sockets)',
            'diff_node': 'two processes on different compute nodes'
        }
        self.descr = f'OSU {self.perf_name} test for {placement_desc[self.placement]}'
        
        if self.placement == 'diff_node':
            self.num_nodes = 2
            self.num_tasks_per_node = 1
        else:
            self.num_nodes = 1
            self.num_tasks_per_node = 2

        if self.placement == 'same_core':
            self.job.launcher.options = ['--cpu-bind=core', '--ntasks-per-core=2']
        elif self.placement == 'same_numa':
            self.job.launcher.options = ['--cpu-bind=cores']
        elif self.placement == 'diff_numa':
            self.job.launcher.options = ['--cpu-bind=sockets']

    @sanity_function
    def validate_output(self):
        return sn.assert_found(rf'^{self.msg_size}\s+\d+\.\d+', self.stdout)

    @run_after('performance')
    def set_reference_values(self):
        all_references = {
            'latency': {
                'aion:batch': {
                    'same_core': (2.3, -0.2, 0.2, 'us'), 'same_numa': (2.3, -0.2, 0.2, 'us'),
                    'diff_numa': (2.3, -0.2, 0.2, 'us'), 'diff_node': (3.9, -0.2, 0.2, 'us')
                },
                'iris:batch': {
                    'same_core': (6.72, -0.2, 0.2, 'us'), 'same_numa': (6.75, -0.2, 0.2, 'us'),
                    'diff_numa': (6.47, -0.2, 0.2, 'us'), 'diff_node': (9.80, -0.2, 0.2, 'us')
                }
            },
            'bandwidth': {
                'aion:batch': {
                    'same_core': (12000, -0.2, None, 'MB/s'), 'same_numa': (12000, -0.2, None, 'MB/s'),
                    'diff_numa': (12000, -0.2, None, 'MB/s'), 'diff_node': (12000, -0.2, None, 'MB/s')
                },
                'iris:batch': {
                    'same_core': (15000, -0.2, None, 'MB/s'), 'same_numa': (15000, -0.2, None, 'MB/s'),
                    'diff_numa': (15000, -0.2, None, 'MB/s'), 'diff_node': (8000, -0.2, None, 'MB/s')
                }
            }
        }
        
        sys_name = self.current_partition.fullname
        self.reference = {
            sys_name: {
                self.perf_name: all_references[self.perf_name][sys_name][self.placement]
            }
        }
