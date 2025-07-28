import reframe as rfm
import reframe.utility.sanity as sn

class OsuPerformanceBase(rfm.RunOnlyRegressionTest):
    '''Base class for OSU Latency and Bandwidth tests. NOT MEANT TO BE RUN DIRECTLY.'''
    valid_systems = ['aion:batch', 'iris:batch']
    
    num_tasks = 2
    exclusive_access = True
    
    benchmark_info = parameter([
        ('latency', 'osu_latency', 8192, 'us'),
        ('bandwidth', 'osu_bw', 1048576, 'MB/s')
    ], fmt=lambda x: x[0])
    
    placement = parameter(['same_core', 'same_numa', 'diff_numa', 'diff_node'])
    
    @run_after('init')
    def setup_from_parameters(self):
        self.perf_name, self.executable, self.msg_size, self.perf_unit = self.benchmark_info
        self.executable_opts = ['-m', f'{self.msg_size}:{self.msg_size}', '-x', '100', '-i', '1000']
        self.perf_variables = {
            self.perf_name: sn.make_performance_function(
                sn.extractsingle(rf'^{self.msg_size}\s+(\S+)', self.stdout, 1, float),
                unit=self.perf_unit
            )
        }
        
    @run_before('run')
    def set_placement(self):
        placement_desc = {
            'same_core': 'on the same core', 'same_numa': 'on the same NUMA node',
            'diff_numa': 'on different NUMA nodes', 'diff_node': 'on different compute nodes'
        }
        self.descr += f' ({placement_desc[self.placement]})'
        if self.placement == 'diff_node':
            self.num_nodes = 2
            self.num_tasks_per_node = 1
        else:
            self.num_nodes = 1
            self.num_tasks_per_node = 2

        if self.placement == 'same_core': self.job.launcher.options = ['--cpu-bind=core', '--ntasks-per-core=2']
        elif self.placement == 'same_numa': self.job.launcher.options = ['--cpu-bind=cores']
        elif self.placement == 'diff_numa': self.job.launcher.options = ['--cpu-bind=sockets']

    @sanity_function
    def validate_output(self):
        return sn.assert_found(rf'^{self.msg_size}\s+\d+\.\d+', self.stdout)

    @run_after('performance')
    def set_reference_values(self):
        all_refs = {
            'latency': {'aion:batch': (3.9, -0.2, 0.2, 'us'), 'iris:batch': (9.8, -0.2, 0.2, 'us')},
            'bandwidth': {'aion:batch': (12000, -0.2, None, 'MB/s'), 'iris:batch': (8000, -0.2, None, 'MB/s')}
        }
        self.reference = { self.current_partition.fullname: { self.perf_name: all_refs[self.perf_name][self.current_partition.fullname] } }
