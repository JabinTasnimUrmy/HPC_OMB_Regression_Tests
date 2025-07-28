import os
import reframe as rfm
import reframe.utility.sanity as sn

@rfm.simple_test
class OsuLatencyPlacementTest(rfm.RunOnlyRegressionTest):
    descr = 'OSU Latency Test for different process placements'
    placement = parameter(['same_core', 'same_numa', 'diff_numa', 'diff_node'])
    valid_systems = ['aion:batch', 'iris:batch']
    valid_prog_environs = ['foss-2023b']
    maintainers = ['jurmy']
    tags = {'performance', 'latency', 'placement'}
    num_tasks = 2
    exclusive_access = True
    executable_opts = ['-m', '8192:8192', '-x', '100', '-i', '1000']

    @run_after('init')
    def set_dependencies(self):
        self.depends_on('OsuBuildSource')

    # In the setup phase, we ONLY configure things that do NOT need self.job
    @run_before('setup')
    def set_resources_by_placement(self):
        placement_desc = {
            'same_core': 'two processes on the same physical core',
            'same_numa': 'two processes on the same NUMA node',
            'diff_numa': 'two processes on different NUMA nodes (sockets)',
            'diff_node': 'two processes on different compute nodes'
        }
        self.descr = f'OSU Latency Test (8192B) for {placement_desc[self.placement]}'
        if self.placement == 'diff_node':
            self.num_nodes = 2
            self.num_tasks_per_node = 1
        else:
            self.num_nodes = 1
            self.num_tasks_per_node = 2

    # In the run phase, we can safely access self.job and the fixture
    @run_before('run')
    def set_executable_and_launcher_options(self):
        # Set launcher options now that self.job exists
        if self.placement == 'same_core':
            self.job.launcher.options = ['--cpu-bind=core', '--ntasks-per-core=2']
        elif self.placement == 'same_numa':
            self.job.launcher.options = ['--cpu-bind=cores']
        elif self.placement == 'diff_numa':
            self.job.launcher.options = ['--cpu-bind=sockets']

        # Set executable path from the dependency
        build_fixture = self.getdep('OsuBuildSource')
        benchmark_bin_path = os.path.join(build_fixture.stagedir, 'install', 'libexec', 
                                          'osu-micro-benchmarks', 'mpi', 'pt2pt')
        self.executable = os.path.join(benchmark_bin_path, 'osu_latency')

    @sanity_function
    def validate_output(self):
        return sn.assert_found(r'^8192\s+\d+\.\d+', self.stdout)

    @performance_function('us')
    def latency(self):
        return sn.extractsingle(r'^8192\s+(\S+)', self.stdout, 1, float)

    @run_after('performance')
    def set_reference_values(self):
        references = {
            'aion:batch': {
                'same_core': (0.59, -0.1, 0.3, 'us'),
                'same_numa': (2.3, -0.1, 0.2, 'us'),
                'diff_numa': (2.29, -0.1, 0.2, 'us'), 
                'diff_node': (4.03, -0.1, 0.2, 'us') 
            },
            'iris:batch': {
                'same_core': (6.72, -0.1, 0.2, 'us'), 
                'same_numa': (6.64, -0.1, 0.2, 'us'),
                'diff_numa': (6.53, -0.1, 0.2, 'us'), 
                'diff_node': (9.84, -0.1, 0.2, 'us')
            }
        }
        sys_part_name = self.current_partition.fullname
        self.reference = {sys_part_name: {'latency': references[sys_part_name][self.placement]}}
