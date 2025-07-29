import os
import reframe as rfm
import reframe.utility.sanity as sn

@rfm.simple_test
class OsuBandwidthPlacementTest(rfm.RunOnlyRegressionTest):
    descr = 'OSU Bandwidth Test for different process placements'

    placement = parameter(['same_core', 'same_numa', 'diff_numa', 'diff_node'])

    valid_systems = ['aion:batch', 'iris:batch']
    valid_prog_environs = ['foss-2023b']
    
    maintainers = ['jurmy']
    tags = {'performance', 'bandwidth', 'placement'}
    
    num_tasks = 2
    exclusive_access = True
    executable_opts = ['-m', '1048576:1048576', '-x', '100', '-i', '1000']

    @run_after('init')
    def set_dependencies(self):
        # This name must match the class name in your osu_build.py file
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
        self.descr = f'OSU Bandwidth Test (1MB) for {placement_desc[self.placement]}'
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
        build = self.getdep('OsuBuildSource')
        osu_binary_path = os.path.join(build.stagedir, 'install', 'libexec', 
                                       'osu-micro-benchmarks', 'mpi', 'pt2pt', 'osu_bw')
        self.executable = osu_binary_path

    @sanity_function
    def validate_output(self):
        return sn.assert_found(r'^1048576\s+\d+\.\d+', self.stdout)

    @performance_function('MB/s')
    def bandwidth(self):
        return sn.extractsingle(r'^1048576\s+(\S+)', self.stdout, 1, float)

    @run_after('performance')
    def set_reference_values(self):
        references = {
            'aion:batch': {
                'same_core': (14545.6, -0.1, 0.1, 'MB/s'),
                'same_numa': (12649.5, -0.1, 0.1, 'MB/s'),
                'diff_numa': (12664.8, -0.1, 0.1, 'MB/s'),
                'diff_node': (12323.0, -0.1, 0.1, 'MB/s')
            },
            'iris:batch': { 
                'same_core': (15000.0, -0.1, 0.1, 'MB/s'),
                'same_numa': (13000.0, -0.1, 0.1, 'MB/s'),
                'diff_numa': (12000.0, -0.1, 0.1, 'MB/s'),
                'diff_node': (8372.26, -0.1, 0.1, 'MB/s')  
            }
        }
        
        sys_part_name = self.current_partition.fullname
        self.reference = {sys_part_name: {'bandwidth': references[sys_part_name][self.placement]}}
